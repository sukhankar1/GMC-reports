# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "user_name",
			"label": "User Name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "sale",
			"label": "Sale",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "sale_return",
			"label": "Sale Return",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "total",
			"label": "Total",
			"fieldtype": "Currency",
			"width": 150
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	invoices = frappe.db.sql(f"""
		SELECT 
			si.owner,
			si.is_return,
			si.grand_total
		FROM `tabSales Invoice` si
		LEFT JOIN `tabSale Bill` sb ON si.name = sb.consolidated_invoice
		WHERE si.docstatus = 1 {conditions}
	""", filters, as_dict=1)
	
	user_wise_data = {}
	
	for inv in invoices:
		user = inv.owner
		if user not in user_wise_data:
			user_wise_data[user] = {
				"user_name": user, 
				"sale": 0.0, 
				"sale_return": 0.0, 
				"total": 0.0
			}
			
		if inv.is_return:
			# In ERPNext, return invoice grand_total is typically negative.
			# Using abs() ensures it displays as a positive amount in the "Sale Return" column.
			user_wise_data[user]["sale_return"] += inv.grand_total
		else:
			user_wise_data[user]["sale"] += inv.grand_total

	data = []
	total_sale = 0.0
	total_sale_return = 0.0
	grand_total_all = 0.0
	
	for user, row in user_wise_data.items():
		# Total is Sale minus Sale Return
		row["total"] = row["sale"] + row["sale_return"]
		
		total_sale += row["sale"]
		total_sale_return += row["sale_return"]
		grand_total_all += row["total"]
		
		# Leave Sale or Sale Return column blank if it is 0
		if row["sale"] == 0:
			row["sale"] = ""
		if row["sale_return"] == 0:
			row["sale_return"] = ""
			
		data.append(row)
		
	# Append grand total row at the end
	if data:
		data.append({
			"user_name": "<b>Grand Total</b>",
			"sale": total_sale,
			"sale_return": total_sale_return,
			"total": grand_total_all
		})
		
	return data

def get_conditions(filters):
	conditions = ""
	if filters:
		if filters.get("from_date") and filters.get("to_date"):
			conditions += " AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s"
		elif filters.get("from_date"):
			conditions += " AND si.posting_date >= %(from_date)s"
		elif filters.get("to_date"):
			conditions += " AND si.posting_date <= %(to_date)s"
			
		if filters.get("department"):
			conditions += " AND sb.department = %(department)s"
			
		if filters.get("users"):
			users = filters.get("users")
			if isinstance(users, str):
				import json
				try:
					users = json.loads(users)
				except:
					users = [users]
			filters["users"] = tuple(users)
			conditions += " AND si.owner IN %(users)s"
	return conditions
