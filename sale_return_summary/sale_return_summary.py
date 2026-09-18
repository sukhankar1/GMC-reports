# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, cstr

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": "Department",
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 180
		},
		{
			"label": "Bill No.",
			"fieldname": "bill_no",
			"fieldtype": "Data",
			"width": 140
		},
		{
			"label": "Date",
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 105
		},
		{
			"label": "Patient/Customer Name",
			"fieldname": "patient_customer_name",
			"fieldtype": "Data",
			"width": 190
		},
		{
			"label": "Patient Department",
			"fieldname": "patient_department",
			"fieldtype": "Data",
			"width": 170
		},
		{
			"label": "Visit Number",
			"fieldname": "visit_number",
			"fieldtype": "Data",
			"width": 140
		},
		{
			"label": "Verified By",
			"fieldname": "verified_by",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"label": "Status",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 80
		},
		{
			"label": "Net Bill Amount",
			"fieldname": "net_bill_amount",
			"fieldtype": "Currency",
			"width": 130
		}
	]

def get_data(filters):
	if not filters:
		filters = {}

	conditions = []
	params = {}

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		params["from_date"] = filters.get("from_date")
	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		params["to_date"] = filters.get("to_date")
	if filters.get("department"):
		conditions.append("sb.department = %(department)s")
		params["department"] = filters.get("department")
	if filters.get("patient_name"):
		conditions.append("(p.full_name LIKE %(patient_name)s OR si.custom_patient_name LIKE %(patient_name)s)")
		params["patient_name"] = f"%{filters.get('patient_name')}%"
	if filters.get("visit_name"):
		conditions.append("(sb.visit_no = %(visit_name)s OR sb.custom_visit_code = %(visit_name)s)")
		params["visit_name"] = filters.get("visit_name")

	if filters.get("payment_type"):
		ptype = filters.get("payment_type")
		if ptype == "Cash":
			conditions.append("EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash')")
		elif ptype == "Credit":
			conditions.append("(si.outstanding_amount > 0 OR NOT EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash'))")

	where_clause = f"AND {' AND '.join(conditions)}" if conditions else ""

	query = f"""
		SELECT
			COALESCE(NULLIF(sb.department, ''), 'KAMALNAYAN BAJAJ PHARMACY') AS department,
			COALESCE(NULLIF(sb.consolidated_invoice, ''), si.name) AS bill_no,
			si.posting_date,
			COALESCE(NULLIF(si.custom_patient_name, ''), p.full_name, si.customer) AS patient_customer_name,
			COALESCE(NULLIF(sb.department, ''), 'GENERAL') AS patient_department,
			COALESCE(NULLIF(sb.visit_no, ''), sb.custom_visit_code, '') AS visit_number,
			COALESCE(NULLIF(si.owner, ''), 'Administrator') AS verified_by,
			'Y' AS status,
			ABS(si.grand_total) AS net_bill_amount
		FROM
			`tabSales Invoice` si
		LEFT JOIN
			`tabSale Bill` sb ON sb.consolidated_invoice = si.name
		LEFT JOIN
			`tabPatient` p ON p.name = si.patient
		WHERE
			si.docstatus = 1
			AND si.is_return = 1
			{where_clause}
		ORDER BY
			si.posting_date DESC, si.name DESC
	"""

	rows = frappe.db.sql(query, params, as_dict=True)

	data = []
	for r in rows:
		data.append({
			"department": r.department,
			"bill_no": r.bill_no,
			"posting_date": r.posting_date,
			"patient_customer_name": r.patient_customer_name or "",
			"patient_department": r.patient_department or "",
			"visit_number": r.visit_number or "",
			"verified_by": r.verified_by or "",
			"status": r.status or "Y",
			"net_bill_amount": flt(r.net_bill_amount)
		})

	return data
