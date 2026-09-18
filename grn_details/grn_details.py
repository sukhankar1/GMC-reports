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
			"width": 180,
		},
		{
			"label": _("GRN Numbers"),
			"fieldname": "grn_number",
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 150,
		},
		{
			"label": _("GRN Date"),
			"fieldname": "grn_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Invoice No."),
			"fieldname": "invoice_no",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Invoice Date"),
			"fieldname": "invoice_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Batch No."),
			"fieldname": "batch_no",
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
			"label": _("Purch Qty."),
			"fieldname": "purch_qty",
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
			"label": _("Total Qty."),
			"fieldname": "total_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Disc %"),
			"fieldname": "disc_percentage",
			"fieldtype": "Float",
			"width": 90,
		},
		{
			"label": _("Disc Amt."),
			"fieldname": "disc_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100,
		},
		{
			"label": _("Landed Cost"),
			"fieldname": "landed_cost",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 110,
		},
		{
			"label": _("MRP"),
			"fieldname": "mrp",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100,
		},
		{
			"label": _("Margin %LC"),
			"fieldname": "margin_lc_pct",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Margin %MRP"),
			"fieldname": "margin_mrp_pct",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("TRP"),
			"fieldname": "trp",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100,
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
	conditions = ["pr.docstatus = 1"]
	params = {}

	if filters.get("from_date"):
		conditions.append("pr.posting_date >= %(from_date)s")
		params["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("pr.posting_date <= %(to_date)s")
		params["to_date"] = filters.get("to_date")

	if filters.get("item_code"):
		conditions.append("pri.item_code = %(item_code)s")
		params["item_code"] = filters.get("item_code")

	if filters.get("supplier"):
		conditions.append("pr.supplier = %(supplier)s")
		params["supplier"] = filters.get("supplier")

	if filters.get("company"):
		conditions.append("pr.company = %(company)s")
		params["company"] = filters.get("company")

	if filters.get("department"):
		conditions.append(
			"(pr.custom_department = %(department)s OR pr.custom_for_department = %(department)s)"
		)
		params["department"] = filters.get("department")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT 
			pri.item_code,
			pri.item_name,
			pr.name AS grn_number,
			pr.posting_date AS grn_date,
			pr.supplier_name,
			COALESCE(NULLIF(pr.custom_invoice_no, ''), NULLIF(pr.supplier_delivery_note, ''), '') AS invoice_no,
			COALESCE(pr.custom_invoice_date, pr.custom_delivery_date, pr.posting_date) AS invoice_date,
			COALESCE(pri.batch_no, pri.custom_user_batch_no, '') AS batch_no,
			COALESCE(pri.custom_expiry_date, b.expiry_date) AS expiry_date,
			pri.qty AS purch_qty,
			COALESCE(pri.custom_free_qty, 0.0) AS free_qty,
			(pri.qty + COALESCE(pri.custom_free_qty, 0.0)) AS total_qty,
			COALESCE(pri.discount_percentage, 0.0) AS disc_percentage,
			COALESCE(pri.discount_amount, 0.0) AS disc_amount,
			COALESCE(pri.valuation_rate, pri.net_rate, pri.rate, 0.0) AS landed_cost,
			COALESCE(pri.custom_mrp, pri.custom_unit_mrp, 0.0) AS mrp,
			CASE 
				WHEN COALESCE(pri.custom_mrp, pri.custom_unit_mrp, 0.0) > 0 THEN 
					ROUND(((COALESCE(pri.custom_mrp, pri.custom_unit_mrp, 0.0) - COALESCE(pri.valuation_rate, pri.net_rate, pri.rate, 0.0)) / COALESCE(pri.custom_mrp, pri.custom_unit_mrp, 0.0)) * 100.0, 2)
				ELSE 0.0 
			END AS margin_lc_pct,
			CASE 
				WHEN COALESCE(pri.custom_mrp, pri.custom_unit_mrp, 0.0) > 0 THEN 
					ROUND(((COALESCE(pri.custom_mrp, pri.custom_unit_mrp, 0.0) - pri.rate) / COALESCE(pri.custom_mrp, pri.custom_unit_mrp, 0.0)) * 100.0, 2)
				ELSE 0.0 
			END AS margin_mrp_pct,
			pri.rate AS trp,
			COALESCE(pri.custom_total_amount, pri.amount, pri.net_amount, 0.0) AS total_amount,
			pr.currency AS currency
		FROM 
			`tabPurchase Receipt` pr
		INNER JOIN 
			`tabPurchase Receipt Item` pri ON pri.parent = pr.name
		LEFT JOIN 
			`tabBatch` b ON b.name = pri.batch_no
		WHERE 
			{where_clause}
		ORDER BY 
			pr.posting_date DESC, pr.name DESC, pri.idx ASC
	"""

	return frappe.db.sql(query, params, as_dict=True)