# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import copy
from collections import OrderedDict

import frappe
from frappe import _, _dict
from frappe.query_builder import Criterion
from frappe.utils import cstr, getdate

from erpnext import get_company_currency, get_default_company
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
	get_dimension_with_children,
)
from erpnext.accounts.report.financial_statements import get_cost_centers_with_children
from erpnext.accounts.report.utils import convert_to_presentation_currency, get_currency
from erpnext.accounts.utils import get_account_currency


def parse_multiselect(val):
	if not val:
		return []
	if isinstance(val, str):
		try:
			val = frappe.parse_json(val)
		except Exception:
			val = [d.strip() for d in val.split(",") if d.strip()]
	if isinstance(val, list):
		return [str(x).strip() for x in val if x and str(x).strip()]
	return [str(val).strip()]


@frappe.whitelist()
def get_uhid_options(txt=None):
	if not txt:
		txt = ""
	search_txt = f"%{txt}%"
	subqueries = []
	params = {"txt": search_txt}

	if frappe.db.has_column("Patient", "name"):
		subqueries.append("SELECT name AS uhid FROM `tabPatient` WHERE name LIKE %(txt)s")
	if frappe.db.has_column("Patient", "uhid"):
		subqueries.append("SELECT uhid FROM `tabPatient` WHERE uhid LIKE %(txt)s")
	if frappe.db.has_column("Sales Invoice", "custom_uhid"):
		subqueries.append("SELECT custom_uhid AS uhid FROM `tabSales Invoice` WHERE custom_uhid LIKE %(txt)s")
	if frappe.db.has_column("Payment Entry", "custom_uhid"):
		subqueries.append("SELECT custom_uhid AS uhid FROM `tabPayment Entry` WHERE custom_uhid LIKE %(txt)s")
	if frappe.db.has_column("Journal Entry", "custom_his_uhid"):
		subqueries.append("SELECT custom_his_uhid AS uhid FROM `tabJournal Entry` WHERE custom_his_uhid LIKE %(txt)s")
	if frappe.db.has_column("Journal Entry", "custom_uhid"):
		subqueries.append("SELECT custom_uhid AS uhid FROM `tabJournal Entry` WHERE custom_uhid LIKE %(txt)s")

	if not subqueries:
		return []

	query = f"SELECT DISTINCT uhid FROM ({' UNION '.join(subqueries)}) t WHERE uhid IS NOT NULL AND uhid != '' LIMIT 20"
	results = frappe.db.sql(query, params, as_dict=True)
	return [r.uhid for r in results]


@frappe.whitelist()
def get_bill_no_options(txt=None):
	if not txt:
		txt = ""
	search_txt = f"%{txt}%"
	subqueries = []
	params = {"txt": search_txt}

	if frappe.db.has_column("Sales Invoice", "custom_bill_no"):
		subqueries.append("SELECT custom_bill_no AS bill_no FROM `tabSales Invoice` WHERE custom_bill_no LIKE %(txt)s")
	if frappe.db.has_column("Sales Invoice", "custom_sale_bill"):
		subqueries.append("SELECT custom_sale_bill AS bill_no FROM `tabSales Invoice` WHERE custom_sale_bill LIKE %(txt)s")
	if frappe.db.has_column("Payment Entry", "custom_bill_no"):
		subqueries.append("SELECT custom_bill_no AS bill_no FROM `tabPayment Entry` WHERE custom_bill_no LIKE %(txt)s")
	if frappe.db.has_column("Journal Entry", "custom_his_bill_no"):
		subqueries.append("SELECT custom_his_bill_no AS bill_no FROM `tabJournal Entry` WHERE custom_his_bill_no LIKE %(txt)s")
	if frappe.db.has_column("Journal Entry", "custom_bill_no"):
		subqueries.append("SELECT custom_bill_no AS bill_no FROM `tabJournal Entry` WHERE custom_bill_no LIKE %(txt)s")

	if not subqueries:
		return []

	query = f"SELECT DISTINCT bill_no FROM ({' UNION '.join(subqueries)}) t WHERE bill_no IS NOT NULL AND bill_no != '' LIMIT 20"
	results = frappe.db.sql(query, params, as_dict=True)
	return [r.bill_no for r in results]


@frappe.whitelist()
def get_bill_id_options(txt=None):
	if not txt:
		txt = ""
	search_txt = f"%{txt}%"
	subqueries = []
	params = {"txt": search_txt}

	if frappe.db.has_column("Sales Invoice", "custom_bill_id"):
		subqueries.append("SELECT custom_bill_id AS bill_id FROM `tabSales Invoice` WHERE custom_bill_id LIKE %(txt)s")
	if frappe.db.has_column("Payment Entry", "custom_bill_id"):
		subqueries.append("SELECT custom_bill_id AS bill_id FROM `tabPayment Entry` WHERE custom_bill_id LIKE %(txt)s")
	if frappe.db.has_column("Journal Entry", "custom_his_bill_id"):
		subqueries.append("SELECT custom_his_bill_id AS bill_id FROM `tabJournal Entry` WHERE custom_his_bill_id LIKE %(txt)s")
	if frappe.db.has_column("Journal Entry", "custom_bill_id"):
		subqueries.append("SELECT custom_bill_id AS bill_id FROM `tabJournal Entry` WHERE custom_bill_id LIKE %(txt)s")

	if not subqueries:
		return []

	query = f"SELECT DISTINCT bill_id FROM ({' UNION '.join(subqueries)}) t WHERE bill_id IS NOT NULL AND bill_id != '' LIMIT 20"
	results = frappe.db.sql(query, params, as_dict=True)
	return [r.bill_id for r in results]


