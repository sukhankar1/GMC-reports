// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Schedule Drug Report"] = {
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
			"fieldname": "schedule_type",
			"label": __("Schedule Type"),
			"fieldtype": "Link",
			"options": "Schedule Type"
		},
		{
			"fieldname": "doctor_name",
			"label": __("Doctor Name"),
			"fieldtype": "Data"
		}
	]
};
