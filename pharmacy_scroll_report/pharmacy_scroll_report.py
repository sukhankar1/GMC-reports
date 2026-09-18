# Copyright (c) 2024, Quantbit Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	view_type = filters.get("view_type", "Summary")
	if view_type == "Detail":
		columns = get_detail_columns()
		data = get_detail_data(filters)
	else:
		columns = get_summary_columns()
		data = get_summary_data(filters)

	return columns, data


def get_summary_columns():
	return [
		{"label": _("User Name"), "fieldname": "user_name", "fieldtype": "Data", "width": 200},
		{"label": _("Voucher Name"), "fieldname": "voucher_name", "fieldtype": "Data", "width": 140},
		{"label": _("Cash"), "fieldname": "cash", "fieldtype": "Currency", "width": 120},
		{"label": _("UPI Hospital"), "fieldname": "upi_hospital", "fieldtype": "Currency", "width": 120},
		{"label": _("Credit Sale"), "fieldname": "credit_sale", "fieldtype": "Currency", "width": 120},
		{"label": _("DebitCard"), "fieldname": "debit_card", "fieldtype": "Currency", "width": 120},
		{"label": _("CreditCard"), "fieldname": "credit_card", "fieldtype": "Currency", "width": 120},
		{"label": _("Total Collection"), "fieldname": "total_collection", "fieldtype": "Currency", "width": 130},
		{"label": _("Total"), "fieldname": "total", "fieldtype": "Currency", "width": 120}
	]


def get_detail_columns():
	return [
		{"label": _("Bill No."), "fieldname": "bill_no", "fieldtype": "Data", "width": 160},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 220},
		{"label": _("Cash"), "fieldname": "cash", "fieldtype": "Currency", "width": 110},
		{"label": _("UPI Hospital"), "fieldname": "upi_hospital", "fieldtype": "Currency", "width": 110},
		{"label": _("Credit Sale"), "fieldname": "credit_sale", "fieldtype": "Currency", "width": 110},
		{"label": _("DebitCard"), "fieldname": "debit_card", "fieldtype": "Currency", "width": 110},
		{"label": _("CreditCard"), "fieldname": "credit_card", "fieldtype": "Currency", "width": 110},
		{"label": _("Total Collection"), "fieldname": "total_collection", "fieldtype": "Currency", "width": 120},
		{"label": _("Total"), "fieldname": "total", "fieldtype": "Currency", "width": 120}
	]


def get_conditions(filters):
	conditions = ["si.docstatus = 1"]
	values = {}

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("department"):
		conditions.append("(sb.department = %(department)s OR si.custom_department = %(department)s)")
		values["department"] = filters.get("department")

	if filters.get("users"):
		users = filters.get("users")
		if isinstance(users, str):
			try:
				users = json.loads(users)
			except Exception:
				users = [u.strip() for u in users.split(",") if u.strip()]
		if isinstance(users, (list, tuple)) and users:
			conditions.append("si.owner IN %(users)s")
			values["users"] = tuple(users)

	return " AND ".join(conditions), values


def fetch_raw_invoices(filters):
	where_clause, values = get_conditions(filters)
	query = f"""
		SELECT 
			si.name AS invoice_name,
			si.owner,
			COALESCE(u.full_name, si.owner) AS user_full_name,
			si.is_return,
			COALESCE(sb.consolidated_invoice, si.name) AS bill_no,
			COALESCE(si.custom_patient_name, sb.custom_patient_name, p.full_name, p.first_name, '') AS patient_name,
			si.grand_total,
			sip.mode_of_payment,
			sip.amount AS payment_amount
		FROM `tabSales Invoice` si
		LEFT JOIN `tabSales Invoice Payment` sip ON sip.parent = si.name
		LEFT JOIN `tabSale Bill` sb ON (sb.consolidated_invoice = si.name OR sb.name = si.name)
		LEFT JOIN `tabPatient` p ON p.name = si.patient
		LEFT JOIN `tabUser` u ON u.name = si.owner
		WHERE {where_clause}
		ORDER BY si.owner ASC, si.is_return ASC, si.posting_date ASC, si.name ASC
	"""
	return frappe.db.sql(query, values, as_dict=True)


