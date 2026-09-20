# Copyright (c) 2024, Quantbit Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	view_type = filters.get("view_type", "Summary")
	if view_type == "Detail":
		columns = get_detail_columns()
		data = get_detail_data(filters)
	else:
		columns = get_summary_columns()
		data = get_summary_data(filters)

	return columns, data


def get_summary_columns():
	return [
		{"label": _("Issue Slip No."), "fieldname": "issue_slip_no", "fieldtype": "Data", "width": 140},
		{"label": _("Issue Acceptance No."), "fieldname": "issue_acceptance_no", "fieldtype": "Data", "width": 160},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("From Department"), "fieldname": "from_department", "fieldtype": "Data", "width": 180},
		{"label": _("To Department"), "fieldname": "to_department", "fieldtype": "Data", "width": 180},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120}
	]


def get_detail_columns():
	return [
		{"label": _("Issue Slip No."), "fieldname": "issue_slip_no", "fieldtype": "Data", "width": 140},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 220},
		{"label": _("Batch No."), "fieldname": "batch_no", "fieldtype": "Data", "width": 130},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 110},
		{"label": _("Quantity"), "fieldname": "qty", "fieldtype": "Float", "width": 90},
		{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120}
	]


def get_conditions(filters):
	conditions = ["se.docstatus = 1"]
	values = {}

	if filters.get("from_date"):
		conditions.append("se.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("se.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("from_department"):
		conditions.append("(se.department = %(from_department)s OR se.from_warehouse LIKE %(from_dept_like)s)")
		values["from_department"] = filters.get("from_department")
		values["from_dept_like"] = f"%{filters.get('from_department')}%"

	if filters.get("to_department"):
		conditions.append("(se.to_warehouse LIKE %(to_dept_like)s)")
		values["to_dept_like"] = f"%{filters.get('to_department')}%"

	if filters.get("therapeutic_group"):
		conditions.append("(i.item_group = %(therapeutic_group)s OR i.custom_category = %(therapeutic_group)s OR i.custom_generic_name = %(therapeutic_group)s)")
		values["therapeutic_group"] = filters.get("therapeutic_group")

	return " AND ".join(conditions), values


def get_summary_data(filters):
	where_clause, values = get_conditions(filters)
	query = f"""
		SELECT
			se.name AS issue_slip_no,
			COALESCE(se.outgoing_stock_entry, se.name) AS issue_acceptance_no,
			se.posting_date AS date,
			COALESCE(se.department, se.from_warehouse, '') AS from_department,
			COALESCE(se.to_warehouse, '') AS to_department,
			COALESCE(SUM(sed.amount), se.total_amount, 0.0) AS amount
		FROM `tabStock Entry` se
		LEFT JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		LEFT JOIN `tabItem` i ON i.name = sed.item_code
		WHERE {where_clause}
		GROUP BY se.name, se.outgoing_stock_entry, se.posting_date, se.department, se.from_warehouse, se.to_warehouse, se.total_amount
		ORDER BY se.posting_date DESC, se.name DESC
	"""
	return frappe.db.sql(query, values, as_dict=True)


def get_detail_data(filters):
	where_clause, values = get_conditions(filters)
	query = f"""
		SELECT
			se.name AS issue_slip_no,
			COALESCE(se.outgoing_stock_entry, se.name) AS issue_acceptance_no,
			se.posting_date AS date,
			COALESCE(se.department, se.from_warehouse, '') AS from_department,
			COALESCE(se.to_warehouse, '') AS to_department,
			COALESCE(sed.item_name, i.item_name, sed.item_code) AS item_name,
			COALESCE(sed.batch_no, '') AS batch_no,
			b.expiry_date AS expiry_date,
			COALESCE(sed.qty, 0.0) AS qty,
			COALESCE(sed.basic_rate, sed.valuation_rate, 0.0) AS rate,
			COALESCE(sed.amount, 0.0) AS amount
		FROM `tabStock Entry` se
		INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		LEFT JOIN `tabItem` i ON i.name = sed.item_code
		LEFT JOIN `tabBatch` b ON b.name = sed.batch_no
		WHERE {where_clause}
		ORDER BY se.outgoing_stock_entry ASC, se.posting_date DESC, se.name DESC, sed.idx ASC
	"""
	raw_rows = frappe.db.sql(query, values, as_dict=True)

	# Group by issue_acceptance_no
	groups = {}
	for r in raw_rows:
		acc_no = r.issue_acceptance_no or r.issue_slip_no
		if acc_no not in groups:
			groups[acc_no] = {
				"date": r.date,
				"from_dept": r.from_department,
				"to_dept": r.to_department,
				"items": []
			}
		groups[acc_no]["items"].append(r)

	data = []
	grand_total_qty = 0.0
	grand_total_amt = 0.0

	for acc_no, g in groups.items():
		header_text = f"<b>Issue Acceptance No. : {acc_no} Date : {g['date']} From : {g['from_dept']} To : {g['to_dept']}</b>"
		data.append({
			"issue_slip_no": header_text,
			"item_name": "",
			"batch_no": "",
			"expiry_date": None,
			"qty": "",
			"rate": "",
			"amount": ""
		})

		sec_qty = 0.0
		sec_amt = 0.0

		for item in g["items"]:
			data.append({
				"issue_slip_no": item.issue_slip_no,
				"item_name": item.item_name,
				"batch_no": item.batch_no,
				"expiry_date": item.expiry_date,
				"qty": item.qty,
				"rate": item.rate,
				"amount": item.amount
			})
			sec_qty += item.qty
			sec_amt += item.amount
			grand_total_qty += item.qty
			grand_total_amt += item.amount

		# Section total row
		data.append({
			"issue_slip_no": "",
			"item_name": "<b>Total :</b>",
			"batch_no": "",
			"expiry_date": None,
			"qty": sec_qty,
			"rate": "",
			"amount": sec_amt
		})
		data.append({})  # spacing row

	if data:
		data.append({
			"issue_slip_no": "",
			"item_name": "<b>Total :</b>",
			"batch_no": "",
			"expiry_date": None,
			"qty": grand_total_qty,
			"rate": "",
			"amount": grand_total_amt
		})

	return data
