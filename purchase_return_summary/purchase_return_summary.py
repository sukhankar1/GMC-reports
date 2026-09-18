# Copyright (c) 2026, Quantbit HIMS Integration and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.utils import format_time


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": _("Return No."),
			"fieldname": "return_no",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 140,
		},
		{
			"label": _("Date"),
			"fieldname": "return_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Time"),
			"fieldname": "return_time",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Invoice No."),
			"fieldname": "invoice_no",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Cash / Credit"),
			"fieldname": "pay_mode",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Gross Amount"),
			"fieldname": "gross_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{
			"label": _("Gate Pass No."),
			"fieldname": "gate_pass_no",
			"fieldtype": "Data",
			"width": 130,
		},
	]


def get_data(filters):
	conditions = ["pi.docstatus = 1", "pi.is_return = 1"]
	params = {}

	if filters.get("from_date"):
		conditions.append("pi.posting_date >= %(from_date)s")
		params["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("pi.posting_date <= %(to_date)s")
		params["to_date"] = filters.get("to_date")

	if filters.get("supplier"):
		conditions.append("pi.supplier = %(supplier)s")
		params["supplier"] = filters.get("supplier")

	if filters.get("company"):
		conditions.append("pi.company = %(company)s")
		params["company"] = filters.get("company")

	if filters.get("payment_type") and filters.get("payment_type") != "All":
		pt = filters.get("payment_type")
		if pt == "Cash":
			conditions.append("pi.mode_of_payment = 'Cash'")
		elif pt == "Credit":
			conditions.append("(pi.mode_of_payment != 'Cash' OR pi.mode_of_payment IS NULL OR pi.mode_of_payment = '')")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT 
			pi.name AS return_no,
			pi.posting_date AS return_date,
			pi.posting_time,
			COALESCE(NULLIF(pi.return_against, ''), NULLIF(pi.bill_no, ''), '') AS invoice_no,
			pi.supplier_name,
			COALESCE(NULLIF(pi.mode_of_payment, ''), 'Credit') AS pay_mode,
			ABS(COALESCE(pi.base_grand_total, pi.grand_total, 0.0)) AS gross_amount,
			COALESCE(NULLIF(pi.custom_sib_no, ''), '') AS gate_pass_no,
			pi.currency AS currency
		FROM 
			`tabPurchase Invoice` pi
		WHERE 
			{where_clause}
		ORDER BY 
			pi.posting_date DESC, pi.posting_time DESC, pi.name DESC
	"""

	rows = frappe.db.sql(query, params, as_dict=True)

	for r in rows:
		if r.get("posting_time"):
			try:
				r["return_time"] = format_time(r["posting_time"], "hh:mm a")
			except Exception:
				r["return_time"] = str(r["posting_time"])
		else:
			r["return_time"] = ""

	return rows