def get_summary_data(filters):
	invoices = fetch_raw_invoices(filters)
	
	# Group by user -> voucher_type ("Sale" / "Sale Return")
	user_summary = {}

	for row in invoices:
		user = row.user_full_name or row.owner
		vtype = "Sale Return" if row.is_return else "Sale"

		if user not in user_summary:
			user_summary[user] = {
				"Sale": {"cash": 0.0, "upi_hospital": 0.0, "credit_sale": 0.0, "debit_card": 0.0, "credit_card": 0.0, "total": 0.0, "has_data": False},
				"Sale Return": {"cash": 0.0, "upi_hospital": 0.0, "credit_sale": 0.0, "debit_card": 0.0, "credit_card": 0.0, "total": 0.0, "has_data": False}
			}

		mop = (row.mode_of_payment or "").strip()
		amt = flt(row.payment_amount) if row.payment_amount is not None else flt(row.grand_total)

		# If return, amounts may be negative or positive depending on entry
		target = user_summary[user][vtype]
		target["has_data"] = True

		if mop == "Cash":
			target["cash"] += amt
		elif mop in ("Online", "UPI", "UPI Hospital"):
			target["upi_hospital"] += amt
		elif mop in ("Bank Draft", "Cheque", "Debit Card", "DebitCard"):
			target["debit_card"] += amt
		elif mop in ("Credit Card", "CreditCard"):
			target["credit_card"] += amt
		else:
			target["credit_sale"] += amt

		target["total"] += amt

	data = []
	grand_totals = {
		"cash": 0.0, "upi_hospital": 0.0, "credit_sale": 0.0,
		"debit_card": 0.0, "credit_card": 0.0, "total_collection": 0.0, "total": 0.0
	}

	for user, vtypes in user_summary.items():
		user_subtotal = {
			"cash": 0.0, "upi_hospital": 0.0, "credit_sale": 0.0,
			"debit_card": 0.0, "credit_card": 0.0, "total_collection": 0.0, "total": 0.0
		}

		user_has_rows = False
		for vtype in ("Sale", "Sale Return"):
			item = vtypes[vtype]
			if not item["has_data"]:
				continue

			user_has_rows = True
			total_coll = item["cash"] + item["upi_hospital"] + item["debit_card"] + item["credit_card"]
			row_dict = {
				"user_name": user if not user_subtotal["total"] and not user_subtotal["cash"] else "",
				"voucher_name": vtype,
				"cash": item["cash"] or "",
				"upi_hospital": item["upi_hospital"] or "",
				"credit_sale": item["credit_sale"] or "",
				"debit_card": item["debit_card"] or "",
				"credit_card": item["credit_card"] or "",
				"total_collection": total_coll or "",
				"total": item["total"] or ""
			}
			data.append(row_dict)

			for k in ("cash", "upi_hospital", "credit_sale", "debit_card", "credit_card", "total"):
				user_subtotal[k] += item[k]
				grand_totals[k] += item[k]
			user_subtotal["total_collection"] += total_coll
			grand_totals["total_collection"] += total_coll

		if user_has_rows:
			subtotal_row = {
				"user_name": "",
				"voucher_name": "<b>Total :</b>",
				"cash": user_subtotal["cash"] or "",
				"upi_hospital": user_subtotal["upi_hospital"] or "",
				"credit_sale": user_subtotal["credit_sale"] or "",
				"debit_card": user_subtotal["debit_card"] or "",
				"credit_card": user_subtotal["credit_card"] or "",
				"total_collection": user_subtotal["total_collection"] or "",
				"total": user_subtotal["total"] or ""
			}
			data.append(subtotal_row)
			data.append({})  # spacing row

	if data:
		grand_total_row = {
			"user_name": "<b>Grand Total</b>",
			"voucher_name": "",
			"cash": grand_totals["cash"] or "",
			"upi_hospital": grand_totals["upi_hospital"] or "",
			"credit_sale": grand_totals["credit_sale"] or "",
			"debit_card": grand_totals["debit_card"] or "",
			"credit_card": grand_totals["credit_card"] or "",
			"total_collection": grand_totals["total_collection"] or "",
			"total": grand_totals["total"] or ""
		}
		data.append(grand_total_row)

	return data


