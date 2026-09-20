# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"fieldname": "voucher_group",
			"label": _("Voucher Group"),
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"fieldname": "voucher_name",
			"label": _("Voucher Name"),
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"fieldname": "voucher_no",
			"label": _("Voucher No."),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "from_department",
			"label": _("From Department"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "to_department",
			"label": _("To Department"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "unit",
			"label": _("Unit"),
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"fieldname": "batch_no",
			"label": _("Batch No."),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "expiry_date",
			"label": _("Expiry Date"),
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"fieldname": "conversion_factor",
			"label": _("Conversion Factor"),
			"fieldtype": "Float",
			"precision": 2,
			"width": 100,
		},
		{
			"fieldname": "mrp",
			"label": _("MRP"),
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"fieldname": "in_qty",
			"label": _("In Qty."),
			"fieldtype": "Float",
			"precision": 2,
			"width": 90,
		},
		{
			"fieldname": "in_purchase_amount",
			"label": _("Purchase Amount"),
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"fieldname": "out_qty",
			"label": _("Out Qty."),
			"fieldtype": "Float",
			"precision": 2,
			"width": 90,
		},
		{
			"fieldname": "out_purchase_amount",
			"label": _("Purchase Amount"),
			"fieldtype": "Currency",
			"width": 110,
		},
	]


def get_data(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	# Fetch warehouse department mapping
	wh_map = {
		w.name: w.custom_department
		for w in frappe.db.sql("SELECT name, custom_department FROM `tabWarehouse`", as_dict=True)
	}

	# Fetch Stock Entries
	se_records = frappe.db.sql(
		"""
		SELECT
			se.name AS voucher_no,
			se.posting_date AS date,
			se.purpose,
			se.stock_entry_type,
			se.custom_department AS se_from_dept,
			se.custom_to_department AS se_to_dept,
			sed.item_code,
			sed.item_name,
			sed.uom AS unit,
			sed.batch_no,
			sed.custom_expiry_date AS expiry_date,
			sed.conversion_factor,
			sed.custom_mrp AS mrp,
			sed.qty,
			sed.basic_rate,
			sed.amount,
			sed.s_warehouse,
			sed.t_warehouse,
			sed.department AS sed_from_dept,
			sed.to_department AS sed_to_dept,
			b.expiry_date AS batch_expiry_date,
			b.custom_mrp AS batch_mrp
		FROM `tabStock Entry` se
		JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		LEFT JOIN `tabBatch` b ON b.name = sed.batch_no
		WHERE se.docstatus = 1
			AND se.posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY se.posting_date ASC, se.name ASC
	""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)

	data = []
	for row in se_records:
		purpose = row.purpose or row.stock_entry_type or ""
		from_dept = (
			row.sed_from_dept
			or row.se_from_dept
			or wh_map.get(row.s_warehouse)
			or row.s_warehouse
			or ""
		)
		to_dept = (
			row.sed_to_dept
			or row.se_to_dept
			or wh_map.get(row.t_warehouse)
			or row.t_warehouse
			or ""
		)

		mrp = flt(row.mrp or row.batch_mrp or 0.0)
		exp_date = row.expiry_date or row.batch_expiry_date or None
		conv_factor = flt(row.conversion_factor or 1.0)
		qty = flt(row.qty or 0.0)
		amt = flt(row.amount or (qty * flt(row.basic_rate)))

		if purpose == "Material Issue":
			voucher_group = "Department Out"
			voucher_name = "Consumption"
			in_qty = 0.0
			in_amt = 0.0
			out_qty = qty
			out_amt = amt
		elif purpose == "Material Transfer":
			voucher_group = "Department Out"
			voucher_name = "Stock Transferred"
			in_qty = 0.0
			in_amt = 0.0
			out_qty = qty
			out_amt = amt
		elif purpose == "Material Receipt":
			voucher_group = "Department In"
			voucher_name = "Material Receipt"
			in_qty = qty
			in_amt = amt
			out_qty = 0.0
			out_amt = 0.0
		else:
			voucher_group = "Department Out"
			voucher_name = purpose
			in_qty = 0.0
			in_amt = 0.0
			out_qty = qty
			out_amt = amt

		data.append(
			{
				"date": row.date,
				"voucher_group": voucher_group,
				"voucher_name": voucher_name,
				"voucher_no": row.voucher_no,
				"from_department": from_dept,
				"to_department": to_dept,
				"item_name": row.item_name or row.item_code,
				"unit": row.unit,
				"batch_no": row.batch_no,
				"expiry_date": exp_date,
				"conversion_factor": conv_factor,
				"mrp": mrp,
				"in_qty": in_qty,
				"in_purchase_amount": in_amt,
				"out_qty": out_qty,
				"out_purchase_amount": out_amt,
			}
		)

	return data


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
