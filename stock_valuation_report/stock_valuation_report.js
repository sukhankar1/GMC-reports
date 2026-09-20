// Copyright (c) 2026, Quantbit Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Valuation Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.nowdate(), -1),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.nowdate(),
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
			"options": "Item"
		},
		{
			"fieldname": "valuation",
			"label": __("Valuation"),
			"fieldtype": "Select",
			"options": "Unit Purchase Rate\nValuation Rate\nMRP",
			"default": "Unit Purchase Rate"
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
			"fieldname": "therapeutic_sub_group",
			"label": __("Therapeutic Sub Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nInactive"
		},
		{
			"fieldname": "classification",
			"label": __("Classification"),
			"fieldtype": "Link",
			"options": "Classification"
		}
	]
};
