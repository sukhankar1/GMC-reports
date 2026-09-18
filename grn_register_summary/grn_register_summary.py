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
			"label": _("Inward No."),
			"fieldname": "inward_no",
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 160,
		},
		{
			"label": _("Inward Date"),
			"fieldname": "inward_date",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("P. O. No."),
			"fieldname": "po_no",
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 160,
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
			"label": _("Cash /Credit"),
			"fieldname": "pay_mode",
			"fieldtype": "Data",
			"width": 100,
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
			"width": 200,
		},
		{
			"label": _("Total Discount"),
			"fieldname": "total_discount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Total Item Disc"),
			"fieldname": "total_item_disc",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Total Expense"),
			"fieldname": "total_expense",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Tally Posting"),
			"fieldname": "tally_posting",
			"fieldtype": "Data",
			"width": 100,
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

	if filters.get("status"):
		st = filters.get("status")
		if st == "Bill Done" or st == "Completed":
			conditions.append("(pr.status = 'Completed' OR pr.per_billed >= 100)")
		elif st == "Partly Billed":
			conditions.append("pr.status = 'Partly Billed'")
		elif st == "To Bill":
			conditions.append("(pr.status = 'To Bill' AND (pr.per_billed < 100 OR pr.per_billed IS NULL))")
		elif st == "Draft":
			conditions.append("pr.docstatus = 0")
		elif st == "Cancelled":
			conditions.append("pr.docstatus = 2")
		elif st in ["Return", "Return Issued"]:
			conditions.append("pr.is_return = 1")
		elif st == "Closed":
			conditions.append("pr.status = 'Closed'")

	if filters.get("manufacturer") or filters.get("classification"):
		item_conditions = []
		if filters.get("manufacturer"):
			item_conditions.append("(item.brand = %(manufacturer)s OR item.manufacturer = %(manufacturer)s)")
			params["manufacturer"] = filters.get("manufacturer")
		if filters.get("classification"):
			item_conditions.append("(item.custom_classification = %(classification)s)")
			params["classification"] = filters.get("classification")

		conditions.append(f"""EXISTS (
			SELECT 1 FROM `tabPurchase Receipt Item` pri_filter
			LEFT JOIN `tabItem` item ON item.name = pri_filter.item_code
			WHERE pri_filter.parent = pr.name AND {' AND '.join(item_conditions)}
		)""")

	if filters.get("indigenous_imported"):
		ind_imp = filters.get("indigenous_imported")
		if ind_imp == "Indigenous":
			conditions.append("(s.country = 'India' OR s.country = 'IN' OR s.country IS NULL OR s.country = '')")
		elif ind_imp == "Imported":
			conditions.append("(s.country != 'India' AND s.country != 'IN' AND s.country IS NOT NULL AND s.country != '')")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT 
			pr.name AS inward_no,
			pr.posting_date AS inward_date,
			COALESCE(
				NULLIF(GROUP_CONCAT(DISTINCT pri.purchase_order SEPARATOR ', '), ''),
				''
			) AS po_no,
			COALESCE(NULLIF(pr.custom_invoice_no, ''), NULLIF(pr.supplier_delivery_note, ''), '') AS invoice_no,
			COALESCE(pr.custom_invoice_date, pr.custom_delivery_date, pr.posting_date) AS invoice_date,
			'Credit' AS pay_mode,
			COALESCE(NULLIF(pr.custom_department, ''), NULLIF(pr.custom_for_department, ''), '') AS department,
			pr.supplier_name AS supplier_name,
			COALESCE(pr.discount_amount, 0.0) AS total_discount,
			COALESCE(SUM(pri.discount_amount), 0.0) AS total_item_disc,
			COALESCE(pr.taxes_and_charges_added, pr.total_taxes_and_charges, 0.0) AS total_expense,
			COALESCE(pr.grand_total, pr.base_grand_total, 0.0) AS total_amount,
			CASE 
				WHEN pr.status = 'Completed' OR pr.per_billed >= 100 THEN 'Bill Done'
				WHEN pr.status = 'Partly Billed' THEN 'Partly Billed'
				WHEN pr.status = 'To Bill' THEN 'To Bill'
				ELSE pr.status
			END AS status,
			'N' AS tally_posting,
			pr.currency AS currency
		FROM 
			`tabPurchase Receipt` pr
		LEFT JOIN 
			`tabPurchase Receipt Item` pri ON pri.parent = pr.name
		LEFT JOIN 
			`tabSupplier` s ON s.name = pr.supplier
		WHERE 
			{where_clause}
		GROUP BY 
			pr.name
		ORDER BY 
			pr.posting_date DESC, pr.name DESC
	"""

	return frappe.db.sql(query, params, as_dict=True)