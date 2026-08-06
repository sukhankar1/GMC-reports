# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

from erpnext.accounts.report.purchase_register.purchase_register import _execute


def execute(filters=None):
	filters = filters or {}
	department_column = {
		"label": "Department",
		"fieldname": "department",
		"fieldtype": "Link",
		"options": "Department",
		"width": 120,
	}
	result = _execute(filters, additional_table_columns=[department_column])

	if filters.get("department"):
		result = list(result)
		result[1] = [row for row in result[1] if row.get("department") == filters.get("department")]
		result = tuple(result)

	return result
