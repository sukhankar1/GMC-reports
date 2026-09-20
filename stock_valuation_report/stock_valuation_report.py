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
		return [
			{"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data", "width": 200},
			{"fieldname": "item_code", "label": _("Item Code"), "fieldtype": "Link", "options": "Item", "width": 120},
			{"fieldname": "department", "label": _("Department"), "fieldtype": "Data", "width": 140},
			{"fieldname": "category", "label": _("Category"), "fieldtype": "Data", "width": 140},
			{"fieldname": "supplier_name", "label": _("Supplier Name"), "fieldtype": "Data", "width": 180},
			{"fieldname": "batch_no", "label": _("Batch No."), "fieldtype": "Data", "width": 130},
			{"fieldname": "expiry_date", "label": _("Expiry Date"), "fieldtype": "Date", "width": 100},
			{"fieldname": "conv_factor", "label": _("Conv. Factor"), "fieldtype": "Float", "precision": 2, "width": 90},
			{"fieldname": "unit_rate_value", "label": _("Unit Rate Value"), "fieldtype": "Currency", "width": 110},
			{"fieldname": "mrp", "label": _("MRP"), "fieldtype": "Currency", "width": 90},
			{"fieldname": "opening_qty", "label": _("Opening Balance Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
			{"fieldname": "opening_amt", "label": _("Opening Balance Amt."), "fieldtype": "Currency", "width": 110},
			{"fieldname": "purchase_qty", "label": _("Purchase Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
			{"fieldname": "purchase_amt", "label": _("Purchase Amt."), "fieldtype": "Currency", "width": 110},
			{"fieldname": "purchase_return_qty", "label": _("Purchase Return Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
			{"fieldname": "purchase_return_amt", "label": _("Purchase Return Amt."), "fieldtype": "Currency", "width": 110},
			{"fieldname": "sales_qty", "label": _("Sales Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
			{"fieldname": "sales_amt", "label": _("Sales Amt."), "fieldtype": "Currency", "width": 110},
			{"fieldname": "sale_return_qty", "label": _("Sale Return Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
			{"fieldname": "sale_return_amt", "label": _("Sale Return Amt."), "fieldtype": "Currency", "width": 110},
			{"fieldname": "dept_in_qty", "label": _("Department In Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
			{"fieldname": "dept_in_amt", "label": _("Department In Amt."), "fieldtype": "Currency", "width": 110},
			{"fieldname": "dept_out_qty", "label": _("Department Out Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
			{"fieldname": "dept_out_amt", "label": _("Department Out Amt."), "fieldtype": "Currency", "width": 110},
			{"fieldname": "closing_qty", "label": _("Closing Balance Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
			{"fieldname": "closing_amt", "label": _("Closing Balance Amt."), "fieldtype": "Currency", "width": 110},
		]

	# Summary View (Image 2)
	return [
		{"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data", "width": 200},
		{"fieldname": "item_code", "label": _("Item Code"), "fieldtype": "Link", "options": "Item", "width": 120},
		{"fieldname": "department", "label": _("Department"), "fieldtype": "Data", "width": 140},
		{"fieldname": "category", "label": _("Category"), "fieldtype": "Data", "width": 140},
		{"fieldname": "supplier_name", "label": _("Supplier Name"), "fieldtype": "Data", "width": 180},
		{"fieldname": "unit_rate_value", "label": _("Unit Rate Value"), "fieldtype": "Currency", "width": 110},
		{"fieldname": "mrp", "label": _("MRP"), "fieldtype": "Currency", "width": 90},
		{"fieldname": "opening_qty", "label": _("Opening Balance Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "opening_amt", "label": _("Opening Balance Amt."), "fieldtype": "Currency", "width": 110},
		{"fieldname": "purchase_qty", "label": _("Purchase Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "purchase_amt", "label": _("Purchase Amt."), "fieldtype": "Currency", "width": 110},
		{"fieldname": "purchase_return_qty", "label": _("Purchase Return Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "purchase_return_amt", "label": _("Purchase Return Amt."), "fieldtype": "Currency", "width": 110},
		{"fieldname": "sales_qty", "label": _("Sales Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "sales_amt", "label": _("Sales Amt."), "fieldtype": "Currency", "width": 110},
		{"fieldname": "sale_return_qty", "label": _("Sale Return Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "sale_return_amt", "label": _("Sale Return Amt."), "fieldtype": "Currency", "width": 110},
		{"fieldname": "dept_in_qty", "label": _("Department In Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "dept_in_amt", "label": _("Department In Amt."), "fieldtype": "Currency", "width": 110},
		{"fieldname": "dept_out_qty", "label": _("Department Out Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "dept_out_amt", "label": _("Department Out Amt."), "fieldtype": "Currency", "width": 110},
		{"fieldname": "closing_qty", "label": _("Closing Balance Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "closing_amt", "label": _("Closing Balance Amt."), "fieldtype": "Currency", "width": 110},
	]


def get_data(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	department = filters.get("department")
	item_filter = filters.get("item_name")
	valuation = filters.get("valuation") or "Unit Purchase Rate"
	view_type = filters.get("view_type") or "Summary"
	therapeutic_group = filters.get("therapeutic_group")
	therapeutic_sub_group = filters.get("therapeutic_sub_group")
	status = filters.get("status")
	classification = filters.get("classification")

	# Warehouse mapping
	wh_records = frappe.db.sql("SELECT name, warehouse_name, custom_department FROM `tabWarehouse`", as_dict=True)
	wh_map = {w.name: (w.custom_department or w.warehouse_name or w.name) for w in wh_records}

	# Items filter
	item_conds = []
	item_params = {}
	if item_filter:
		item_conds.append("(i.name = %(item_filter)s OR i.item_name LIKE %(item_like)s)")
		item_params["item_filter"] = item_filter
		item_params["item_like"] = f"%{item_filter}%"

	if therapeutic_group:
		item_conds.append("i.item_group = %(therapeutic_group)s")
		item_params["therapeutic_group"] = therapeutic_group

	if therapeutic_sub_group:
		item_conds.append("i.custom_subtitute_group = %(therapeutic_sub_group)s")
		item_params["therapeutic_sub_group"] = therapeutic_sub_group

	if classification:
		item_conds.append("i.custom_classification = %(classification)s")
		item_params["classification"] = classification

	if status == "Active":
		item_conds.append("i.disabled = 0")
	elif status == "Inactive":
		item_conds.append("i.disabled = 1")

	item_cond_sql = f"WHERE {' AND '.join(item_conds)}" if item_conds else ""
	items = frappe.db.sql(
		f"""
		SELECT
			i.name AS item_code,
			i.item_name,
			i.custom_category,
			i.item_group,
			i.stock_uom,
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

	# Default Suppliers
	suppliers = frappe.db.sql(
		"""
		SELECT parent AS item_code, default_supplier
		FROM `tabItem Default`
		WHERE default_supplier IS NOT NULL AND default_supplier != ''
	""",
		as_dict=True,
	)
	supp_map = {s.item_code: s.default_supplier for s in suppliers}

	# Latest PR suppliers & Purchase Rates
	latest_prs = frappe.db.sql(
		"""
		SELECT pri.item_code, pr.supplier, pri.rate, pri.base_rate, pri.custom_mrp
		FROM `tabPurchase Receipt Item` pri
		JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
		WHERE pr.docstatus = 1
		ORDER BY pr.posting_date DESC
	""",
		as_dict=True,
	)
	last_pur_rate = {}
	for lp in latest_prs:
		if lp.item_code not in supp_map and lp.supplier:
			supp_map[lp.item_code] = lp.supplier
		if lp.item_code not in last_pur_rate:
			last_pur_rate[lp.item_code] = flt(lp.rate or lp.base_rate)

	# Batch info
	batch_records = frappe.db.sql("SELECT name, expiry_date, custom_mrp FROM `tabBatch`", as_dict=True)
	batch_map = {b.name: b for b in batch_records}

	# Query Stock Ledger Entries for movements
	sle_conds = ["sle.item_code IN %(item_codes)s", "sle.is_cancelled = 0"]
	sle_params = {"item_codes": tuple(item_map.keys())}

	sles = frappe.db.sql(
		f"""
		SELECT
			sle.item_code,
			sle.warehouse,
			sle.batch_no,
			sle.actual_qty,
			sle.valuation_rate,
			sle.posting_date,
			sle.voucher_type,
			sle.voucher_no
		FROM `tabStock Ledger Entry` sle
		WHERE {' AND '.join(sle_conds)}
		ORDER BY sle.posting_date ASC, sle.posting_time ASC, sle.creation ASC
	""",
		sle_params,
		as_dict=True,
	)

	# Aggregate movements per item (or item + batch)
	# Key: (item_code, department) for Summary or (item_code, batch_no, department) for Detail
	groups = {}

	for sle in sles:
		item_code = sle.item_code
		wh = sle.warehouse
		dept = wh_map.get(wh, wh)

		if department and dept != department and wh != department:
			continue

		batch_no = sle.batch_no or ""
		key = (item_code, dept) if view_type == "Summary" else (item_code, batch_no, dept)

		if key not in groups:
			groups[key] = {
				"item_code": item_code,
				"dept": dept,
				"batch_no": batch_no,
				"opening_qty": 0.0,
				"purchase_qty": 0.0,
				"purchase_return_qty": 0.0,
				"sales_qty": 0.0,
				"sale_return_qty": 0.0,
				"dept_in_qty": 0.0,
				"dept_out_qty": 0.0,
				"closing_qty": 0.0,
				"val_rate": flt(sle.valuation_rate),
			}

		qty = flt(sle.actual_qty)
		post_date = str(sle.posting_date)
		v_type = sle.voucher_type or ""

		if post_date < str(from_date):
			groups[key]["opening_qty"] += qty
		elif post_date <= str(to_date):
			if v_type == "Purchase Receipt" or v_type == "Purchase Invoice":
				if qty > 0:
					groups[key]["purchase_qty"] += qty
				else:
					groups[key]["purchase_return_qty"] += abs(qty)
			elif v_type == "Delivery Note" or v_type == "Sales Invoice":
				if qty < 0:
					groups[key]["sales_qty"] += abs(qty)
				else:
					groups[key]["sale_return_qty"] += qty
			elif v_type == "Stock Entry":
				if qty > 0:
					groups[key]["dept_in_qty"] += qty
				else:
					groups[key]["dept_out_qty"] += abs(qty)
			else:
				if qty > 0:
					groups[key]["dept_in_qty"] += qty
				else:
					groups[key]["dept_out_qty"] += abs(qty)

		if post_date <= str(to_date):
			groups[key]["closing_qty"] += qty
			if flt(sle.valuation_rate) > 0:
				groups[key]["val_rate"] = flt(sle.valuation_rate)

	data = []
	for key, g in groups.items():
		item_code = g["item_code"]
		item = item_map.get(item_code)
		if not item:
			continue

		b_info = batch_map.get(g["batch_no"]) if g["batch_no"] else None
		mrp = flt((b_info.custom_mrp if b_info else 0.0) or item.custom_mrp or 0.0)
		pur_rate = flt(last_pur_rate.get(item_code, 0.0) or item.custom_quoted_price or item.valuation_rate or 0.0)
		val_rate_sys = flt(g["val_rate"] or item.valuation_rate or pur_rate)

		if valuation == "MRP":
			unit_rate = mrp or pur_rate
		elif valuation == "Valuation Rate":
			unit_rate = val_rate_sys
		else:  # Unit Purchase Rate
			unit_rate = pur_rate or val_rate_sys

		op_qty = g["opening_qty"]
		op_amt = op_qty * unit_rate

		p_qty = g["purchase_qty"]
		p_amt = p_qty * unit_rate

		pr_qty = g["purchase_return_qty"]
		pr_amt = pr_qty * unit_rate

		s_qty = g["sales_qty"]
		s_amt = s_qty * unit_rate

		sr_qty = g["sale_return_qty"]
		sr_amt = sr_qty * unit_rate

		din_qty = g["dept_in_qty"]
		din_amt = din_qty * unit_rate

		dout_qty = g["dept_out_qty"]
		dout_amt = dout_qty * unit_rate

		cl_qty = g["closing_qty"]
		cl_amt = cl_qty * unit_rate

		# Skip rows with all zero quantities
		if (
			op_qty == 0
			and p_qty == 0
			and pr_qty == 0
			and s_qty == 0
			and sr_qty == 0
			and din_qty == 0
			and dout_qty == 0
			and cl_qty == 0
		):
			continue

		row = {
			"item_name": item.item_name or item_code,
			"item_code": item_code,
			"department": g["dept"],
			"category": item.custom_category or item.item_group or "",
			"supplier_name": supp_map.get(item_code, ""),
			"unit_rate_value": unit_rate,
			"mrp": mrp,
			"opening_qty": op_qty,
			"opening_amt": op_amt,
			"purchase_qty": p_qty,
			"purchase_amt": p_amt,
			"purchase_return_qty": pr_qty,
			"purchase_return_amt": pr_amt,
			"sales_qty": s_qty,
			"sales_amt": s_amt,
			"sale_return_qty": sr_qty,
			"sale_return_amt": sr_amt,
			"dept_in_qty": din_qty,
			"dept_in_amt": din_amt,
			"dept_out_qty": dout_qty,
			"dept_out_amt": dout_amt,
			"closing_qty": cl_qty,
			"closing_amt": cl_amt,
		}

		if view_type == "Detail":
			row["batch_no"] = g["batch_no"]
			row["expiry_date"] = b_info.expiry_date if b_info else None
			row["conv_factor"] = 1.0

		data.append(row)

	# Sort by Item Name
	data.sort(key=lambda x: x.get("item_name", ""))

	return data


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
