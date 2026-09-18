# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": "Patient Name",
			"fieldname": "patient_name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": "UHID",
			"fieldname": "uhid",
			"fieldtype": "Data",
			"width": 130
		},
		{
			"label": "Voucher Name",
			"fieldname": "voucher_name",
			"fieldtype": "Data",
			"width": 110
		},
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
			"label": "Cash/Credit",
			"fieldname": "cash_credit",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": "Customer",
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150
		},
		{
			"label": "Bill Amount",
			"fieldname": "bill_amount",
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"label": "Disc. Amt.",
			"fieldname": "discount_amount",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": "Net Bill Amount",
			"fieldname": "net_bill_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "Amount Received",
			"fieldname": "amount_received",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "Total Dues Amount",
			"fieldname": "total_dues_amount",
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
	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		params["customer"] = filters.get("customer")
	if filters.get("patient_name"):
		conditions.append("(p.full_name LIKE %(patient_name)s OR si.custom_patient_name LIKE %(patient_name)s)")
		params["patient_name"] = f"%{filters.get('patient_name')}%"

	where_clause = f"AND {' AND '.join(conditions)}" if conditions else ""

	query = f"""
		SELECT
			si.name AS inv_name,
			COALESCE(NULLIF(si.custom_patient_name, ''), p.full_name, 'Unknown') AS patient_name,
			COALESCE(NULLIF(p.uhid, ''), '') AS uhid,
			'Sale' AS voucher_name,
			COALESCE(NULLIF(sb.consolidated_invoice, ''), si.name) AS bill_no,
			si.posting_date,
			CASE
				WHEN EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash') AND si.outstanding_amount = 0 THEN 'CASH'
				ELSE 'CREDIT'
			END AS cash_credit,
			si.customer,
			COALESCE(NULLIF(si.net_total, 0), si.total, si.grand_total) AS bill_amount,
			IFNULL(si.discount_amount, 0) AS discount_amount,
			si.grand_total AS net_bill_amount,
			IFNULL(si.paid_amount, 0) AS amount_received,
			si.outstanding_amount AS total_dues_amount
		FROM
			`tabSales Invoice` si
		LEFT JOIN
			`tabSale Bill` sb ON sb.consolidated_invoice = si.name
		LEFT JOIN
			`tabPatient` p ON p.name = si.patient
		WHERE
			si.docstatus = 1
			AND si.outstanding_amount > 0
			{where_clause}
		ORDER BY
			patient_name ASC, si.posting_date ASC, si.name ASC
	"""

	rows = frappe.db.sql(query, params, as_dict=True)

	if not rows:
		return []

	# Group by patient
	patient_groups = {}
	for r in rows:
		pname = r.patient_name
		if pname not in patient_groups:
			patient_groups[pname] = []
		patient_groups[pname].append(r)

	data = []

	for pname, items in patient_groups.items():
		patient_dues_accum = 0.0

		for it in items:
			dues = flt(it.total_dues_amount)
			patient_dues_accum += dues

			# Transaction row
			data.append({
				"patient_name": it.patient_name,
				"uhid": it.uhid,
				"voucher_name": it.voucher_name,
				"bill_no": it.bill_no,
				"posting_date": it.posting_date,
				"cash_credit": it.cash_credit,
				"customer": it.customer,
				"bill_amount": flt(it.bill_amount),
				"discount_amount": flt(it.discount_amount),
				"net_bill_amount": flt(it.net_bill_amount),
				"amount_received": flt(it.amount_received),
				"total_dues_amount": dues
			})

			# Total Dues row for this bill
			data.append({
				"patient_name": "",
				"uhid": "",
				"voucher_name": "",
				"bill_no": "",
				"posting_date": None,
				"cash_credit": "",
				"customer": "",
				"bill_amount": None,
				"discount_amount": None,
				"net_bill_amount": "<b>Total Dues :</b>",
				"amount_received": None,
				"total_dues_amount": dues
			})

		# Cumulative patient dues
		data.append({
			"patient_name": "",
			"uhid": "",
			"voucher_name": "",
			"bill_no": "",
			"posting_date": None,
			"cash_credit": "",
			"customer": "",
			"bill_amount": None,
			"discount_amount": None,
			"net_bill_amount": "<b>Total Dues :</b>",
			"amount_received": None,
			"total_dues_amount": patient_dues_accum
		})

		# Empty row for spacing
		data.append({})

	return data