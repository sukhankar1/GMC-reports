// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Sale Return Summary"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "patient_name",
			"label": __("Patient Name"),
			"fieldtype": "Data",
			"placeholder": __("Search Patient Name")
		},
		{
			"fieldname": "deposit",
			"label": __("Deposit"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "visit_name",
			"label": __("Visit Name"),
			"fieldtype": "Link",
			"options": "Visit Details"
		},
		{
			"fieldname": "payment_type",
			"label": __("Payment Type"),
			"fieldtype": "Select",
			"options": "All\nCash\nCredit",
			"default": "All"
		}
	]
};
