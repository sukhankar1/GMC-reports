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
		{"label": _("Requisition No."), "fieldname": "requisition_no", "fieldtype": "Data", "width": 130},
		{"label": _("Requisition Date"), "fieldname": "requisition_date", "fieldtype": "Date", "width": 110},
		{"label": _("Requisition Time"), "fieldname": "requisition_time", "fieldtype": "Time", "width": 100},
		{"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 100},
		{"label": _("From Department"), "fieldname": "from_department", "fieldtype": "Data", "width": 150},
		{"label": _("To Location"), "fieldname": "to_location", "fieldtype": "Data", "width": 140},
		{"label": _("To Department"), "fieldname": "to_department", "fieldtype": "Data", "width": 150},
		{"label": _("Order Type"), "fieldname": "order_type", "fieldtype": "Data", "width": 120},
		{"label": _("Bill No."), "fieldname": "bill_no", "fieldtype": "Data", "width": 130},
		{"label": _("Bill Date & Time"), "fieldname": "bill_date_time", "fieldtype": "Datetime", "width": 150},
		{"label": _("Visit Code"), "fieldname": "visit_code", "fieldtype": "Data", "width": 120},
		{"label": _("UHID"), "fieldname": "uhid", "fieldtype": "Data", "width": 120},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 180},
		{"label": _("Company Name"), "fieldname": "company_name", "fieldtype": "Data", "width": 150},
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
		{"label": _("Substitute Item Name"), "fieldname": "substitute_item_name", "fieldtype": "Data", "width": 180},
		{"label": _("Requested Qty."), "fieldname": "requested_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Requested By"), "fieldname": "requested_by", "fieldtype": "Data", "width": 130},
		{"label": _("Approved Date"), "fieldname": "approved_date", "fieldtype": "Date", "width": 110},
		{"label": _("Approved Time"), "fieldname": "approved_time", "fieldtype": "Time", "width": 100},
		{"label": _("Approved Qty."), "fieldname": "approved_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Approved By"), "fieldname": "approved_by", "fieldtype": "Data", "width": 130},
		{"label": _("Approver Remark"), "fieldname": "approver_remark", "fieldtype": "Data", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Cancelled Qty."), "fieldname": "cancelled_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Cancelled By"), "fieldname": "cancelled_by", "fieldtype": "Data", "width": 130},
		{"label": _("Stock Transfer No."), "fieldname": "stock_transfer_no", "fieldtype": "Data", "width": 140},
		{"label": _("Stock Transfer Date"), "fieldname": "stock_transfer_date", "fieldtype": "Date", "width": 120},
		{"label": _("Stock Transfer Time"), "fieldname": "stock_transfer_time", "fieldtype": "Time", "width": 110},
		{"label": _("Transfered Qty."), "fieldname": "transferred_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Transfered By"), "fieldname": "transferred_by", "fieldtype": "Data", "width": 130},
		{"label": _("Acceptance Qty."), "fieldname": "acceptance_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Acceptance By"), "fieldname": "acceptance_by", "fieldtype": "Data", "width": 130},
		{"label": _("Rejected Qty."), "fieldname": "rejected_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Sale Date"), "fieldname": "sale_date", "fieldtype": "Date", "width": 110},
		{"label": _("Sale Time"), "fieldname": "sale_time", "fieldtype": "Time", "width": 100},
		{"label": _("Sale Qty."), "fieldname": "sale_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Sale By"), "fieldname": "sale_by", "fieldtype": "Data", "width": 130},
		{"label": _("Pending Qty."), "fieldname": "pending_qty", "fieldtype": "Float", "width": 100}
	]


def get_data(filters):
	if not filters:
		filters = {}

	type_filter = filters.get("type_filter", "All")
	data = []

	if type_filter in ("All", "Patient"):
		data.extend(get_patient_requisitions(filters))

	if type_filter in ("All", "Department"):
		data.extend(get_department_requisitions(filters))

	# Sort by date desc
	data.sort(key=lambda x: str(x.get("requisition_date") or ""), reverse=True)
	return data


