# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, cstr

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters=None):
	view_type = filters.get("view_type") if filters else "Summary"
	
	if view_type == "Detail":
		return [
			{
				"label": "Bill No.",
				"fieldname": "bill_no",
				"fieldtype": "Data",
				"width": 130
			},
			{
				"label": "Indent No.",
				"fieldname": "indent_no",
				"fieldtype": "Data",
				"width": 120
			},
			{
				"label": "Bill Date",
				"fieldname": "bill_date",
				"fieldtype": "Datetime",
				"width": 150
			},
			{
				"label": "Cash/Credit",
				"fieldname": "cash_credit",
				"fieldtype": "Data",
				"width": 100
			},
			{
				"label": "Customer Name",
				"fieldname": "customer_name",
				"fieldtype": "Data",
				"width": 170
			},
			{
				"label": "Patient Company",
				"fieldname": "patient_company",
				"fieldtype": "Data",
				"width": 150
			},
			{
				"label": "Visit Number",
				"fieldname": "visit_number",
				"fieldtype": "Data",
				"width": 130
			},
			{
				"label": "Patient Name",
				"fieldname": "patient_name",
				"fieldtype": "Data",
				"width": 170
			},
			{
				"label": "Counter",
				"fieldname": "counter",
				"fieldtype": "Data",
				"width": 160
			},
			{
				"label": "Department",
				"fieldname": "department",
				"fieldtype": "Data",
				"width": 140
			},
			{
				"label": "Bed Name",
				"fieldname": "bed_name",
				"fieldtype": "Data",
				"width": 130
			},
			{
				"label": "User Name",
				"fieldname": "user_name",
				"fieldtype": "Data",
				"width": 150
			},
			{
				"label": "Sale Amount",
				"fieldname": "sale_amount",
				"fieldtype": "Currency",
				"width": 120
			},
			{
				"label": "Return Amount",
				"fieldname": "return_amount",
				"fieldtype": "Currency",
				"width": 120
			},
			{
				"label": "Net Amount",
				"fieldname": "net_amount",
				"fieldtype": "Currency",
				"width": 120
			}
		]
	else:
		return [
			{
				"label": "Bill Date",
				"fieldname": "posting_date",
				"fieldtype": "Date",
				"width": 120
			},
			{
				"label": "Sale Amount",
				"fieldname": "sale_amount",
				"fieldtype": "Currency",
				"width": 130
			},
			{
				"label": "Return Amount",
				"fieldname": "return_amount",
				"fieldtype": "Currency",
				"width": 130
			},
			{
				"label": "Net Amount",
				"fieldname": "net_amount",
				"fieldtype": "Currency",
				"width": 140
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

	if filters.get("concession_100"):
		conditions.append("si.additional_discount_percentage = 100")

	docstatus_cond = "si.docstatus = 2" if filters.get("cancelled_bills") else "si.docstatus = 1"

	if filters.get("payment_type"):
		ptype = filters.get("payment_type")
		if ptype == "Cash":
			conditions.append("EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash')")
		elif ptype == "Credit":
			conditions.append("(si.outstanding_amount > 0 OR NOT EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash'))")

	where_clause = f"AND {' AND '.join(conditions)}" if conditions else ""

	view_type = filters.get("view_type") or "Summary"

	if view_type == "Detail":
		query = f"""
			SELECT
				COALESCE(NULLIF(sb.consolidated_invoice, ''), si.name) AS bill_no,
				'' AS indent_no,
				si.creation AS bill_date,
				CASE
					WHEN EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash') AND si.outstanding_amount = 0 THEN 'CASH'
					ELSE 'CREDIT'
				END AS cash_credit,
				si.customer AS customer_name,
				COALESCE(NULLIF(si.customer, ''), 'Self pay Cash') AS patient_company,
				COALESCE(NULLIF(sb.visit_no, ''), sb.custom_visit_code, '') AS visit_number,
				COALESCE(NULLIF(si.custom_patient_name, ''), p.full_name, si.customer) AS patient_name,
				COALESCE(NULLIF(sb.department, ''), 'KAMALNAYAN BAJAJ PHARMACY') AS counter,
				COALESCE(NULLIF(sb.department, ''), '') AS department,
				COALESCE(NULLIF(sb.custom_bed_no, ''), '') AS bed_name,
				si.owner AS user_name,
				CASE WHEN IFNULL(si.is_return, 0) = 0 THEN si.grand_total ELSE 0 END AS sale_amount,
				CASE WHEN si.is_return = 1 THEN ABS(si.grand_total) ELSE 0 END AS return_amount
			FROM
				`tabSales Invoice` si
			LEFT JOIN
				`tabSale Bill` sb ON sb.consolidated_invoice = si.name
			LEFT JOIN
				`tabPatient` p ON p.name = si.patient
			WHERE
				{docstatus_cond}
				{where_clause}
			ORDER BY
				si.creation DESC
		"""
		rows = frappe.db.sql(query, params, as_dict=True)

		data = []
		for r in rows:
			s_amt = flt(r.sale_amount)
			r_amt = flt(r.return_amount)
			data.append({
				"bill_no": r.bill_no,
				"indent_no": r.indent_no or "",
				"bill_date": r.bill_date,
				"cash_credit": r.cash_credit,
				"customer_name": r.customer_name or "",
				"patient_company": r.patient_company or "",
				"visit_number": r.visit_number or "",
				"patient_name": r.patient_name or "",
				"counter": r.counter or "",
				"department": r.department or "",
				"bed_name": r.bed_name or "",
				"user_name": r.user_name or "",
				"sale_amount": s_amt,
				"return_amount": r_amt,
				"net_amount": s_amt - r_amt
			})
		return data

	else:
		query = f"""
			SELECT
				si.posting_date,
				SUM(CASE WHEN IFNULL(si.is_return, 0) = 0 THEN si.grand_total ELSE 0 END) AS sale_amount,
				SUM(CASE WHEN si.is_return = 1 THEN ABS(si.grand_total) ELSE 0 END) AS return_amount
			FROM
				`tabSales Invoice` si
			LEFT JOIN
				`tabSale Bill` sb ON sb.consolidated_invoice = si.name
			LEFT JOIN
				`tabPatient` p ON p.name = si.patient
			WHERE
				{docstatus_cond}
				{where_clause}
			GROUP BY
				si.posting_date
			ORDER BY
				si.posting_date DESC
		"""
		rows = frappe.db.sql(query, params, as_dict=True)

		data = []
		tot_sale = 0.0
		tot_ret = 0.0
		tot_net = 0.0

		for r in rows:
			s_amt = flt(r.sale_amount)
			r_amt = flt(r.return_amount)
			n_amt = s_amt - r_amt

			tot_sale += s_amt
			tot_ret += r_amt
			tot_net += n_amt

			data.append({
				"posting_date": r.posting_date,
				"sale_amount": s_amt,
				"return_amount": r_amt,
				"net_amount": n_amt
			})

		if data:
			data.append({
				"posting_date": "<b>Total:</b>",
				"sale_amount": tot_sale,
				"return_amount": tot_ret,
				"net_amount": tot_net
			})

		return data
