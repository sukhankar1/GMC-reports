// Copyright (c) 2026, Quantbit Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Item Ledger"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.nowdate(), -1),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.nowdate(),
			"reqd": 1
		},
		{
			"fieldname": "hospital_name",
			"label": __("Hospital Name"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "voucher_name",
			"label": __("Voucher Name"),
			"fieldtype": "Select",
			"options": "\nConsumption\nStock Transferred\nMaterial Receipt\nMaterial Issue\nSales Invoice\nPurchase Receipt\nDelivery Note"
		},
		{
			"fieldname": "item_name",
			"label": __("Item Name"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "therapeutic_group",
			"label": __("Therapeutic Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		}
	]
};
