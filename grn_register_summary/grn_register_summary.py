# Copyright (c) 2026, Quantbit HIMS Integration and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.utils import get_party_details


def execute(filters=None):
	return _execute(filters)


def _execute(filters=None):
	if not filters:
		filters = {}

	grn_list = get_purchase_receipts(filters)

	if not grn_list:
		columns = get_columns([])[0]
		return columns, []

	columns, expense_accounts, tax_accounts = get_columns(grn_list)

	grn_expense_map = get_grn_expense_map(grn_list)
	grn_expense_map, grn_tax_map = get_grn_tax_map(grn_list, grn_expense_map, expense_accounts)
	grn_po_map = get_grn_po_map(grn_list)

	suppliers = list(set(d.supplier for d in grn_list if d.supplier))
	supplier_details = get_party_details("Supplier", suppliers) if suppliers else {}

	company_currency = frappe.get_cached_value("Company", filters.get("company"), "default_currency")

	data = []
	for grn in grn_list:
		purchase_order = list(set(grn_po_map.get(grn.name, {}).get("purchase_order", [])))
		supp_info = supplier_details.get(grn.supplier, {}) if grn.supplier else {}

		row = {
			"voucher_type": "Purchase Receipt",
			"voucher_no": grn.name,
			"posting_date": grn.posting_date,
			"supplier_id": grn.supplier,
			"supplier_name": grn.supplier_name,
			"supplier_group": supp_info.get("supplier_group"),
			"tax_id": supp_info.get("tax_id"),
			"custom_invoice_no": grn.custom_invoice_no,
			"purchase_order": ", ".join(purchase_order),
			"currency": company_currency or grn.currency,
		}

		# Dynamic Expense Columns
		base_net_total = 0
		for expense_acc in expense_accounts:
			expense_amount = flt(grn_expense_map.get(grn.name, {}).get(expense_acc))
			base_net_total += expense_amount
			row.update({frappe.scrub(expense_acc): expense_amount})

		# Net Total
		row.update({"net_total": base_net_total or grn.base_net_total})

		# Dynamic Tax Columns
		total_tax = 0
		for tax_acc in tax_accounts:
			if tax_acc not in expense_accounts:
				tax_amount = flt(grn_tax_map.get(grn.name, {}).get(tax_acc))
				total_tax += tax_amount
				row.update({frappe.scrub(tax_acc): tax_amount})

		# Totals
		row.update(
			{
				"total_tax": total_tax,
				"grand_total": grn.base_grand_total,
				"rounded_total": grn.base_rounded_total,
			}
		)

		data.append(row)

	data = sorted(data, key=lambda x: x["posting_date"])
	return columns, data


