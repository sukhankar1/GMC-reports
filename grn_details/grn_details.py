# Copyright (c) 2026, Quantbit HIMS Integration and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	return _execute(filters)


def _execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_grn_items(filters)

	return columns, data


def get_columns():
	return [
		# Header Info
		{
			"label": _("Voucher"),
			"fieldname": "voucher_no",
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 140,
		},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 130,
		},
		{"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 130},
		{"label": _("Supplier Invoice No"), "fieldname": "custom_invoice_no", "fieldtype": "Data", "width": 120},
		{
			"label": _("Purchase Order"),
			"fieldname": "purchase_order",
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 130,
		},
		
		# Item Info
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 130,
		},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 140},
		{
			"label": _("Item Group"),
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 110,
		},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Data", "width": 100},
		{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Data", "width": 80},
		{"label": _("Batch No"), "fieldname": "batch_no", "fieldtype": "Data", "width": 130},
		
		# Quantities
		{"label": _("Received Qty"), "fieldname": "received_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Accepted Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
		{"label": _("Rejected Qty"), "fieldname": "rejected_qty", "fieldtype": "Float", "width": 100},
		
		# Pricing & Values
		{"label": _("MRP"), "fieldname": "custom_mrp", "fieldtype": "Currency", "options": "currency", "width": 90},
		{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "options": "currency", "width": 100},
		{"label": _("Discount %"), "fieldname": "discount_percentage", "fieldtype": "Float", "width": 90},
		{"label": _("Net Rate"), "fieldname": "net_rate", "fieldtype": "Currency", "options": "currency", "width": 100},
		{"label": _("Net Amount"), "fieldname": "net_amount", "fieldtype": "Currency", "options": "currency", "width": 110},
		
		# Accounting & Warehousing
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 130,
		},
		{
			"label": _("Expense Account"),
			"fieldname": "expense_account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 140,
		},
		{
			"label": _("Cost Center"),
			"fieldname": "cost_center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 120,
		},
		{"fieldname": "currency", "label": _("Currency"), "fieldtype": "Data", "width": 70},
	]


def get_grn_items(filters):
	conditions = ["pr.docstatus = 1"]
	params = {}

	if filters.get("from_date"):
		conditions.append("pr.posting_date >= %(from_date)s")
		params["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("pr.posting_date <= %(to_date)s")
		params["to_date"] = filters.get("to_date")

	if filters.get("supplier"):
		conditions.append("pr.supplier = %(supplier)s")
		params["supplier"] = filters.get("supplier")

	if filters.get("company"):
		conditions.append("pr.company = %(company)s")
		params["company"] = filters.get("company")

	if filters.get("warehouse"):
		conditions.append("pri.warehouse = %(warehouse)s")
		params["warehouse"] = filters.get("warehouse")

	if filters.get("cost_center"):
		conditions.append("pri.cost_center = %(cost_center)s")
		params["cost_center"] = filters.get("cost_center")

	if filters.get("item_group"):
		conditions.append("pri.item_group = %(item_group)s")
		params["item_group"] = filters.get("item_group")

	if filters.get("item_code"):
		conditions.append("pri.item_code = %(item_code)s")
		params["item_code"] = filters.get("item_code")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT 
			pr.name AS voucher_no,
			pr.posting_date,
			pr.supplier,
			pr.supplier_name,
			pr.custom_invoice_no,
			pr.currency,
			pri.purchase_order,
			pri.item_code,
			pri.item_name,
			pri.item_group,
			pri.brand,
			pri.uom,
			COALESCE(pri.custom_user_batch_no, pri.batch_no) AS batch_no,
			pri.received_qty,
			pri.qty,
			pri.rejected_qty,
			pri.custom_mrp,
			pri.rate,
			pri.discount_percentage,
			pri.net_rate,
			pri.net_amount,
			pri.warehouse,
			pri.expense_account,
			pri.cost_center
		FROM `tabPurchase Receipt` pr
		INNER JOIN `tabPurchase Receipt Item` pri ON pri.parent = pr.name
		WHERE {where_clause}
		ORDER BY pr.posting_date DESC, pr.name DESC, pri.idx ASC
	"""

	return frappe.db.sql(query, params, as_dict=True)