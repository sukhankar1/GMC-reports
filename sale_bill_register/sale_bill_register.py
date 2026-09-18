# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, cstr, strip_html

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"label": "Type", "fieldname": "patient_category", "fieldtype": "Data", "width": 120},
		{"label": "Bill Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 105},
		{"label": "Bill Type", "fieldname": "bill_type", "fieldtype": "Data", "width": 120},
		{"label": "Bill No.", "fieldname": "bill_no", "fieldtype": "Data", "width": 130},
		{"label": "Issue Date & Time", "fieldname": "issue_date_time", "fieldtype": "Datetime", "width": 150},
		{"label": "UHID", "fieldname": "uhid", "fieldtype": "Data", "width": 130},
		{"label": "Patient/ Customer Name", "fieldname": "patient_customer_name", "fieldtype": "Data", "width": 180},
		{"label": "GNHP No.", "fieldname": "gnhp_no", "fieldtype": "Data", "width": 120},
		{"label": "Visit Type", "fieldname": "visit_type", "fieldtype": "Data", "width": 110},
		{"label": "IPD Effect", "fieldname": "ipd_effect", "fieldtype": "Data", "width": 100},
		{"label": "Company Type", "fieldname": "company_type", "fieldtype": "Data", "width": 130},
		{"label": "Company Name", "fieldname": "company_name", "fieldtype": "Data", "width": 150},
		{"label": "Department Name", "fieldname": "department_name", "fieldtype": "Data", "width": 140},
		{"label": "Doctor", "fieldname": "doctor", "fieldtype": "Data", "width": 150},
		{"label": "Doctor Department", "fieldname": "doctor_department", "fieldtype": "Data", "width": 140},
		{"label": "User Name", "fieldname": "user_name", "fieldtype": "Data", "width": 140},
		{"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 130},
		{"label": "Subcategory", "fieldname": "subcategory", "fieldtype": "Data", "width": 130},
		{"label": "Admit Date", "fieldname": "admit_date", "fieldtype": "Date", "width": 105},
		{"label": "Discharge Date", "fieldname": "discharge_date", "fieldtype": "Date", "width": 105},
		{"label": "Is Consignment", "fieldname": "is_consignment", "fieldtype": "Data", "width": 110},
		{"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": "Material Description", "fieldname": "description", "fieldtype": "Data", "width": 180},
		{"label": "High Risk Medicine", "fieldname": "high_risk_medicine", "fieldtype": "Data", "width": 120},
		{"label": "Basic Rate", "fieldname": "basic_rate", "fieldtype": "Currency", "width": 110},
		{"label": "Payment Type", "fieldname": "payment_type_col", "fieldtype": "Data", "width": 120},
		{"label": "Paymode 1", "fieldname": "paymode_1", "fieldtype": "Data", "width": 110},
		{"label": "Paymode 2", "fieldname": "paymode_2", "fieldtype": "Data", "width": 110},
		{"label": "Quantity", "fieldname": "qty", "fieldtype": "Float", "width": 90},
		{"label": "EPR", "fieldname": "epr", "fieldtype": "Currency", "width": 100},
		{"label": "EPR Value", "fieldname": "epr_value", "fieldtype": "Currency", "width": 110},
		{"label": "MRP", "fieldname": "mrp", "fieldtype": "Currency", "width": 100},
		{"label": "MRP Value", "fieldname": "mrp_value", "fieldtype": "Currency", "width": 110},
		{"label": "Concession (%)", "fieldname": "concession_pct", "fieldtype": "Percent", "width": 110},
		{"label": "Concession Amt.", "fieldname": "concession_amt", "fieldtype": "Currency", "width": 120},
		{"label": "On Bill Conc. (%)", "fieldname": "on_bill_conc_pct", "fieldtype": "Percent", "width": 110},
		{"label": "On Bill Concession", "fieldname": "on_bill_concession", "fieldtype": "Currency", "width": 120},
		{"label": "Bill Value", "fieldname": "bill_value", "fieldtype": "Currency", "width": 110},
		{"label": "Taxable Amt.", "fieldname": "taxable_amt", "fieldtype": "Currency", "width": 110},
		{"label": "Net Total Amt.", "fieldname": "net_total_amt", "fieldtype": "Currency", "width": 120}
	]

def get_data(filters):
	if not filters:
		filters = {}

	conditions = []
	params = {}

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		params["from_date"] = filters.get("from_date")
	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		params["to_date"] = filters.get("to_date")
	if filters.get("department"):
		conditions.append("sb.department = %(department)s")
		params["department"] = filters.get("department")
	if filters.get("patient_name"):
		conditions.append("(p.full_name LIKE %(patient_name)s OR si.custom_patient_name LIKE %(patient_name)s)")
		params["patient_name"] = f"%{filters.get('patient_name')}%"
	if filters.get("item_name"):
		conditions.append("(i.item_name LIKE %(item_name)s OR sii.item_code LIKE %(item_name)s)")
		params["item_name"] = f"%{filters.get('item_name')}%"
	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		params["customer"] = filters.get("customer")
	if filters.get("schedule_type"):
		conditions.append("i.custom_schedule_type = %(schedule_type)s")
		params["schedule_type"] = filters.get("schedule_type")

	if filters.get("therapeutic_group"):
		conditions.append("""(
			i.custom_generic_name IN (SELECT gn.name FROM `tabGeneric Name` gn WHERE gn.generic_group = %(therapeutic_group)s)
			OR i.item_group = %(therapeutic_group)s
			OR i.custom_category = %(therapeutic_group)s
		)""")
		params["therapeutic_group"] = filters.get("therapeutic_group")

	if filters.get("therapeutic_sub_group"):
		conditions.append("""(
			i.custom_generic_name IN (SELECT gn.name FROM `tabGeneric Name` gn WHERE gn.generic_group = %(therapeutic_sub_group)s)
			OR i.item_group = %(therapeutic_sub_group)s
		)""")
		params["therapeutic_sub_group"] = filters.get("therapeutic_sub_group")

	if filters.get("ipd_opd_effect"):
		eff = filters.get("ipd_opd_effect")
		if eff == "IPD Effect":
			conditions.append("sb.custom_ipd_effect = 1")
		elif eff == "OPD Effect":
			conditions.append("(sb.custom_ipd_effect = 0 OR sb.custom_ipd_effect IS NULL)")

	if filters.get("payment_mode"):
		conditions.append("EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = %(payment_mode)s)")
		params["payment_mode"] = filters.get("payment_mode")

	if filters.get("payment_type"):
		ptype = filters.get("payment_type")
		if ptype == "Cash":
			conditions.append("EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash')")
		elif ptype == "Credit":
			conditions.append("(si.outstanding_amount > 0 OR NOT EXISTS(SELECT 1 FROM `tabSales Invoice Payment` sip WHERE sip.parent = si.name AND sip.mode_of_payment = 'Cash'))")

	if filters.get("concession_100"):
		conditions.append("si.additional_discount_percentage = 100")

	where_clause = f"AND {' AND '.join(conditions)}" if conditions else ""

	query = f"""
		SELECT
			p.patient_category,
			si.posting_date,
			'Sales Invoice' AS bill_type,
			COALESCE(NULLIF(sb.consolidated_invoice, ''), si.name) AS bill_no,
			si.creation AS issue_date_time,
			p.uhid,
			COALESCE(NULLIF(si.custom_patient_name, ''), p.full_name, si.customer) AS patient_customer_name,
			COALESCE(NULLIF(sb.visit_no, ''), sb.custom_visit_code, '') AS gnhp_no,
			COALESCE(NULLIF(sb.visit_type, ''), si.custom_visit_type, '') AS visit_type,
			CASE WHEN sb.custom_ipd_effect = 1 THEN 'Yes' ELSE 'No' END AS ipd_effect,
			cust.customer_group AS company_type,
			si.customer AS company_name,
			COALESCE(NULLIF(sb.department, ''), 'KAMALNAYAN BAJAJ PHARMACY') AS department_name,
			COALESCE(NULLIF(sb.custom_doctor_name, ''), p.consulting_doctor, '') AS doctor,
			COALESCE(NULLIF(sb.department, ''), '') AS doctor_department,
			si.owner AS user_name,
			i.custom_category AS category,
			i.item_group AS subcategory,
			NULL AS admit_date,
			NULL AS discharge_date,
			CASE WHEN i.custom_consignment_items = 1 THEN 'Yes' ELSE 'No' END AS is_consignment,
			sii.item_code,
			i.description,
			CASE WHEN i.custom_high_risk_drug = 1 THEN 'Yes' ELSE 'No' END AS high_risk_medicine,
			sii.rate AS basic_rate,
			sii.qty,
			sii.amount AS epr_value,
			i.custom_mrp AS mrp,
			sii.discount_percentage AS concession_pct,
			sii.discount_amount AS concession_amt,
			si.additional_discount_percentage AS on_bill_conc_pct,
			si.discount_amount AS on_bill_concession,
			sii.amount AS bill_value,
			sii.net_amount AS taxable_amt,
			si.grand_total AS net_total_amt,
			(
				SELECT GROUP_CONCAT(DISTINCT mode_of_payment SEPARATOR ', ')
				FROM `tabSales Invoice Payment`
				WHERE parent = si.name
			) AS all_paymodes
		FROM
			`tabSales Invoice` si
		INNER JOIN
			`tabSales Invoice Item` sii ON sii.parent = si.name
		LEFT JOIN
			`tabPatient` p ON p.name = si.patient
		LEFT JOIN
			`tabItem` i ON i.name = sii.item_code
		LEFT JOIN
			`tabCustomer` cust ON cust.name = si.customer
		LEFT JOIN
			`tabSale Bill` sb ON sb.consolidated_invoice = si.name
		WHERE
			si.docstatus = 1
			{where_clause}
		ORDER BY
			si.posting_date DESC, si.name DESC
	"""

	rows = frappe.db.sql(query, params, as_dict=True)

	data = []
	for r in rows:
		modes = (r.all_paymodes or "").split(", ")
		pm1 = modes[0] if len(modes) > 0 and modes[0] else ""
		pm2 = modes[1] if len(modes) > 1 and modes[1] else ""

		q = flt(r.qty)
		rate = flt(r.basic_rate)
		mrp = flt(r.mrp) or rate

		desc = strip_html(r.description or "")
		if desc:
			desc = desc.replace("\n", " ").strip()

		data.append({
			"patient_category": r.patient_category or "",
			"posting_date": r.posting_date,
			"bill_type": r.bill_type,
			"bill_no": r.bill_no,
			"issue_date_time": r.issue_date_time,
			"uhid": r.uhid or "",
			"patient_customer_name": r.patient_customer_name or "",
			"gnhp_no": r.gnhp_no or "",
			"visit_type": r.visit_type or "",
			"ipd_effect": r.ipd_effect or "No",
			"company_type": r.company_type or "",
			"company_name": r.company_name or "",
			"department_name": r.department_name or "",
			"doctor": r.doctor or "",
			"doctor_department": r.doctor_department or "",
			"user_name": r.user_name or "",
			"category": r.category or "",
			"subcategory": r.subcategory or "",
			"admit_date": r.admit_date,
			"discharge_date": r.discharge_date,
			"is_consignment": r.is_consignment or "No",
			"item_code": r.item_code or "",
			"description": desc,
			"high_risk_medicine": r.high_risk_medicine or "No",
			"basic_rate": rate,
			"payment_type_col": r.all_paymodes or "Credit",
			"paymode_1": pm1,
			"paymode_2": pm2,
			"qty": q,
			"epr": rate,
			"epr_value": flt(r.epr_value) or (rate * q),
			"mrp": mrp,
			"mrp_value": mrp * q,
			"concession_pct": flt(r.concession_pct),
			"concession_amt": flt(r.concession_amt),
			"on_bill_conc_pct": flt(r.on_bill_conc_pct),
			"on_bill_concession": flt(r.on_bill_concession),
			"bill_value": flt(r.bill_value),
			"taxable_amt": flt(r.taxable_amt) or flt(r.bill_value),
			"net_total_amt": flt(r.net_total_amt)
		})

	return data
