// Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Balance Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},

		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},

		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},

		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},

		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "MultiSelectList",
			options: "Item",
		},

		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "MultiSelectList",
			options: "Warehouse",
		},

		{
			fieldname: "custom_classification",
			label: __("Classification"),
			fieldtype: "Link",
			options: "Classification",
		},

		{
			fieldname: "custom_department_name",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},

		{
			fieldname: "valuation_field_type",
			label: __("Valuation Field Type"),
			fieldtype: "Select",
			options: "Currency\nFloat",
			default: "Currency",
		},
	],

	onload: function (report) {
		report.page.add_inner_button(__("View Stock Ledger"), function () {
			let filters = report.get_values();

			frappe.set_route("query-report", "Stock Ledger", filters);
		});
	},
};
