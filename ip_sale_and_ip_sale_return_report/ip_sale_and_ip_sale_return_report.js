// Copyright (c) 2024, Quantbit Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["IP Sale and IP Sale Return Report"] = {
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
			"fieldname": "patient_name",
			"label": __("Patient Name"),
			"fieldtype": "Data",
			"placeholder": __("Search Patient Name")
		},
		{
			"fieldname": "transaction_type",
			"label": __("Transaction Type"),
			"fieldtype": "Select",
			"options": "\nBoth\nSale\nSale Return",
			"default": "Both"
		},
		{
			"fieldname": "parent_category",
			"label": __("Parent Category"),
			"fieldtype": "Link",
			"options": "Item Group"
		}
	]
};
