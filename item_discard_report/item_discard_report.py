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
			"fieldname": "discard_no",
			"label": _("Discard No."),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "discard_date",
			"label": _("Discard Date"),
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "department",
			"label": _("Department"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "category",
			"label": _("Category"),
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"fieldname": "unit",
			"label": _("Unit"),
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"fieldname": "batch_no",
			"label": _("Batch No."),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "mrp",
			"label": _("MRP"),
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"fieldname": "discard_qty",
			"label": _("Discard Qty."),
			"fieldtype": "Float",
			"precision": 2,
			"width": 100,
		},
		{
			"fieldname": "unit_purchase_rate",
			"label": _("Unit Purchase Rate"),
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"fieldname": "purchase_value",
			"label": _("Purchase Value"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "remark",
			"label": _("Remark"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100,
		},
	]


def get_data(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	item_filter = filters.get("item_name")

	# Fetch item categories & MRP
	item_map = {}
	item_records = frappe.db.sql(
		"""
		SELECT name, item_name, custom_category, item_group
		FROM `tabItem`
	""",
		as_dict=True,
	)
	for i in item_records:
		item_map[i.name] = {
			"item_name": i.item_name,
			"category": i.custom_category or i.item_group or "",
		}

	# Fetch batch MRP
	batch_map = {}
	batch_records = frappe.db.sql(
		"""
		SELECT name, custom_mrp
		FROM `tabBatch`
	""",
		as_dict=True,
	)
	for b in batch_records:
		batch_map[b.name] = flt(b.custom_mrp)

	data = []

	# 1. From Stock Entry Item For Item Discard child table
	item_cond_d = ""
	params_d = {"from_date": from_date, "to_date": to_date}
	if item_filter:
		item_cond_d = "AND (d.item_code = %(item_filter)s OR d.item_name LIKE %(item_like)s)"
		params_d["item_filter"] = item_filter
		params_d["item_like"] = f"%{item_filter}%"

	discard_rows = frappe.db.sql(
		f"""
		SELECT
			se.name AS discard_no,
			se.posting_date AS discard_date,
			se.docstatus,
			se.remarks,
			d.item_code,
			d.item_name,
			d.uom AS unit,
			d.batch_no,
			d.discard_qty,
			d.pur_rate,
			d.total_amount,
			d.discard_method,
			d.department
		FROM `tabStock Entry` se
		JOIN `tabStock Entry Item For Item Discard` d ON d.parent = se.name
		WHERE se.posting_date BETWEEN %(from_date)s AND %(to_date)s
			{item_cond_d}
		ORDER BY se.posting_date ASC, se.name ASC
	""",
		params_d,
		as_dict=True,
	)

	status_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}

	for row in discard_rows:
		cat = item_map.get(row.item_code, {}).get("category", "")
		mrp = batch_map.get(row.batch_no, 0.0)
		status_str = status_map.get(row.docstatus, "Submitted")
		qty = flt(row.discard_qty)
		rate = flt(row.pur_rate)
		val = flt(row.total_amount) or (qty * rate)

		data.append(
			{
				"discard_no": row.discard_no,
				"discard_date": row.discard_date,
				"item_name": row.item_name or row.item_code,
				"department": row.department or "",
				"category": cat,
				"unit": row.unit or "",
				"batch_no": row.batch_no or "",
				"mrp": mrp,
				"discard_qty": qty,
				"unit_purchase_rate": rate,
				"purchase_value": val,
				"remark": row.discard_method or row.remarks or "",
				"status": status_str,
			}
		)

	# 2. Also check Stock Entry Detail with discard / scrap / material issue with discard remarks
	item_cond_se = ""
	params_se = {"from_date": from_date, "to_date": to_date}
	if item_filter:
		item_cond_se = "AND (sed.item_code = %(item_filter)s OR sed.item_name LIKE %(item_like)s)"
		params_se["item_filter"] = item_filter
		params_se["item_like"] = f"%{item_filter}%"

	se_detail_rows = frappe.db.sql(
		f"""
		SELECT
			se.name AS discard_no,
			se.posting_date AS discard_date,
			se.docstatus,
			se.remarks,
			se.stock_entry_type,
			sed.item_code,
			sed.item_name,
			sed.uom AS unit,
			sed.batch_no,
			sed.qty,
			sed.basic_rate,
			sed.amount,
			sed.custom_mrp,
			sed.custom_discard_method,
			sed.department,
			se.custom_department
		FROM `tabStock Entry` se
		JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		WHERE se.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND (sed.custom_discard_method IS NOT NULL AND sed.custom_discard_method != ''
				OR sed.is_scrap_item = 1
				OR se.stock_entry_type = 'Item Discard'
				OR se.stock_entry_type = 'Discard'
				OR se.remarks LIKE '%%discard%%')
			{item_cond_se}
		ORDER BY se.posting_date ASC, se.name ASC
	""",
		params_se,
		as_dict=True,
	)

	for row in se_detail_rows:
		cat = item_map.get(row.item_code, {}).get("category", "")
		mrp = flt(row.custom_mrp) or batch_map.get(row.batch_no, 0.0)
		status_str = status_map.get(row.docstatus, "Submitted")
		qty = flt(row.qty)
		rate = flt(row.basic_rate)
		val = flt(row.amount) or (qty * rate)
		dept = row.department or row.custom_department or ""

		data.append(
			{
				"discard_no": row.discard_no,
				"discard_date": row.discard_date,
				"item_name": row.item_name or row.item_code,
				"department": dept,
				"category": cat,
				"unit": row.unit or "",
				"batch_no": row.batch_no or "",
				"mrp": mrp,
				"discard_qty": qty,
				"unit_purchase_rate": rate,
				"purchase_value": val,
				"remark": row.custom_discard_method or row.remarks or "",
				"status": status_str,
			}
		)

	return data


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
