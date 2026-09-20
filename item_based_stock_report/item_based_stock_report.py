# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_columns(filters):
	view_type = filters.get("view_type") or "Summary"

	if view_type == "Detail":
		return [
			{
				"fieldname": "dept_name",
				"label": _("Dept Name"),
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"fieldname": "category_name",
				"label": _("Category Name"),
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"fieldname": "item_code",
				"label": _("Itemcode"),
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
				"fieldname": "bin_location",
				"label": _("Bin Location"),
				"fieldtype": "Data",
				"width": 110,
			},
			{
				"fieldname": "mrp",
				"label": _("MRP"),
				"fieldtype": "Currency",
				"width": 90,
			},
			{
				"fieldname": "stock_quantity",
				"label": _("Stock Quantity"),
				"fieldtype": "Float",
				"precision": 2,
				"width": 110,
			},
			{
				"fieldname": "unit_rate",
				"label": _("Unit Rate"),
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

	# Summary View (Image 4)
	return [
		{
			"fieldname": "dept_name",
			"label": _("Dept Name"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "category_name",
			"label": _("Category Name"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "item_code",
			"label": _("Itemcode"),
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
			"fieldname": "unit",
			"label": _("Unit"),
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"fieldname": "bin_location",
			"label": _("Bin Location"),
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"fieldname": "stock_quantity",
			"label": _("Stock Quantity"),
			"fieldtype": "Float",
			"precision": 2,
			"width": 110,
		},
		{
			"fieldname": "unit_rate",
			"label": _("Unit Rate"),
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
	as_on_date = filters.get("as_on_date")
	hospital_name = filters.get("hospital_name")
	item_filter = filters.get("item_name")
	department = filters.get("department")
	view_type = filters.get("view_type") or "Summary"
	category = filters.get("category")
	sub_category = filters.get("sub_category")
	substitute_item = filters.get("substitute_item")
	status = filters.get("status")
	order_by = filters.get("order_by") or "Item Name"
	bin_location = filters.get("bin_location")
	show_zero_stock = filters.get("show_zero_stock")

	# Build Item Conditions
	item_conditions = []
	item_params = {}

	if item_filter:
		item_conditions.append("(i.name = %(item_filter)s OR i.item_name LIKE %(item_like)s)")
		item_params["item_filter"] = item_filter
		item_params["item_like"] = f"%{item_filter}%"

	if category:
		item_conditions.append("(i.custom_category = %(category)s OR i.item_group = %(category)s)")
		item_params["category"] = category

	if sub_category:
		item_conditions.append("(i.item_group = %(sub_category)s)")
		item_params["sub_category"] = sub_category

	if substitute_item:
		item_conditions.append("(i.custom_subtitute_group = %(substitute_item)s)")
		item_params["substitute_item"] = substitute_item

	if status == "Active":
		item_conditions.append("i.disabled = 0")
	elif status == "Inactive":
		item_conditions.append("i.disabled = 1")

	item_cond_sql = f"WHERE {' AND '.join(item_conditions)}" if item_conditions else ""

	# Fetch items
	items = frappe.db.sql(
		f"""
		SELECT
			i.name AS item_code,
			i.item_name,
			i.custom_category,
			i.item_group,
			i.stock_uom,
			i.disabled
		FROM `tabItem` i
		{item_cond_sql}
	""",
		item_params,
		as_dict=True,
	)

	item_map = {i.item_code: i for i in items}
	if not item_map:
		return []

	# Fetch Warehouses
	wh_conditions = []
	wh_params = {}
	if hospital_name:
		wh_conditions.append("(w.company = %(hospital_name)s OR w.company IS NULL)")
		wh_params["hospital_name"] = hospital_name
	if department:
		wh_conditions.append("(w.custom_department = %(department)s OR w.name = %(department)s)")
		wh_params["department"] = department

	wh_cond_sql = f"WHERE {' AND '.join(wh_conditions)}" if wh_conditions else ""
	warehouses = frappe.db.sql(
		f"""
		SELECT name, warehouse_name, custom_department, company
		FROM `tabWarehouse` w
		{wh_cond_sql}
	""",
		wh_params,
		as_dict=True,
	)

	wh_map = {w.name: w for w in warehouses}
	if department and not wh_map:
		wh_map[department] = frappe._dict(
			{"name": department, "custom_department": department, "warehouse_name": department}
		)

	# Fetch Bin locations from Item/Bin/Stock Entry
	bin_loc_map = {}
	bin_loc_records = frappe.db.sql(
		"""
		SELECT sed.item_code, sed.custom_bin_location
		FROM `tabStock Entry Detail` sed
		WHERE sed.custom_bin_location IS NOT NULL AND sed.custom_bin_location != ''
		ORDER BY sed.creation DESC
	""",
		as_dict=True,
	)
	for bl in bin_loc_records:
		if bl.item_code not in bin_loc_map:
			bin_loc_map[bl.item_code] = bl.custom_bin_location

	# Query stock balances per item and warehouse
	item_codes = tuple(item_map.keys())
	wh_names = tuple(wh_map.keys()) if wh_map else tuple()

	bin_conds = ["b.item_code IN %(item_codes)s"]
	b_params = {"item_codes": item_codes}
	if wh_names:
		bin_conds.append("b.warehouse IN %(wh_names)s")
		b_params["wh_names"] = wh_names

	bins = frappe.db.sql(
		f"""
		SELECT
			b.item_code,
			b.warehouse,
			b.actual_qty,
			b.valuation_rate,
			b.stock_uom
		FROM `tabBin` b
		WHERE {' AND '.join(bin_conds)}
	""",
		b_params,
		as_dict=True,
	)

	data = []
	for b in bins:
		qty = flt(b.actual_qty)
		if not show_zero_stock and qty <= 0:
			continue

		item = item_map.get(b.item_code)
		if not item:
			continue

		wh = wh_map.get(b.warehouse)
		dept = (
			wh.custom_department
			if wh and wh.custom_department
			else (wh.warehouse_name if wh else b.warehouse)
		)
		cat = item.custom_category or item.item_group or ""
		bin_loc = bin_loc_map.get(b.item_code, "")
		if bin_location and bin_loc != bin_location:
			continue

		rate = flt(b.valuation_rate)
		amt = qty * rate

		row = {
			"dept_name": dept,
			"category_name": cat,
			"item_code": b.item_code,
			"item_name": item.item_name or b.item_code,
			"unit": item.stock_uom or b.stock_uom or "NOS",
			"bin_location": bin_loc,
			"stock_quantity": qty,
			"unit_rate": rate,
			"amount": amt,
		}

		if view_type == "Detail":
			row["batch_no"] = ""
			row["expiry_date"] = None
			row["mrp"] = 0.0

		data.append(row)

	# If show_zero_stock is checked, include items with no bin record
	if show_zero_stock:
		existing_items = {d["item_code"] for d in data}
		for ic, item in item_map.items():
			if ic not in existing_items:
				dept = department or ""
				cat = item.custom_category or item.item_group or ""
				bin_loc = bin_loc_map.get(ic, "")
				if bin_location and bin_loc != bin_location:
					continue
				row = {
					"dept_name": dept,
					"category_name": cat,
					"item_code": ic,
					"item_name": item.item_name or ic,
					"unit": item.stock_uom or "NOS",
					"bin_location": bin_loc,
					"stock_quantity": 0.0,
					"unit_rate": 0.0,
					"amount": 0.0,
				}
				if view_type == "Detail":
					row["batch_no"] = ""
					row["expiry_date"] = None
					row["mrp"] = 0.0
				data.append(row)

	# Order By
	if order_by == "Item Code":
		data.sort(key=lambda x: x.get("item_code", ""))
	elif order_by == "Stock Quantity":
		data.sort(key=lambda x: x.get("stock_quantity", 0.0), reverse=True)
	else:
		data.sort(key=lambda x: x.get("item_name", ""))

	return data


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
