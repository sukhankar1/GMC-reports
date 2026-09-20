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
			"width": 220,
		},
		{
			"fieldname": "balance_stock",
			"label": _("Balance Stock"),
			"fieldtype": "Float",
			"precision": 2,
			"width": 120,
		},
		{
			"fieldname": "sales",
			"label": _("Sales"),
			"fieldtype": "Float",
			"precision": 2,
			"width": 120,
		},
		{
			"fieldname": "supplier_name",
			"label": _("Supplier Name"),
			"fieldtype": "Data",
			"width": 200,
		},
	]


def get_data(filters):
	department = filters.get("department")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	stock_filter = filters.get("stock_filter")

	warehouses = []
	if department:
		wh_records = frappe.db.sql(
			"""
			SELECT name FROM `tabWarehouse`
			WHERE custom_department = %(department)s OR name = %(department)s
		""",
			{"department": department},
			as_dict=True,
		)
		warehouses = [w.name for w in wh_records]
		if not warehouses:
			warehouses = [department]

	# Get all active items
	items = frappe.db.sql(
		"""
		SELECT name AS item_code, item_name, is_stock_item
		FROM `tabItem`
		WHERE disabled = 0
		ORDER BY item_name ASC
	""",
		as_dict=True,
	)

	# Get stock balances from Bin
	bin_cond = ""
	bin_params = {}
	if warehouses:
		bin_cond = "WHERE warehouse IN %(warehouses)s"
		bin_params["warehouses"] = tuple(warehouses)

	bin_data = frappe.db.sql(
		f"""
		SELECT item_code, SUM(actual_qty) AS balance_stock
		FROM `tabBin`
		{bin_cond}
		GROUP BY item_code
	""",
		bin_params,
		as_dict=True,
	)
	stock_map = {b.item_code: flt(b.balance_stock) for b in bin_data}

	# Get sales in date range
	sales_cond = "si.docstatus = 1 AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s"
	sales_params = {"from_date": from_date, "to_date": to_date}
	if department:
		if warehouses:
			sales_cond += " AND (si.department = %(department)s OR sii.warehouse IN %(warehouses)s)"
			sales_params["warehouses"] = tuple(warehouses)
		else:
			sales_cond += " AND si.department = %(department)s"
		sales_params["department"] = department

	sales_data = frappe.db.sql(
		f"""
		SELECT sii.item_code, SUM(sii.qty) AS total_sales
		FROM `tabSales Invoice Item` sii
		JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE {sales_cond}
		GROUP BY sii.item_code
	""",
		sales_params,
		as_dict=True,
	)
	sales_map = {s.item_code: flt(s.total_sales) for s in sales_data}

	# Get default supplier mapping
	default_suppliers = frappe.db.sql(
		"""
		SELECT parent AS item_code, default_supplier
		FROM `tabItem Default`
		WHERE default_supplier IS NOT NULL AND default_supplier != ''
	""",
		as_dict=True,
	)
	supplier_map = {s.item_code: s.default_supplier for s in default_suppliers}

	# Get latest purchase supplier if not in Item Default
	latest_suppliers = frappe.db.sql(
		"""
		SELECT pri.item_code, pr.supplier
		FROM `tabPurchase Receipt Item` pri
		JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
		WHERE pr.docstatus = 1 AND pr.supplier IS NOT NULL AND pr.supplier != ''
		ORDER BY pr.posting_date DESC
	""",
		as_dict=True,
	)
	for ls in latest_suppliers:
		if ls.item_code not in supplier_map:
			supplier_map[ls.item_code] = ls.supplier

	data = []
	for item in items:
		item_code = item.item_code
		bal_stock = stock_map.get(item_code, 0.0)

		# Filter for Zero Stock
		if bal_stock != 0.0 and bal_stock > 0:
			continue

		sales_qty = sales_map.get(item_code, 0.0)
		supp_name = supplier_map.get(item_code, "")

		if stock_filter and sales_qty == 0.0 and bal_stock == 0.0 and not supp_name:
			continue

		data.append(
			{
				"item_code": item_code,
				"item_name": item.item_name or item_code,
				"balance_stock": bal_stock,
				"sales": sales_qty if sales_qty != 0 else None,
				"supplier_name": supp_name,
			}
		)

	return data


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
