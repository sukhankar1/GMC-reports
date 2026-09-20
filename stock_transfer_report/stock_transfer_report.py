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
		{"label": _("Req. No."), "fieldname": "req_no", "fieldtype": "Data", "width": 130},
		{"label": _("Req Date"), "fieldname": "req_date", "fieldtype": "Date", "width": 110},
		{"label": _("Issue No."), "fieldname": "issue_no", "fieldtype": "Data", "width": 130},
		{"label": _("Issue date"), "fieldname": "issue_date", "fieldtype": "Date", "width": 110},
		{"label": _("From Department"), "fieldname": "from_department", "fieldtype": "Data", "width": 160},
		{"label": _("To Department"), "fieldname": "to_department", "fieldtype": "Data", "width": 160},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
		{"label": _("Batch No."), "fieldname": "batch_no", "fieldtype": "Data", "width": 130},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 110},
		{"label": _("Issue Qty."), "fieldname": "issue_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Acceptance Qty."), "fieldname": "acceptance_qty", "fieldtype": "Float", "width": 120},
		{"label": _("Rejected Qty."), "fieldname": "rejected_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110}
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

	if filters.get("item_name"):
		conditions.append("(sed.item_code = %(item_name)s OR sed.item_name LIKE %(item_like)s)")
		values["item_name"] = filters.get("item_name")
		values["item_like"] = f"%{filters.get('item_name')}%"

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

	if filters.get("indent_type") == "With Indent":
		conditions.append("IFNULL(sed.material_request, '') != ''")
	elif filters.get("indent_type") == "Without Indent":
		conditions.append("IFNULL(sed.material_request, '') = ''")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			COALESCE(sed.material_request, '') AS req_no,
			mr.transaction_date AS req_date,
			se.name AS issue_no,
			se.posting_date AS issue_date,
			COALESCE(se.department, se.from_warehouse, '') AS from_department,
			COALESCE(se.to_warehouse, '') AS to_department,
			COALESCE(sed.item_name, i.item_name, sed.item_code) AS item_name,
			COALESCE(sed.batch_no, '') AS batch_no,
			b.expiry_date AS expiry_date,
			COALESCE(sed.qty, 0.0) AS issue_qty,
			COALESCE(sed.qty, 0.0) AS acceptance_qty,
			0.0 AS rejected_qty,
			'Accepted' AS status
		FROM `tabStock Entry` se
		INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		LEFT JOIN `tabMaterial Request` mr ON mr.name = sed.material_request
		LEFT JOIN `tabItem` i ON i.name = sed.item_code
		LEFT JOIN `tabBatch` b ON b.name = sed.batch_no
		WHERE {where_clause}
		ORDER BY se.posting_date DESC, se.name DESC, sed.idx ASC
	"""

	res = frappe.db.sql(query, values, as_dict=True)

	# Apply status filter in python if needed
	if filters.get("status"):
		st = filters.get("status").strip()
		res = [r for r in res if r.get("status") == st]

	return res
