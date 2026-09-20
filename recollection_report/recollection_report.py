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
		{"label": _("Recollection No."), "fieldname": "recollection_no", "fieldtype": "Data", "width": 140},
		{"label": _("Recollection Date & Time"), "fieldname": "recollection_date_time", "fieldtype": "Datetime", "width": 160},
		{"label": _("Rejected /Accepted No."), "fieldname": "rejected_accepted_no", "fieldtype": "Data", "width": 150},
		{"label": _("Rejected Date & Time"), "fieldname": "rejected_date_time", "fieldtype": "Datetime", "width": 160},
		{"label": _("Issued No."), "fieldname": "issued_no", "fieldtype": "Data", "width": 130},
		{"label": _("Issue Date & Time"), "fieldname": "issue_date_time", "fieldtype": "Datetime", "width": 160},
		{"label": _("Issued From"), "fieldname": "issued_from", "fieldtype": "Data", "width": 150},
		{"label": _("Issued To"), "fieldname": "issued_to", "fieldtype": "Data", "width": 150},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
		{"label": _("Unit"), "fieldname": "unit", "fieldtype": "Data", "width": 90},
		{"label": _("Batch No."), "fieldname": "batch_no", "fieldtype": "Data", "width": 130},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 110},
		{"label": _("Requested Qty."), "fieldname": "requested_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Issued Qty."), "fieldname": "issued_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Issued By"), "fieldname": "issued_by", "fieldtype": "Data", "width": 130},
		{"label": _("Accepted Qty."), "fieldname": "accepted_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Rejected Qty."), "fieldname": "rejected_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Rejected/Accepted By"), "fieldname": "rejected_accepted_by", "fieldtype": "Data", "width": 150},
		{"label": _("Recollection Qty."), "fieldname": "recollection_qty", "fieldtype": "Float", "width": 120},
		{"label": _("Recollected By"), "fieldname": "recollected_by", "fieldtype": "Data", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120}
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

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			COALESCE(se.name, '') AS recollection_no,
			TIMESTAMP(se.posting_date, se.posting_time) AS recollection_date_time,
			COALESCE(se.outgoing_stock_entry, '') AS rejected_accepted_no,
			TIMESTAMP(se.posting_date, se.posting_time) AS rejected_date_time,
			COALESCE(se.outgoing_stock_entry, se.name) AS issued_no,
			TIMESTAMP(se.posting_date, se.posting_time) AS issue_date_time,
			COALESCE(se.from_warehouse, se.department, '') AS issued_from,
			COALESCE(se.to_warehouse, '') AS issued_to,
			COALESCE(sed.item_name, i.item_name, sed.item_code) AS item_name,
			COALESCE(sed.uom, sed.stock_uom, '') AS unit,
			COALESCE(sed.batch_no, '') AS batch_no,
			b.expiry_date AS expiry_date,
			COALESCE(sed.qty, 0.0) AS requested_qty,
			COALESCE(sed.qty, 0.0) AS issued_qty,
			COALESCE(se.owner, '') AS issued_by,
			COALESCE(sed.qty, 0.0) AS accepted_qty,
			0.0 AS rejected_qty,
			COALESCE(se.owner, '') AS rejected_accepted_by,
			COALESCE(sed.qty, 0.0) AS recollection_qty,
			COALESCE(se.owner, '') AS recollected_by,
			'Recollected' AS status
		FROM `tabStock Entry` se
		INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		LEFT JOIN `tabItem` i ON i.name = sed.item_code
		LEFT JOIN `tabBatch` b ON b.name = sed.batch_no
		WHERE {where_clause}
		ORDER BY se.posting_date DESC, se.name DESC, sed.idx ASC
	"""

	res = frappe.db.sql(query, values, as_dict=True)

	if filters.get("status"):
		st = filters.get("status").strip()
		res = [r for r in res if r.get("status") == st]

	return res