def get_columns(grn_list):
	columns = [
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
		{
			"label": _("Voucher"),
			"fieldname": "voucher_no",
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 140,
		},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Supplier"),
			"fieldname": "supplier_id",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 140,
		},
		{"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 140},
		{
			"label": _("Supplier Group"),
			"fieldname": "supplier_group",
			"fieldtype": "Link",
			"options": "Supplier Group",
			"width": 120,
		},
		{"label": _("Tax ID"), "fieldname": "tax_id", "fieldtype": "Data", "width": 100},
		{"label": _("Supplier Invoice No"), "fieldname": "custom_invoice_no", "fieldtype": "Data", "width": 130},
		{
			"label": _("Purchase Order"),
			"fieldname": "purchase_order",
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 130,
		},
		{"fieldname": "currency", "label": _("Currency"), "fieldtype": "Data", "width": 80},
	]

	account_columns, accounts = get_account_columns(grn_list)

	columns = (
		columns
		+ account_columns[0]
		+ [
			{
				"label": _("Net Total"),
				"fieldname": "net_total",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		]
		+ account_columns[1]
		+ [
			{
				"label": _("Total Tax"),
				"fieldname": "total_tax",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Grand Total"),
				"fieldname": "grand_total",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Rounded Total"),
				"fieldname": "rounded_total",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
		]
	)
	return columns, accounts[0], accounts[1]


def get_account_columns(grn_list):
	expense_accounts = []
	tax_accounts = []
	expense_columns = []
	tax_columns = []

	if grn_list:
		grn_names = tuple(d.name for d in grn_list)

		expense_accounts = frappe.db.sql_list(
			f"""SELECT DISTINCT expense_account
			FROM `tabPurchase Receipt Item` 
			WHERE docstatus = 1
			AND (expense_account IS NOT NULL AND expense_account != '')
			AND parenttype = 'Purchase Receipt'
			AND parent IN ({', '.join(['%s'] * len(grn_names))}) 
			ORDER BY expense_account""",
			grn_names,
		)

		tax_accounts = frappe.db.sql_list(
			f"""SELECT DISTINCT account_head
			FROM `tabPurchase Taxes and Charges` 
			WHERE docstatus = 1
			AND (account_head IS NOT NULL AND account_head != '')
			AND parenttype = 'Purchase Receipt'
			AND parent IN ({', '.join(['%s'] * len(grn_names))}) 
			ORDER BY account_head""",
			grn_names,
		)

	for account in expense_accounts:
		expense_columns.append(
			{
				"label": account,
				"fieldname": frappe.scrub(account),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)

	for account in tax_accounts:
		if account not in expense_accounts:
			tax_columns.append(
				{
					"label": account,
					"fieldname": frappe.scrub(account),
					"fieldtype": "Currency",
					"options": "currency",
					"width": 120,
				}
			)

	return [expense_columns, tax_columns], [expense_accounts, tax_accounts]


def get_purchase_receipts(filters):
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

	child_join = ""
	if filters.get("warehouse") or filters.get("item_group") or filters.get("cost_center"):
		child_join = " INNER JOIN `tabPurchase Receipt Item` pri ON pri.parent = pr.name "
		if filters.get("warehouse"):
			conditions.append("pri.warehouse = %(warehouse)s")
			params["warehouse"] = filters.get("warehouse")
		if filters.get("cost_center"):
			conditions.append("pri.cost_center = %(cost_center)s")
			params["cost_center"] = filters.get("cost_center")
		if filters.get("item_group"):
			conditions.append("pri.item_group = %(item_group)s")
			params["item_group"] = filters.get("item_group")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT DISTINCT
			pr.name,
			pr.posting_date,
			pr.supplier,
			pr.supplier_name,
			pr.custom_invoice_no,
			pr.currency,
			pr.base_net_total,
			pr.base_grand_total,
			pr.base_rounded_total
		FROM `tabPurchase Receipt` pr
		{child_join}
		WHERE {where_clause}
		ORDER BY pr.posting_date DESC, pr.name DESC
	"""

	return frappe.db.sql(query, params, as_dict=True)


def get_grn_expense_map(grn_list):
	grn_names = tuple(d.name for d in grn_list)
	expense_details = frappe.db.sql(
		f"""
		SELECT parent, expense_account, SUM(base_net_amount) AS amount
		FROM `tabPurchase Receipt Item`
		WHERE parent IN ({', '.join(['%s'] * len(grn_names))}) AND parenttype = 'Purchase Receipt'
		GROUP BY parent, expense_account
	""",
		grn_names,
		as_dict=1,
	)

	grn_expense_map = {}
	for d in expense_details:
		grn_expense_map.setdefault(d.parent, frappe._dict()).setdefault(d.expense_account, 0.0)
		grn_expense_map[d.parent][d.expense_account] = flt(d.amount)

	return grn_expense_map


def get_grn_tax_map(grn_list, grn_expense_map, expense_accounts):
	grn_names = tuple(d.name for d in grn_list)
	tax_details = frappe.db.sql(
		f"""
		SELECT parent, account_head,
			CASE add_deduct_tax WHEN 'Add' THEN SUM(base_tax_amount_after_discount_amount)
			ELSE SUM(base_tax_amount_after_discount_amount) * -1 END AS tax_amount
		FROM `tabPurchase Taxes and Charges`
		WHERE parent IN ({', '.join(['%s'] * len(grn_names))}) AND parenttype = 'Purchase Receipt'
			AND category IN ('Total', 'Valuation and Total')
			AND base_tax_amount_after_discount_amount != 0
		GROUP BY parent, account_head, add_deduct_tax
	""",
		grn_names,
		as_dict=1,
	)

	grn_tax_map = {}
	for d in tax_details:
		if d.account_head in expense_accounts:
			if d.account_head in grn_expense_map.get(d.parent, {}):
				grn_expense_map[d.parent][d.account_head] += flt(d.tax_amount)
			else:
				grn_expense_map.setdefault(d.parent, frappe._dict())[d.account_head] = flt(d.tax_amount)
		else:
			grn_tax_map.setdefault(d.parent, frappe._dict())[d.account_head] = flt(d.tax_amount)

	return grn_expense_map, grn_tax_map


def get_grn_po_map(grn_list):
	grn_names = tuple(d.name for d in grn_list)
	pr_items = frappe.db.sql(
		f"""
		SELECT parent, purchase_order
		FROM `tabPurchase Receipt Item`
		WHERE parent IN ({', '.join(['%s'] * len(grn_names))}) AND parenttype = 'Purchase Receipt'
	""",
		grn_names,
		as_dict=1,
	)

	grn_po_map = {}
	for d in pr_items:
		if d.purchase_order:
			grn_po_map.setdefault(d.parent, frappe._dict()).setdefault("purchase_order", []).append(
				d.purchase_order
			)

	return grn_po_map