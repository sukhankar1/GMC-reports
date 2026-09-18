// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Department Wise Collection Detail Report"] = {
	"filters": [
		{
			"fieldname": "from_date_time",
			"label": __("From Date Time"),
			"fieldtype": "Datetime",
			"default": frappe.datetime.now_date() + " 00:00:00"
		},
		{
			"fieldname": "to_date_time",
			"label": __("To Date Time"),
			"fieldtype": "Datetime",
			"default": frappe.datetime.now_date() + " 23:59:59"
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "report_type",
			"label": __("Report Type"),
			"fieldtype": "Select",
			"options": "Detail\nSummary",
			"default": "Detail"
		},
		{
			"fieldname": "payment_type",
			"label": __("Payment Type"),
			"fieldtype": "Select",
			"options": "All\nCash\nCredit",
			"default": "All"
		},
		{
			"fieldname": "users",
			"label": __("User"),
			"fieldtype": "MultiSelectList",
			"get_data": function(txt) {
				return frappe.db.get_link_options("User", txt);
			}
		}
	]
};
