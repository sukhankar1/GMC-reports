# Copyright (c) 2024, Quantbit Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Issue Slip No."), "fieldname": "issue_slip_no", "fieldtype": "Data", "width": 140},
		{"label": _("Issue Acceptance No."), "fieldname": "issue_acceptance_no", "fieldtype": "Data", "width": 160},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("From Department"), "fieldname": "from_department", "fieldtype": "Data", "width": 180},
		{"label": _("To Department"), "fieldname": "to_department", "fieldtype": "Data", "width": 180},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120}
	]


def get_data(filters):
	if not filters:
		filters = {}

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

	where_clause = " AND ".join(conditions)

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
		WHERE {where_clause}
		GROUP BY se.name, se.outgoing_stock_entry, se.posting_date, se.department, se.from_warehouse, se.to_warehouse, se.total_amount
		ORDER BY se.posting_date DESC, se.name DESC
	"""

	res = frappe.db.sql(query, values, as_dict=True)
	return res
