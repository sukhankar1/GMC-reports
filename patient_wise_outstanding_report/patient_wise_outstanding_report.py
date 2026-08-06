# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Patient Name",
			"fieldname": "patient",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": "Patient MRN",
			"fieldname": "mrn",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Outstanding Amount",
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"width": 150
		}
	]


def get_data(filters):

	conditions = ""

	if filters.get("from_date"):
		conditions += " AND si.posting_date >= %(from_date)s"

	if filters.get("to_date"):
		conditions += " AND si.posting_date <= %(to_date)s"

	if filters.get("patient"):
		conditions += " AND si.patient = %(patient)s"


	query = f"""
		SELECT
			p.full_name AS patient,
			p.uhid AS mrn,
			SUM(si.outstanding_amount) AS outstanding_amount

		FROM `tabSales Invoice` si

		LEFT JOIN `tabPatient` p
			ON si.patient = p.name

		WHERE 
			si.docstatus = 1
			AND si.customer = 'Self_Pay'
			AND si.outstanding_amount > 0
			AND si.patient IS NOT NULL
			{conditions}

		GROUP BY
			si.patient

		ORDER BY
			outstanding_amount DESC
	"""

	return frappe.db.sql(query, filters, as_dict=True)