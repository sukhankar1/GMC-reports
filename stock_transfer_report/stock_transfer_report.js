// Copyright (c) 2024, Quantbit Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Transfer Report"] = {
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
			"fieldname": "item_name",
			"label": __("Item Name"),
			"fieldtype": "Link",
			"options": "Item",
			"placeholder": __("Enter Item")
		},
		{
			"fieldname": "view_type",
			"label": __("Report View"),
			"fieldtype": "Select",
			"options": "Summary\nDetail",
			"default": "Summary"
		},
		{
			"fieldname": "therapeutic_group",
			"label": __("Therapeutic Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nAccepted\nPending\nRejected"
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
			"fieldname": "indent_type",
			"label": __("Indent Option"),
			"fieldtype": "Select",
			"options": "All\nWithout Indent\nWith Indent",
			"default": "All"
		}
	]
};
