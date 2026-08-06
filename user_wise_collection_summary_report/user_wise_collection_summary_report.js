// Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
// For license information, please see license.txt

frappe.query_reports["User Wise Collection Summary Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "users",
			"label": __("User"),
			"fieldtype": "MultiSelectList",
			"get_data": function (txt) {
				return frappe.db.get_link_options("User", txt);
			}
		}
	]
};
