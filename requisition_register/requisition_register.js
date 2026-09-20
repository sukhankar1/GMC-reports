// Copyright (c) 2024, Quantbit Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Requisition Register"] = {
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
			"fieldname": "from_department",
			"label": __("From Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "to_department",
			"label": __("To Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "item_name",
			"label": __("Item Name"),
			"fieldtype": "Link",
			"options": "Item",
			"placeholder": __("Enter Item")
		},
		{
			"fieldname": "patient_name",
			"label": __("Patient Name"),
			"fieldtype": "Data",
			"placeholder": __("Search Patient Name")
		},
		{
			"fieldname": "type_filter",
			"label": __("Requisition Type"),
			"fieldtype": "Select",
			"options": "All\nPatient\nDepartment",
			"default": "All"
		},
		{
			"fieldname": "issue_status",
			"label": __("Issue Status"),
			"fieldtype": "Select",
			"options": "\nPending\nIssued\nPartially Issued\nCancelled"
		},
		{
			"fieldname": "patient_company",
			"label": __("Patient Company"),
			"fieldtype": "Check"
		},
		{
			"fieldname": "requisition_status",
			"label": __("Requisition Status"),
			"fieldtype": "Select",
			"options": "\nPending\nApproved\nCancelled"
		}
	]
};
