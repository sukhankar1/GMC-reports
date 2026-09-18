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
			"label": _("Supplier Code"),
			"fieldname": "supplier_code",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 140,
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Category"),
			"fieldname": "category",
			"fieldtype": "Link",
			"options": "Supplier Group",
			"width": 140,
		},
		{
			"label": _("Transaction Type"),
			"fieldname": "transaction_type",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Address"),
			"fieldname": "address",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Contact Person"),
			"fieldname": "contact_person",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Contact Number"),
			"fieldname": "contact_number",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Email 1"),
			"fieldname": "email_1",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Email 2"),
			"fieldname": "email_2",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Manufacturer"),
			"fieldname": "manufacturer",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Drug Lic No"),
			"fieldname": "drug_lic_no",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Payment Terms"),
			"fieldname": "payment_terms",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("PAN No."),
			"fieldname": "pan_no",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Bank Name"),
			"fieldname": "bank_name",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("IFSC Code"),
			"fieldname": "ifsc_code",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Bank Account"),
			"fieldname": "bank_account",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("DL Valid From"),
			"fieldname": "dl_valid_from",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("DL Valid Upto"),
			"fieldname": "dl_valid_upto",
			"fieldtype": "Date",
			"width": 105,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 90,
		},
	]


def get_data(filters):
	conditions = []
	params = {}

	if filters.get("supplier"):
		conditions.append("s.name = %(supplier)s")
		params["supplier"] = filters.get("supplier")

	if filters.get("transaction_type"):
		tt = filters.get("transaction_type")
		conditions.append("(s.supplier_type = %(transaction_type)s OR s.payment_terms = %(transaction_type)s)")
		params["transaction_type"] = tt

	where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

	query = f"""
		SELECT 
			s.name AS supplier_code,
			s.supplier_name,
			s.supplier_group AS category,
			COALESCE(NULLIF(s.supplier_type, ''), 'Company') AS transaction_type,
			COALESCE(NULLIF(s.primary_address, ''), '') AS address,
			COALESCE(c.first_name, s.supplier_primary_contact, '') AS contact_person,
			COALESCE(s.mobile_no, c.mobile_no, c.phone, '') AS contact_number,
			COALESCE(s.email_id, c.email_id, '') AS email_1,
			'' AS email_2,
			COALESCE(NULLIF(s.country, ''), 'India') AS manufacturer,
			'' AS department,
			COALESCE(NULLIF(s.tax_id, ''), '') AS drug_lic_no,
			COALESCE(NULLIF(s.payment_terms, ''), '') AS payment_terms,
			COALESCE(NULLIF(s.tax_id, ''), '') AS pan_no,
			COALESCE(ba.bank, '') AS bank_name,
			COALESCE(ba.branch_code, '') AS ifsc_code,
			COALESCE(ba.bank_account_no, '') AS bank_account,
			NULL AS dl_valid_from,
			NULL AS dl_valid_upto,
			CASE WHEN s.disabled = 1 THEN 'Disabled' ELSE 'Active' END AS status
		FROM 
			`tabSupplier` s
		LEFT JOIN 
			`tabContact` c ON c.name = s.supplier_primary_contact
		LEFT JOIN 
			`tabBank Account` ba ON ba.party_type = 'Supplier' AND ba.party = s.name AND ba.is_default = 1
		{where_clause}
		ORDER BY 
			s.supplier_name ASC
	"""

	return frappe.db.sql(query, params, as_dict=True)
