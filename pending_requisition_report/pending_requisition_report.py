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
		{"label": _("Req. Date"), "fieldname": "req_date", "fieldtype": "Date", "width": 110},
		{"label": _("Req. Time"), "fieldname": "req_time", "fieldtype": "Time", "width": 100},
		{"label": _("Approved Date"), "fieldname": "approved_date", "fieldtype": "Date", "width": 110},
		{"label": _("Approved Time"), "fieldname": "approved_time", "fieldtype": "Time", "width": 100},
		{"label": _("Cancelled Date"), "fieldname": "cancelled_date", "fieldtype": "Date", "width": 110},
		{"label": _("Cancelled Time"), "fieldname": "cancelled_time", "fieldtype": "Time", "width": 100},
		{"label": _("Issued Date"), "fieldname": "issued_date", "fieldtype": "Date", "width": 110},
		{"label": _("Issued Time"), "fieldname": "issued_time", "fieldtype": "Time", "width": 100},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 180},
		{"label": _("Patient Company"), "fieldname": "patient_company", "fieldtype": "Data", "width": 150},
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
		{"label": _("Req. Qty."), "fieldname": "req_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Approved Qty."), "fieldname": "approved_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Cancelled Qty."), "fieldname": "cancelled_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Issued Qty."), "fieldname": "issued_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Pending Qty."), "fieldname": "pending_qty", "fieldtype": "Float", "width": 100},
		{"label": _("From Department"), "fieldname": "from_department", "fieldtype": "Data", "width": 150},
		{"label": _("To Location"), "fieldname": "to_location", "fieldtype": "Data", "width": 140},
		{"label": _("To Department"), "fieldname": "to_department", "fieldtype": "Data", "width": 150},
		{"label": _("Pending status"), "fieldname": "pending_status", "fieldtype": "Data", "width": 130}
	]


def get_data(filters):
	if not filters:
		filters = {}

	type_filter = filters.get("type_filter", "Patient")
	if type_filter == "Department":
		return get_department_pending_requisitions(filters)
	else:
		return get_patient_pending_requisitions(filters)


def get_patient_pending_requisitions(filters):
	conditions = []
	values = {}

	if filters.get("from_date"):
		conditions.append("pr.creation >= %(from_date)s")
		values["from_date"] = filters.get("from_date") + " 00:00:00"

	if filters.get("to_date"):
		conditions.append("pr.creation <= %(to_date)s")
		values["to_date"] = filters.get("to_date") + " 23:59:59"

	if filters.get("from_department"):
		conditions.append("(pr.requisition_from LIKE %(from_dept)s OR pr.department LIKE %(from_dept)s)")
		values["from_dept"] = f"%{filters.get('from_department')}%"

	if filters.get("to_department"):
		conditions.append("(pr.requisition_to LIKE %(to_dept)s)")
		values["to_dept"] = f"%{filters.get('to_department')}%"

	if filters.get("patient_name"):
		conditions.append("(pr.full_name LIKE %(patient_name)s OR p.full_name LIKE %(patient_name)s)")
		values["patient_name"] = f"%{filters.get('patient_name')}%"

	where_clause = (" AND " + " AND ".join(conditions)) if conditions else ""

	query = f"""
		SELECT
			COALESCE(pr.name, '') AS req_no,
			DATE(pr.creation) AS req_date,
			TIME(pr.creation) AS req_time,
			DATE(pr.creation) AS approved_date,
			TIME(pr.creation) AS approved_time,
			NULL AS cancelled_date,
			NULL AS cancelled_time,
			NULL AS issued_date,
			NULL AS issued_time,
			COALESCE(pr.full_name, p.full_name, '') AS patient_name,
			COALESCE(pr.patient_company, '') AS patient_company,
			COALESCE(prid.item_code, '') AS item_code,
			COALESCE(prid.item_name, i.item_name, prid.item_code) AS item_name,
			COALESCE(prid.req_qty, 0.0) AS req_qty,
			COALESCE(prid.req_qty, 0.0) AS approved_qty,
			0.0 AS cancelled_qty,
			0.0 AS issued_qty,
			COALESCE(prid.req_qty, 0.0) AS pending_qty,
			COALESCE(pr.requisition_from, pr.department, '') AS from_department,
			COALESCE(pr.to_location, '') AS to_location,
			COALESCE(pr.requisition_to, '') AS to_department,
			CASE 
				WHEN pr.docstatus = 1 THEN 'Approved - Pending Issue'
				WHEN pr.docstatus = 2 THEN 'Cancelled'
				ELSE 'Pending Approval'
			END AS pending_status
		FROM `tabPatient Requisition` pr
		INNER JOIN `tabPatient Requisition Item Details` prid ON prid.parent = pr.name
		LEFT JOIN `tabPatient` p ON p.name = pr.patient_id
		LEFT JOIN `tabItem` i ON i.name = prid.item_code
		WHERE 1=1 {where_clause}
		ORDER BY pr.creation DESC
	"""
	return frappe.db.sql(query, values, as_dict=True)


def get_department_pending_requisitions(filters):
	conditions = []
	values = {}

	if filters.get("from_date"):
		conditions.append("mr.transaction_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("mr.transaction_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("from_department"):
		conditions.append("(IFNULL(mr.set_from_warehouse, '') LIKE %(from_dept)s)")
		values["from_dept"] = f"%{filters.get('from_department')}%"

	if filters.get("to_department"):
		conditions.append("(IFNULL(mr.set_warehouse, '') LIKE %(to_dept)s)")
		values["to_dept"] = f"%{filters.get('to_department')}%"

	where_clause = (" AND " + " AND ".join(conditions)) if conditions else ""

	query = f"""
		SELECT
			COALESCE(mr.name, '') AS req_no,
			mr.transaction_date AS req_date,
			TIME(mr.creation) AS req_time,
			mr.transaction_date AS approved_date,
			TIME(mr.creation) AS approved_time,
			NULL AS cancelled_date,
			NULL AS cancelled_time,
			NULL AS issued_date,
			NULL AS issued_time,
			'' AS patient_name,
			'' AS patient_company,
			COALESCE(mri.item_code, '') AS item_code,
			COALESCE(mri.item_name, i.item_name, mri.item_code) AS item_name,
			COALESCE(mri.qty, 0.0) AS req_qty,
			COALESCE(mri.qty, 0.0) AS approved_qty,
			0.0 AS cancelled_qty,
			COALESCE(mri.ordered_qty, 0.0) AS issued_qty,
			(COALESCE(mri.qty, 0.0) - COALESCE(mri.ordered_qty, 0.0)) AS pending_qty,
			COALESCE(mr.set_from_warehouse, '') AS from_department,
			'' AS to_location,
			COALESCE(mr.set_warehouse, '') AS to_department,
			CASE 
				WHEN mr.docstatus = 1 THEN 'Approved - Pending Issue'
				WHEN mr.docstatus = 2 THEN 'Cancelled'
				ELSE 'Pending Approval'
			END AS pending_status
		FROM `tabMaterial Request` mr
		INNER JOIN `tabMaterial Request Item` mri ON mri.parent = mr.name
		LEFT JOIN `tabItem` i ON i.name = mri.item_code
		WHERE (mri.qty - mri.ordered_qty) > 0 {where_clause}
		ORDER BY mr.transaction_date DESC, mr.name DESC
	"""
	return frappe.db.sql(query, values, as_dict=True)
