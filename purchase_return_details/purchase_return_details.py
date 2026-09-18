# Copyright (c) 2026, Quantbit HIMS Integration and Contributors
# License: GNU General Public License v3. See license.txt

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
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Unit"),
			"fieldname": "uom",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("Batch No."),
			"fieldname": "batch_no",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Parent Category"),
			"fieldname": "parent_category",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Expiry Date"),
			"fieldname": "expiry_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Purchase Return No."),
			"fieldname": "purchase_return_no",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 150,
		},
		{
			"label": _("Date"),
			"fieldname": "return_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Pay Mode"),
			"fieldname": "pay_mode",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Conversion Factor"),
			"fieldname": "conversion_factor",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Return Qty."),
			"fieldname": "return_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Free Qty."),
			"fieldname": "free_qty",
			"fieldtype": "Float",
			"width": 90,
		},
		{
			"label": _("MRP"),
			"fieldname": "mrp",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100,
		},
		{
			"label": _("Rate"),
			"fieldname": "rate",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100,
		},
		{
			"label": _("Discount Amt."),
			"fieldname": "discount_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 110,
		},
		{
			"label": _("Rate After Discount"),
			"fieldname": "rate_after_discount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{
			"label": _("Total Amt."),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
	]


def get_data(filters):
	conditions = ["pi.docstatus = 1", "pi.is_return = 1"]
	params = {}

	if filters.get("from_date"):
		conditions.append("pi.posting_date >= %(from_date)s")
		params["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("pi.posting_date <= %(to_date)s")
		params["to_date"] = filters.get("to_date")

	if filters.get("supplier"):
		conditions.append("pi.supplier = %(supplier)s")
		params["supplier"] = filters.get("supplier")

	if filters.get("company"):
		conditions.append("pi.company = %(company)s")
		params["company"] = filters.get("company")

	if filters.get("department"):
		conditions.append(
			"(pi.custom_department = %(department)s OR pi.custom_for_department = %(department)s)"
		)
		params["department"] = filters.get("department")

	if filters.get("item_code"):
		conditions.append("pii.item_code = %(item_code)s")
		params["item_code"] = filters.get("item_code")

	if filters.get("manufacturer"):
		conditions.append("(i.brand = %(manufacturer)s OR i.manufacturer = %(manufacturer)s)")
		params["manufacturer"] = filters.get("manufacturer")

	if filters.get("therapeutic_group"):
		conditions.append("(i.custom_classification = %(therapeutic_group)s OR i.custom_category = %(therapeutic_group)s)")
		params["therapeutic_group"] = filters.get("therapeutic_group")

	if filters.get("therapeutic_sub_group"):
		conditions.append("(i.custom_classification_type = %(therapeutic_sub_group)s OR i.item_group = %(therapeutic_sub_group)s)")
		params["therapeutic_sub_group"] = filters.get("therapeutic_sub_group")

	if filters.get("payment_type") and filters.get("payment_type") != "All":
		pt = filters.get("payment_type")
		if pt == "Cash":
			conditions.append("pi.mode_of_payment = 'Cash'")
		elif pt == "Credit":
			conditions.append("(pi.mode_of_payment != 'Cash' OR pi.mode_of_payment IS NULL OR pi.mode_of_payment = '')")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT 
			pii.item_code,
			pii.item_name,
			pii.uom,
			COALESCE(pii.batch_no, pii.custom_user_batch_no, '') AS batch_no,
			COALESCE(NULLIF(i.custom_category, ''), 'PHARMACY MEDICINE') AS parent_category,
			COALESCE(pii.custom_expiry_date, b.expiry_date) AS expiry_date,
			COALESCE(NULLIF(pi.custom_department, ''), NULLIF(pi.custom_for_department, ''), '') AS department,
			pi.supplier_name,
			pi.name AS purchase_return_no,
			pi.posting_date AS return_date,
			COALESCE(NULLIF(pi.mode_of_payment, ''), 'Credit') AS pay_mode,
			COALESCE(pii.conversion_factor, 1.0) AS conversion_factor,
			ABS(pii.qty) AS return_qty,
			COALESCE(pii.custom_free_qty, 0.0) AS free_qty,
			COALESCE(pii.custom_mrp, 0.0) AS mrp,
			pii.rate,
			COALESCE(pii.discount_amount, 0.0) AS discount_amount,
			COALESCE(pii.net_rate, pii.rate) AS rate_after_discount,
			ABS(COALESCE(pii.base_net_amount, pii.net_amount, pii.amount)) AS total_amount,
			pi.currency AS currency
		FROM 
			`tabPurchase Invoice` pi
		INNER JOIN 
			`tabPurchase Invoice Item` pii ON pii.parent = pi.name
		LEFT JOIN 
			`tabItem` i ON i.name = pii.item_code
		LEFT JOIN 
			`tabBatch` b ON b.name = pii.batch_no
		WHERE 
			{where_clause}
		ORDER BY 
			pi.posting_date DESC, pi.name DESC, pii.idx ASC
	"""

	return frappe.db.sql(query, params, as_dict=True)
