# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}
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
			"width": 160,
		},
		{
			"label": _("Category"),
			"fieldname": "category",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 130,
		},
		{
			"label": _("Sub Category"),
			"fieldname": "sub_category",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 130,
		},
		{
			"label": _("HSN Code"),
			"fieldname": "hsn_code",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Unit"),
			"fieldname": "unit",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 80,
		},
		{
			"label": _("Batch No."),
			"fieldname": "batch_no",
			"fieldtype": "Link",
			"options": "Batch",
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
			"width": 140,
		},
		{
			"label": _("Schedule Type"),
			"fieldname": "schedule_type",
			"fieldtype": "Link",
			"options": "Schedule Type",
			"width": 120,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("Supplier GSTN"),
			"fieldname": "supplier_gstin",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Supplier Location"),
			"fieldname": "supplier_location",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Purchase Reg No"),
			"fieldname": "purchase_reg_no",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 150,
		},
		{
			"label": _("PO Date"),
			"fieldname": "po_date",
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
			"label": _("Invoice No"),
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
			"label": _("Conversion Factor"),
			"fieldname": "conversion_factor",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Purchase Qty."),
			"fieldname": "purchase_qty",
			"fieldtype": "Float",
			"width": 110,
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
			"label": _("Rate After Conc."),
			"fieldname": "rate_after_conc",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Concession Amt."),
			"fieldname": "concession_amt",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Taxable Value"),
			"fieldname": "taxable_value",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Total Amt."),
			"fieldname": "total_amt",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
	]


def get_data(filters):
	conditions, values = get_conditions(filters)

	query = f"""
		SELECT 
			pi.name AS purchase_reg_no,
			pi.posting_date AS posting_date,
			pi.bill_no AS invoice_no,
			pi.bill_date AS invoice_date,
			pi.supplier AS supplier,
			pi.supplier_name AS supplier_name,
			pi.supplier_gstin AS supplier_gstin,
			pi.mode_of_payment AS pay_mode,
			pi.is_paid AS is_paid,
			pi.outstanding_amount AS outstanding_amount,
			pi.department AS inv_department,
			pi.custom_department AS inv_custom_dept,
			pi.custom_for_department AS inv_custom_for_dept,
			pi.currency AS currency,
			pii.item_code AS item_code,
			pii.item_name AS item_name,
			COALESCE(pii.gst_hsn_code, item.gst_hsn_code) AS hsn_code,
			COALESCE(pii.uom, pii.stock_uom) AS unit,
			pii.batch_no AS batch_no,
			COALESCE(pii.custom_expiry_date, batch.expiry_date) AS expiry_date,
			COALESCE(pii.department, pi.department, pi.custom_department, pi.custom_for_department) AS department,
			pii.conversion_factor AS conversion_factor,
			pii.qty AS purchase_qty,
			COALESCE(pii.custom_free_qty, 0.0) AS free_qty,
			COALESCE(pii.custom_mrp, item.custom_mrp, 0.0) AS mrp,
			pii.rate AS rate,
			COALESCE(pii.discount_amount, 0.0) AS concession_amt,
			COALESCE(pii.taxable_value, pii.base_net_amount, pii.amount, 0.0) AS taxable_value,
			COALESCE(pii.custom_total_amount, pii.amount, pii.base_net_amount, 0.0) AS total_amt,
			item.custom_category AS category,
			COALESCE(pii.item_group, item.item_group) AS sub_category,
			item.custom_schedule_type AS schedule_type,
			COALESCE(pii.custom_brand_new, item.brand) AS manufacturer,
			po.transaction_date AS po_date,
			COALESCE(NULLIF(addr.city, ''), NULLIF(addr.state, ''), addr.address_line1, '') AS supplier_location
		FROM 
			`tabPurchase Invoice Item` pii
		INNER JOIN 
			`tabPurchase Invoice` pi ON pi.name = pii.parent
		LEFT JOIN 
			`tabItem` item ON item.name = pii.item_code
		LEFT JOIN 
			`tabBatch` batch ON batch.name = pii.batch_no
		LEFT JOIN 
			`tabPurchase Order` po ON po.name = pii.purchase_order
		LEFT JOIN 
			`tabAddress` addr ON addr.name = pi.supplier_address
		WHERE 
			pi.docstatus = 1
			{conditions}
		ORDER BY 
			pi.posting_date DESC, pi.name DESC
	"""

	raw_data = frappe.db.sql(query, values, as_dict=True)
	data = []

	for idx, row in enumerate(raw_data, 1):
		purchase_qty = flt(row.get("purchase_qty"))
		rate = flt(row.get("rate"))
		concession_amt = flt(row.get("concession_amt"))

		if purchase_qty > 0 and concession_amt > 0:
			rate_after_conc = flt(rate - (concession_amt / purchase_qty), 2)
		else:
			rate_after_conc = rate

		pay_mode = row.get("pay_mode")
		if not pay_mode:
			if row.get("is_paid") or flt(row.get("outstanding_amount")) <= 0:
				pay_mode = "Cash"
			else:
				pay_mode = "Credit"

		data.append({
			"sr_no": idx,
			"item_code": row.get("item_code"),
			"item_name": row.get("item_name"),
			"category": row.get("category"),
			"sub_category": row.get("sub_category"),
			"hsn_code": row.get("hsn_code"),
			"unit": row.get("unit"),
			"batch_no": row.get("batch_no"),
			"expiry_date": row.get("expiry_date"),
			"department": row.get("department"),
			"schedule_type": row.get("schedule_type"),
			"supplier_name": row.get("supplier_name") or row.get("supplier"),
			"supplier_gstin": row.get("supplier_gstin"),
			"supplier_location": row.get("supplier_location"),
			"purchase_reg_no": row.get("purchase_reg_no"),
			"po_date": row.get("po_date") or row.get("posting_date"),
			"pay_mode": pay_mode,
			"invoice_no": row.get("invoice_no") or row.get("purchase_reg_no"),
			"invoice_date": row.get("invoice_date") or row.get("posting_date"),
			"conversion_factor": flt(row.get("conversion_factor") or 1.0),
			"purchase_qty": purchase_qty,
			"free_qty": flt(row.get("free_qty")),
			"mrp": flt(row.get("mrp")),
			"rate": rate,
			"rate_after_conc": rate_after_conc,
			"concession_amt": concession_amt,
			"taxable_value": flt(row.get("taxable_value")),
			"total_amt": flt(row.get("total_amt")),
			"currency": row.get("currency"),
		})

	return data


