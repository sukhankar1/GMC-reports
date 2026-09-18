// Copyright (c) 2026, Quantbit HIMS Integration and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Re-Order Level Report"] = {
	filters: [
		{
			fieldname: "date",
			label: __("Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
			width: "90",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
			width: "120",
		},
		{
			fieldname: "therapeutic_group",
			label: __("Therapeutic Group"),
			fieldtype: "Link",
			options: "Classification",
			width: "110",
		},
		{
			fieldname: "therapeutic_sub_group",
			label: __("Therapeutic Sub Group"),
			fieldtype: "Link",
			options: "Classification Type",
			width: "110",
		},
		{
			fieldname: "rol_amount",
			label: __("ROL Amount"),
			fieldtype: "Select",
			options: "All\nBelow ROL\nAt/Above ROL",
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