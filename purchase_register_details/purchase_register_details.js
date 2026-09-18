// Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
// For license information, please see license.txt

frappe.query_reports["Purchase Register Details"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
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
			fieldname: "item_code",
			label: __("Item Name"),
			fieldtype: "Link",
			options: "Item",
			width: "120",
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
			width: "120",
		},
		{
			fieldname: "manufacturer",
			label: __("Manufacturer"),
			fieldtype: "Link",
			options: "Brand",
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
			fieldname: "therapeutic_group",
			label: __("Therapeutic Group"),
			fieldtype: "Link",
			options: "Item Group",
			width: "120",
		},
		{
			fieldname: "therapeutic_sub_group",
			label: __("Therapeutic Sub Group"),
			fieldtype: "Link",
			options: "Item Group",
			width: "120",
		},
		{
			fieldname: "payment_type",
			label: __("Payment Type"),
			fieldtype: "Select",
			options: ["All", "Cash", "Credit"],
			default: "All",
			width: "100",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			width: "120",
		},
	],
};
