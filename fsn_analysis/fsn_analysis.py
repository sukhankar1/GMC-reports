# Copyright (c) 2026, Quantbit HIMS Integration and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.utils import add_months, date_diff, flt, getdate, today


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Category Name"),
			"fieldname": "category_name",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Sub Category Name"),
			"fieldname": "sub_category_name",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Opening Qty"),
			"fieldname": "opening_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Received Qty"),
			"fieldname": "received_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Return Qty"),
			"fieldname": "return_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Adjusted Qty"),
			"fieldname": "adjusted_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Issue Qty"),
			"fieldname": "issue_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Close Qty"),
			"fieldname": "close_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Holding stock till date (Days)"),
			"fieldname": "holding_stock_days",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": _("Average Stay (Days)"),
			"fieldname": "avg_stay_days",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Cumulative Avg. Stay"),
			"fieldname": "cumulative_avg_stay",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Avg. Stay (%)"),
			"fieldname": "avg_stay_pct",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Status (Avg. Stay)"),
			"fieldname": "status_avg_stay",
			"fieldtype": "Data",
			"width": 120,
		},
	]


def get_data(filters):
	from_date = filters.get("from_date") or add_months(today(), -1)
	to_date = filters.get("to_date") or today()

	dept_warehouse = None
	if filters.get("department"):
		dept_warehouse = frappe.db.get_value(
			"Department", filters.get("department"), "custom_stock_location"
		)

	sle_warehouse_cond = ""
	sle_params = {
		"from_date": from_date,
		"to_date": to_date,
	}

	if dept_warehouse:
		sle_warehouse_cond = "AND sle.warehouse = %(warehouse)s"
		sle_params["warehouse"] = dept_warehouse
	elif filters.get("company"):
		sle_warehouse_cond = "AND sle.company = %(company)s"
		sle_params["company"] = filters.get("company")

	query = f"""
		SELECT 
			i.name AS item_code,
			i.item_name,
			COALESCE(NULLIF(i.custom_category, ''), 'PHARMACY MEDICINE') AS category_name,
			COALESCE(NULLIF(i.item_group, ''), 'Consumable Medical') AS sub_category_name,
			COALESCE(SUM(CASE WHEN sle.posting_date < %(from_date)s THEN sle.actual_qty ELSE 0 END), 0.0) AS opening_qty,
			COALESCE(SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty > 0 AND sle.voucher_type = 'Purchase Receipt' THEN sle.actual_qty ELSE 0 END), 0.0) AS received_qty,
			COALESCE(SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty < 0 AND sle.voucher_type = 'Purchase Receipt' THEN ABS(sle.actual_qty) ELSE 0 END), 0.0) AS return_qty,
			COALESCE(SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.voucher_type = 'Stock Reconciliation' THEN sle.actual_qty ELSE 0 END), 0.0) AS adjusted_qty,
			COALESCE(SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty < 0 AND sle.voucher_type != 'Purchase Receipt' THEN ABS(sle.actual_qty) ELSE 0 END), 0.0) AS issue_qty,
			COALESCE(SUM(CASE WHEN sle.posting_date <= %(to_date)s THEN sle.actual_qty ELSE 0 END), 0.0) AS close_qty
		FROM 
			`tabItem` i
		LEFT JOIN 
			`tabStock Ledger Entry` sle ON sle.item_code = i.name AND sle.docstatus = 1 AND sle.is_cancelled = 0 {sle_warehouse_cond}
		WHERE 
			i.is_stock_item = 1 AND i.disabled = 0
		GROUP BY 
			i.name
		HAVING 
			(opening_qty != 0 OR received_qty != 0 OR issue_qty != 0 OR close_qty != 0)
		ORDER BY 
			i.item_name ASC
	"""

	rows = frappe.db.sql(query, sle_params, as_dict=True)
	if not rows:
		return []

	# Initial calculations
	calculated_rows = []
	for r in rows:
		close_qty = flt(r.close_qty, 2)
		issue_qty = flt(r.issue_qty, 2)
		opening_qty = flt(r.opening_qty, 2)
		received_qty = flt(r.received_qty, 2)
		return_qty = flt(r.return_qty, 2)
		adjusted_qty = flt(r.adjusted_qty, 2)

		holding_days = int(round(close_qty)) if close_qty > 0 else 0
		avg_stay = 1.00

		if issue_qty == 0:
			status = "Non Moving"
		elif issue_qty > (opening_qty + received_qty) * 0.5 or issue_qty >= 50:
			status = "Fast Moving"
		else:
			status = "Slow Moving"

		calculated_rows.append({
			"item_name": r.item_name,
			"category_name": r.category_name,
			"sub_category_name": r.sub_category_name,
			"opening_qty": opening_qty,
			"received_qty": received_qty,
			"return_qty": return_qty,
			"adjusted_qty": adjusted_qty,
			"issue_qty": issue_qty,
			"close_qty": close_qty,
			"holding_stock_days": holding_days,
			"avg_stay_days": avg_stay,
			"status_avg_stay": status,
		})

	# Calculate cumulative average stay and percentage
	running_cum_stay = 0.0
	for r in calculated_rows:
		running_cum_stay += r["holding_stock_days"] if r["holding_stock_days"] > 0 else 1.0
		r["cumulative_avg_stay"] = round(running_cum_stay, 2)

	total_cum = running_cum_stay or 1.0
	for r in calculated_rows:
		r["avg_stay_pct"] = round((r["cumulative_avg_stay"] / total_cum) * 100.0, 2)

	fsn_filter = filters.get("fsn_type") or "All"
	if fsn_filter != "All":
		calculated_rows = [r for r in calculated_rows if r["status_avg_stay"] == fsn_filter]

	return calculated_rows
