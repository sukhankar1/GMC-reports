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
		{"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 110},
		{"fieldname": "voucher_name", "label": _("Voucher Name"), "fieldtype": "Data", "width": 140},
		{"fieldname": "voucher_no", "label": _("Voucher No."), "fieldtype": "Data", "width": 130},
		{"fieldname": "from_department", "label": _("From Department"), "fieldtype": "Data", "width": 150},
		{"fieldname": "to_department", "label": _("To Department"), "fieldtype": "Data", "width": 150},
		{"fieldname": "unit", "label": _("Unit"), "fieldtype": "Data", "width": 80},
		{"fieldname": "batch_no", "label": _("Batch No."), "fieldtype": "Data", "width": 130},
		{"fieldname": "expiry_date", "label": _("Expiry Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "rack", "label": _("Rack"), "fieldtype": "Data", "width": 100},
		{"fieldname": "shelf", "label": _("Shelf"), "fieldtype": "Data", "width": 100},
		{"fieldname": "conversion_factor", "label": _("Conversion Factor"), "fieldtype": "Float", "precision": 2, "width": 100},
		{"fieldname": "mrp", "label": _("MRP"), "fieldtype": "Currency", "width": 90},
		{"fieldname": "in_qty", "label": _("In Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "out_qty", "label": _("Out Qty."), "fieldtype": "Float", "precision": 2, "width": 90},
		{"fieldname": "balance_qty", "label": _("Balance Qty."), "fieldtype": "Float", "precision": 2, "width": 100},
		{"fieldname": "amount", "label": _("Amount"), "fieldtype": "Currency", "width": 110},
	]


def get_data(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	hospital_name = filters.get("hospital_name")
	department = filters.get("department")
	voucher_name_filter = filters.get("voucher_name")
	item_filter = filters.get("item_name")
	therapeutic_group = filters.get("therapeutic_group")

	# Fetch Warehouse mapping
	wh_conditions = []
	wh_params = {}
	if hospital_name:
		wh_conditions.append("(w.company = %(hospital_name)s OR w.company IS NULL)")
		wh_params["hospital_name"] = hospital_name
	if department:
		wh_conditions.append("(w.custom_department = %(department)s OR w.name = %(department)s)")
		wh_params["department"] = department

	wh_sql = f"WHERE {' AND '.join(wh_conditions)}" if wh_conditions else ""
	warehouses = frappe.db.sql(f"SELECT name, warehouse_name, custom_department, company FROM `tabWarehouse` w {wh_sql}", wh_params, as_dict=True)
	wh_map = {w.name: (w.custom_department or w.warehouse_name or w.name) for w in warehouses}

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

	item_cond_sql = f"WHERE {' AND '.join(item_conds)}" if item_conds else ""
	items = frappe.db.sql(f"SELECT name, item_name, item_group, stock_uom, custom_mrp FROM `tabItem` i {item_cond_sql}", item_params, as_dict=True)
	item_map = {i.name: i for i in items}
	if not item_map:
		return []

	# Batch info
	batches = frappe.db.sql("SELECT name, expiry_date, custom_mrp FROM `tabBatch`", as_dict=True)
	batch_map = {b.name: b for b in batches}

	# Stock Entry Detail extra fields (conversion factor, mrp, rack, shelf, from/to dept)
	sed_info = {}
	sed_rows = frappe.db.sql(
		"""
		SELECT sed.parent, sed.item_code, sed.batch_no, sed.conversion_factor, sed.custom_mrp, sed.department, sed.to_department, sed.custom_bin_location
		FROM `tabStock Entry Detail` sed
	""",
		as_dict=True,
	)
	for s in sed_rows:
		sed_info[(s.parent, s.item_code, s.batch_no)] = s
		sed_info[(s.parent, s.item_code)] = s

	# Stock Ledger Entries
	sle_conds = ["sle.item_code IN %(item_codes)s", "sle.is_cancelled = 0"]
	sle_params = {"item_codes": tuple(item_map.keys())}
	if wh_map:
		sle_conds.append("sle.warehouse IN %(wh_names)s")
		sle_params["wh_names"] = tuple(wh_map.keys())

	sles = frappe.db.sql(
		f"""
		SELECT
			sle.name,
			sle.item_code,
			sle.warehouse,
			sle.posting_date,
			sle.posting_time,
			sle.voucher_type,
			sle.voucher_no,
			sle.actual_qty,
			sle.qty_after_transaction,
			sle.incoming_rate,
			sle.valuation_rate,
			sle.stock_value_difference,
			sle.batch_no
		FROM `tabStock Ledger Entry` sle
		WHERE {' AND '.join(sle_conds)}
		ORDER BY sle.posting_date ASC, sle.posting_time ASC, sle.creation ASC
	""",
		sle_params,
		as_dict=True,
	)

	data = []
	for sle in sles:
		item_code = sle.item_code
		item = item_map.get(item_code)
		if not item:
			continue

		v_type = sle.voucher_type or ""
		v_no = sle.voucher_no or ""
		post_date = str(sle.posting_date)

		# Filter by date range
		if post_date < str(from_date) or post_date > str(to_date):
			continue

		qty = flt(sle.actual_qty)
		in_qty = qty if qty > 0 else 0.0
		out_qty = abs(qty) if qty < 0 else 0.0
		bal_qty = flt(sle.qty_after_transaction)

		# Determine Voucher Name & Departments
		s_info = sed_info.get((v_no, item_code, sle.batch_no)) or sed_info.get((v_no, item_code))
		from_dept = ""
		to_dept = ""

		if v_type == "Stock Entry":
			if s_info and s_info.department:
				from_dept = s_info.department
			else:
				from_dept = wh_map.get(sle.warehouse, sle.warehouse)

			if s_info and s_info.to_department:
				to_dept = s_info.to_department

			if in_qty > 0 and out_qty == 0:
				v_name = "Material Receipt"
				if not to_dept:
					to_dept = wh_map.get(sle.warehouse, sle.warehouse)
			elif out_qty > 0 and in_qty == 0 and to_dept:
				v_name = "Stock Transferred"
			else:
				v_name = "Consumption"
		elif v_type == "Purchase Receipt" or v_type == "Purchase Invoice":
			v_name = "Purchase Receipt"
			to_dept = wh_map.get(sle.warehouse, sle.warehouse)
		elif v_type == "Sales Invoice" or v_type == "Delivery Note":
			v_name = "Sales Invoice" if v_type == "Sales Invoice" else "Delivery Note"
			from_dept = wh_map.get(sle.warehouse, sle.warehouse)
		else:
			v_name = v_type
			from_dept = wh_map.get(sle.warehouse, sle.warehouse)

		if voucher_name_filter and voucher_name_filter != v_name:
			continue

		b_info = batch_map.get(sle.batch_no)
		exp_date = b_info.expiry_date if b_info else None
		mrp = flt((s_info.custom_mrp if s_info else 0.0) or (b_info.custom_mrp if b_info else 0.0) or item.custom_mrp or 0.0)
		conv_factor = flt(s_info.conversion_factor if s_info else 1.0) or 1.0
		amt = abs(flt(sle.stock_value_difference)) or (abs(qty) * flt(sle.valuation_rate or sle.incoming_rate))

		data.append(
			{
				"date": sle.posting_date,
				"voucher_name": v_name,
				"voucher_no": v_no,
				"from_department": from_dept,
				"to_department": to_dept,
				"unit": item.stock_uom or "NOS",
				"batch_no": sle.batch_no or "",
				"expiry_date": exp_date,
				"rack": "",
				"shelf": "",
				"conversion_factor": conv_factor,
				"mrp": mrp,
				"in_qty": in_qty,
				"out_qty": out_qty,
				"balance_qty": bal_qty,
				"amount": amt,
			}
		)

	return data


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
