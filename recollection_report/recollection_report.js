// Copyright (c) 2024, Quantbit Technologies Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Recollection Report"] = {
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
			"fieldname": "from_department",
			"label": __("From Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "to_department",
			"label": __("To Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "item_name",
			"label": __("Item Name"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nPending Recollection(Rejected)\nRecollected"
		}
	]
};
