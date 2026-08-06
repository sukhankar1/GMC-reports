import frappe
from frappe import _
from frappe.query_builder.functions import Abs, Sum
from frappe.utils import add_months, flt, getdate, today
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition


def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	# Set default date filters if missing
	if not filters.get("to_date"):
		filters["to_date"] = today()

	if not filters.get("from_date"):
		filters["from_date"] = add_months(filters["to_date"], -1)

	float_precision = frappe.db.get_default("float_precision")

	diff = ((getdate(filters.get("to_date")) - getdate(filters.get("from_date"))).days) + 1
	if diff <= 0:
		frappe.throw(_("'From Date' must be before 'To Date'"))

	columns = get_columns()
	items = get_item_info(filters)
	consumed_item_map = get_consumed_items(filters)
	sales_item_map = get_sales_invoice_items(filters)

	data = []
	for item in items:
		consumed_qty = flt(consumed_item_map.get(item.name, 0))
		sales_qty = flt(sales_item_map.get(item.name, 0))
		total_outgoing = consumed_qty + sales_qty

		avg_daily_outgoing = flt(total_outgoing / diff, float_precision)
		reorder_level = (avg_daily_outgoing * flt(item.lead_time_days)) + flt(item.safety_stock)

		data.append(
			[
				item.name,
				item.item_name,
				item.item_group,
				item.custom_category or "",  # Category value from Item Master
				item.brand,
				item.description,
				item.safety_stock,
				item.lead_time_days,
				consumed_qty,
				sales_qty,
				total_outgoing,
				avg_daily_outgoing,
				reorder_level,
			]
		)

	return columns, data


def get_columns():
	return [
		_("Item") + ":Link/Item:120",
		_("Item Name") + ":Data:120",
		_("Item Group") + ":Link/Item Group:100",
		_("Category") + ":Data:120",  # Change to :Link/DocTypeName if custom_category links to a DocType
		_("Brand") + ":Link/Brand:100",
		_("Description") + "::160",
		_("Safety Stock") + ":Float:120",
		_("Lead Time Days") + ":Float:120",
		_("Consumed") + ":Float:120",
		_("Sales Invoice Qty") + ":Float:140",
		_("Total Outgoing") + ":Float:120",
		_("Avg Daily Outgoing") + ":Float:160",
		_("Reorder Level") + ":Float:120",
	]


def get_item_info(filters):
	item = frappe.qb.DocType("Item")
	query = (
		frappe.qb.from_(item)
		.select(
			item.name,
			item.item_name,
			item.description,
			item.brand,
			item.item_group,
			item.custom_category,  # Selected from Item DocType
			item.safety_stock,
			item.lead_time_days,
		)
		.where((item.is_stock_item == 1) & (item.disabled == 0))
	)

	# Apply Category Filter if selected
	if category := filters.get("custom_category"):
		query = query.where(item.custom_category == category)

	if brand := filters.get("brand"):
		query = query.where(item.brand == brand)

	if conditions := get_item_group_condition(filters.get("item_group"), item):
		query = query.where(conditions)

	return query.run(as_dict=True)


def get_consumed_items(filters):
	purpose_to_exclude = [
		"Material Transfer for Manufacture",
		"Material Transfer",
		"Send to Subcontractor",
	]

	se = frappe.qb.DocType("Stock Entry")
	sle = frappe.qb.DocType("Stock Ledger Entry")

	query = (
		frappe.qb.from_(sle)
		.left_join(se)
		.on(sle.voucher_no == se.name)
		.select(sle.item_code, Abs(Sum(sle.actual_qty)).as_("consumed_qty"))
		.where(
			(sle.actual_qty < 0)
			& (sle.is_cancelled == 0)
			& (sle.voucher_type != "Sales Invoice")
			& ((se.purpose.isnull()) | (se.purpose.notin(purpose_to_exclude)))
		)
	)

	query = get_filtered_query(filters, sle, query).groupby(sle.item_code)
	consumed_items = query.run(as_dict=True)
	return {item.item_code: item.consumed_qty for item in consumed_items}


def get_sales_invoice_items(filters):
	parent = frappe.qb.DocType("Sales Invoice")
	child = frappe.qb.DocType("Sales Invoice Item")

	query = (
		frappe.qb.from_(parent)
		.from_(child)
		.select(child.item_code, Sum(child.stock_qty).as_("si_qty"))
		.where(
			(parent.name == child.parent)
			& (parent.docstatus == 1)
			& (parent.update_stock == 1)
		)
	)

	query = get_filtered_query(filters, parent, query).groupby(child.item_code)
	si_items = query.run(as_dict=True)
	return {item.item_code: flt(item.si_qty) for item in si_items}


def get_filtered_query(filters, table, query):
	if filters.get("from_date") and filters.get("to_date"):
		query = query.where(table.posting_date.between(filters["from_date"], filters["to_date"]))
	else:
		frappe.throw(_("From and To dates are required"))

	return query