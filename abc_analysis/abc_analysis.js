// Copyright (c) 2024, Quantbit Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["ABC Analysis"] = {
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
			"fieldname": "therapeutic_group",
			"label": __("Therapeutic Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		}
	]
};
