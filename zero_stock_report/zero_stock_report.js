// Copyright (c) 2026, Quantbit Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Zero Stock Report"] = {
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
			"fieldname": "stock_filter",
			"label": __("Stock Filter"),
			"fieldtype": "Check"
		}
	]
};
