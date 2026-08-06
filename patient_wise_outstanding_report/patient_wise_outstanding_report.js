// Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributors

frappe.query_reports["Patient Wise Outstanding Report"] = {

	"filters": [

		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(
				frappe.datetime.get_today(),
				-1
			),
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
			"fieldname": "patient",
			"label": __("Patient Name"),
			"fieldtype": "Link",
			"options": "Patient"
		}

	]

};