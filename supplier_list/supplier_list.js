// Copyright (c) 2026, Quantbit HIMS Integration and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Supplier List"] = {
	filters: [
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
			width: "140",
		},
		{
			fieldname: "transaction_type",
			label: __("Transaction Type"),
			fieldtype: "Select",
			options: "\nCompany\nIndividual\nPartnership\nCash\nCredit",
			width: "120",
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
