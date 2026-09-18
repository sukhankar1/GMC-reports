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
			"label": "Date",
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 110
		},
		{
			"label": "Bill No. / Receipt No.",
			"fieldname": "bill_no",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"label": "Name",
			"fieldname": "name_display",
			"fieldtype": "Data",
			"width": 220
		},
		{
			"label": "Type",
			"fieldname": "voucher_type",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Bill Amount",
			"fieldname": "bill_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "Collection",
			"fieldname": "collection",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "Balance",
			"fieldname": "balance",
			"fieldtype": "Currency",
			"width": 120
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
	if filters.get("voucher"):
		conditions.append("(si.name LIKE %(voucher)s OR sb.consolidated_invoice LIKE %(voucher)s)")
		params["voucher"] = f"%{filters.get('voucher')}%"

	where_clause = f"AND {' AND '.join(conditions)}" if conditions else ""

	query = f"""
		SELECT
			si.name AS inv_name,
			si.posting_date,
			COALESCE(NULLIF(sb.consolidated_invoice, ''), si.name) AS bill_no,
			COALESCE(NULLIF(si.custom_patient_name, ''), p.full_name, si.customer) AS patient_name,
			si.customer,
			si.is_return,
			si.grand_total,
			si.outstanding_amount,
			(
				SELECT SUM(amount)
				FROM `tabSales Invoice Payment`
				WHERE parent = si.name
			) AS paid_amount
		FROM
			`tabSales Invoice` si
		LEFT JOIN
			`tabSale Bill` sb ON sb.consolidated_invoice = si.name
		LEFT JOIN
			`tabPatient` p ON p.name = si.patient
		WHERE
			si.docstatus = 1 {where_clause}
		ORDER BY
			si.posting_date DESC, si.name DESC
	"""

	invoices = frappe.db.sql(query, params, as_dict=True)

	data = []

	for inv in invoices:
		# Display Name: PATIENT_NAME( Customer or Self_Paying )
		p_name = inv.patient_name or "Unknown"
		c_name = inv.customer or "Self_Paying"
		display_name = f"{p_name}( {c_name} )"

		is_ret = bool(inv.is_return)
		g_total = flt(inv.grand_total)
		paid = flt(inv.paid_amount)
		out = flt(inv.outstanding_amount)

		if is_ret:
			v_type = "Sale Return"
			b_amt = -abs(g_total)
			coll_amt = 0.0
			bal_amt = 0.0
		else:
			v_type = "Sale"
			b_amt = g_total
			coll_amt = paid if paid > 0 else g_total
			bal_amt = out

		# Primary transaction row
		data.append({
			"posting_date": inv.posting_date,
			"bill_no": inv.bill_no,
			"name_display": display_name,
			"voucher_type": v_type,
			"bill_amount": b_amt,
			"collection": coll_amt,
			"balance": bal_amt
		})

		# Bill Wise Total sub-row
		data.append({
			"posting_date": None,
			"bill_no": "",
			"name_display": "",
			"voucher_type": "<b>Bill Wise Total :</b>",
			"bill_amount": b_amt,
			"collection": coll_amt,
			"balance": bal_amt
		})

		# Empty spacing row
		data.append({})

	return data
