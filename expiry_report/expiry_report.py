# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "item_code", "label": _("Item Code"), "fieldtype": "Link", "options": "Item", "width": 120},
		{"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data", "width": 200},
		{"fieldname": "parent_category", "label": _("Parent Category"), "fieldtype": "Data", "width": 140},
		{"fieldname": "batch_no", "label": _("Batch No."), "fieldtype": "Data", "width": 130},
		{"fieldname": "department", "label": _("Department"), "fieldtype": "Data", "width": 150},
		{"fieldname": "exp_date", "label": _("Exp. Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "recommended_dr_dept", "label": _("Recommended DR./ Dept."), "fieldtype": "Data", "width": 180},
		{"fieldname": "supplier_name", "label": _("Supplier Name"), "fieldtype": "Data", "width": 180},
		{"fieldname": "grn_no", "label": _("GRN No."), "fieldtype": "Data", "width": 130},
		{"fieldname": "critical_category", "label": _("Critical Category"), "fieldtype": "Data", "width": 130},
		{"fieldname": "grn_date", "label": _("GRN Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "basic_rate", "label": _("Basic Rate"), "fieldtype": "Currency", "width": 100},
		{"fieldname": "concession", "label": _("Concession"), "fieldtype": "Currency", "width": 100},
		{"fieldname": "epr", "label": _("EPR"), "fieldtype": "Currency", "width": 100},
		{"fieldname": "mrp", "label": _("MRP"), "fieldtype": "Currency", "width": 90},
		{"fieldname": "quantity", "label": _("Quantity"), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "pur_rate", "label": _("Pur. Rate"), "fieldtype": "Currency", "width": 100},
		{"fieldname": "amount", "label": _("Amount"), "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	item_filter = filters.get("item_name")
	supplier_filter = filters.get("supplier")
	department_filter = filters.get("department")

	# Fetch Warehouse mapping
	wh_records = frappe.db.sql("SELECT name, warehouse_name, custom_department FROM `tabWarehouse`", as_dict=True)
	wh_map = {w.name: (w.custom_department or w.warehouse_name or w.name) for w in wh_records}

	# Items mapping
	item_conds = []
	item_params = {}
	if item_filter:
		item_conds.append("(i.name = %(item_filter)s OR i.item_name LIKE %(item_like)s)")
		item_params["item_filter"] = item_filter
		item_params["item_like"] = f"%{item_filter}%"

	item_cond_sql = f"WHERE {' AND '.join(item_conds)}" if item_conds else ""
	items = frappe.db.sql(
		f"""
		SELECT
			i.name AS item_code,
			i.item_name,
			i.custom_category,
			i.item_group,
			i.custom_recommended_dr,
			i.custom_recommended_department,
			i.custom_classification,
			i.custom_mrp,
			i.custom_quoted_price,
			i.valuation_rate
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
	def_supps = frappe.db.sql(
		"SELECT parent AS item_code, default_supplier FROM `tabItem Default` WHERE default_supplier IS NOT NULL AND default_supplier != ''",
		as_dict=True,
	)
	supp_map = {ds.item_code: ds.default_supplier for ds in def_supps}

	# Purchase Receipt info (GRN No, GRN Date, Supplier, Rate, MRP, Concession)
	pr_info_map = {}
	pr_records = frappe.db.sql(
		"""
		SELECT
			pri.item_code,
			pri.batch_no,
			pr.name AS grn_no,
			pr.posting_date AS grn_date,
			pr.supplier,
			pri.rate,
			pri.base_rate,
			pri.custom_mrp,
			pri.discount_amount,
			pri.discount_percentage
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

	# Batch records expiring within date range
	batch_conds = ["b.expiry_date BETWEEN %(from_date)s AND %(to_date)s"]
	batch_params = {"from_date": from_date, "to_date": to_date}
	batches = frappe.db.sql(
		f"""
		SELECT b.name AS batch_no, b.item AS item_code, b.expiry_date, b.custom_mrp, b.supplier, b.batch_qty
		FROM `tabBatch` b
		WHERE {' AND '.join(batch_conds)}
	""",
		batch_params,
		as_dict=True,
	)

	data = []
	for b_info in batches:
		item_code = b_info.item_code
		item = item_map.get(item_code)
		if not item:
			continue

		pr_info = pr_info_map.get((item_code, b_info.batch_no)) or pr_info_map.get((item_code, None))
		supp_name = (b_info.supplier if b_info else "") or (pr_info.supplier if pr_info else "") or supp_map.get(item_code, "")

		if supplier_filter and supp_name != supplier_filter:
			continue

		dept = department_filter or ""
		qty = flt(b_info.batch_qty)
		rec_dr_dept = item.custom_recommended_dr or item.custom_recommended_department or ""
		cat = item.custom_category or item.item_group or ""

		basic_rate = flt((pr_info.base_rate if pr_info else 0.0) or (pr_info.rate if pr_info else 0.0) or item.custom_quoted_price or item.valuation_rate or 0.0)
		concession = flt(pr_info.discount_amount if pr_info else 0.0)
		epr = flt((pr_info.rate if pr_info else 0.0) or basic_rate)
		pur_rate = epr or basic_rate
		mrp = flt((b_info.custom_mrp if b_info else 0.0) or (pr_info.custom_mrp if pr_info else 0.0) or item.custom_mrp or 0.0)
		amt = qty * pur_rate

		data.append(
			{
				"item_code": item_code,
				"item_name": item.item_name or item_code,
				"parent_category": cat,
				"batch_no": b_info.batch_no or "",
				"department": dept,
				"exp_date": b_info.expiry_date,
				"recommended_dr_dept": rec_dr_dept,
				"supplier_name": supp_name,
				"grn_no": pr_info.grn_no if pr_info else "",
				"critical_category": item.custom_classification or "",
				"grn_date": pr_info.grn_date if pr_info else None,
				"basic_rate": basic_rate,
				"concession": concession,
				"epr": epr,
				"mrp": mrp,
				"quantity": qty,
				"pur_rate": pur_rate,
				"amount": amt,
			}
		)

	# Sort by Exp. Date ASC
	data.sort(key=lambda x: str(x.get("exp_date") or ""))

	return data


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
