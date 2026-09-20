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
			"fieldname": "department",
			"label": _("Department"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "item_code",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "category_name",
			"label": _("Category Name"),
			"fieldtype": "Data",
			"width": 150,
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
			"width": 110,
		},
		{
			"fieldname": "conversion_factor",
			"label": _("Conversion Factor"),
			"fieldtype": "Float",
			"precision": 2,
			"width": 110,
		},
		{
			"fieldname": "quantity",
			"label": _("Quantity"),
			"fieldtype": "Float",
			"precision": 2,
			"width": 90,
		},
		{
			"fieldname": "purchase_rate",
			"label": _("Purchase Rate"),
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"fieldname": "mrp",
			"label": _("MRP"),
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"width": 120,
		},
	]


def get_data(filters):
	item_filter = filters.get("item_name")
	department_filter = filters.get("department")

	# Fetch item categories
	items = frappe.db.sql(
		"""
		SELECT name, item_name, custom_category, item_group, stock_uom
		FROM `tabItem`
	""",
		as_dict=True,
	)
	item_map = {i.name: i for i in items}

	# Fetch warehouse departments
	whs = frappe.db.sql(
		"""
		SELECT name, warehouse_name, custom_department
		FROM `tabWarehouse`
	""",
		as_dict=True,
	)
	wh_map = {w.name: w for w in whs}

	# Fetch batch info
	batches = frappe.db.sql(
		"""
		SELECT name, expiry_date, custom_mrp
		FROM `tabBatch`
	""",
		as_dict=True,
	)
	batch_map = {b.name: b for b in batches}

	data = []

	# 1. From Stock Entry where purpose = 'Material Receipt' or is_opening = 'Yes' or custom_type = 'Opening'
	se_conds = ["se.docstatus = 1", "(se.purpose = 'Material Receipt' OR se.is_opening = 'Yes')"]
	se_params = {}

	if item_filter:
		se_conds.append("(sed.item_code = %(item_filter)s OR sed.item_name LIKE %(item_like)s)")
		se_params["item_filter"] = item_filter
		se_params["item_like"] = f"%{item_filter}%"

	if department_filter:
		se_conds.append(
			"(sed.department = %(department)s OR se.custom_department = %(department)s OR sed.t_warehouse = %(department)s)"
		)
		se_params["department"] = department_filter

	se_sql = f"""
		SELECT
			se.name AS voucher_no,
			se.posting_date,
			se.custom_department AS se_dept,
			sed.item_code,
			sed.item_name,
			sed.uom,
			sed.batch_no,
			sed.custom_expiry_date,
			sed.conversion_factor,
			sed.qty,
			sed.basic_rate,
			sed.amount,
			sed.custom_mrp,
			sed.department AS sed_dept,
			sed.t_warehouse
		FROM `tabStock Entry` se
		JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		WHERE {' AND '.join(se_conds)}
		ORDER BY se.posting_date ASC, se.name ASC
	"""

	se_rows = frappe.db.sql(se_sql, se_params, as_dict=True)

	for row in se_rows:
		item = item_map.get(row.item_code)
		cat_name = (
			(item.custom_category or item.item_group)
			if item
			else ""
		)
		wh = wh_map.get(row.t_warehouse)
		dept = (
			row.sed_dept
			or row.se_dept
			or (wh.custom_department if wh else "")
			or (wh.warehouse_name if wh else row.t_warehouse)
			or ""
		)

		b_info = batch_map.get(row.batch_no)
		exp_date = (
			row.custom_expiry_date
			or (b_info.expiry_date if b_info else None)
		)
		mrp = flt(row.custom_mrp or (b_info.custom_mrp if b_info else 0.0))
		conv = flt(row.conversion_factor or 1.0)
		qty = flt(row.qty)
		rate = flt(row.basic_rate)
		amt = flt(row.amount or (qty * rate))

		data.append(
			{
				"department": dept,
				"item_code": row.item_code,
				"item_name": row.item_name or (item.item_name if item else row.item_code),
				"category_name": cat_name,
				"unit": row.uom or (item.stock_uom if item else "NOS"),
				"batch_no": row.batch_no or "",
				"expiry_date": exp_date,
				"conversion_factor": conv,
				"quantity": qty,
				"purchase_rate": rate,
				"mrp": mrp,
				"amount": amt,
			}
		)

	# 2. Also check Stock Reconciliation Item if purpose = 'Opening Stock'
	sr_conds = ["sr.docstatus = 1", "(sr.purpose = 'Opening Stock' OR sr.custom_is_opening = 1)"]
	sr_params = {}

	if item_filter:
		sr_conds.append("(sri.item_code = %(item_filter)s OR sri.item_name LIKE %(item_like)s)")
		sr_params["item_filter"] = item_filter
		sr_params["item_like"] = f"%{item_filter}%"

	if department_filter:
		sr_conds.append(
			"(sr.custom_department = %(department)s OR sri.warehouse = %(department)s)"
		)
		sr_params["department"] = department_filter

	try:
		sr_sql = f"""
			SELECT
				sr.name,
				sr.posting_date,
				sr.custom_department,
				sri.item_code,
				sri.item_name,
				sri.warehouse,
				sri.batch_no,
				sri.qty,
				sri.valuation_rate,
				sri.amount
			FROM `tabStock Reconciliation` sr
			JOIN `tabStock Reconciliation Item` sri ON sri.parent = sr.name
			WHERE {' AND '.join(sr_conds)}
			ORDER BY sr.posting_date ASC
		"""
		sr_rows = frappe.db.sql(sr_sql, sr_params, as_dict=True)

		for r in sr_rows:
			item = item_map.get(r.item_code)
			cat_name = (
				(item.custom_category or item.item_group)
				if item
				else ""
			)
			wh = wh_map.get(r.warehouse)
			dept = (
				r.custom_department
				or (wh.custom_department if wh else "")
				or (wh.warehouse_name if wh else r.warehouse)
				or ""
			)
			b_info = batch_map.get(r.batch_no)
			exp_date = b_info.expiry_date if b_info else None
			mrp = flt(b_info.custom_mrp if b_info else 0.0)
			qty = flt(r.qty)
			rate = flt(r.valuation_rate)
			amt = flt(r.amount or (qty * rate))

			data.append(
				{
					"department": dept,
					"item_code": r.item_code,
					"item_name": r.item_name or (item.item_name if item else r.item_code),
					"category_name": cat_name,
					"unit": (item.stock_uom if item else "NOS"),
					"batch_no": r.batch_no or "",
					"expiry_date": exp_date,
					"conversion_factor": 1.0,
					"quantity": qty,
					"purchase_rate": rate,
					"mrp": mrp,
					"amount": amt,
				}
			)
	except Exception:
		pass

	return data


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
