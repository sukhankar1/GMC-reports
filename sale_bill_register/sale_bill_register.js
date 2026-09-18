// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Sale Bill Register"] = {
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
			"fieldtype": "Data",
			"placeholder": __("Enter Item")
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "patient_name",
			"label": __("Patient Name"),
			"fieldtype": "Data",
			"placeholder": __("Search Patient Name")
		},
		{
			"fieldname": "therapeutic_group",
			"label": __("Therapeutic Group"),
			"fieldtype": "Link",
			"options": "Generic Group"
		},
		{
			"fieldname": "therapeutic_sub_group",
			"label": __("Therapeutic Sub Group"),
			"fieldtype": "Link",
			"options": "Generic Group"
		},
		{
			"fieldname": "payment_mode",
			"label": __("Payment Mode"),
			"fieldtype": "Link",
			"options": "Mode of Payment"
		},
		{
			"fieldname": "schedule_type",
			"label": __("Drug Schedule Type"),
			"fieldtype": "Link",
			"options": "Schedule Type"
		},
		{
			"fieldname": "ward",
			"label": __("Ward"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "ipd_opd_effect",
			"label": __("IPD/OPD Effect"),
			"fieldtype": "Select",
			"options": "All\nIPD Effect\nOPD Effect",
			"default": "All"
		},
		{
			"fieldname": "payment_type",
			"label": __("Payment Type"),
			"fieldtype": "Select",
			"options": "All\nCash\nCredit",
			"default": "All"
		},
		{
			"fieldname": "concession_100",
			"label": __("100% Concession"),
			"fieldtype": "Check",
			"default": 0
		}
	]
};
