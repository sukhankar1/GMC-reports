// Copyright (c) 2026, Quantbit HIMS Integration and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["FSN Analysis"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
			width: "90",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
			width: "90",
		},
		{
			fieldname: "company",
			label: __("Hospital Name"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			width: "120",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
			width: "120",
		},
		{
			fieldname: "analysis_type",
			label: __("Analysis Type"),
			fieldtype: "Select",
			options: "Average Stay\nconsumption rate\nCombine",
			default: "Average Stay",
			width: "110",
		},
		{
			fieldname: "fsn_type",
			label: __("Movement Type"),
			fieldtype: "Select",
			options: "All\nFast Moving\nSlow Moving\nNon Moving",
			default: "All",
			width: "110",
		},
	],
};