def get_matching_vouchers(filters):
	patients = parse_multiselect(filters.get("patient"))
	uhids = parse_multiselect(filters.get("uhid"))
	bill_nos = parse_multiselect(filters.get("bill_no"))
	bill_ids = parse_multiselect(filters.get("bill_id"))

	if not (patients or uhids or bill_nos or bill_ids):
		return None

	patient_set = set(patients)
	uhid_set = set(uhids)
	bill_no_set = set(bill_nos)
	bill_id_set = set(bill_ids)

	if patient_set or uhid_set:
		p_conds = []
		p_params = {}
		if patient_set:
			p_conds.append("name IN %(patients)s OR uhid IN %(patients)s")
			p_params["patients"] = tuple(patient_set)
		if uhid_set:
			p_conds.append("name IN %(uhids)s OR uhid IN %(uhids)s")
			p_params["uhids"] = tuple(uhid_set)

		patient_records = frappe.db.sql(f"""
			SELECT name, uhid FROM `tabPatient`
			WHERE {" OR ".join(p_conds)}
		""", p_params, as_dict=True)
		for pr in patient_records:
			if pr.name:
				patient_set.add(pr.name)
				uhid_set.add(pr.name)
			if pr.uhid:
				patient_set.add(pr.uhid)
				uhid_set.add(pr.uhid)

	matching_vouchers = set()
	matching_si = set()
	matching_pe = set()

	# 1. Sales Invoice
	si_conds = []
	si_params = {}
	if patient_set:
		si_conds.append("patient IN %(patients)s")
		si_params["patients"] = tuple(patient_set)
	if uhid_set and frappe.db.has_column("Sales Invoice", "custom_uhid"):
		si_conds.append("custom_uhid IN %(uhids)s")
		si_params["uhids"] = tuple(uhid_set)
	if bill_no_set:
		or_bill_no = ["name IN %(bill_nos)s"]
		if frappe.db.has_column("Sales Invoice", "custom_bill_no"):
			or_bill_no.append("custom_bill_no IN %(bill_nos)s")
		if frappe.db.has_column("Sales Invoice", "custom_sale_bill"):
			or_bill_no.append("custom_sale_bill IN %(bill_nos)s")
		si_conds.append(f"({' OR '.join(or_bill_no)})")
		si_params["bill_nos"] = tuple(bill_no_set)
	if bill_id_set and frappe.db.has_column("Sales Invoice", "custom_bill_id"):
		si_conds.append("custom_bill_id IN %(bill_ids)s")
		si_params["bill_ids"] = tuple(bill_id_set)

	if si_conds:
		si_rows = frappe.db.sql(f"""
			SELECT name, patient, custom_uhid, custom_bill_no, custom_bill_id
			FROM `tabSales Invoice`
			WHERE ({" OR ".join(si_conds)})
		""", si_params, as_dict=True)
		for row in si_rows:
			matching_vouchers.add(row.name)
			matching_si.add(row.name)
			if row.patient:
				patient_set.add(row.patient)
			if row.get("custom_uhid"):
				uhid_set.add(row.custom_uhid)
			if row.get("custom_bill_no"):
				bill_no_set.add(row.custom_bill_no)
			if row.get("custom_bill_id"):
				bill_id_set.add(row.custom_bill_id)

	if (bill_no_set or bill_id_set) and frappe.db.has_column("Sales Invoice", "custom_consolidate_bill_id_and_bill_no"):
		all_idents = list(bill_no_set | bill_id_set)
		json_conds = ["custom_consolidate_bill_id_and_bill_no LIKE %s" for _ in all_idents]
		json_params = [f"%{ident}%" for ident in all_idents]
		if json_conds:
			c_rows = frappe.db.sql(f"""
				SELECT name, patient, custom_uhid FROM `tabSales Invoice`
				WHERE ({" OR ".join(json_conds)})
			""", tuple(json_params), as_dict=True)
			for row in c_rows:
				matching_vouchers.add(row.name)
				matching_si.add(row.name)
				if row.patient:
					patient_set.add(row.patient)
				if row.get("custom_uhid"):
					uhid_set.add(row.custom_uhid)

	# 2. Payment Entry
	pe_conds = []
	pe_params = {}
	if patient_set and frappe.db.has_column("Payment Entry", "patient"):
		pe_conds.append("patient IN %(patients)s")
		pe_params["patients"] = tuple(patient_set)
	if uhid_set and frappe.db.has_column("Payment Entry", "custom_uhid"):
		pe_conds.append("custom_uhid IN %(uhids)s")
		pe_params["uhids"] = tuple(uhid_set)
	if bill_no_set:
		or_pe_bill = ["name IN %(bill_nos)s", "reference_no IN %(bill_nos)s"]
		if frappe.db.has_column("Payment Entry", "custom_bill_no"):
			or_pe_bill.append("custom_bill_no IN %(bill_nos)s")
		pe_conds.append(f"({' OR '.join(or_pe_bill)})")
		pe_params["bill_nos"] = tuple(bill_no_set)
	if bill_id_set and frappe.db.has_column("Payment Entry", "custom_bill_id"):
		pe_conds.append("custom_bill_id IN %(bill_ids)s")
		pe_params["bill_ids"] = tuple(bill_id_set)

	if pe_conds:
		pe_rows = frappe.db.sql(f"""
			SELECT name, patient, custom_uhid FROM `tabPayment Entry`
			WHERE ({" OR ".join(pe_conds)})
		""", pe_params, as_dict=True)
		for row in pe_rows:
			matching_vouchers.add(row.name)
			matching_pe.add(row.name)

	if matching_si:
		ref_rows = frappe.db.sql("""
			SELECT DISTINCT parent FROM `tabPayment Entry Reference`
			WHERE reference_doctype = 'Sales Invoice' AND reference_name IN %s
		""", (tuple(matching_si),), as_dict=True)
		for row in ref_rows:
			matching_vouchers.add(row.parent)
			matching_pe.add(row.parent)

	# 3. Journal Entry
	je_conds = []
	je_params = {}
	if uhid_set or patient_set:
		all_uhids_pats = tuple(uhid_set | patient_set)
		or_je_uhid = []
		if frappe.db.has_column("Journal Entry", "custom_his_uhid"):
			or_je_uhid.append("custom_his_uhid IN %(uhids)s")
		if frappe.db.has_column("Journal Entry", "custom_uhid"):
			or_je_uhid.append("custom_uhid IN %(uhids)s")
		if or_je_uhid:
			je_conds.append(f"({' OR '.join(or_je_uhid)})")
			je_params["uhids"] = all_uhids_pats

	if bill_no_set:
		or_je_bill = ["name IN %(bill_nos)s"]
		if frappe.db.has_column("Journal Entry", "custom_his_bill_no"):
			or_je_bill.append("custom_his_bill_no IN %(bill_nos)s")
		if frappe.db.has_column("Journal Entry", "custom_bill_no"):
			or_je_bill.append("custom_bill_no IN %(bill_nos)s")
		if frappe.db.has_column("Journal Entry", "custom_source_bill_no"):
			or_je_bill.append("custom_source_bill_no IN %(bill_nos)s")
		je_conds.append(f"({' OR '.join(or_je_bill)})")
		je_params["bill_nos"] = tuple(bill_no_set)

	if bill_id_set:
		or_je_id = []
		if frappe.db.has_column("Journal Entry", "custom_his_bill_id"):
			or_je_id.append("custom_his_bill_id IN %(bill_ids)s")
		if frappe.db.has_column("Journal Entry", "custom_bill_id"):
			or_je_id.append("custom_bill_id IN %(bill_ids)s")
		if or_je_id:
			je_conds.append(f"({' OR '.join(or_je_id)})")
			je_params["bill_ids"] = tuple(bill_id_set)

	if matching_si or matching_pe:
		linked_docs = tuple(matching_si | matching_pe)
		or_je_link = []
		if frappe.db.has_column("Journal Entry", "custom_doctype_name"):
			or_je_link.append("custom_doctype_name IN %(linked_docs)s")
		if or_je_link:
			je_conds.append(f"({' OR '.join(or_je_link)})")
			je_params["linked_docs"] = linked_docs

	if je_conds:
		je_rows = frappe.db.sql(f"""
			SELECT name FROM `tabJournal Entry`
			WHERE ({" OR ".join(je_conds)})
		""", je_params, as_dict=True)
		for row in je_rows:
			matching_vouchers.add(row.name)

	jea_conds = []
	jea_params = {}
	if (patient_set or uhid_set) and frappe.db.has_column("Journal Entry Account", "patient"):
		jea_conds.append("patient IN %(patients)s")
		jea_params["patients"] = tuple(patient_set | uhid_set)
	if matching_si or matching_pe:
		jea_conds.append("reference_name IN %(linked_docs)s")
		jea_params["linked_docs"] = tuple(matching_si | matching_pe)

	if jea_conds:
		jea_rows = frappe.db.sql(f"""
			SELECT DISTINCT parent FROM `tabJournal Entry Account`
			WHERE ({" OR ".join(jea_conds)})
		""", jea_params, as_dict=True)
		for row in jea_rows:
			matching_vouchers.add(row.parent)

	if bill_no_set or matching_si:
		search_terms = list(bill_no_set | matching_si)
		rem_conds = ["user_remark LIKE %s OR remark LIKE %s" for _ in search_terms]
		rem_params = []
		for term in search_terms:
			rem_params.extend([f"%{term}%", f"%{term}%"])
		if rem_conds:
			rem_rows = frappe.db.sql(f"""
				SELECT name FROM `tabJournal Entry`
				WHERE ({" OR ".join(rem_conds)})
			""", tuple(rem_params), as_dict=True)
			for row in rem_rows:
				matching_vouchers.add(row.name)

	if matching_vouchers:
		against_rows = frappe.db.sql("""
			SELECT DISTINCT voucher_no FROM `tabGL Entry`
			WHERE against_voucher IN %s
		""", (tuple(matching_vouchers),), as_dict=True)
		for row in against_rows:
			matching_vouchers.add(row.voucher_no)

	return list(matching_vouchers)


