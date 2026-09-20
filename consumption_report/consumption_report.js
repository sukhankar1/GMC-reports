// Copyright (c) 2024, Quantbit Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Consumption Report"] = {
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
			"fieldname": "item_name",
			"label": __("Item Name"),
			"fieldtype": "Link",
			"options": "Item",
			"placeholder": __("Enter Item")
		},
		{
			"fieldname": "valuation",
			"label": __("Valuation"),
			"fieldtype": "Select",
			"options": "Unit Purchase Rate\nEPR\nMRP\nCost Price",
			"default": "Unit Purchase Rate"
		},
		{
			"fieldname": "therapeutic_group",
			"label": __("Therapeutic Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname": "type_filter",
			"label": __("Consumption Type"),
			"fieldtype": "Select",
			"options": "All\nDeptWise\nPatientWise",
			"default": "All"
		}
	]
};
