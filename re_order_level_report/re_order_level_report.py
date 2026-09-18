# Copyright (c) 2026, Quantbit HIMS Integration and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.utils import add_months, flt, getdate, today


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 160,
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Module Name"),
			"fieldname": "module_name",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Last 6 Months Consumption"),
			"fieldname": "last_6_months_consumption",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Dept Name"),
			"fieldname": "dept_name",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Per Day Consumption for Next 7 days"),
			"fieldname": "per_day_consumption_7_days",
			"fieldtype": "Float",
			"width": 140,
		},
		{
			"label": _("Current Stock"),
			"fieldname": "current_stock",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("ROL"),
			"fieldname": "rol",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Cat Name"),
			"fieldname": "cat_name",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Purchase Rate"),
			"fieldname": "purchase_rate",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Sub Category Name"),
			"fieldname": "sub_category_name",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Unit Mrp"),
			"fieldname": "unit_mrp",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 110,
		},
	]


def get_data(filters):
	as_of_date = filters.get("date") or today()
	six_months_ago = add_months(as_of_date, -6)

	selected_dept = filters.get("department")
	dept_warehouse = None
	dept_display_name = ""

	if selected_dept:
		dept_doc = frappe.db.get_value(
			"Department",
			selected_dept,
			["department_name", "custom_stock_location"],
			as_dict=True,
		)
		if dept_doc:
			dept_display_name = dept_doc.department_name or selected_dept
			dept_warehouse = dept_doc.custom_stock_location

	company_currency = None
	if filters.get("company"):
		company_currency = frappe.get_cached_value("Company", filters.get("company"), "default_currency")

	item_conditions = ["i.is_stock_item = 1", "i.disabled = 0"]
	item_params = {}

	if filters.get("therapeutic_group"):
		item_conditions.append("(i.custom_classification = %(therapeutic_group)s OR i.custom_category = %(therapeutic_group)s)")
		item_params["therapeutic_group"] = filters.get("therapeutic_group")

	if filters.get("therapeutic_sub_group"):
		item_conditions.append("(i.custom_classification_type = %(therapeutic_sub_group)s OR i.item_group = %(therapeutic_sub_group)s)")
		item_params["therapeutic_sub_group"] = filters.get("therapeutic_sub_group")

	items = frappe.db.sql(
		f"""
		SELECT 
			i.name AS item_code,
			i.item_name,
			i.custom_category,
			i.item_group,
			i.custom_mrp,
			i.last_purchase_rate,
			i.valuation_rate,
			i.safety_stock,
			COALESCE(
				(SELECT s.supplier_name FROM `tabItem Supplier` isup 
				 INNER JOIN `tabSupplier` s ON s.name = isup.supplier 
				 WHERE isup.parent = i.name LIMIT 1),
				(SELECT pr.supplier_name FROM `tabPurchase Receipt Item` pri 
				 INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent 
				 WHERE pri.item_code = i.name AND pr.docstatus = 1 
				 ORDER BY pr.posting_date DESC LIMIT 1),
				''
			) AS supplier_name
		FROM `tabItem` i
		WHERE {' AND '.join(item_conditions)}
		ORDER BY i.item_name ASC
	""",
		item_params,
		as_dict=True,
	)

	if not items:
		return []

	# Get 6 months consumption map from Stock Ledger Entry
	sle_conditions = [
		"sle.docstatus = 1",
		"sle.is_cancelled = 0",
		"sle.posting_date BETWEEN %(from_date)s AND %(to_date)s",
		"sle.actual_qty < 0",
	]
	sle_params = {
		"from_date": six_months_ago,
		"to_date": as_of_date,
	}

	if dept_warehouse:
		sle_conditions.append("sle.warehouse = %(warehouse)s")
		sle_params["warehouse"] = dept_warehouse

	consumption_rows = frappe.db.sql(
		f"""
		SELECT 
			sle.item_code,
			ABS(SUM(sle.actual_qty)) AS consumption_qty
		FROM `tabStock Ledger Entry` sle
		WHERE {' AND '.join(sle_conditions)}
		GROUP BY sle.item_code
	""",
		sle_params,
		as_dict=True,
	)
	consumption_map = {r.item_code: flt(r.consumption_qty) for r in consumption_rows}

	# Get Current Stock map
	bin_conditions = []
	bin_params = {}
	if dept_warehouse:
		bin_conditions.append("b.warehouse = %(warehouse)s")
		bin_params["warehouse"] = dept_warehouse

	bin_where = f"WHERE {' AND '.join(bin_conditions)}" if bin_conditions else ""
	bin_rows = frappe.db.sql(
		f"""
		SELECT 
			b.item_code,
			SUM(b.actual_qty) AS stock_qty,
			AVG(b.valuation_rate) AS avg_valuation
		FROM `tabBin` b
		{bin_where}
		GROUP BY b.item_code
	""",
		bin_params,
		as_dict=True,
	)
	stock_map = {r.item_code: flt(r.stock_qty) for r in bin_rows}
	val_map = {r.item_code: flt(r.avg_valuation) for r in bin_rows}

	rol_filter = filters.get("rol_amount") or "All"

	data = []
	for item in items:
		code = item.item_code
		six_month_cons = flt(consumption_map.get(code, 0.0), 2)
		next_7_day_cons = round((six_month_cons / 180.0) * 7.0, 2)
		current_stock = flt(stock_map.get(code, 0.0), 2)
		
		# ROL calculation
		if item.safety_stock and item.safety_stock > 0:
			rol_val = flt(item.safety_stock, 2)
		elif six_month_cons > 0 or current_stock > 0:
			rol_val = round(current_stock - next_7_day_cons, 2)
		else:
			rol_val = 0.0

		# Apply ROL Amount filter
		if rol_filter == "Below ROL" and current_stock >= rol_val:
			continue
		elif rol_filter == "At/Above ROL" and current_stock < rol_val:
			continue

		purch_rate = flt(item.last_purchase_rate) or flt(val_map.get(code)) or flt(item.valuation_rate)

		row = {
			"department": selected_dept or "Pharmacy",
			"item_name": item.item_name,
			"module_name": "Pharmacy",
			"supplier_name": item.supplier_name,
			"last_6_months_consumption": six_month_cons,
			"dept_name": dept_display_name or selected_dept or "Pharmacy",
			"per_day_consumption_7_days": next_7_day_cons,
			"current_stock": current_stock,
			"rol": rol_val,
			"cat_name": item.custom_category or "PHARMACY MEDICINE",
			"purchase_rate": purch_rate,
			"sub_category_name": item.item_group or "",
			"unit_mrp": flt(item.custom_mrp, 2),
			"currency": company_currency or "QAR",
		}
		data.append(row)

	return data