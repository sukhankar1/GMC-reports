// Copyright (c) 2026, Quantbit Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Item Based Stock Report"] = {
	"filters": [
		{
			"fieldname": "as_on_date",
			"label": __("As On Date"),
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
			"fieldname": "item_name",
			"label": __("Item Name"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "view_type",
			"label": __("Report View"),
			"fieldtype": "Select",
			"options": "Summary\nDetail",
			"default": "Summary"
		},
		{
			"fieldname": "category",
			"label": __("Category"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname": "sub_category",
			"label": __("Sub Category"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname": "substitute_item",
			"label": __("Substitute Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nInactive"
		},
		{
			"fieldname": "order_by",
			"label": __("Order By"),
			"fieldtype": "Select",
			"options": "Item Name\nItem Code\nStock Quantity",
			"default": "Item Name"
		},
		{
			"fieldname": "bin_location",
			"label": __("Bin Location"),
			"fieldtype": "Link",
			"options": "Bin Location"
		},
		{
			"fieldname": "show_zero_stock",
			"label": __("Show Zero Stock"),
			"fieldtype": "Check"
		}
	]
};
