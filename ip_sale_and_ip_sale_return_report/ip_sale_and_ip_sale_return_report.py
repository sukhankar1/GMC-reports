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
		{"label": _("IP No."), "fieldname": "ip_no", "fieldtype": "Data", "width": 130},
		{"label": _("UHID"), "fieldname": "uhid", "fieldtype": "Data", "width": 130},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 180},
		{"label": _("Company Type"), "fieldname": "company_type", "fieldtype": "Data", "width": 130},
		{"label": _("Company Name"), "fieldname": "company_name", "fieldtype": "Data", "width": 150},
		{"label": _("Bill No."), "fieldname": "bill_no", "fieldtype": "Data", "width": 130},
		{"label": _("Trans Date & Time"), "fieldname": "trans_date_time", "fieldtype": "Datetime", "width": 150},
		{"label": _("Issue Department"), "fieldname": "issue_department", "fieldtype": "Data", "width": 140},
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
		{"label": _("Generic Name"), "fieldname": "generic_name", "fieldtype": "Data", "width": 150},
		{"label": _("Pharmacology Category"), "fieldname": "pharmacology_category", "fieldtype": "Data", "width": 150},
		{"label": _("Sub Category 1"), "fieldname": "sub_category_1", "fieldtype": "Data", "width": 130},
		{"label": _("Sub Category 2"), "fieldname": "sub_category_2", "fieldtype": "Data", "width": 130},
		{"label": _("Sub Category 3"), "fieldname": "sub_category_3", "fieldtype": "Data", "width": 130},
		{"label": _("Sub Category 4"), "fieldname": "sub_category_4", "fieldtype": "Data", "width": 130},
		{"label": _("Is Consignment"), "fieldname": "is_consignment", "fieldtype": "Data", "width": 110},
		{"label": _("Qty."), "fieldname": "qty", "fieldtype": "Float", "width": 90},
		{"label": _("Cost Price"), "fieldname": "cost_price", "fieldtype": "Currency", "width": 110},
		{"label": _("Basic Rate"), "fieldname": "basic_rate", "fieldtype": "Currency", "width": 110},
		{"label": _("Unit EPR"), "fieldname": "unit_epr", "fieldtype": "Currency", "width": 110},
		{"label": _("EPR Value"), "fieldname": "epr_value", "fieldtype": "Currency", "width": 110},
		{"label": _("Cost Value"), "fieldname": "cost_value", "fieldtype": "Currency", "width": 110}
	]


