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
			"label": "Bill No.",
			"fieldname": "bill_no",
			"fieldtype": "Data",
			"width": 130
		},
		{
			"label": "Date",
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 105
		},
		{
			"label": "Patient/ Customer Name",
			"fieldname": "patient_customer_name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": "Company Name",
			"fieldname": "company_name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": "Doctors Name",
			"fieldname": "doctor_name",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"label": "Address & Mobile No.",
			"fieldname": "address_mobile_no",
			"fieldtype": "Data",
			"width": 240
		},
		{
			"label": "Product Name",
			"fieldname": "product_name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": "Schedule Type",
			"fieldname": "schedule_type",
			"fieldtype": "Data",
			"width": 110
		},
		{
			"label": "Qty.",
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 90
		},
		{
			"label": "Batch No.",
			"fieldname": "batch_no",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Expiry Date",
			"fieldname": "expiry_date",
			"fieldtype": "Date",
			"width": 105
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
	if filters.get("schedule_type"):
		conditions.append("i.custom_schedule_type = %(schedule_type)s")
		params["schedule_type"] = filters.get("schedule_type")
	if filters.get("doctor_name"):
		conditions.append("(sb.custom_doctor_name LIKE %(doctor_name)s OR p.consulting_doctor LIKE %(doctor_name)s)")
		params["doctor_name"] = f"%{filters.get('doctor_name')}%"

	where_clause = f"AND {' AND '.join(conditions)}" if conditions else ""

	query = f"""
		SELECT
			COALESCE(NULLIF(sb.consolidated_invoice, ''), si.name) AS bill_no,
			si.posting_date,
			COALESCE(NULLIF(si.custom_patient_name, ''), p.full_name, si.customer) AS patient_customer_name,
			si.customer AS company_name,
			COALESCE(NULLIF(sb.custom_doctor_name, ''), p.consulting_doctor, '') AS doctor_name,
			p.present_address,
			p.permanent_address,
			p.mobile_number,
			i.item_name AS product_name,
			COALESCE(NULLIF(i.custom_schedule_type, ''), '-') AS schedule_type,
			sii.qty,
			sii.batch_no,
			b.expiry_date
		FROM
			`tabSales Invoice` si
		INNER JOIN
			`tabSales Invoice Item` sii ON sii.parent = si.name
		LEFT JOIN
			`tabItem` i ON i.name = sii.item_code
		LEFT JOIN
			`tabBatch` b ON b.name = sii.batch_no
		LEFT JOIN
			`tabSale Bill` sb ON sb.consolidated_invoice = si.name
		LEFT JOIN
			`tabPatient` p ON p.name = si.patient
		WHERE
			si.docstatus = 1
			{where_clause}
		ORDER BY
			si.posting_date DESC, si.name DESC
	"""

	rows = frappe.db.sql(query, params, as_dict=True)

	data = []
	for r in rows:
		addr_parts = []
		addr = r.present_address or r.permanent_address or ""
		if addr:
			addr_parts.append(cstr(addr).strip().replace("\n", ", "))
		if r.mobile_number:
			addr_parts.append(f"Mobile No.-{r.mobile_number}")
		addr_mobile = ", ".join(addr_parts) if addr_parts else ""

		data.append({
			"bill_no": r.bill_no,
			"posting_date": r.posting_date,
			"patient_customer_name": r.patient_customer_name or "",
			"company_name": r.company_name or "",
			"doctor_name": r.doctor_name or "",
			"address_mobile_no": addr_mobile,
			"product_name": r.product_name or "",
			"schedule_type": r.schedule_type or "-",
			"qty": flt(r.qty),
			"batch_no": r.batch_no or "",
			"expiry_date": r.expiry_date
		})

	return data
