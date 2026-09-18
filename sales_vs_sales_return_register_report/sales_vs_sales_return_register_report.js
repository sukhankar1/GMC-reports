// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Vs Sales Return Register Report"] = {
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
			"fieldname": "ipd_opd_effect",
			"label": __("IPD/OPD Effect"),
			"fieldtype": "Select",
			"options": "All\nIPD Effect\nOPD Effect",
			"default": "All"
		},
		{
			"fieldname": "view_type",
			"label": __("View Type"),
			"fieldtype": "Select",
			"options": "UserWise Summary\nDateWise Summary",
			"default": "UserWise Summary"
		},
		{
			"fieldname": "counter",
			"label": __("Counter"),
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
