# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.report.purchase_register.purchase_register import _execute

# Map of group_by filter value -> (fieldname, label) used as the grouping key
GROUP_BY_FIELD_MAP = {
	"Supplier": ("supplier", "Supplier"),
	"Supplier Group": ("supplier_group", "Supplier Group"),
	"Department": ("department", "Department"),
}

# fieldtypes that should be summed instead of just carried over from the first row
NUMERIC_FIELDTYPES = ("Currency", "Float", "Int")


def execute(filters=None):
	filters = frappe._dict(filters or {})

	department_column = {
		"label": "Department",
		"fieldname": "department",
		"fieldtype": "Link",
		"options": "Department",
		"width": 120,
	}

	result = _execute(filters, additional_table_columns=[department_column])
	columns, data = result[0], result[1]
	data = list(data)

	# Row-level department filter, same as Purchase Register Details
	if filters.get("department"):
		data = [row for row in data if row.get("department") == filters.get("department")]

	group_by_key, group_by_label = GROUP_BY_FIELD_MAP.get(
		filters.get("group_by") or "Supplier", GROUP_BY_FIELD_MAP["Supplier"]
	)

	summary_columns, summary_data = get_summary(columns, data, group_by_key, group_by_label)

	return summary_columns, summary_data


def get_summary(columns, data, group_by_key, group_by_label):
	numeric_fields = [
		col["fieldname"]
		for col in columns
		if col.get("fieldtype") in NUMERIC_FIELDTYPES and col.get("fieldname") != group_by_key
	]

	# Columns to display: grouping key + supplier name (if grouping by supplier) + numeric totals
	summary_columns = [
		{
			"label": group_by_label,
			"fieldname": group_by_key,
			"fieldtype": "Data" if group_by_key != "supplier" else "Link",
			"options": "" if group_by_key != "supplier" else "Supplier",
			"width": 180,
		}
	]

	if group_by_key == "supplier":
		summary_columns.append(
			{
				"label": "Supplier Name",
				"fieldname": "supplier_name",
				"fieldtype": "Data",
				"width": 180,
			}
		)

	summary_columns.append(
		{
			"label": "No. of Invoices",
			"fieldname": "no_of_invoices",
			"fieldtype": "Int",
			"width": 110,
		}
	)

	for col in columns:
		if col.get("fieldname") in numeric_fields:
			summary_columns.append(
				{
					"label": col.get("label"),
					"fieldname": col.get("fieldname"),
					"fieldtype": col.get("fieldtype"),
					"width": col.get("width") or 120,
				}
			)

	grouped = frappe._dict()

	for row in data:
		key = row.get(group_by_key) or "Not Set"

		if key not in grouped:
			grouped[key] = frappe._dict({group_by_key: key, "no_of_invoices": 0})
			if group_by_key == "supplier":
				grouped[key]["supplier_name"] = row.get("supplier_name")
			for field in numeric_fields:
				grouped[key][field] = 0

		grouped[key]["no_of_invoices"] += 1
		for field in numeric_fields:
			grouped[key][field] = (grouped[key][field] or 0) + (row.get(field) or 0)

	summary_data = list(grouped.values())
	summary_data.sort(key=lambda r: (r.get(group_by_key) or ""))

	return summary_columns, summary_data