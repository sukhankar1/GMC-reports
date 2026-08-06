import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "bill_no",
			"label": "Bill No",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "patient_name",
			"label": "Patient Name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "department",
			"label": "Department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 150
		},
		{
			"fieldname": "cash",
			"label": "Cash",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "upi_hospital",
			"label": "UPI Hospital",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "credit_sale",
			"label": "Credit Sale",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "debit_card",
			"label": "Debit Card",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "credit_card",
			"label": "Credit Card",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "total_collection",
			"label": "Total Collection",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "total",
			"label": "Total",
			"fieldtype": "Currency",
			"width": 120
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	invoices = frappe.db.sql(f"""
		SELECT 
			si.name,
			si.owner,
			sb.consolidated_invoice,
			si.custom_patient_name,
			sb.department,
			si.grand_total,
			sip.mode_of_payment,
			sip.amount
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Payment` sip ON sip.parent = si.name
		INNER JOIN `tabSale Bill` sb ON si.name = sb.consolidated_invoice
		WHERE si.docstatus = 1 {conditions}
	""", filters, as_dict=1)
	
	user_invoices = {}
	
	for row in invoices:
		user = row.owner
		inv_id = row.name
		
		if user not in user_invoices:
			user_invoices[user] = {}
			
		if inv_id not in user_invoices[user]:
			user_invoices[user][inv_id] = {
				"bill_no": row.consolidated_invoice,
				"patient_name": row.custom_patient_name,
				"department": row.department,
				"cash": 0.0,
				"upi_hospital": 0.0,
				"credit_sale": 0.0,
				"debit_card": 0.0,
				"credit_card": 0.0,
				"total_collection": 0.0,
				"total": 0.0
			}
			
		mop = row.mode_of_payment
		# The user explicitly requested to use grand_total instead of the payment amount
		amount = row.grand_total or 0.0
		
		if mop == "Cash":
			user_invoices[user][inv_id]["cash"] += amount
		elif mop == "Online":
			user_invoices[user][inv_id]["upi_hospital"] += amount
		elif mop in ("Bank Draft", "Cheque"):
			user_invoices[user][inv_id]["debit_card"] += amount
		elif mop == "Credit Card":
			user_invoices[user][inv_id]["credit_card"] += amount
			
		if mop and mop != "Cash":
			user_invoices[user][inv_id]["credit_sale"] += amount

	data = []
	
	grand_totals = {
		"cash": 0.0,
		"upi_hospital": 0.0,
		"credit_sale": 0.0,
		"debit_card": 0.0,
		"credit_card": 0.0,
		"total_collection": 0.0,
		"total": 0.0
	}
	for user, inv_map in user_invoices.items():
		# The top header row has been removed per user request
		
		sub_totals = {
			"cash": 0.0,
			"upi_hospital": 0.0,
			"credit_sale": 0.0,
			"debit_card": 0.0,
			"credit_card": 0.0,
			"total_collection": 0.0,
			"total": 0.0
		}
		
		for inv_id, r in inv_map.items():
			r["total_collection"] = r["cash"] + r["upi_hospital"] + r["debit_card"]
			r["total"] = r["cash"] + r["upi_hospital"] + r["credit_sale"] + r["debit_card"] + r["credit_card"]
			
			for k in sub_totals:
				sub_totals[k] += r[k]
				grand_totals[k] += r[k]
				
			# Blank out zero values in the row
			for k in sub_totals:
				if r[k] == 0:
					r[k] = ""
				
			data.append(r)
			
		# Add Sub Total row but label it with the user's name
		sub_totals_row = {
			"bill_no": f"<b>User Name : {user}</b>",
			"patient_name": "",
			"department": ""
		}
		for k in sub_totals:
			sub_totals_row[k] = sub_totals[k] if sub_totals[k] != 0 else ""
			
		data.append(sub_totals_row)
		
		# Add empty row for spacing between users
		data.append({})
		
	if data:
		grand_totals_row = {
			"bill_no": "<b>Grand Total</b>",
			"patient_name": "",
			"department": ""
		}
		for k in grand_totals:
			grand_totals_row[k] = grand_totals[k] if grand_totals[k] != 0 else ""
			
		data.append(grand_totals_row)
		
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
