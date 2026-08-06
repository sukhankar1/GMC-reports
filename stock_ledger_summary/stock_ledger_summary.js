// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// Copyright (c) 2026

frappe.query_reports["Stock Ledger Summary"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},

		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},

		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},

		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "MultiSelectList",
			options: "Warehouse",
		},

		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "MultiSelectList",
			options: "Item",
		},

		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},

		{
			fieldname: "brand",
			label: __("Brand"),
			fieldtype: "Link",
			options: "Brand",
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
			fieldname: "batch_no",
			label: __("Batch No"),
			fieldtype: "Link",
			options: "Batch",
		},

		{
			fieldname: "voucher_no",
			label: __("Voucher #"),
			fieldtype: "Data",
		},

		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},

		{
			fieldname: "include_uom",
			label: __("Include UOM"),
			fieldtype: "Link",
			options: "UOM",
		},

		{
			fieldname: "valuation_field_type",
			label: __("Valuation Field Type"),
			fieldtype: "Select",
			options: "Currency\nFloat",
			default: "Currency",
		},
		{
			fieldname: "segregate_serial_batch_bundle",
			label: __("Segregate Serial / Batch Bundle"),
			fieldtype: "Check",
			default: 0,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "out_qty" && data && data.out_qty < 0) {
			value = "<span style='color:red'>" + value + "</span>";
		}

		if (column.fieldname == "in_qty" && data && data.in_qty > 0) {
			value = "<span style='color:green'>" + value + "</span>";
		}

		return value;
	},

	onload: function (report) {
		report.page.add_inner_button(__("View Stock Balance"), function () {
			let filters = report.get_values();

			frappe.set_route("query-report", "Stock Balance", filters);
		});
	},
};
