# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": "Type", "fieldname": "patient_category", "fieldtype": "Data", "width": 120},
		{"label": "Bill Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Bill Type", "fieldname": "bill_type", "fieldtype": "Data", "width": 120},
		{"label": "Bill No.", "fieldname": "sb_name", "fieldtype": "Data", "width": 120},
		{"label": "Issue Date & Time", "fieldname": "creation", "fieldtype": "Datetime", "width": 160},
		{"label": "UHID", "fieldname": "custom_uhid", "fieldtype": "Data", "width": 120},
		{"label": "Patient Name", "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 150},
		{"label": "IPD Effect", "fieldname": "custom_ipd_effect", "fieldtype": "Data", "width": 100},
		{"label": "Company Type", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 120},
		{"label": "Department Name", "fieldname": "department", "fieldtype": "Data", "width": 120},
		{"label": "Doctor", "fieldname": "consulting_doctor", "fieldtype": "Data", "width": 150},
		{"label": "User Name", "fieldname": "owner", "fieldtype": "Data", "width": 120},
		{"label": "Category", "fieldname": "custom_category", "fieldtype": "Data", "width": 120},
		{"label": "Subcategory", "fieldname": "item_group", "fieldtype": "Data", "width": 120},
		{"label": "HSN Code", "fieldname": "gst_hsn_code", "fieldtype": "Data", "width": 100},
		{"label": "Is Consignment", "fieldname": "custom_consignment_items", "fieldtype": "Data", "width": 100},
		{"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": "Material Description", "fieldname": "description", "fieldtype": "Data", "width": 150},
		{"label": "High Risk Medicine", "fieldname": "custom_high_risk_drug", "fieldtype": "Data", "width": 100},
		{"label": "Basic Rate", "fieldname": "rate", "fieldtype": "Currency", "width": 100},
		{"label": "Payment Type", "fieldname": "mode_of_payment", "fieldtype": "Data", "width": 120},
		{"label": "Quantity", "fieldname": "qty", "fieldtype": "Float", "width": 100},
		{"label": "EPR", "fieldname": "epr", "fieldtype": "Currency", "width": 100},
		{"label": "Concession (%)", "fieldname": "additional_discount_percentage", "fieldtype": "Percent", "width": 120},
		{"label": "Concession Amt.", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Bill Value", "fieldname": "bill_value", "fieldtype": "Currency", "width": 100},
		{"label": "Net Total Amt.", "fieldname": "net_total", "fieldtype": "Currency", "width": 120},
	]

def get_data(filters):
	conditions = ""
	
	if filters.get("from_date"):
		conditions += " AND si.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND si.posting_date <= %(to_date)s"
	if filters.get("patient"):
		conditions += " AND si.patient = %(patient)s"
	if filters.get("department"):
		conditions += " AND si.department = %(department)s"
	if filters.get("mode_of_payment"):
		conditions += " AND EXISTS(SELECT name FROM `tabSales Invoice Payment` WHERE parent=si.name AND mode_of_payment=%(mode_of_payment)s)"
		
	query = f"""
		SELECT 
			p.patient_category,
			si.posting_date,
			'Sales Invoice' AS bill_type,
			sb.name as sb_name,
			si.creation,
			p.uhid AS custom_uhid,
			p.full_name AS patient,
			sb.custom_ipd_effect,
			si.customer,
			sb.department,
			p.consulting_doctor,
			si.owner,
			i.custom_category,
			i.item_group,
			i.gst_hsn_code,
			i.custom_consignment_items,
			sii.item_code,
			i.description,
			i.custom_high_risk_drug,
			sii.rate,
			(SELECT GROUP_CONCAT(mode_of_payment SEPARATOR ', ') FROM `tabSales Invoice Payment` WHERE parent = si.name) AS mode_of_payment,
			sii.qty,
			sii.amount AS epr,
			si.additional_discount_percentage,
			si.discount_amount,
			sii.amount AS bill_value,			
			si.grand_total AS net_total
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		LEFT JOIN `tabPatient` p ON si.patient = p.name
		LEFT JOIN `tabItem` i ON sii.item_code = i.name
		LEFT JOIN `tabSale Bill` sb ON sb.consolidated_invoice = si.name
		WHERE si.docstatus = 1 {conditions}
		ORDER BY si.posting_date DESC, si.name DESC
	"""
	
	return frappe.db.sql(query, filters, as_dict=True)
