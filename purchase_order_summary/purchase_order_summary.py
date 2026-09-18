# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, format_datetime, get_datetime, get_fullname, getdate


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("P.O. No."),
			"fieldname": "po_no",
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 170,
		},
		{
			"label": _("P.O. Date"),
			"fieldname": "po_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("From Dept."),
			"fieldname": "from_dept",
			"fieldtype": "Link",
			"options": "Department",
			"width": 160,
		},
		{
			"label": _("First Level Approval"),
			"fieldname": "first_level_approval",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Verified Date & Time"),
			"fieldname": "verified_datetime",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("Second Level Approval"),
			"fieldname": "second_level_approval",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Approved Date & Time"),
			"fieldname": "approved_datetime",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("Delivery Status"),
			"fieldname": "delivery_status",
			"fieldtype": "Data",
			"width": 130,
		},
	]


def get_data(filters):
	conditions, values = get_conditions(filters)

	query = f"""
		SELECT 
			po.name AS po_no,
			po.transaction_date AS po_date,
			po.supplier AS supplier,
			po.supplier_name AS supplier_name,
			COALESCE(po.department, po.custom_department, '') AS from_dept,
			po.status AS status,
			po.workflow_state AS workflow_state,
			po.per_received AS per_received,
			po.docstatus AS docstatus,
			po.creation AS creation,
			po.modified AS modified
		FROM 
			`tabPurchase Order` po
		LEFT JOIN 
			`tabSupplier` supp ON supp.name = po.supplier
		WHERE 
			po.docstatus < 2
			{conditions}
		ORDER BY 
			po.transaction_date DESC, po.name DESC
	"""

	raw_data = frappe.db.sql(query, values, as_dict=True)
	if not raw_data:
		return []

	po_names = [row["po_no"] for row in raw_data if row.get("po_no")]
	workflow_map = get_workflow_map(po_names)

	data = []

	for row in raw_data:
		po_name = row.get("po_no")
		wf_info = workflow_map.get(po_name, {})

		# First level approval (Verification)
		first_level = "No"
		verified_dt = ""
		if wf_info.get("verifier"):
			first_level = "Verified"
			dt = wf_info["verifier"].get("creation")
			if dt:
				verified_dt = format_datetime(dt, "dd/MM/yyyy hh:mm a")
		elif row.get("workflow_state") in ["Pending For Approval", "Approved", "Completed"]:
			first_level = "Verified"
			dt = row.get("creation")
			if dt:
				verified_dt = format_datetime(dt, "dd/MM/yyyy hh:mm a")

		# Second level approval (Approval)
		second_level = "No"
		approved_dt = ""
		if wf_info.get("approver"):
			second_level = "Approved"
			dt = wf_info["approver"].get("creation")
			if dt:
				approved_dt = format_datetime(dt, "dd/MM/yyyy hh:mm a")
		elif row.get("workflow_state") == "Approved" or row.get("docstatus") == 1:
			second_level = "Approved"
			dt = row.get("modified") or row.get("creation")
			if dt:
				approved_dt = format_datetime(dt, "dd/MM/yyyy hh:mm a")

		# Delivery status
		per_rec = flt(row.get("per_received"))
		st = row.get("status")
		if st in ["Completed", "Delivered"] or per_rec >= 100:
			delivery_status = "Delivered"
		elif per_rec > 0:
			delivery_status = "Partially Delivered"
		else:
			delivery_status = "pending"

		if filters.get("delivery_status") and filters.get("delivery_status") != "All":
			if filters.get("delivery_status").strip().lower() != delivery_status.lower():
				continue

		data.append({
			"po_no": po_name,
			"po_date": row.get("po_date"),
			"supplier_name": row.get("supplier_name") or row.get("supplier"),
			"from_dept": row.get("from_dept"),
			"first_level_approval": first_level,
			"verified_datetime": verified_dt,
			"second_level_approval": second_level,
			"approved_datetime": approved_dt,
			"delivery_status": delivery_status,
		})

	return data


def get_workflow_map(po_names):
	if not po_names:
		return {}

	actions = frappe.db.sql(
		"""
		SELECT 
			reference_name, completed_by, completed_by_role, owner, creation, workflow_state, status
		FROM 
			`tabWorkflow Action`
		WHERE 
			reference_doctype = 'Purchase Order'
			AND reference_name IN %(po_names)s
		ORDER BY 
			creation ASC
	""",
		{"po_names": tuple(po_names)},
		as_dict=True,
	)

	wf_map = {}
	for act in actions:
		ref = act["reference_name"]
		if ref not in wf_map:
			wf_map[ref] = {}

		role = act.get("completed_by_role") or ""
		state = act.get("workflow_state") or ""

		if "Verifier" in role or "Verification" in state:
			wf_map[ref]["verifier"] = act
		elif "Approver" in role or "Approval" in state or state == "Approved":
			wf_map[ref]["approver"] = act

	return wf_map


def get_conditions(filters):
	conditions = []
	values = {}

	if filters.get("company"):
		conditions.append("po.company = %(company)s")
		values["company"] = filters.get("company")

	if filters.get("from_date"):
		conditions.append("po.transaction_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("po.transaction_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("supplier"):
		conditions.append("po.supplier = %(supplier)s")
		values["supplier"] = filters.get("supplier")

	if filters.get("department"):
		conditions.append("(po.department = %(department)s OR po.custom_department = %(department)s)")
		values["department"] = filters.get("department")

	if filters.get("status") and filters.get("status") != "All":
		conditions.append("po.status = %(status)s")
		values["status"] = filters.get("status")

	if filters.get("indigenous_imported") and filters.get("indigenous_imported") != "All":
		val = filters.get("indigenous_imported").strip().lower()
		if val == "indigenous":
			conditions.append("(supp.country = 'Qatar' OR supp.country IS NULL OR supp.country = '')")
		elif val == "imported":
			conditions.append("(supp.country IS NOT NULL AND supp.country != '' AND supp.country != 'Qatar')")

	cond_str = " AND " + " AND ".join(conditions) if conditions else ""
	return cond_str, values