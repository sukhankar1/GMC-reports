# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
		{"label": "User Name", "fieldname": "user_name", "fieldtype": "Data", "width": 150},
		{"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": "No of Sale Bills", "fieldname": "no_of_sale_bills", "fieldtype": "Int", "width": 120},
		{"label": "Sale Amount", "fieldname": "sale_amount", "fieldtype": "Currency", "width": 120},
		{"label": "No of Returns", "fieldname": "no_of_returns", "fieldtype": "Int", "width": 120},
		{"label": "Return Amount", "fieldname": "return_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Credit Amount", "fieldname": "credit_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Cash Amount", "fieldname": "cash_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Card Amount", "fieldname": "card_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Net Amount", "fieldname": "net_amount", "fieldtype": "Currency", "width": 120},
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	query = f"""
		SELECT
			si.posting_date AS date,
			si.owner AS user_name,
			sb.department AS department,
			SUM(CASE WHEN IFNULL(si.is_return, 0) = 0 AND sb.consolidated_invoice IS NOT NULL THEN 1 ELSE 0 END) AS no_of_sale_bills,
			SUM(CASE WHEN IFNULL(si.is_return, 0) = 0 AND sb.consolidated_invoice IS NOT NULL THEN si.grand_total ELSE 0 END) AS sale_amount,
			SUM(CASE WHEN si.is_return = 1 THEN 1 ELSE 0 END) AS no_of_returns,
			SUM(CASE WHEN si.is_return = 1 THEN si.grand_total ELSE 0 END) AS return_amount,
			SUM(CASE WHEN si.outstanding_amount > 0 THEN si.outstanding_amount ELSE 0 END) AS credit_amount,
			SUM(CASE WHEN sip.has_cash = 1 THEN si.grand_total ELSE 0 END) AS cash_amount,
			SUM(CASE WHEN sip.has_card = 1 THEN si.grand_total ELSE 0 END) AS card_amount
		FROM `tabSales Invoice` si
		LEFT JOIN `tabSale Bill` sb ON sb.consolidated_invoice = si.name
		LEFT JOIN (
			SELECT parent,
				MAX(CASE WHEN mode_of_payment = 'Cash' THEN 1 ELSE 0 END) AS has_cash,
				MAX(CASE WHEN mode_of_payment != 'Cash' AND mode_of_payment IS NOT NULL THEN 1 ELSE 0 END) AS has_card
			FROM `tabSales Invoice Payment`
			GROUP BY parent
		) sip ON sip.parent = si.name
		WHERE si.docstatus = 1 {conditions}
		GROUP BY si.posting_date, si.owner, sb.department
		ORDER BY si.posting_date DESC
	"""
	
	data = frappe.db.sql(query, filters, as_dict=True)
	
	for row in data:
		row.return_amount = abs(flt(row.return_amount))
		row.net_amount = flt(row.sale_amount) - row.return_amount
	
	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += " AND si.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND si.posting_date <= %(to_date)s"
	if filters.get("patient"):
		conditions += " AND si.patient = %(patient)s"
	if filters.get("department"):
		conditions += " AND sb.department = %(department)s"
	if filters.get("mode_of_payment"):
		conditions += " AND EXISTS(SELECT name FROM `tabSales Invoice Payment` WHERE parent=si.name AND mode_of_payment=%(mode_of_payment)s)"
	return conditions
