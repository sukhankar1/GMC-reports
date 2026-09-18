# Copyright (c) 2024, Quantbit Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Item Class"), "fieldname": "item_class", "fieldtype": "Data", "width": 100},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Link", "options": "Item", "width": 220},
		{"label": _("Stock"), "fieldname": "stock_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Stock Value"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 130},
		{"label": _("Qty.(%)"), "fieldname": "qty_percent", "fieldtype": "Float", "width": 100},
		{"label": _("Value(%)"), "fieldname": "value_percent", "fieldtype": "Float", "width": 100},
		{"label": _("Therapeutic Group"), "fieldname": "therapeutic_group", "fieldtype": "Data", "width": 180},
		{"label": _("Therapeutic Sub Group"), "fieldname": "therapeutic_sub_group", "fieldtype": "Data", "width": 180}
	]


def get_data(filters):
	if not filters:
		filters = {}

	conditions = ["i.disabled = 0"]
	values = {}

	if filters.get("therapeutic_group"):
		conditions.append("(i.item_group = %(therapeutic_group)s OR i.custom_category = %(therapeutic_group)s OR i.custom_generic_name = %(therapeutic_group)s)")
		values["therapeutic_group"] = filters.get("therapeutic_group")

	where_clause = " AND ".join(conditions)

	# Query items and stock from tabBin / tabItem
	query = f"""
		SELECT
			i.name AS item_code,
			i.item_name AS item_name,
			COALESCE(i.custom_generic_name, i.custom_material_category, i.custom_category, '') AS therapeutic_group,
			COALESCE(i.item_group, '') AS therapeutic_sub_group,
			COALESCE(SUM(b.actual_qty), 0.0) AS stock_qty,
			COALESCE(SUM(b.stock_value), 0.0) AS stock_value
		FROM `tabItem` i
		LEFT JOIN `tabBin` b ON b.item_code = i.name
		WHERE {where_clause}
		GROUP BY i.name, i.item_name, i.custom_generic_name, i.custom_material_category, i.custom_category, i.item_group
		ORDER BY stock_value DESC, stock_qty DESC, i.item_name ASC
	"""

	items = frappe.db.sql(query, values, as_dict=True)

	total_stock_qty = sum(flt(item.get("stock_qty", 0)) for item in items if flt(item.get("stock_qty", 0)) > 0)
	total_stock_value = sum(flt(item.get("stock_value", 0)) for item in items if flt(item.get("stock_value", 0)) > 0)

	running_val_cum = 0.0
	result = []

	for item in items:
		s_qty = flt(item.get("stock_qty", 0))
		s_val = flt(item.get("stock_value", 0))

		qty_pct = (s_qty / total_stock_qty * 100.0) if total_stock_qty > 0 and s_qty > 0 else 0.0
		val_pct = (s_val / total_stock_value * 100.0) if total_stock_value > 0 and s_val > 0 else 0.0

		running_val_cum += val_pct

		# ABC Classification:
		# A: Top 70% of total value
		# B: Next 20% (70% - 90%)
		# C: Remaining 10% (90% - 100%) or zero/negative stock
		if s_val <= 0:
			item_class = "C"
		elif running_val_cum <= 70.0 or len(result) == 0:
			item_class = "A"
		elif running_val_cum <= 90.0:
			item_class = "B"
		else:
			item_class = "C"

		result.append({
			"item_class": item_class,
			"item_name": item.get("item_name") or item.get("item_code"),
			"stock_qty": s_qty,
			"stock_value": s_val,
			"qty_percent": round(qty_pct, 2),
			"value_percent": round(val_pct, 2),
			"therapeutic_group": item.get("therapeutic_group"),
			"therapeutic_sub_group": item.get("therapeutic_sub_group")
		})

	return result


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
