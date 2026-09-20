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
		{"label": _("Physical Stock Adjustment No."), "fieldname": "physical_stock_adjustment_no", "fieldtype": "Data", "width": 180},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 160},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
		{"label": _("Item Catogory"), "fieldname": "item_category", "fieldtype": "Data", "width": 140},
		{"label": _("Unit"), "fieldname": "unit", "fieldtype": "Data", "width": 90},
		{"label": _("Batch No."), "fieldname": "batch_no", "fieldtype": "Data", "width": 130},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 110},
		{"label": _("Adjustment Qty."), "fieldname": "adjustment_qty", "fieldtype": "Float", "width": 120},
		{"label": _("Adjustment Type"), "fieldname": "adjustment_type", "fieldtype": "Data", "width": 130},
		{"label": _("Unit Puchase Rate"), "fieldname": "unit_purchase_rate", "fieldtype": "Currency", "width": 130},
		{"label": _("MRP"), "fieldname": "mrp", "fieldtype": "Currency", "width": 100},
		{"label": _("Purchase Amount"), "fieldname": "purchase_amount", "fieldtype": "Currency", "width": 130},
		{"label": _("Reason"), "fieldname": "reason", "fieldtype": "Data", "width": 150}
	]


def get_data(filters):
	if not filters:
		filters = {}

	# First, check Stock Reconciliation
	recon_data = get_reconciliation_data(filters)

	# Also check Stock Entry with purpose Material Receipt / Issue / Adjustment
	entry_data = get_stock_entry_data(filters)

	data = recon_data + entry_data
	data.sort(key=lambda x: str(x.get("date") or ""), reverse=True)
	return data


def get_reconciliation_data(filters):
	conditions = ["sr.docstatus = 1"]
	values = {}

	if filters.get("from_date"):
		conditions.append("sr.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("sr.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("item_name"):
		conditions.append("(sri.item_code = %(item_name)s OR sri.item_name LIKE %(item_like)s)")
		values["item_name"] = filters.get("item_name")
		values["item_like"] = f"%{filters.get('item_name')}%"

	if filters.get("department"):
		conditions.append("(IFNULL(sr.custom_department, '') LIKE %(dept_like)s OR sri.warehouse LIKE %(dept_like)s)")
		values["dept_like"] = f"%{filters.get('department')}%"

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			sr.name AS physical_stock_adjustment_no,
			sr.posting_date AS date,
			COALESCE(sri.warehouse, '') AS department,
			COALESCE(sri.item_name, i.item_name, sri.item_code) AS item_name,
			COALESCE(i.custom_material_category, i.custom_category, i.item_group, '') AS item_category,
			COALESCE(i.stock_uom, '') AS unit,
			COALESCE(sri.batch_no, '') AS batch_no,
			b.expiry_date AS expiry_date,
			(COALESCE(sri.qty, 0.0) - COALESCE(sri.current_qty, 0.0)) AS adjustment_qty,
			CASE 
				WHEN (COALESCE(sri.qty, 0.0) - COALESCE(sri.current_qty, 0.0)) > 0 THEN 'Excess'
				WHEN (COALESCE(sri.qty, 0.0) - COALESCE(sri.current_qty, 0.0)) < 0 THEN 'Shortage'
				ELSE 'Physical Stock Adjustment'
			END AS adjustment_type,
			COALESCE(sri.valuation_rate, i.last_purchase_rate, 0.0) AS unit_purchase_rate,
			COALESCE(b.custom_mrp, sri.valuation_rate, 0.0) AS mrp,
			(COALESCE(sri.valuation_rate, i.last_purchase_rate, 0.0) * ABS(COALESCE(sri.qty, 0.0) - COALESCE(sri.current_qty, 0.0))) AS purchase_amount,
			COALESCE(sr.purpose, '') AS reason
		FROM `tabStock Reconciliation` sr
		INNER JOIN `tabStock Reconciliation Item` sri ON sri.parent = sr.name
		LEFT JOIN `tabItem` i ON i.name = sri.item_code
		LEFT JOIN `tabBatch` b ON b.name = sri.batch_no
		WHERE {where_clause}
		ORDER BY sr.posting_date DESC, sr.name DESC
	"""
	return frappe.db.sql(query, values, as_dict=True)


def get_stock_entry_data(filters):
	conditions = ["se.docstatus = 1", "se.purpose IN ('Material Receipt', 'Material Issue', 'Stock Reconciliation', 'Physical Stock')"]
	values = {}

	if filters.get("from_date"):
		conditions.append("se.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("se.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("item_name"):
		conditions.append("(sed.item_code = %(item_name)s OR sed.item_name LIKE %(item_like)s)")
		values["item_name"] = filters.get("item_name")
		values["item_like"] = f"%{filters.get('item_name')}%"

	if filters.get("department"):
		conditions.append("(se.department = %(department)s OR se.from_warehouse LIKE %(dept_like)s OR se.to_warehouse LIKE %(dept_like)s)")
		values["department"] = filters.get("department")
		values["dept_like"] = f"%{filters.get('department')}%"

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			se.name AS physical_stock_adjustment_no,
			se.posting_date AS date,
			COALESCE(se.department, se.from_warehouse, se.to_warehouse, '') AS department,
			COALESCE(sed.item_name, i.item_name, sed.item_code) AS item_name,
			COALESCE(i.custom_material_category, i.custom_category, i.item_group, '') AS item_category,
			COALESCE(sed.uom, sed.stock_uom, '') AS unit,
			COALESCE(sed.batch_no, '') AS batch_no,
			b.expiry_date AS expiry_date,
			COALESCE(sed.qty, 0.0) AS adjustment_qty,
			CASE 
				WHEN se.purpose = 'Material Receipt' THEN 'Excess'
				WHEN se.purpose = 'Material Issue' THEN 'Shortage'
				ELSE 'Physical Stock Adjustment'
			END AS adjustment_type,
			COALESCE(sed.basic_rate, sed.valuation_rate, i.last_purchase_rate, 0.0) AS unit_purchase_rate,
			COALESCE(b.custom_mrp, sed.valuation_rate, 0.0) AS mrp,
			(COALESCE(sed.basic_rate, sed.valuation_rate, i.last_purchase_rate, 0.0) * COALESCE(sed.qty, 0.0)) AS purchase_amount,
			COALESCE(se.remarks, se.purpose, '') AS reason
		FROM `tabStock Entry` se
		INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		LEFT JOIN `tabItem` i ON i.name = sed.item_code
		LEFT JOIN `tabBatch` b ON b.name = sed.batch_no
		WHERE {where_clause}
		ORDER BY se.posting_date DESC, se.name DESC
	"""
	return frappe.db.sql(query, values, as_dict=True)
