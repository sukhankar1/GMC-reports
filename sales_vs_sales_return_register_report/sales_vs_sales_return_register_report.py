# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters=None):
	view_type = filters.get("view_type") if filters else "UserWise Summary"
	
	if view_type == "DateWise Summary":
		first_col = {
			"label": "Date",
			"fieldname": "date",
			"fieldtype": "Date",
			"width": 120
		}
	else:
		first_col = {
			"label": "User Name",
			"fieldname": "user_name",
			"fieldtype": "Data",
			"width": 180
		}

	return [
		first_col,
		{
			"label": "Department",
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 160
		},
		{
			"label": "No. Of Sale Bills",
			"fieldname": "no_of_sale_bills",
			"fieldtype": "Int",
			"width": 120
		},
		{
			"label": "Sale Amount",
			"fieldname": "sale_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "No. Of Returns",
			"fieldname": "no_of_returns",
			"fieldtype": "Int",
			"width": 110
		},
		{
			"label": "Ret. Amount",
			"fieldname": "return_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "Credit Amount",
			"fieldname": "credit_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "Cash Amount",
			"fieldname": "cash_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "Card Amount",
			"fieldname": "card_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "Net Amount",
			"fieldname": "net_amount",
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

	if filters.get("ipd_opd_effect"):
		eff = filters.get("ipd_opd_effect")
		if eff == "IPD Effect":
			conditions.append("sb.custom_ipd_effect = 1")
		elif eff == "OPD Effect":
			conditions.append("(sb.custom_ipd_effect = 0 OR sb.custom_ipd_effect IS NULL)")

	if filters.get("payment_type"):
		ptype = filters.get("payment_type")
		if ptype == "Cash":
			conditions.append("EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash')")
		elif ptype == "Credit":
			conditions.append("(si.outstanding_amount > 0 OR NOT EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash'))")

	where_clause = f"AND {' AND '.join(conditions)}" if conditions else ""

	view_type = filters.get("view_type") or "UserWise Summary"
	group_by = "si.posting_date, sb.department" if view_type == "DateWise Summary" else "si.owner, sb.department"
	order_by = "si.posting_date DESC, sb.department ASC" if view_type == "DateWise Summary" else "si.owner ASC, sb.department ASC"

	query = f"""
		SELECT
			si.posting_date AS date,
			si.owner AS user_name,
			COALESCE(NULLIF(sb.department, ''), 'KAMALNAYAN BAJAJ PHARMACY') AS department,
			SUM(CASE WHEN IFNULL(si.is_return, 0) = 0 THEN 1 ELSE 0 END) AS no_of_sale_bills,
			SUM(CASE WHEN IFNULL(si.is_return, 0) = 0 THEN si.grand_total ELSE 0 END) AS sale_amount,
			SUM(CASE WHEN si.is_return = 1 THEN 1 ELSE 0 END) AS no_of_returns,
			SUM(CASE WHEN si.is_return = 1 THEN ABS(si.grand_total) ELSE 0 END) AS return_amount,
			SUM(CASE WHEN si.outstanding_amount > 0 THEN si.outstanding_amount ELSE 0 END) AS credit_amount,
			SUM(IFNULL(sip.cash_amt, 0)) AS cash_amount,
			SUM(IFNULL(sip.card_amt, 0)) AS card_amount
		FROM `tabSales Invoice` si
		LEFT JOIN `tabSale Bill` sb ON sb.consolidated_invoice = si.name
		LEFT JOIN (
			SELECT parent,
				SUM(CASE WHEN mode_of_payment = 'Cash' THEN amount ELSE 0 END) AS cash_amt,
				SUM(CASE WHEN mode_of_payment IN ('Card', 'Credit Card', 'Debit Card', 'Cheque', 'Bank Draft', 'Online') THEN amount ELSE 0 END) AS card_amt
			FROM `tabSales Invoice Payment`
			GROUP BY parent
		) sip ON sip.parent = si.name
		WHERE si.docstatus = 1 {where_clause}
		GROUP BY {group_by}
		ORDER BY {order_by}
	"""

	data = frappe.db.sql(query, params, as_dict=True)

	total_sale_bills = 0
	total_sale_amt = 0.0
	total_returns = 0
	total_ret_amt = 0.0
	total_credit_amt = 0.0
	total_cash_amt = 0.0
	total_card_amt = 0.0
	total_net_amt = 0.0

	for row in data:
		s_amt = flt(row.sale_amount)
		r_amt = flt(row.return_amount)
		c_amt = flt(row.credit_amount)
		cash_amt = flt(row.cash_amount)
		card_amt = flt(row.card_amount)
		n_amt = s_amt - r_amt

		row.sale_amount = s_amt
		row.return_amount = r_amt
		row.credit_amount = c_amt
		row.cash_amount = cash_amt
		row.card_amount = card_amt
		row.net_amount = n_amt

		total_sale_bills += row.no_of_sale_bills or 0
		total_sale_amt += s_amt
		total_returns += row.no_of_returns or 0
		total_ret_amt += r_amt
		total_credit_amt += c_amt
		total_cash_amt += cash_amt
		total_card_amt += card_amt
		total_net_amt += n_amt

	if data:
		data.append({
			"user_name": "<b>Total</b>",
			"date": "<b>Total</b>",
			"department": "",
			"no_of_sale_bills": total_sale_bills,
			"sale_amount": total_sale_amt,
			"no_of_returns": total_returns,
			"return_amount": total_ret_amt,
			"credit_amount": total_credit_amt,
			"cash_amount": total_cash_amt,
			"card_amount": total_card_amt,
			"net_amount": total_net_amt
		})

	return data
