# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": "Particulars",
			"fieldname": "particulars",
			"fieldtype": "Data",
			"width": 320
		},
		{
			"label": "Sale Amount",
			"fieldname": "sale_amount",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"label": "Return Amount",
			"fieldname": "return_amount",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"label": "Net Amount",
			"fieldname": "net_amount",
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"label": "Discount",
			"fieldname": "discount",
			"fieldtype": "Currency",
			"width": 120
		}
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

	where_clause = f"AND {' AND '.join(conditions)}" if conditions else ""

	# Fetch sales and returns grouped by payment type and department
	query = f"""
		SELECT
			CASE
				WHEN sip.mode_of_payment IN ('Card', 'Credit Card', 'Debit Card') THEN 'Card Sales'
				WHEN sip.mode_of_payment = 'Cash' THEN 'Cash Sales'
				ELSE 'Credit Sales'
			END AS pay_category,
			COALESCE(NULLIF(sb.department, ''), 'PHARMACY') AS department,
			SUM(CASE WHEN IFNULL(si.is_return, 0) = 0 THEN si.grand_total ELSE 0 END) AS sale_amount,
			SUM(CASE WHEN si.is_return = 1 THEN ABS(si.grand_total) ELSE 0 END) AS return_amount,
			SUM(IFNULL(si.discount_amount, 0)) AS discount
		FROM
			`tabSales Invoice` si
		LEFT JOIN
			`tabSale Bill` sb ON sb.consolidated_invoice = si.name
		LEFT JOIN (
			SELECT parent, mode_of_payment
			FROM `tabSales Invoice Payment`
			GROUP BY parent
		) sip ON sip.parent = si.name
		WHERE
			si.docstatus = 1 {where_clause}
		GROUP BY
			pay_category, department
		ORDER BY
			pay_category, department
	"""

	rows = frappe.db.sql(query, params, as_dict=True)

	categories = ["Card Sales", "Cash Sales", "Credit Sales"]
	cat_data = {c: [] for c in categories}

	for r in rows:
		pcat = r.pay_category
		if pcat not in cat_data:
			pcat = "Credit Sales"
		cat_data[pcat].append(r)

	data = []
	grand_total_sale = 0.0
	grand_total_return = 0.0
	grand_total_net = 0.0
	grand_total_discount = 0.0

	for cat in categories:
		items = cat_data.get(cat, [])
		if not items:
			continue

		# Category Header
		data.append({
			"particulars": f"<b>{cat}</b>",
			"sale_amount": None,
			"return_amount": None,
			"net_amount": None,
			"discount": None
		})

		sub_sale = 0.0
		sub_return = 0.0
		sub_net = 0.0
		sub_discount = 0.0

		for it in items:
			s_amt = flt(it.sale_amount)
			r_amt = flt(it.return_amount)
			n_amt = s_amt - r_amt
			d_amt = flt(it.discount)

			sub_sale += s_amt
			sub_return += r_amt
			sub_net += n_amt
			sub_discount += d_amt

			dept_label = it.department
			if cat == "Credit Sales":
				line_title = f"IP Credit Sales-{dept_label}"
			elif cat == "Card Sales":
				line_title = f"Card Sales-{dept_label}"
			else:
				line_title = f"Cash Sales-{dept_label}"

			data.append({
				"particulars": line_title,
				"sale_amount": s_amt,
				"return_amount": r_amt,
				"net_amount": n_amt,
				"discount": d_amt
			})

		grand_total_sale += sub_sale
		grand_total_return += sub_return
		grand_total_net += sub_net
		grand_total_discount += sub_discount

		# Net Subtotal Row
		net_label = f"Net {cat}"
		data.append({
			"particulars": f"<b>{net_label}</b>",
			"sale_amount": sub_sale,
			"return_amount": sub_return,
			"net_amount": sub_net,
			"discount": sub_discount
		})

		# Empty spacing row
		data.append({})

	if data:
		data.append({
			"particulars": "<b>Total Discount</b>",
			"sale_amount": None,
			"return_amount": None,
			"net_amount": None,
			"discount": grand_total_discount
		})
		data.append({
			"particulars": "<b>Total Sale</b>",
			"sale_amount": None,
			"return_amount": None,
			"net_amount": grand_total_net,
			"discount": None
		})

	return data