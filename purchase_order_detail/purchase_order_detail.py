# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, get_fullname, getdate


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
			"width": 160,
		},
		{
			"label": _("P.O. Date"),
			"fieldname": "po_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("From Dept."),
			"fieldname": "from_dept",
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("Unit"),
			"fieldname": "unit",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 80,
		},
		{
			"label": _("Qty."),
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("PO Free Qty."),
			"fieldname": "free_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Inward Loose Qty."),
			"fieldname": "inward_loose_qty",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("MRP"),
			"fieldname": "mrp",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100,
		},
		{
			"label": _("Disc. Amt."),
			"fieldname": "disc_amt",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 110,
		},
		{
			"label": _("Total Amt."),
			"fieldname": "total_amt",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Verified"),
			"fieldname": "verified",
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"label": _("Verified By"),
			"fieldname": "verified_by",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Verified Date"),
			"fieldname": "verified_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Approved"),
			"fieldname": "approved",
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"label": _("Approved By"),
			"fieldname": "approved_by",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Approved Date"),
			"fieldname": "approved_date",
			"fieldtype": "Date",
			"width": 105,
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
			po.owner AS owner,
			po.modified_by AS modified_by,
			po.modified AS modified_datetime,
			po.creation AS creation_datetime,
			po.currency AS currency,
			poi.item_code AS item_code,
			poi.item_name AS item_name,
			COALESCE(poi.uom, poi.stock_uom) AS unit,
			poi.qty AS qty,
			COALESCE(poi.custom_free_qty, 0.0) AS free_qty,
			COALESCE(poi.custom_inward_loose_qty, (poi.qty * COALESCE(poi.conversion_factor, 1.0)), poi.stock_qty) AS inward_loose_qty,
			COALESCE(poi.custom_mrp, item.custom_mrp, 0.0) AS mrp,
			COALESCE(poi.discount_amount, 0.0) AS disc_amt,
			COALESCE(poi.custom_total_amount, poi.base_net_amount, poi.amount, 0.0) AS total_amt
		FROM 
			`tabPurchase Order Item` poi
		INNER JOIN 
			`tabPurchase Order` po ON po.name = poi.parent
		LEFT JOIN 
			`tabItem` item ON item.name = poi.item_code
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

	# Pre-fetch workflow actions for all retrieved POs
	po_names = list({row.get("po_no") for row in raw_data if row.get("po_no")})
	workflow_map = get_workflow_map(po_names)
	user_fullnames = {}

	def get_user_name(user_id):
		if not user_id:
			return ""
		if user_id not in user_fullnames:
			user_fullnames[user_id] = get_fullname(user_id) or user_id
		return user_fullnames[user_id]

	data = []

	for row in raw_data:
		po_name = row.get("po_no")
		wf_info = workflow_map.get(po_name, {})

		# Workflow Verification resolution
		verified = "No"
		verified_by = ""
		verified_date = None

		if wf_info.get("verifier"):
			verified = "Yes"
			verified_by = get_user_name(wf_info["verifier"].get("completed_by") or wf_info["verifier"].get("owner"))
			verified_date = getdate(wf_info["verifier"].get("creation"))
		elif row.get("workflow_state") in ["Pending For Approval", "Approved", "Completed"]:
			verified = "Yes"
			verified_by = get_user_name(row.get("owner"))
			verified_date = getdate(row.get("creation_datetime"))

		# Workflow Approval resolution
		approved = "No"
		approved_by = ""
		approved_date = None

		if wf_info.get("approver"):
			approved = "Yes"
			approved_by = get_user_name(wf_info["approver"].get("completed_by") or wf_info["approver"].get("owner"))
			approved_date = getdate(wf_info["approver"].get("creation"))
		elif row.get("workflow_state") == "Approved" or row.get("docstatus") == 1:
			approved = "Yes"
			approved_by = get_user_name(row.get("modified_by") or row.get("owner"))
			approved_date = getdate(row.get("modified_datetime") or row.get("creation_datetime"))

		# Delivery Status resolution
		per_received = flt(row.get("per_received"))
		status = row.get("status")

		if status in ["Completed", "Delivered"] or per_received >= 100:
			delivery_status = "Delivered"
		elif per_received > 0:
			delivery_status = "Partially Delivered"
		else:
			delivery_status = "To Receive"

		# Apply delivery_status filter if selected
		if filters.get("delivery_status") and filters.get("delivery_status") != "All":
			if filters.get("delivery_status").strip().lower() != delivery_status.lower():
				continue

		data.append({
			"po_no": po_name,
			"po_date": row.get("po_date"),
			"supplier_name": row.get("supplier_name") or row.get("supplier"),
			"from_dept": row.get("from_dept"),
			"item_code": row.get("item_code"),
			"item_name": row.get("item_name"),
			"unit": row.get("unit"),
			"qty": flt(row.get("qty")),
			"free_qty": flt(row.get("free_qty")),
			"inward_loose_qty": flt(row.get("inward_loose_qty")),
			"mrp": flt(row.get("mrp")),
			"disc_amt": flt(row.get("disc_amt")),
			"total_amt": flt(row.get("total_amt")),
			"verified": verified,
			"verified_by": verified_by,
			"verified_date": verified_date,
			"approved": approved,
			"approved_by": approved_by,
			"approved_date": approved_date,
			"delivery_status": delivery_status,
			"currency": row.get("currency"),
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

	if filters.get("item_code"):
		conditions.append("poi.item_code = %(item_code)s")
		values["item_code"] = filters.get("item_code")

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