def enrich_gl_entries_with_hims_data(gl_entries):
	if not gl_entries:
		return

	voucher_map = {}
	for gle in gl_entries:
		vtype = gle.get("voucher_type")
		vno = gle.get("voucher_no")
		if vtype and vno:
			voucher_map.setdefault(vtype, set()).add(vno)

	hims_data = {}

	if "Sales Invoice" in voucher_map:
		si_names = list(voucher_map["Sales Invoice"])
		si_fields = ["name", "patient"]
		if frappe.db.has_column("Sales Invoice", "custom_uhid"):
			si_fields.append("custom_uhid")
		if frappe.db.has_column("Sales Invoice", "custom_bill_no"):
			si_fields.append("custom_bill_no")
		if frappe.db.has_column("Sales Invoice", "custom_sale_bill"):
			si_fields.append("custom_sale_bill")
		if frappe.db.has_column("Sales Invoice", "custom_bill_id"):
			si_fields.append("custom_bill_id")

		si_rows = frappe.db.sql(f"""
			SELECT {", ".join(si_fields)}
			FROM `tabSales Invoice`
			WHERE name IN %s
		""", (tuple(si_names),), as_dict=True)
		for r in si_rows:
			hims_data[("Sales Invoice", r.name)] = {
				"patient": r.get("patient") or "",
				"custom_uhid": r.get("custom_uhid") or r.get("patient") or "",
				"custom_bill_no": r.get("custom_bill_no") or r.get("custom_sale_bill") or r.name or "",
				"custom_bill_id": r.get("custom_bill_id") or "",
			}

	if "Payment Entry" in voucher_map:
		pe_names = list(voucher_map["Payment Entry"])
		pe_fields = ["name"]
		if frappe.db.has_column("Payment Entry", "patient"):
			pe_fields.append("patient")
		if frappe.db.has_column("Payment Entry", "custom_uhid"):
			pe_fields.append("custom_uhid")
		if frappe.db.has_column("Payment Entry", "custom_bill_no"):
			pe_fields.append("custom_bill_no")
		if frappe.db.has_column("Payment Entry", "custom_bill_id"):
			pe_fields.append("custom_bill_id")

		pe_rows = frappe.db.sql(f"""
			SELECT {", ".join(pe_fields)}
			FROM `tabPayment Entry`
			WHERE name IN %s
		""", (tuple(pe_names),), as_dict=True)
		for r in pe_rows:
			hims_data[("Payment Entry", r.name)] = {
				"patient": r.get("patient") or "",
				"custom_uhid": r.get("custom_uhid") or r.get("patient") or "",
				"custom_bill_no": r.get("custom_bill_no") or "",
				"custom_bill_id": r.get("custom_bill_id") or "",
			}

	if "Journal Entry" in voucher_map:
		je_names = list(voucher_map["Journal Entry"])
		je_fields = ["name"]
		if frappe.db.has_column("Journal Entry", "custom_his_uhid"):
			je_fields.append("custom_his_uhid")
		if frappe.db.has_column("Journal Entry", "custom_uhid"):
			je_fields.append("custom_uhid")
		if frappe.db.has_column("Journal Entry", "custom_his_bill_no"):
			je_fields.append("custom_his_bill_no")
		if frappe.db.has_column("Journal Entry", "custom_bill_no"):
			je_fields.append("custom_bill_no")
		if frappe.db.has_column("Journal Entry", "custom_his_bill_id"):
			je_fields.append("custom_his_bill_id")
		if frappe.db.has_column("Journal Entry", "custom_bill_id"):
			je_fields.append("custom_bill_id")

		je_rows = frappe.db.sql(f"""
			SELECT {", ".join(je_fields)}
			FROM `tabJournal Entry`
			WHERE name IN %s
		""", (tuple(je_names),), as_dict=True)

		je_patients = {}
		if frappe.db.has_column("Journal Entry Account", "patient"):
			jea_rows = frappe.db.sql("""
				SELECT DISTINCT parent, patient FROM `tabJournal Entry Account`
				WHERE parent IN %s AND patient IS NOT NULL AND patient != ''
			""", (tuple(je_names),), as_dict=True)
			for jea in jea_rows:
				je_patients[jea.parent] = jea.patient

		for r in je_rows:
			patient_val = je_patients.get(r.name) or r.get("custom_his_uhid") or r.get("custom_uhid") or ""
			hims_data[("Journal Entry", r.name)] = {
				"patient": patient_val,
				"custom_uhid": r.get("custom_his_uhid") or r.get("custom_uhid") or patient_val,
				"custom_bill_no": r.get("custom_his_bill_no") or r.get("custom_bill_no") or "",
				"custom_bill_id": r.get("custom_his_bill_id") or r.get("custom_bill_id") or "",
			}

	for gle in gl_entries:
		key = (gle.get("voucher_type"), gle.get("voucher_no"))
		info = hims_data.get(key, {})
		gle["patient"] = info.get("patient") or ""
		gle["custom_uhid"] = info.get("custom_uhid") or ""
		gle["custom_bill_no"] = info.get("custom_bill_no") or ""
		gle["custom_bill_id"] = info.get("custom_bill_id") or ""


