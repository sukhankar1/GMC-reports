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
		{"label": _("Consumption No."), "fieldname": "consumption_no", "fieldtype": "Data", "width": 140},
		{"label": _("Cons. Date"), "fieldname": "cons_date", "fieldtype": "Date", "width": 110},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 150},
		{"label": _("Classification"), "fieldname": "classification", "fieldtype": "Data", "width": 130},
		{"label": _("Category"), "fieldname": "category", "fieldtype": "Data", "width": 130},
		{"label": _("Sub Category"), "fieldname": "sub_category", "fieldtype": "Data", "width": 130},
		{"label": _("Sub Category 2"), "fieldname": "sub_category_2", "fieldtype": "Data", "width": 130},
		{"label": _("Sub Category 3"), "fieldname": "sub_category_3", "fieldtype": "Data", "width": 130},
		{"label": _("Sub Category 4"), "fieldname": "sub_category_4", "fieldtype": "Data", "width": 130},
		{"label": _("Company Name"), "fieldname": "company_name", "fieldtype": "Data", "width": 150},
		{"label": _("Is Consignment"), "fieldname": "is_consignment", "fieldtype": "Data", "width": 110},
		{"label": _("Generic Name"), "fieldname": "generic_name", "fieldtype": "Data", "width": 150},
		{"label": _("Pharmacological Category"), "fieldname": "pharmacological_category", "fieldtype": "Data", "width": 160},
		{"label": _("UHID"), "fieldname": "uhid", "fieldtype": "Data", "width": 120},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 180},
		{"label": _("IP/OP No."), "fieldname": "ip_op_no", "fieldtype": "Data", "width": 130},
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
		{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Data", "width": 90},
		{"label": _("EPR"), "fieldname": "epr", "fieldtype": "Currency", "width": 100},
		{"label": _("EPR Value"), "fieldname": "epr_value", "fieldtype": "Currency", "width": 110},
		{"label": _("MRP"), "fieldname": "mrp", "fieldtype": "Currency", "width": 100},
		{"label": _("MRP Value"), "fieldname": "mrp_value", "fieldtype": "Currency", "width": 110},
		{"label": _("Batch No."), "fieldname": "batch_no", "fieldtype": "Data", "width": 130},
		{"label": _("Admit Date"), "fieldname": "admit_date", "fieldtype": "Date", "width": 110},
		{"label": _("Discharge Date"), "fieldname": "discharge_date", "fieldtype": "Date", "width": 110},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 110},
		{"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 90},
		{"label": _("User Name"), "fieldname": "user_name", "fieldtype": "Data", "width": 130},
		{"label": _("Unit Pur. Rate"), "fieldname": "unit_pur_rate", "fieldtype": "Currency", "width": 120},
		{"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 120}
	]


def get_data(filters):
	if not filters:
		filters = {}

	conditions = ["se.docstatus = 1"]
	values = {}

	if filters.get("from_date"):
		conditions.append("se.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("se.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("department"):
		conditions.append("(se.department = %(department)s OR se.from_warehouse LIKE %(dept_like)s)")
		values["department"] = filters.get("department")
		values["dept_like"] = f"%{filters.get('department')}%"

	if filters.get("item_name"):
		conditions.append("(sed.item_code = %(item_name)s OR sed.item_name LIKE %(item_like)s)")
		values["item_name"] = filters.get("item_name")
		values["item_like"] = f"%{filters.get('item_name')}%"

	if filters.get("therapeutic_group"):
		conditions.append("(i.item_group = %(therapeutic_group)s OR i.custom_category = %(therapeutic_group)s OR i.custom_generic_name = %(therapeutic_group)s)")
		values["therapeutic_group"] = filters.get("therapeutic_group")

	# Type filter
	type_filter = filters.get("type_filter", "All")
	if type_filter == "DeptWise":
		conditions.append("(se.purpose IN ('Material Issue', 'Material Consumption', 'Manufacture'))")
	elif type_filter == "PatientWise":
		conditions.append("(se.purpose LIKE '%%Patient%%' OR IFNULL(se.from_warehouse, '') LIKE '%%Patient%%')")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			se.name AS consumption_no,
			se.posting_date AS cons_date,
			COALESCE(se.department, se.from_warehouse, '') AS department,
			COALESCE(i.item_group, '') AS classification,
			COALESCE(i.custom_material_category, i.custom_category, '') AS category,
			COALESCE(i.item_group, '') AS sub_category,
			'' AS sub_category_2,
			'' AS sub_category_3,
			'' AS sub_category_4,
			COALESCE(se.company, '') AS company_name,
			CASE WHEN i.custom_consignment_items = 1 THEN 'Yes' ELSE 'No' END AS is_consignment,
			COALESCE(i.custom_generic_name, '') AS generic_name,
			COALESCE(i.custom_material_category, i.custom_category, '') AS pharmacological_category,
			'' AS uhid,
			'' AS patient_name,
			'' AS ip_op_no,
			COALESCE(sed.item_code, '') AS item_code,
			COALESCE(sed.item_name, i.item_name, sed.item_code) AS item_name,
			COALESCE(sed.uom, sed.stock_uom, '') AS uom,
			COALESCE(sed.basic_rate, sed.valuation_rate, 0.0) AS epr,
			(COALESCE(sed.basic_rate, sed.valuation_rate, 0.0) * COALESCE(sed.qty, 0.0)) AS epr_value,
			COALESCE(b.custom_mrp, sed.valuation_rate, 0.0) AS mrp,
			(COALESCE(b.custom_mrp, sed.valuation_rate, 0.0) * COALESCE(sed.qty, 0.0)) AS mrp_value,
			COALESCE(sed.batch_no, '') AS batch_no,
			NULL AS admit_date,
			NULL AS discharge_date,
			b.expiry_date AS expiry_date,
			COALESCE(sed.qty, 0.0) AS quantity,
			COALESCE(se.owner, '') AS user_name,
			COALESCE(i.last_purchase_rate, sed.valuation_rate, 0.0) AS unit_pur_rate,
			COALESCE(sed.amount, 0.0) AS total_amount
		FROM `tabStock Entry` se
		INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		LEFT JOIN `tabItem` i ON i.name = sed.item_code
		LEFT JOIN `tabBatch` b ON b.name = sed.batch_no
		WHERE {where_clause}
		ORDER BY se.posting_date DESC, se.name DESC, sed.idx ASC
	"""

	res = frappe.db.sql(query, values, as_dict=True)

	# Calculate Total Amount based on selected valuation if needed
	valuation = filters.get("valuation", "Unit Purchase Rate")
	for r in res:
		qty = float(r.get("quantity") or 0.0)
		if valuation == "MRP":
			r["total_amount"] = float(r.get("mrp") or 0.0) * qty
		elif valuation == "EPR":
			r["total_amount"] = float(r.get("epr") or 0.0) * qty
		elif valuation == "Unit Purchase Rate":
			r["total_amount"] = float(r.get("unit_pur_rate") or 0.0) * qty
		else:
			r["total_amount"] = float(r.get("total_amount") or 0.0)

	return res