def get_detail_data(filters):
	raw_rows = fetch_raw_invoices(filters)

	# Group by user -> voucher_type -> invoice_name
	user_grouped = {}
	for r in raw_rows:
		user = r.user_full_name or r.owner
		vtype = "Sale Return" if r.is_return else "Sale"
		inv = r.invoice_name

		if user not in user_grouped:
			user_grouped[user] = {}
		if vtype not in user_grouped[user]:
			user_grouped[user][vtype] = {}
		if inv not in user_grouped[user][vtype]:
			user_grouped[user][vtype][inv] = {
				"bill_no": r.bill_no or inv,
				"patient_name": r.patient_name,
				"cash": 0.0,
				"upi_hospital": 0.0,
				"credit_sale": 0.0,
				"debit_card": 0.0,
				"credit_card": 0.0,
				"total_collection": 0.0,
				"total": 0.0
			}

		mop = (r.mode_of_payment or "").strip()
		amt = flt(r.payment_amount) if r.payment_amount is not None else flt(r.grand_total)

		target = user_grouped[user][vtype][inv]
		if mop == "Cash":
			target["cash"] += amt
		elif mop in ("Online", "UPI", "UPI Hospital"):
			target["upi_hospital"] += amt
		elif mop in ("Bank Draft", "Cheque", "Debit Card", "DebitCard"):
			target["debit_card"] += amt
		elif mop in ("Credit Card", "CreditCard"):
			target["credit_card"] += amt
		else:
			target["credit_sale"] += amt

		target["total"] += amt

	data = []
	grand_totals = {
		"cash": 0.0, "upi_hospital": 0.0, "credit_sale": 0.0,
		"debit_card": 0.0, "credit_card": 0.0, "total_collection": 0.0, "total": 0.0
	}

	for user, vtypes in user_grouped.items():
		user_total_collection = 0.0
		user_grand_total = 0.0

		for vtype, inv_map in vtypes.items():
			# Header row: User Name & Voucher Name
			data.append({
				"bill_no": f"<b>User Name : {user}</b>",
				"patient_name": ""
			})
			data.append({
				"bill_no": f"<b>Voucher Name : {vtype}</b>",
				"patient_name": ""
			})

			sub_totals = {
				"cash": 0.0, "upi_hospital": 0.0, "credit_sale": 0.0,
				"debit_card": 0.0, "credit_card": 0.0, "total_collection": 0.0, "total": 0.0
			}

			for inv_id, inv_data in inv_map.items():
				inv_data["total_collection"] = inv_data["cash"] + inv_data["upi_hospital"] + inv_data["debit_card"] + inv_data["credit_card"]
				
				row_item = {
					"bill_no": inv_data["bill_no"],
					"patient_name": inv_data["patient_name"],
					"cash": inv_data["cash"] or "",
					"upi_hospital": inv_data["upi_hospital"] or "",
					"credit_sale": inv_data["credit_sale"] or "",
					"debit_card": inv_data["debit_card"] or "",
					"credit_card": inv_data["credit_card"] or "",
					"total_collection": inv_data["total_collection"] or "",
					"total": inv_data["total"] or ""
				}
				data.append(row_item)

				for k in ("cash", "upi_hospital", "credit_sale", "debit_card", "credit_card", "total"):
					sub_totals[k] += inv_data[k]
					grand_totals[k] += inv_data[k]
				sub_totals["total_collection"] += inv_data["total_collection"]
				grand_totals["total_collection"] += inv_data["total_collection"]

			# Sub Total row
			sub_total_row = {
				"bill_no": "<b>Sub Total :</b>",
				"patient_name": "",
				"cash": sub_totals["cash"] or "",
				"upi_hospital": sub_totals["upi_hospital"] or "",
				"credit_sale": sub_totals["credit_sale"] or "",
				"debit_card": sub_totals["debit_card"] or "",
				"credit_card": sub_totals["credit_card"] or "",
				"total_collection": sub_totals["total_collection"] or "",
				"total": sub_totals["total"] or ""
			}
			data.append(sub_total_row)

			user_total_collection += sub_totals["total_collection"]
			user_grand_total += sub_totals["total"]

		# Total Collection Of User row
		user_tot_row = {
			"bill_no": f"<b>Total Collection Of {user} :</b>",
			"patient_name": "",
			"cash": "",
			"upi_hospital": "",
			"credit_sale": "",
			"debit_card": "",
			"credit_card": "",
			"total_collection": user_total_collection or "",
			"total": user_grand_total or ""
		}
		data.append(user_tot_row)
		data.append({})  # Spacing row

	if data:
		grand_total_row = {
			"bill_no": "<b>Grand Total</b>",
			"patient_name": "",
			"cash": grand_totals["cash"] or "",
			"upi_hospital": grand_totals["upi_hospital"] or "",
			"credit_sale": grand_totals["credit_sale"] or "",
			"debit_card": grand_totals["debit_card"] or "",
			"credit_card": grand_totals["credit_card"] or "",
			"total_collection": grand_totals["total_collection"] or "",
			"total": grand_totals["total"] or ""
		}
		data.append(grand_total_row)

	return data


def flt(val):
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return 0.0
