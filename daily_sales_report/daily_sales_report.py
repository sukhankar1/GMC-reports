# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "customer",
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 200
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "amount",
			"label": "Amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		}
	]

def get_data(filters):
	conditions = "si.docstatus = 1"
	
	if filters.get("from_date"):
		conditions += " AND si.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND si.posting_date <= %(to_date)s"

	query = f"""
		SELECT
			si.customer AS customer,
			si.status AS status,
			SUM(si.grand_total) AS amount,
			si.currency AS currency
		FROM
			`tabSales Invoice` si
		LEFT JOIN
			`tabSales Invoice Payment` sip 
			ON sip.parent = si.name 
			AND sip.parenttype = 'Sales Invoice'
		WHERE
			{conditions}
		GROUP BY
			si.customer, si.status, si.currency
		ORDER BY
			si.customer, si.status
	"""

	return frappe.db.sql(query, filters, as_dict=1)