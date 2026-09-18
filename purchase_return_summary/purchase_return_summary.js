// Copyright (c) 2026, Quantbit HIMS Integration and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Purchase Return Summary"] = {
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
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
			width: "120",
		},
		{
			fieldname: "payment_type",
			label: __("Payment Type"),
			fieldtype: "Select",
			options: "All\nCash\nCredit",
			default: "All",
			width: "100",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			width: "100",
		},
	],
};
