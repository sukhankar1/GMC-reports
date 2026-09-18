# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, cstr

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters=None):
	return [
		{
			"label": "Bill No.",
			"fieldname": "bill_no",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"label": "Pay Mode",
			"fieldname": "pay_mode",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Patient Name",
			"fieldname": "patient_name",
			"fieldtype": "Data",
			"width": 220
		},
		{
			"label": "Cash Amount",
			"fieldname": "cash_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "Card / Cheque Amount",
			"fieldname": "card_cheque_amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": "Amount",
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 130
		}
	]

def get_data(filters):
	if not filters:
		filters = {}

	conditions = []
	params = {}

	if filters.get("from_date_time"):
		conditions.append("si.creation >= %(from_date_time)s")
		params["from_date_time"] = filters.get("from_date_time")
	elif filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		params["from_date"] = filters.get("from_date")

	if filters.get("to_date_time"):
		conditions.append("si.creation <= %(to_date_time)s")
		params["to_date_time"] = filters.get("to_date_time")
	elif filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		params["to_date"] = filters.get("to_date")

	if filters.get("department"):
		conditions.append("sb.department = %(department)s")
		params["department"] = filters.get("department")

	if filters.get("users"):
		users = filters.get("users")
		if isinstance(users, str):
			import json
			try:
				users = json.loads(users)
			except Exception:
				users = [u.strip() for u in users.split(",") if u.strip()]
		if users:
			conditions.append("si.owner IN %(users)s")
			params["users"] = tuple(users)

	if filters.get("payment_type"):
		ptype = filters.get("payment_type")
		if ptype == "Cash":
			conditions.append("EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash')")
		elif ptype == "Credit":
			conditions.append("(si.outstanding_amount > 0 OR NOT EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash'))")

	where_clause = f"AND {' AND '.join(conditions)}" if conditions else ""

	query = f"""
		SELECT 
			si.name AS inv_name,
			COALESCE(NULLIF(sb.consolidated_invoice, ''), si.name) AS bill_no,
			COALESCE(NULLIF(si.custom_patient_name, ''), p.full_name, si.customer) AS patient_name,
			COALESCE(NULLIF(sb.department, ''), 'KAMALNAYAN BAJAJ PHARMACY') AS department,
			si.owner AS user_name,
			si.grand_total,
			(
				SELECT GROUP_CONCAT(DISTINCT mode_of_payment SEPARATOR ', ')
				FROM `tabSales Invoice Payment`
				WHERE parent = si.name
			) AS mode_of_payment,
			(
				SELECT SUM(amount)
				FROM `tabSales Invoice Payment`
				WHERE parent = si.name AND mode_of_payment = 'Cash'
			) AS cash_paid,
			(
				SELECT SUM(amount)
				FROM `tabSales Invoice Payment`
				WHERE parent = si.name AND mode_of_payment IN ('Card', 'Credit Card', 'Debit Card', 'Cheque', 'Bank Draft', 'Online')
			) AS card_paid
		FROM `tabSales Invoice` si
		LEFT JOIN `tabSale Bill` sb ON sb.consolidated_invoice = si.name
		LEFT JOIN `tabPatient` p ON p.name = si.patient
		WHERE si.docstatus = 1 {where_clause}
		ORDER BY sb.department, si.owner, si.creation ASC
	"""

	rows = frappe.db.sql(query, params, as_dict=True)

	if not rows:
		return []

	# Group by (Department, User)
	grouped = {}
	for r in rows:
		dept = r.department or "KAMALNAYAN BAJAJ PHARMACY"
		user = r.user_name or "Administrator"
		key = (dept, user)
		if key not in grouped:
			grouped[key] = []
		grouped[key].append(r)

	data = []

	for (dept, user), records in grouped.items():
		# Counter & Dept Header
		data.append({
			"bill_no": "<b>Counter Name :</b>",
			"pay_mode": "",
			"patient_name": "",
			"cash_amount": None,
			"card_cheque_amount": None,
			"amount": None
		})
		data.append({
			"bill_no": f"<b>Department Name : {dept}</b>",
			"pay_mode": "",
			"patient_name": "",
			"cash_amount": None,
			"card_cheque_amount": None,
			"amount": None
		})
		data.append({
			"bill_no": f"<b>User Name : {user}</b>",
			"pay_mode": "",
			"patient_name": f"<b>Cashier Name : {user}</b>",
			"cash_amount": None,
			"card_cheque_amount": None,
			"amount": None
		})
		data.append({
			"bill_no": "<b>Sale</b>",
			"pay_mode": "",
			"patient_name": "",
			"cash_amount": None,
			"card_cheque_amount": None,
			"amount": None
		})

		sub_cash = 0.0
		sub_card = 0.0
		sub_total = 0.0

		for rec in records:
			c_amt = flt(rec.cash_paid)
			card_amt = flt(rec.card_paid)
			t_amt = flt(rec.grand_total)

			pmode = rec.mode_of_payment
			if not pmode:
				pmode = "Credit" if t_amt > 0 else "Cash"

			sub_cash += c_amt
			sub_card += card_amt
			sub_total += t_amt

			data.append({
				"bill_no": rec.bill_no,
				"pay_mode": pmode,
				"patient_name": rec.patient_name,
				"cash_amount": c_amt if c_amt > 0 else 0.0,
				"card_cheque_amount": card_amt if card_amt > 0 else 0.0,
				"amount": t_amt
			})

		# Subtotal for User
		data.append({
			"bill_no": f"<b>Sub Total ({user})</b>",
			"pay_mode": "",
			"patient_name": "",
			"cash_amount": sub_cash,
			"card_cheque_amount": sub_card,
			"amount": sub_total
		})
		data.append({})

	return data
