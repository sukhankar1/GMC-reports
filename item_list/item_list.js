// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Item List"] = {
	"filters": [
		{
			"fieldname": "classification",
			"label": __("Classification"),
			"fieldtype": "Link",
			"options": "Classification"
		},
		{
			"fieldname": "therapeutic_group",
			"label": __("Therapeutic Group"),
			"fieldtype": "Link",
			"options": "Generic Group"
		},
		{
			"fieldname": "therapeutic_sub_group",
			"label": __("Therapeutic Sub Group"),
			"fieldtype": "Link",
			"options": "Generic Group"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nDisabled"
		}
	]
};
