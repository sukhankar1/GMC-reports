# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Bill No."),
			"fieldname": "bill_no",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 160,
		},
		{
			"label": _("Bill Date"),
			"fieldname": "bill_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Challan No."),
			"fieldname": "challan_no",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Challan Date"),
			"fieldname": "challan_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Credit/Cash"),
			"fieldname": "pay_mode",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Gross Amount"),
			"fieldname": "gross_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
	]


def get_data(filters):
	conditions, values = get_conditions(filters)

	query = f"""
		SELECT 
			pi.name AS voucher_no,
			COALESCE(NULLIF(pi.bill_no, ''), pi.name) AS bill_no,
			COALESCE(pi.bill_date, pi.posting_date) AS bill_date,
			COALESCE(
				NULLIF(GROUP_CONCAT(DISTINCT pr.supplier_delivery_note SEPARATOR ', '), ''),
				NULLIF(GROUP_CONCAT(DISTINCT pr.custom_sib_no SEPARATOR ', '), ''),
				NULLIF(GROUP_CONCAT(DISTINCT pr.lr_no SEPARATOR ', '), ''),
				NULLIF(GROUP_CONCAT(DISTINCT pii.purchase_receipt SEPARATOR ', '), ''),
				NULLIF(pi.custom_sib_no, ''),
				''
			) AS challan_no,
			COALESCE(
				MAX(pr.custom_delivery_date),
				MAX(pr.custom_sib_date),
				MAX(pr.lr_date),
				MAX(pr.posting_date),
				pi.custom_sib_date,
				pi.posting_date
			) AS challan_date,
			pi.supplier_name AS supplier_name,
			pi.supplier AS supplier,
			pi.mode_of_payment AS mode_of_payment,
			pi.is_paid AS is_paid,
			pi.outstanding_amount AS outstanding_amount,
			pi.grand_total AS gross_amount,
			pi.currency AS currency
		FROM 
			`tabPurchase Invoice` pi
		LEFT JOIN 
			`tabPurchase Invoice Item` pii ON pii.parent = pi.name
		LEFT JOIN 
			`tabPurchase Receipt` pr ON pr.name = pii.purchase_receipt
		WHERE 
			pi.docstatus = 1
			{conditions}
		GROUP BY 
			pi.name
		ORDER BY 
			pi.posting_date DESC, pi.name DESC
	"""

	raw_data = frappe.db.sql(query, values, as_dict=True)
	data = []

	for row in raw_data:
		pay_mode = row.get("mode_of_payment")
		if not pay_mode:
			if row.get("is_paid") or flt(row.get("outstanding_amount")) <= 0:
				pay_mode = "Cash"
			else:
				pay_mode = "Credit"

		data.append({
			"bill_no": row.get("bill_no"),
			"bill_date": row.get("bill_date"),
			"challan_no": row.get("challan_no"),
			"challan_date": row.get("challan_date"),
			"supplier_name": row.get("supplier_name") or row.get("supplier"),
			"pay_mode": pay_mode,
			"gross_amount": flt(row.get("gross_amount")),
			"currency": row.get("currency"),
		})

	return data


def get_conditions(filters):
	conditions = []
	values = {}

	if filters.get("company"):
		conditions.append("pi.company = %(company)s")
		values["company"] = filters.get("company")

	if filters.get("from_date"):
		conditions.append("pi.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("pi.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("supplier"):
		conditions.append("pi.supplier = %(supplier)s")
		values["supplier"] = filters.get("supplier")

	if filters.get("payment_type"):
		payment_type = filters.get("payment_type").strip().lower()
		if payment_type == "cash":
			conditions.append("(pi.mode_of_payment LIKE '%%Cash%%' OR pi.is_paid = 1)")
		elif payment_type == "credit":
			conditions.append("(pi.mode_of_payment LIKE '%%Credit%%' OR (pi.is_paid = 0 AND (pi.mode_of_payment IS NULL OR pi.mode_of_payment = '' OR pi.mode_of_payment NOT LIKE '%%Cash%%')))")

	cond_str = " AND " + " AND ".join(conditions) if conditions else ""
	return cond_str, values