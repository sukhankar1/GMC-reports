# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe
from frappe import _

# Import the standard report's execute method (item-level / detail data)
from erpnext.buying.report.purchase_order_analysis.purchase_order_analysis import execute as standard_execute


def execute(filters=None):
	if not filters:
		filters = {}

	# 1. Run the base ERPNext Purchase Order Analysis report (item-wise detail)
	res = standard_execute(filters)

	# Handle both tuple returns: (columns, data) or (columns, data, message, chart, summary, ...)
	columns = list(res[0])
	data = list(res[1])
	extra_args = res[2:] if len(res) > 2 else ()

	# 2. Add the Department Column
	department_column = {
		"label": _("Department"),
		"fieldname": "department",
		"fieldtype": "Link",
		"options": "Department",
		"width": 140
	}

	# Insert column after "Purchase Order" (or append to the end)
	po_idx = next((i for i, col in enumerate(columns) if col.get("fieldname") == "name"), None)
	if po_idx is not None:
		columns.insert(po_idx + 1, department_column)
	else:
		columns.append(department_column)

	if not data:
		return (columns, data) + extra_args

	# 3. Fetch Department details for all Purchase Orders in the report data
	po_names = list({row.get("name") for row in data if row.get("name")})

	po_departments = {}
	if po_names:
		# Purchase Order has 'department' on the parent header
		po_dept_list = frappe.get_all(
			"Purchase Order",
			filters={"name": ["in", po_names]},
			fields=["name", "department"]
		)
		po_departments = {d["name"]: d.get("department") for d in po_dept_list}

	# 4. Attach Department to each row & apply the Department filter
	filtered_data = []
	selected_dept = filters.get("department")

	for row in data:
		po_name = row.get("name")
		dept = po_departments.get(po_name)
		row["department"] = dept

		# Filter by department if a filter value is selected
		if selected_dept:
			if dept == selected_dept:
				filtered_data.append(row)
		else:
			filtered_data.append(row)

	# Return updated columns and filtered data
	return (columns, filtered_data) + extra_args