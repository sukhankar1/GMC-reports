# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_columns(filters):
	view_type = filters.get("view_type") or "Summary"

	if view_type == "Detail":
		# 24 columns matching Image 2
		return [
			{"fieldname": "department", "label": _("Department"), "fieldtype": "Data", "width": 150},
			{"fieldname": "category_name", "label": _("Category Name"), "fieldtype": "Data", "width": 140},
			{"fieldname": "parent_category", "label": _("Parent Category"), "fieldtype": "Data", "width": 140},
			{"fieldname": "sub_category_1", "label": _("Sub Category 1"), "fieldtype": "Data", "width": 120},
			{"fieldname": "sub_category_2", "label": _("Sub Category 2"), "fieldtype": "Data", "width": 120},
			{"fieldname": "sub_category_3", "label": _("Sub Category 3"), "fieldtype": "Data", "width": 120},
			{"fieldname": "sub_category_4", "label": _("Sub Category 4"), "fieldtype": "Data", "width": 120},
			{"fieldname": "consignment_item", "label": _("Consignment Item"), "fieldtype": "Data", "width": 120},
			{"fieldname": "generic_name", "label": _("Generic Name"), "fieldtype": "Data", "width": 150},
			{"fieldname": "item_code", "label": _("Item Code"), "fieldtype": "Link", "options": "Item", "width": 120},
			{"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data", "width": 200},
			{"fieldname": "unit", "label": _("Unit"), "fieldtype": "Data", "width": 80},
			{"fieldname": "critical_category", "label": _("Critical Category"), "fieldtype": "Data", "width": 130},
			{"fieldname": "batch_no", "label": _("Batch No."), "fieldtype": "Data", "width": 130},
			{"fieldname": "bin_location", "label": _("Bin Location"), "fieldtype": "Data", "width": 110},
			{"fieldname": "expiry_date", "label": _("Expiry Date"), "fieldtype": "Date", "width": 100},
			{"fieldname": "supplier_name", "label": _("Supplier Name"), "fieldtype": "Data", "width": 180},
			{"fieldname": "grn_no", "label": _("GRN No."), "fieldtype": "Data", "width": 130},
			{"fieldname": "grn_date", "label": _("GRN Date"), "fieldtype": "Date", "width": 100},
			{"fieldname": "stock_quantity", "label": _("Stock Quantity"), "fieldtype": "Float", "precision": 2, "width": 110},
			{"fieldname": "mrp", "label": _("MRP"), "fieldtype": "Currency", "width": 90},
			{"fieldname": "mrp_value", "label": _("MRP Value"), "fieldtype": "Currency", "width": 110},
			{"fieldname": "epr", "label": _("EPR"), "fieldtype": "Currency", "width": 100},
			{"fieldname": "amount", "label": _("Amount"), "fieldtype": "Currency", "width": 120},
		]

	# Summary View (Image 4 from earlier batch - 9 columns)
	return [
		{"fieldname": "dept_name", "label": _("Dept Name"), "fieldtype": "Data", "width": 160},
		{"fieldname": "category_name", "label": _("Category Name"), "fieldtype": "Data", "width": 160},
		{"fieldname": "item_code", "label": _("Itemcode"), "fieldtype": "Link", "options": "Item", "width": 120},
		{"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data", "width": 200},
		{"fieldname": "unit", "label": _("Unit"), "fieldtype": "Data", "width": 80},
		{"fieldname": "bin_location", "label": _("Bin Location"), "fieldtype": "Data", "width": 110},
		{"fieldname": "stock_quantity", "label": _("Stock Quantity"), "fieldtype": "Float", "precision": 2, "width": 110},
		{"fieldname": "unit_rate", "label": _("Unit Rate"), "fieldtype": "Currency", "width": 100},
		{"fieldname": "amount", "label": _("Amount"), "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	as_on_date = filters.get("as_on_date")
	hospital_name = filters.get("hospital_name")
	item_filter = filters.get("item_name")
	department = filters.get("department")
	view_type = filters.get("view_type") or "Summary"
	category = filters.get("category")
	sub_category = filters.get("sub_category")
	substitute_item = filters.get("substitute_item")
	status = filters.get("status")
	order_by = filters.get("order_by") or "Item Name"
	bin_location = filters.get("bin_location")
	show_zero_stock = filters.get("show_zero_stock")

	# Build Item Conditions
	item_conditions = []
	item_params = {}

	if item_filter:
		item_conditions.append("(i.name = %(item_filter)s OR i.item_name LIKE %(item_like)s)")
		item_params["item_filter"] = item_filter
		item_params["item_like"] = f"%{item_filter}%"

	if category:
		item_conditions.append("(i.custom_category = %(category)s OR i.item_group = %(category)s)")
		item_params["category"] = category

	if sub_category:
		item_conditions.append("(i.item_group = %(sub_category)s)")
		item_params["sub_category"] = sub_category

	if substitute_item:
		item_conditions.append("(i.custom_subtitute_group = %(substitute_item)s)")
		item_params["substitute_item"] = substitute_item

	if status == "Active":
		item_conditions.append("i.disabled = 0")
	elif status == "Inactive":
		item_conditions.append("i.disabled = 1")

	item_cond_sql = f"WHERE {' AND '.join(item_conditions)}" if item_conditions else ""

	# Fetch items
	items = frappe.db.sql(
		f"""
		SELECT
			i.name AS item_code,
			i.item_name,
			i.custom_category,
			i.item_group,
			i.stock_uom,
			i.disabled,
			i.custom_generic_name,
			i.custom_consignment_items,
			i.custom_classification,
			i.valuation_rate,
			i.custom_mrp,
			i.custom_quoted_price
		FROM `tabItem` i
		{item_cond_sql}
	""",
		item_params,
		as_dict=True,
	)

	item_map = {i.item_code: i for i in items}
	if not item_map:
		return []

	# Fetch Warehouses
	wh_conditions = []
	wh_params = {}
	if hospital_name:
		wh_conditions.append("(w.company = %(hospital_name)s OR w.company IS NULL)")
		wh_params["hospital_name"] = hospital_name
	if department:
		wh_conditions.append("(w.custom_department = %(department)s OR w.name = %(department)s)")
		wh_params["department"] = department

	wh_cond_sql = f"WHERE {' AND '.join(wh_conditions)}" if wh_conditions else ""
	warehouses = frappe.db.sql(
		f"""
		SELECT name, warehouse_name, custom_department, company
		FROM `tabWarehouse` w
		{wh_cond_sql}
	""",
		wh_params,
		as_dict=True,
	)

	wh_map = {w.name: w for w in warehouses}
	if department and not wh_map:
		wh_map[department] = frappe._dict(
			{"name": department, "custom_department": department, "warehouse_name": department}
		)

	# Fetch Bin locations
	bin_loc_map = {}
	bin_loc_records = frappe.db.sql(
		"""
		SELECT sed.item_code, sed.custom_bin_location
		FROM `tabStock Entry Detail` sed
		WHERE sed.custom_bin_location IS NOT NULL AND sed.custom_bin_location != ''
		ORDER BY sed.creation DESC
	""",
		as_dict=True,
	)
	for bl in bin_loc_records:
		if bl.item_code not in bin_loc_map:
			bin_loc_map[bl.item_code] = bl.custom_bin_location

	# Suppliers mapping
	supp_map = {}
	def_supps = frappe.db.sql(
		"SELECT parent AS item_code, default_supplier FROM `tabItem Default` WHERE default_supplier IS NOT NULL AND default_supplier != ''",
		as_dict=True,
	)
	for ds in def_supps:
		supp_map[ds.item_code] = ds.default_supplier

	# Latest PR info (Supplier, GRN No, GRN Date, Rate, Batch)
	pr_info_map = {}
	pr_records = frappe.db.sql(
		"""
		SELECT pri.item_code, pri.batch_no, pr.name AS grn_no, pr.posting_date AS grn_date, pr.supplier, pri.rate, pri.custom_mrp
		FROM `tabPurchase Receipt Item` pri
		JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
		WHERE pr.docstatus = 1
		ORDER BY pr.posting_date DESC
	""",
		as_dict=True,
	)
	for pr in pr_records:
		if pr.item_code not in supp_map and pr.supplier:
			supp_map[pr.item_code] = pr.supplier
		if (pr.item_code, pr.batch_no) not in pr_info_map:
			pr_info_map[(pr.item_code, pr.batch_no)] = pr
		if (pr.item_code, None) not in pr_info_map:
			pr_info_map[(pr.item_code, None)] = pr

	# Batch info
	batches = frappe.db.sql("SELECT name, item, expiry_date, custom_mrp FROM `tabBatch`", as_dict=True)
	batch_map = {b.name: b for b in batches}

	item_codes = tuple(item_map.keys())
	wh_names = tuple(wh_map.keys()) if wh_map else tuple()

	if view_type == "Detail":
		# Detail View query from Stock Ledger Entry / Bin / Batch
		sle_conds = ["sle.item_code IN %(item_codes)s", "sle.is_cancelled = 0"]
		sle_params = {"item_codes": item_codes}
		if wh_names:
			sle_conds.append("sle.warehouse IN %(wh_names)s")
			sle_params["wh_names"] = wh_names

		sles = frappe.db.sql(
			f"""
			SELECT
				sle.item_code,
				sle.warehouse,
				sle.batch_no,
				SUM(sle.actual_qty) AS stock_qty,
				sle.valuation_rate
			FROM `tabStock Ledger Entry` sle
			WHERE {' AND '.join(sle_conds)}
			GROUP BY sle.item_code, sle.warehouse, sle.batch_no
		""",
			sle_params,
			as_dict=True,
		)

		data = []
		for row in sles:
			qty = flt(row.stock_qty)
			if not show_zero_stock and qty <= 0:
				continue

			item = item_map.get(row.item_code)
			if not item:
				continue

			wh = wh_map.get(row.warehouse)
			dept = (
				wh.custom_department
				if wh and wh.custom_department
				else (wh.warehouse_name if wh else row.warehouse)
			)
			cat = item.custom_category or item.item_group or ""
			b_info = batch_map.get(row.batch_no)
			pr_info = pr_info_map.get((row.item_code, row.batch_no)) or pr_info_map.get((row.item_code, None))

			mrp = flt((b_info.custom_mrp if b_info else 0.0) or (pr_info.custom_mrp if pr_info else 0.0) or item.custom_mrp or 0.0)
			epr = flt((pr_info.rate if pr_info else 0.0) or item.custom_quoted_price or row.valuation_rate or item.valuation_rate or 0.0)
			mrp_val = qty * mrp
			amt = qty * epr
			bin_loc = bin_loc_map.get(row.item_code, "")
			if bin_location and bin_loc != bin_location:
				continue

			data.append(
				{
					"department": dept,
					"category_name": cat,
					"parent_category": cat,
					"sub_category_1": item.item_group or "",
					"sub_category_2": "",
					"sub_category_3": "",
					"sub_category_4": "",
					"consignment_item": "Yes" if item.custom_consignment_items else "No",
					"generic_name": item.custom_generic_name or "",
					"item_code": row.item_code,
					"item_name": item.item_name or row.item_code,
					"unit": item.stock_uom or "NOS",
					"critical_category": item.custom_classification or "",
					"batch_no": row.batch_no or "",
					"bin_location": bin_loc,
					"expiry_date": b_info.expiry_date if b_info else None,
					"supplier_name": (pr_info.supplier if pr_info else "") or supp_map.get(row.item_code, ""),
					"grn_no": pr_info.grn_no if pr_info else "",
					"grn_date": pr_info.grn_date if pr_info else None,
					"stock_quantity": qty,
					"mrp": mrp,
					"mrp_value": mrp_val,
					"epr": epr,
					"amount": amt,
				}
			)

	else:
		# Summary View
		bin_conds = ["b.item_code IN %(item_codes)s"]
		b_params = {"item_codes": item_codes}
		if wh_names:
			bin_conds.append("b.warehouse IN %(wh_names)s")
			b_params["wh_names"] = wh_names

		bins = frappe.db.sql(
			f"""
			SELECT
				b.item_code,
				b.warehouse,
				b.actual_qty,
				b.valuation_rate,
				b.stock_uom
			FROM `tabBin` b
			WHERE {' AND '.join(bin_conds)}
		""",
			b_params,
			as_dict=True,
		)

		data = []
		for b in bins:
			qty = flt(b.actual_qty)
			if not show_zero_stock and qty <= 0:
				continue

			item = item_map.get(b.item_code)
			if not item:
				continue

			wh = wh_map.get(b.warehouse)
			dept = (
				wh.custom_department
				if wh and wh.custom_department
				else (wh.warehouse_name if wh else b.warehouse)
			)
			cat = item.custom_category or item.item_group or ""
			bin_loc = bin_loc_map.get(b.item_code, "")
			if bin_location and bin_loc != bin_location:
				continue

			rate = flt(b.valuation_rate)
			amt = qty * rate

			data.append(
				{
					"dept_name": dept,
					"category_name": cat,
					"item_code": b.item_code,
					"item_name": item.item_name or b.item_code,
					"unit": item.stock_uom or b.stock_uom or "NOS",
					"bin_location": bin_loc,
					"stock_quantity": qty,
					"unit_rate": rate,
					"amount": amt,
				}
			)

	# Order By
	if order_by == "Item Code":
		data.sort(key=lambda x: x.get("item_code", ""))
	elif order_by == "Stock Quantity":
		data.sort(key=lambda x: x.get("stock_quantity", 0.0), reverse=True)
	else:
		data.sort(key=lambda x: x.get("item_name", ""))

	return data


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