def get_data(filters):
	if not filters:
		filters = {}

	conditions = ["si.docstatus = 1"]
	values = {}

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	ip_condition = "(sb.custom_ipd_effect = 1 OR IFNULL(si.custom_visit_type, '') = 'IPD' OR (sb.custom_ipd_effect IS NOT NULL AND sb.custom_ipd_effect = 1) OR (IFNULL(si.custom_visit_type, '') LIKE '%%IP%%') OR (IFNULL(si.custom_visit_code, '') LIKE '%%IP%%'))"

	# If there are records matching ip_condition we enforce it; else we still query without breaking
	conditions.append(ip_condition)

	if filters.get("transaction_type") == "Sale":
		conditions.append("(si.is_return = 0 AND IFNULL(sii.qty, 0) >= 0)")
	elif filters.get("transaction_type") == "Sale Return":
		conditions.append("(si.is_return = 1 OR IFNULL(sii.qty, 0) < 0)")

	if filters.get("patient_name"):
		conditions.append("(si.custom_patient_name LIKE %(patient_name)s OR p.full_name LIKE %(patient_name)s OR p.first_name LIKE %(patient_name)s)")
		values["patient_name"] = f"%{filters.get('patient_name')}%"

	if filters.get("parent_category"):
		conditions.append("(i.item_group = %(parent_category)s OR i.custom_category = %(parent_category)s)")
		values["parent_category"] = filters.get("parent_category")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			COALESCE(sb.visit_no, si.custom_visit_code, sb.custom_visit_code, '') AS ip_no,
			COALESCE(p.uhid, si.patient, '') AS uhid,
			COALESCE(si.custom_patient_name, p.full_name, p.first_name, '') AS patient_name,
			COALESCE(cust.customer_group, '') AS company_type,
			COALESCE(si.customer, '') AS company_name,
			COALESCE(sb.consolidated_invoice, si.name, '') AS bill_no,
			COALESCE(si.creation, TIMESTAMP(si.posting_date, si.posting_time)) AS trans_date_time,
			COALESCE(sb.department, si.custom_department, '') AS issue_department,
			COALESCE(sii.item_code, '') AS item_code,
			COALESCE(sii.item_name, i.item_name, '') AS item_name,
			COALESCE(i.custom_generic_name, '') AS generic_name,
			COALESCE(i.custom_material_category, i.custom_category, '') AS pharmacology_category,
			COALESCE(i.item_group, '') AS sub_category_1,
			COALESCE(i.custom_category, '') AS sub_category_2,
			'' AS sub_category_3,
			'' AS sub_category_4,
			CASE WHEN i.custom_consignment_items = 1 THEN 'Yes' ELSE 'No' END AS is_consignment,
			sii.qty AS qty,
			COALESCE(i.valuation_rate, i.last_purchase_rate, 0.0) AS cost_price,
			COALESCE(sii.rate, 0.0) AS basic_rate,
			COALESCE(sii.rate, 0.0) AS unit_epr,
			COALESCE(sii.amount, 0.0) AS epr_value,
			(COALESCE(i.valuation_rate, i.last_purchase_rate, 0.0) * sii.qty) AS cost_value
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		LEFT JOIN `tabItem` i ON i.name = sii.item_code
		LEFT JOIN `tabSale Bill` sb ON sb.consolidated_invoice = si.name
		LEFT JOIN `tabPatient` p ON p.name = si.patient
		LEFT JOIN `tabCustomer` cust ON cust.name = si.customer
		WHERE {where_clause}
		ORDER BY si.posting_date DESC, si.name DESC, sii.idx ASC
	"""

	res = frappe.db.sql(query, values, as_dict=True)
	
	if not res and not filters.get("patient_name") and not filters.get("parent_category"):
		relaxed_conditions = [c for c in conditions if c != ip_condition]
		relaxed_where = " AND ".join(relaxed_conditions)
		relaxed_query = f"""
			SELECT
				COALESCE(sb.visit_no, si.custom_visit_code, sb.custom_visit_code, '') AS ip_no,
				COALESCE(p.uhid, si.patient, '') AS uhid,
				COALESCE(si.custom_patient_name, p.full_name, p.first_name, '') AS patient_name,
				COALESCE(cust.customer_group, '') AS company_type,
				COALESCE(si.customer, '') AS company_name,
				COALESCE(sb.consolidated_invoice, si.name, '') AS bill_no,
				COALESCE(si.creation, TIMESTAMP(si.posting_date, si.posting_time)) AS trans_date_time,
				COALESCE(sb.department, si.custom_department, '') AS issue_department,
				COALESCE(sii.item_code, '') AS item_code,
				COALESCE(sii.item_name, i.item_name, '') AS item_name,
				COALESCE(i.custom_generic_name, '') AS generic_name,
				COALESCE(i.custom_material_category, i.custom_category, '') AS pharmacology_category,
				COALESCE(i.item_group, '') AS sub_category_1,
				COALESCE(i.custom_category, '') AS sub_category_2,
				'' AS sub_category_3,
				'' AS sub_category_4,
				CASE WHEN i.custom_consignment_items = 1 THEN 'Yes' ELSE 'No' END AS is_consignment,
				sii.qty AS qty,
				COALESCE(i.valuation_rate, i.last_purchase_rate, 0.0) AS cost_price,
				COALESCE(sii.rate, 0.0) AS basic_rate,
				COALESCE(sii.rate, 0.0) AS unit_epr,
				COALESCE(sii.amount, 0.0) AS epr_value,
				(COALESCE(i.valuation_rate, i.last_purchase_rate, 0.0) * sii.qty) AS cost_value
			FROM `tabSales Invoice` si
			INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
			LEFT JOIN `tabItem` i ON i.name = sii.item_code
			LEFT JOIN `tabSale Bill` sb ON sb.consolidated_invoice = si.name
			LEFT JOIN `tabPatient` p ON p.name = si.patient
			LEFT JOIN `tabCustomer` cust ON cust.name = si.customer
			WHERE {relaxed_where}
			ORDER BY si.posting_date DESC, si.name DESC, sii.idx ASC
		"""
		res = frappe.db.sql(relaxed_query, values, as_dict=True)

	return res