def execute(filters=None):
	if not filters:
		return [], []

	filters = _dict(filters)

	account_details = {}

	if filters and filters.get("print_in_account_currency") and not filters.get("account"):
		frappe.throw(_("Select an account to print in account currency"))

	for acc in frappe.db.sql("""select name, is_group from tabAccount""", as_dict=1):
		account_details.setdefault(acc.name, acc)

	if filters.get("party"):
		filters.party = frappe.parse_json(filters.get("party"))

	if filters.get("patient"):
		filters.patient = parse_multiselect(filters.get("patient"))

	if filters.get("uhid"):
		filters.uhid = parse_multiselect(filters.get("uhid"))

	if filters.get("bill_no"):
		filters.bill_no = parse_multiselect(filters.get("bill_no"))

	if filters.get("bill_id"):
		filters.bill_id = parse_multiselect(filters.get("bill_id"))

	validate_filters(filters, account_details)

	validate_party(filters)

	filters = set_account_currency(filters)

	columns = get_columns(filters)

	res = get_result(filters, account_details)

	return columns, res


def validate_filters(filters, account_details):
	if not filters.get("company"):
		frappe.throw(_("{0} is mandatory").format(_("Company")))

	if not filters.get("from_date") and not filters.get("to_date"):
		frappe.throw(
			_("{0} and {1} are mandatory").format(frappe.bold(_("From Date")), frappe.bold(_("To Date")))
		)

	if filters.get("account"):
		filters.account = frappe.parse_json(filters.get("account"))
		for account in filters.account:
			if not account_details.get(account):
				frappe.throw(_("Account {0} does not exists").format(account))

	if not filters.get("categorize_by") and filters.get("group_by"):
		filters["categorize_by"] = filters["group_by"]
		filters["categorize_by"] = filters["categorize_by"].replace("Group by", "Categorize by")

	if filters.get("account") and filters.get("categorize_by") == "Categorize by Account":
		filters.account = frappe.parse_json(filters.get("account"))
		for account in filters.account:
			if account_details[account].is_group == 0:
				frappe.throw(_("Can not filter based on Child Account, if grouped by Account"))

	if filters.get("voucher_no") and filters.get("categorize_by") in ["Categorize by Voucher"]:
		frappe.throw(_("Can not filter based on Voucher No, if grouped by Voucher"))

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

	if filters.get("project"):
		filters.project = frappe.parse_json(filters.get("project"))

	if filters.get("cost_center"):
		filters.cost_center = frappe.parse_json(filters.get("cost_center"))