def get_patient_requisitions(filters):
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

	if filters.get("item_name"):
		conditions.append("(prid.item_code = %(item_name)s OR prid.item_name LIKE %(item_like)s)")
		values["item_name"] = filters.get("item_name")
		values["item_like"] = f"%{filters.get('item_name')}%"

	if filters.get("patient_name"):
		conditions.append("(pr.full_name LIKE %(patient_name)s OR p.full_name LIKE %(patient_name)s)")
		values["patient_name"] = f"%{filters.get('patient_name')}%"

	if filters.get("patient_company"):
		conditions.append("IFNULL(pr.patient_company, '') != ''")

	where_clause = (" AND " + " AND ".join(conditions)) if conditions else ""

	query = f"""
		SELECT
			COALESCE(pr.name, '') AS requisition_no,
			DATE(pr.creation) AS requisition_date,
			TIME(pr.creation) AS requisition_time,
			'Patient' AS type,
			COALESCE(pr.requisition_from, pr.department, '') AS from_department,
			COALESCE(pr.to_location, '') AS to_location,
			COALESCE(pr.requisition_to, '') AS to_department,
			COALESCE(pr.sale_type, 'Routine') AS order_type,
			'' AS bill_no,
			NULL AS bill_date_time,
			COALESCE(pr.visit_id, '') AS visit_code,
			COALESCE(pr.patient_id, p.uhid, '') AS uhid,
			COALESCE(pr.full_name, p.full_name, '') AS patient_name,
			COALESCE(pr.patient_company, '') AS company_name,
			COALESCE(prid.item_code, '') AS item_code,
			COALESCE(prid.item_name, i.item_name, prid.item_code) AS item_name,
			'' AS substitute_item_name,
			COALESCE(prid.req_qty, 0.0) AS requested_qty,
			COALESCE(pr.owner, '') AS requested_by,
			DATE(pr.creation) AS approved_date,
			TIME(pr.creation) AS approved_time,
			COALESCE(prid.req_qty, 0.0) AS approved_qty,
			COALESCE(pr.doctor, pr.owner, '') AS approved_by,
			COALESCE(pr.remark, prid.remak, '') AS approver_remark,
			CASE WHEN pr.docstatus = 1 THEN 'Approved' WHEN pr.docstatus = 2 THEN 'Cancelled' ELSE 'Pending' END AS status,
			0.0 AS cancelled_qty,
			'' AS cancelled_by,
			'' AS stock_transfer_no,
			NULL AS stock_transfer_date,
			NULL AS stock_transfer_time,
			0.0 AS transferred_qty,
			'' AS transferred_by,
			0.0 AS acceptance_qty,
			'' AS acceptance_by,
			0.0 AS rejected_qty,
			NULL AS sale_date,
			NULL AS sale_time,
			0.0 AS sale_qty,
			'' AS sale_by,
			COALESCE(prid.req_qty, 0.0) AS pending_qty
		FROM `tabPatient Requisition` pr
		INNER JOIN `tabPatient Requisition Item Details` prid ON prid.parent = pr.name
		LEFT JOIN `tabPatient` p ON p.name = pr.patient_id
		LEFT JOIN `tabItem` i ON i.name = prid.item_code
		WHERE 1=1 {where_clause}
		ORDER BY pr.creation DESC
	"""
	res = frappe.db.sql(query, values, as_dict=True)

	if filters.get("requisition_status"):
		st = filters.get("requisition_status").strip()
		res = [r for r in res if r.get("status") == st]

	return res


def get_department_requisitions(filters):
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

	if filters.get("item_name"):
		conditions.append("(mri.item_code = %(item_name)s OR mri.item_name LIKE %(item_like)s)")
		values["item_name"] = filters.get("item_name")
		values["item_like"] = f"%{filters.get('item_name')}%"

	where_clause = (" AND " + " AND ".join(conditions)) if conditions else ""

	query = f"""
		SELECT
			COALESCE(mr.name, '') AS requisition_no,
			mr.transaction_date AS requisition_date,
			TIME(mr.creation) AS requisition_time,
			'Department' AS type,
			COALESCE(mr.set_from_warehouse, '') AS from_department,
			'' AS to_location,
			COALESCE(mr.set_warehouse, '') AS to_department,
			COALESCE(mr.material_request_type, 'Material Transfer') AS order_type,
			'' AS bill_no,
			NULL AS bill_date_time,
			'' AS visit_code,
			'' AS uhid,
			'' AS patient_name,
			'' AS company_name,
			COALESCE(mri.item_code, '') AS item_code,
			COALESCE(mri.item_name, i.item_name, mri.item_code) AS item_name,
			'' AS substitute_item_name,
			COALESCE(mri.qty, 0.0) AS requested_qty,
			COALESCE(mr.owner, '') AS requested_by,
			mr.transaction_date AS approved_date,
			TIME(mr.creation) AS approved_time,
			COALESCE(mri.qty, 0.0) AS approved_qty,
			COALESCE(mr.owner, '') AS approved_by,
			'' AS approver_remark,
			CASE WHEN mr.docstatus = 1 THEN 'Approved' WHEN mr.docstatus = 2 THEN 'Cancelled' ELSE 'Pending' END AS status,
			0.0 AS cancelled_qty,
			'' AS cancelled_by,
			'' AS stock_transfer_no,
			NULL AS stock_transfer_date,
			NULL AS stock_transfer_time,
			COALESCE(mri.ordered_qty, 0.0) AS transferred_qty,
			'' AS transferred_by,
			COALESCE(mri.received_qty, 0.0) AS acceptance_qty,
			'' AS acceptance_by,
			0.0 AS rejected_qty,
			NULL AS sale_date,
			NULL AS sale_time,
			0.0 AS sale_qty,
			'' AS sale_by,
			(COALESCE(mri.qty, 0.0) - COALESCE(mri.ordered_qty, 0.0)) AS pending_qty
		FROM `tabMaterial Request` mr
		INNER JOIN `tabMaterial Request Item` mri ON mri.parent = mr.name
		LEFT JOIN `tabItem` i ON i.name = mri.item_code
		WHERE 1=1 {where_clause}
		ORDER BY mr.transaction_date DESC, mr.name DESC
	"""
	res = frappe.db.sql(query, values, as_dict=True)

	if filters.get("requisition_status"):
		st = filters.get("requisition_status").strip()
		res = [r for r in res if r.get("status") == st]

	return res
