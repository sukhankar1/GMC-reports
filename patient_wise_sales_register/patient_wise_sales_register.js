// Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
// For license information, please see license.txt

frappe.query_reports["Patient Wise Sales Register"] = {
	"filters": [
		{ "fieldname": "from_date", "label": __("From Date"), "fieldtype": "Date", "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1), "reqd": 1 },
		{ "fieldname": "to_date", "label": __("To Date"), "fieldtype": "Date", "default": frappe.datetime.get_today(), "reqd": 1 },
		{ "fieldname": "patient", "label": __("Patient"), "fieldtype": "Link", "options": "Patient" },
		{ "fieldname": "mode_of_payment", "label": __("Payment Type"), "fieldtype": "Link", "options": "Mode of Payment" },
		{ "fieldname": "department", "label": __("Department"), "fieldtype": "Link", "options": "Medical Department" }
	]
};