def validate_party(filters):
	party_type, party = filters.get("party_type"), filters.get("party")

	if party and party_type:
		for d in party:
			if not frappe.db.exists(party_type, d):
				frappe.throw(_("Invalid {0}: {1}").format(party_type, d))


def set_account_currency(filters):
	if filters.get("account") or (filters.get("party") and len(filters.party) == 1):
		filters["company_currency"] = frappe.get_cached_value("Company", filters.company, "default_currency")
		account_currency = None

		if filters.get("account"):
			if len(filters.get("account")) == 1:
				account_currency = get_account_currency(filters.account[0])
			else:
				currency = get_account_currency(filters.account[0])
				is_same_account_currency = True
				for account in filters.get("account"):
					if get_account_currency(account) != currency:
						is_same_account_currency = False
						break

				if is_same_account_currency:
					account_currency = currency

		elif filters.get("party") and filters.get("party_type"):
			gle_currency = frappe.db.get_value(
				"GL Entry",
				{"party_type": filters.party_type, "party": filters.party[0], "company": filters.company},
				"account_currency",
			)

			if gle_currency:
				account_currency = gle_currency
			else:
				account_currency = (
					None
					if filters.party_type in ["Employee", "Shareholder", "Member"]
					else frappe.get_cached_value(filters.party_type, filters.party[0], "default_currency")
				)

		filters["account_currency"] = account_currency or filters.company_currency
		if filters.account_currency != filters.company_currency and not filters.presentation_currency:
			filters.presentation_currency = filters.account_currency

	return filters


def get_result(filters, account_details):
	accounting_dimensions = []
	if filters.get("include_dimensions"):
		accounting_dimensions = get_accounting_dimensions()

	gl_entries = get_gl_entries(filters, accounting_dimensions)

	data = get_data_with_opening_closing(filters, account_details, accounting_dimensions, gl_entries)

	result = get_result_as_list(data, filters)

	return result


def get_gl_entries(filters, accounting_dimensions):
	currency_map = get_currency(filters)
	select_fields = """, debit, credit, debit_in_account_currency,
		credit_in_account_currency """

	if filters.get("show_remarks"):
		if remarks_length := frappe.db.get_single_value("Accounts Settings", "general_ledger_remarks_length"):
			select_fields += f",substr(remarks, 1, {remarks_length}) as 'remarks'"
		else:
			select_fields += """,remarks"""

	order_by_statement = "order by posting_date, account, creation"

	if filters.get("include_dimensions"):
		order_by_statement = "order by posting_date, creation"

	if filters.get("categorize_by") == "Categorize by Voucher":
		order_by_statement = "order by posting_date, voucher_type, voucher_no"
	if filters.get("categorize_by") == "Categorize by Account":
		order_by_statement = "order by account, posting_date, creation"

	if filters.get("include_default_book_entries"):
		filters["company_fb"] = frappe.get_cached_value(
			"Company", filters.get("company"), "default_finance_book"
		)

	dimension_fields = ""
	if accounting_dimensions:
		dimension_fields = ", ".join(accounting_dimensions) + ","

	transaction_currency_fields = ""
	if filters.get("add_values_in_transaction_currency"):
		transaction_currency_fields = (
			"debit_in_transaction_currency, credit_in_transaction_currency, transaction_currency,"
		)

	gl_entries = frappe.db.sql(
		f"""
		select
			name as gl_entry, posting_date, account, party_type, party,
			voucher_type, voucher_subtype, voucher_no, {dimension_fields}
			cost_center, project, {transaction_currency_fields}
			against_voucher_type, against_voucher, account_currency,
			against, is_opening, creation {select_fields}
		from `tabGL Entry`
		where company=%(company)s {get_conditions(filters)}
		{order_by_statement}
	""",
		filters,
		as_dict=1,
	)

	party_name_map = get_party_name_map()

	for gl_entry in gl_entries:
		if gl_entry.party_type and gl_entry.party:
			gl_entry.party_name = party_name_map.get(gl_entry.party_type, {}).get(gl_entry.party)

	enrich_gl_entries_with_hims_data(gl_entries)

	if filters.get("presentation_currency"):
		return convert_to_presentation_currency(gl_entries, currency_map, filters)
	else:
		return gl_entries