def get_conditions(filters):
	conditions = []
	values = {}

	if filters.get("company"):
		conditions.append("pi.company = %(company)s")
		values["company"] = filters.get("company")

	if filters.get("from_date"):
		conditions.append("pi.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("pi.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("item_code"):
		conditions.append("pii.item_code = %(item_code)s")
		values["item_code"] = filters.get("item_code")

	if filters.get("supplier"):
		conditions.append("pi.supplier = %(supplier)s")
		values["supplier"] = filters.get("supplier")

	if filters.get("manufacturer"):
		conditions.append("(item.brand = %(manufacturer)s OR pii.custom_brand_new = %(manufacturer)s)")
		values["manufacturer"] = filters.get("manufacturer")

	if filters.get("department"):
		conditions.append(
			"(pii.department = %(department)s OR pi.department = %(department)s OR pi.custom_department = %(department)s OR pi.custom_for_department = %(department)s)"
		)
		values["department"] = filters.get("department")

	if filters.get("therapeutic_group"):
		conditions.append("(item.custom_category = %(therapeutic_group)s OR item.item_group = %(therapeutic_group)s)")
		values["therapeutic_group"] = filters.get("therapeutic_group")

	if filters.get("therapeutic_sub_group"):
		conditions.append("(item.item_group = %(therapeutic_sub_group)s OR pii.item_group = %(therapeutic_sub_group)s)")
		values["therapeutic_sub_group"] = filters.get("therapeutic_sub_group")

	if filters.get("payment_type"):
		payment_type = filters.get("payment_type").strip().lower()
		if payment_type == "cash":
			conditions.append("(pi.mode_of_payment LIKE '%%Cash%%' OR pi.is_paid = 1)")
		elif payment_type == "credit":
			conditions.append("(pi.mode_of_payment LIKE '%%Credit%%' OR (pi.is_paid = 0 AND (pi.mode_of_payment IS NULL OR pi.mode_of_payment = '' OR pi.mode_of_payment NOT LIKE '%%Cash%%')))")

	cond_str = " AND " + " AND ".join(conditions) if conditions else ""
	return cond_str, values