def get_conditions(filters):
	conditions = []

	matching_vouchers = get_matching_vouchers(filters)
	if matching_vouchers is not None:
		if matching_vouchers:
			filters["matching_hims_vouchers"] = matching_vouchers
			conditions.append("(voucher_no in %(matching_hims_vouchers)s or against_voucher in %(matching_hims_vouchers)s)")
		else:
			conditions.append("1=0")

	ignore_is_opening = frappe.db.get_single_value(
		"Accounts Settings", "ignore_is_opening_check_for_reporting"
	)

	if filters.get("account"):
		filters.account = get_accounts_with_children(filters.account)
		if filters.account:
			conditions.append("account in %(account)s")

	if filters.get("cost_center"):
		filters.cost_center = get_cost_centers_with_children(filters.cost_center)
		conditions.append("cost_center in %(cost_center)s")

	if filters.get("voucher_no"):
		conditions.append("voucher_no=%(voucher_no)s")

	if filters.get("against_voucher_no"):
		conditions.append("against_voucher=%(against_voucher_no)s")

	if filters.get("ignore_err"):
		err_journals = frappe.db.get_all(
			"Journal Entry",
			filters={
				"company": filters.get("company"),
				"docstatus": 1,
				"voucher_type": ("in", ["Exchange Rate Revaluation", "Exchange Gain Or Loss"]),
			},
			as_list=True,
		)
		if err_journals:
			filters.update({"voucher_no_not_in": [x[0] for x in err_journals]})

	if filters.get("ignore_cr_dr_notes"):
		system_generated_cr_dr_journals = frappe.db.get_all(
			"Journal Entry",
			filters={
				"company": filters.get("company"),
				"docstatus": 1,
				"voucher_type": ("in", ["Credit Note", "Debit Note"]),
				"is_system_generated": 1,
			},
			as_list=True,
		)
		if system_generated_cr_dr_journals:
			vouchers_to_ignore = (filters.get("voucher_no_not_in") or []) + [
				x[0] for x in system_generated_cr_dr_journals
			]
			filters.update({"voucher_no_not_in": vouchers_to_ignore})

	if filters.get("voucher_no_not_in"):
		conditions.append("voucher_no not in %(voucher_no_not_in)s")

	if filters.get("categorize_by") == "Categorize by Party" and not filters.get("party_type"):
		conditions.append("party_type in ('Customer', 'Supplier')")

	if filters.get("party_type"):
		conditions.append("party_type=%(party_type)s")

	if filters.get("party"):
		conditions.append("party in %(party)s")

	if not (
		filters.get("account")
		or filters.get("party")
		or filters.get("patient")
		or filters.get("uhid")
		or filters.get("bill_no")
		or filters.get("bill_id")
		or filters.get("categorize_by") in ["Categorize by Account", "Categorize by Party"]
	):
		if not ignore_is_opening:
			conditions.append("(posting_date >=%(from_date)s or is_opening = 'Yes')")
		else:
			conditions.append("posting_date >=%(from_date)s")

	if not ignore_is_opening:
		conditions.append("(posting_date <=%(to_date)s or is_opening = 'Yes')")
	else:
		conditions.append("posting_date <=%(to_date)s")

	if filters.get("project"):
		conditions.append("project in %(project)s")

	if filters.get("include_default_book_entries"):
		if filters.get("finance_book"):
			if filters.get("company_fb") and cstr(filters.get("finance_book")) != cstr(
				filters.get("company_fb")
			):
				frappe.throw(
					_("To use a different finance book, please uncheck 'Include Default FB Entries'")
				)
			else:
				conditions.append("(finance_book in (%(finance_book)s, '') OR finance_book IS NULL)")
		else:
			conditions.append("(finance_book in (%(company_fb)s, '') OR finance_book IS NULL)")
	else:
		if filters.get("finance_book"):
			conditions.append("(finance_book in (%(finance_book)s, '') OR finance_book IS NULL)")
		else:
			conditions.append("(finance_book in ('') OR finance_book IS NULL)")

	if not filters.get("show_cancelled_entries"):
		conditions.append("is_cancelled = 0")

	from frappe.desk.reportview import build_match_conditions

	match_conditions = build_match_conditions("GL Entry")

	if match_conditions:
		conditions.append(match_conditions)

	accounting_dimensions = get_accounting_dimensions(as_list=False)

	if accounting_dimensions:
		for dimension in accounting_dimensions:
			# Ignore 'Finance Book' set up as dimension in below logic, as it is already handled in above section
			if not dimension.disabled and dimension.document_type != "Finance Book":
				if filters.get(dimension.fieldname):
					if frappe.get_cached_value("DocType", dimension.document_type, "is_tree"):
						filters[dimension.fieldname] = get_dimension_with_children(
							dimension.document_type, filters.get(dimension.fieldname)
						)
						conditions.append(f"{dimension.fieldname} in %({dimension.fieldname})s")
					else:
						conditions.append(f"{dimension.fieldname} in %({dimension.fieldname})s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_party_name_map():
	party_map = {}

	customers = frappe.get_all("Customer", fields=["name", "customer_name"])
	party_map["Customer"] = {c.name: c.customer_name for c in customers}

	suppliers = frappe.get_all("Supplier", fields=["name", "supplier_name"])
	party_map["Supplier"] = {s.name: s.supplier_name for s in suppliers}

	employees = frappe.get_all("Employee", fields=["name", "employee_name"])
	party_map["Employee"] = {e.name: e.employee_name for e in employees}
	return party_map


def get_accounts_with_children(accounts):
	if not isinstance(accounts, list):
		accounts = [d.strip() for d in accounts.strip().split(",") if d]

	if not accounts:
		return

	doctype = frappe.qb.DocType("Account")
	accounts_data = (
		frappe.qb.from_(doctype)
		.select(doctype.lft, doctype.rgt)
		.where(doctype.name.isin(accounts))
		.run(as_dict=True)
	)

	conditions = []
	for account in accounts_data:
		conditions.append((doctype.lft >= account.lft) & (doctype.rgt <= account.rgt))

	return frappe.qb.from_(doctype).select(doctype.name).where(Criterion.any(conditions)).run(pluck=True)


def set_bill_no(gl_entries):
	inv_details = get_supplier_invoice_details()
	for gl in gl_entries:
		gl["bill_no"] = inv_details.get(gl.get("against_voucher"), "")


def get_data_with_opening_closing(filters, account_details, accounting_dimensions, gl_entries):
	data = []
	totals_dict = get_totals_dict()

	set_bill_no(gl_entries)

	gle_map = initialize_gle_map(gl_entries, filters, totals_dict)

	totals, entries = get_accountwise_gle(filters, accounting_dimensions, gl_entries, gle_map, totals_dict)

	# Opening for filtered account
	data.append(totals.opening)

	if filters.get("categorize_by") != "Categorize by Voucher (Consolidated)":
		for _acc, acc_dict in gle_map.items():
			# acc
			if acc_dict.entries:
				# opening
				data.append({"debit_in_transaction_currency": None, "credit_in_transaction_currency": None})
				if (not filters.get("categorize_by") and not filters.get("voucher_no")) or (
					filters.get("categorize_by") and filters.get("categorize_by") != "Categorize by Voucher"
				):
					data.append(acc_dict.totals.opening)

				data += acc_dict.entries

				# totals
				if filters.get("categorize_by") or not filters.voucher_no:
					data.append(acc_dict.totals.total)

				# closing
				if (not filters.get("categorize_by") and not filters.get("voucher_no")) or (
					filters.get("categorize_by") and filters.get("categorize_by") != "Categorize by Voucher"
				):
					data.append(acc_dict.totals.closing)

		data.append({"debit_in_transaction_currency": None, "credit_in_transaction_currency": None})
	else:
		data += entries

	# totals
	data.append(totals.total)

	# closing
	data.append(totals.closing)

	return data


def get_totals_dict():
	def _get_debit_credit_dict(label):
		return _dict(
			account=f"'{label}'",
			debit=0.0,
			credit=0.0,
			debit_in_account_currency=0.0,
			credit_in_account_currency=0.0,
			debit_in_transaction_currency=None,
			credit_in_transaction_currency=None,
		)

	return _dict(
		opening=_get_debit_credit_dict(_("Opening")),
		total=_get_debit_credit_dict(_("Total")),
		closing=_get_debit_credit_dict(_("Closing (Opening + Total)")),
	)


def group_by_field(group_by):
	if group_by == "Categorize by Party":
		return "party"
	elif group_by in ["Categorize by Voucher (Consolidated)", "Categorize by Account"]:
		return "account"
	else:
		return "voucher_no"


def initialize_gle_map(gl_entries, filters, totals_dict):
	gle_map = OrderedDict()
	group_by = group_by_field(filters.get("categorize_by"))

	for gle in gl_entries:
		gle_map.setdefault(gle.get(group_by), _dict(totals=copy.deepcopy(totals_dict), entries=[]))
	return gle_map


def get_accountwise_gle(filters, accounting_dimensions, gl_entries, gle_map, totals):
	entries = []
	consolidated_gle = OrderedDict()
	group_by = group_by_field(filters.get("categorize_by"))
	group_by_voucher_consolidated = filters.get("categorize_by") == "Categorize by Voucher (Consolidated)"

	if filters.get("show_net_values_in_party_account"):
		account_type_map = get_account_type_map(filters.get("company"))

	immutable_ledger = frappe.db.get_single_value("Accounts Settings", "enable_immutable_ledger")

	def update_value_in_dict(data, key, gle, show_net_values=False):
		data[key].debit += gle.debit
		data[key].credit += gle.credit

		data[key].debit_in_account_currency += gle.debit_in_account_currency
		data[key].credit_in_account_currency += gle.credit_in_account_currency

		if filters.get("add_values_in_transaction_currency") and key not in ["opening", "closing", "total"]:
			data[key].debit_in_transaction_currency += gle.debit_in_transaction_currency
			data[key].credit_in_transaction_currency += gle.credit_in_transaction_currency

		if (
			filters.get("show_net_values_in_party_account")
			and account_type_map.get(data[key].account)
			in (
				"Receivable",
				"Payable",
			)
		) or show_net_values:
			net_value = data[key].debit - data[key].credit
			net_value_in_account_currency = (
				data[key].debit_in_account_currency - data[key].credit_in_account_currency
			)

			if net_value < 0:
				dr_or_cr = "credit"
				rev_dr_or_cr = "debit"
			else:
				dr_or_cr = "debit"
				rev_dr_or_cr = "credit"

			data[key][dr_or_cr] = abs(net_value)
			data[key][dr_or_cr + "_in_account_currency"] = abs(net_value_in_account_currency)
			data[key][rev_dr_or_cr] = 0
			data[key][rev_dr_or_cr + "_in_account_currency"] = 0

		if data[key].against_voucher and gle.against_voucher:
			data[key].against_voucher += ", " + gle.against_voucher

	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	show_opening_entries = filters.get("show_opening_entries")

	for gle in gl_entries:
		group_by_value = gle.get(group_by)
		gle.voucher_type = gle.voucher_type

		if gle.posting_date < from_date or (cstr(gle.is_opening) == "Yes" and not show_opening_entries):
			if not group_by_voucher_consolidated:
				update_value_in_dict(gle_map[group_by_value].totals, "opening", gle, True)
				update_value_in_dict(gle_map[group_by_value].totals, "closing", gle, True)

			update_value_in_dict(totals, "opening", gle, True)
			update_value_in_dict(totals, "closing", gle, True)

		elif gle.posting_date <= to_date or (cstr(gle.is_opening) == "Yes" and show_opening_entries):
			if not group_by_voucher_consolidated:
				update_value_in_dict(gle_map[group_by_value].totals, "total", gle)
				update_value_in_dict(gle_map[group_by_value].totals, "closing", gle)
				update_value_in_dict(totals, "total", gle)
				update_value_in_dict(totals, "closing", gle)

				gle_map[group_by_value].entries.append(gle)

			elif group_by_voucher_consolidated:
				keylist = [
					gle.get("posting_date"),
					gle.get("voucher_type"),
					gle.get("voucher_no"),
					gle.get("account"),
					gle.get("party_type"),
					gle.get("party"),
				]

				if immutable_ledger:
					keylist.append(gle.get("creation"))

				if filters.get("include_dimensions"):
					for dim in accounting_dimensions:
						keylist.append(gle.get(dim))
					keylist.append(gle.get("cost_center"))
					keylist.append(gle.get("project"))

				key = tuple(keylist)
				if key not in consolidated_gle:
					consolidated_gle.setdefault(key, gle)
				else:
					update_value_in_dict(consolidated_gle, key, gle)

		if filters.get("include_dimensions"):
			dimensions = [*accounting_dimensions, "cost_center", "project"]

			for dimension in dimensions:
				if val := gle.get(dimension):
					gle[dimension] = _(val)

	for value in consolidated_gle.values():
		update_value_in_dict(totals, "total", value)
		update_value_in_dict(totals, "closing", value)
		entries.append(value)

	return totals, entries


def get_account_type_map(company):
	account_type_map = frappe._dict(
		frappe.get_all("Account", fields=["name", "account_type"], filters={"company": company}, as_list=1)
	)

	return account_type_map


def get_result_as_list(data, filters):
	balance = 0

	for d in data:
		if not d.get("posting_date"):
			balance = 0

		balance = get_balance(d, balance, "debit", "credit")

		d["balance"] = balance

		d["account_currency"] = filters.account_currency

		d["presentation_currency"] = filters.presentation_currency

	return data


def get_supplier_invoice_details():
	inv_details = {}
	for d in frappe.db.sql(
		""" select name, bill_no from `tabPurchase Invoice`
		where docstatus = 1 and bill_no is not null and bill_no != '' """,
		as_dict=1,
	):
		inv_details[d.name] = d.bill_no

	return inv_details


def get_balance(row, balance, debit_field, credit_field):
	balance += row.get(debit_field, 0) - row.get(credit_field, 0)

	return balance


def get_columns(filters):
	if filters.get("presentation_currency"):
		currency = filters["presentation_currency"]
	else:
		company = filters.get("company") or get_default_company()
		filters["presentation_currency"] = currency = get_company_currency(company)

	company_currency = get_company_currency(filters.get("company") or get_default_company())

	if (
		filters.get("show_amount_in_company_currency")
		and filters["presentation_currency"] != company_currency
	):
		frappe.throw(
			_(
				f'Presentation Currency cannot be {frappe.bold(filters["presentation_currency"])} , When {frappe.bold("Show Credit / Debit in Company Currency")} is enabled.'
			)
		)

	columns = [
		{
			"label": _("GL Entry"),
			"fieldname": "gl_entry",
			"fieldtype": "Link",
			"options": "GL Entry",
			"hidden": 1,
		},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{
			"label": _("Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 180,
		},
		{
			"label": _("Debit ({0})").format(currency),
			"fieldname": "debit",
			"fieldtype": "Currency",
			"options": "presentation_currency",
			"width": 130,
		},
		{
			"label": _("Credit ({0})").format(currency),
			"fieldname": "credit",
			"fieldtype": "Currency",
			"options": "presentation_currency",
			"width": 130,
		},
		{
			"label": _("Balance ({0})").format(currency),
			"fieldname": "balance",
			"fieldtype": "Currency",
			"options": "presentation_currency",
			"width": 130,
		},
	]

	if filters.get("add_values_in_transaction_currency"):
		columns += [
			{
				"label": _("Debit (Transaction)"),
				"fieldname": "debit_in_transaction_currency",
				"fieldtype": "Currency",
				"width": 130,
				"options": "transaction_currency",
			},
			{
				"label": _("Credit (Transaction)"),
				"fieldname": "credit_in_transaction_currency",
				"fieldtype": "Currency",
				"width": 130,
				"options": "transaction_currency",
			},
			{
				"label": "Transaction Currency",
				"fieldname": "transaction_currency",
				"fieldtype": "Link",
				"options": "Currency",
				"width": 70,
			},
		]

	columns += [
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "width": 120},
		{
			"label": _("Voucher Subtype"),
			"fieldname": "voucher_subtype",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 180,
		},
		{"label": _("Patient"), "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 110},
		{"label": _("UHID"), "fieldname": "custom_uhid", "fieldtype": "Data", "width": 110},
		{"label": _("Bill No"), "fieldname": "custom_bill_no", "fieldtype": "Data", "width": 130},
		{"label": _("Bill ID"), "fieldname": "custom_bill_id", "fieldtype": "Data", "width": 150},
		{"label": _("Against Account"), "fieldname": "against", "width": 120},
		{"label": _("Party Type"), "fieldname": "party_type", "width": 100},
		{"label": _("Party"), "fieldname": "party", "width": 100},
	]

	supplier_master_name = frappe.db.get_single_value("Buying Settings", "supp_master_name")
	customer_master_name = frappe.db.get_single_value("Selling Settings", "cust_master_name")

	if supplier_master_name != "Supplier Name" or customer_master_name != "Customer Name":
		columns.append(
			{
				"label": _("Party Name"),
				"fieldname": "party_name",
				"fieldtype": "Data",
				"width": 150,
			}
		)

	if filters.get("include_dimensions"):
		columns.append({"label": _("Project"), "options": "Project", "fieldname": "project", "width": 100})

		for dim in get_accounting_dimensions(as_list=False):
			columns.append(
				{"label": _(dim.label), "options": dim.label, "fieldname": dim.fieldname, "width": 100}
			)
		columns.append(
			{"label": _("Cost Center"), "options": "Cost Center", "fieldname": "cost_center", "width": 100}
		)

	columns.extend(
		[
			{"label": _("Against Voucher Type"), "fieldname": "against_voucher_type", "width": 100},
			{
				"label": _("Against Voucher"),
				"fieldname": "against_voucher",
				"fieldtype": "Dynamic Link",
				"options": "against_voucher_type",
				"width": 100,
			},
			{"label": _("Supplier Invoice No"), "fieldname": "bill_no", "fieldtype": "Data", "width": 100},
		]
	)

	if filters.get("show_remarks"):
		columns.extend([{"label": _("Remarks"), "fieldname": "remarks", "width": 400}])

	return columns
