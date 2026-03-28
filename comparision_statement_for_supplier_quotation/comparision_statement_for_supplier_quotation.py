import frappe
from collections import defaultdict
from erpnext.buying.report.supplier_quotation_comparison.supplier_quotation_comparison import (
    get_columns,
    get_message,
    validate_filters,
    prepare_chart_data,
)
from frappe.utils import cint, flt


def get_data(filters):
    sq = frappe.qb.DocType("Supplier Quotation")
    sqi = frappe.qb.DocType("Supplier Quotation Item")

    query = (
        frappe.qb.from_(sqi)
        .inner_join(sq)
        .on(sqi.parent == sq.name)
        .select(
            sqi.parent,
            sqi.item_code,
            sqi.qty,
            sqi.uom,
            sqi.stock_uom,
            sqi.amount,
            sqi.rate,
            sqi.price_list_rate,
            sqi.discount_percentage,
            sqi.discount_amount,
            sqi.custom_free_qty,
            sqi.custom_mrp,  
            sq.currency,
            sq.supplier.as_("supplier_name"),
            sq.valid_till,
            sqi.request_for_quotation,
            sqi.lead_time_days,
        )
        .where(
            (sqi.docstatus < 2)
            & (sq.company == filters.company)
            & (sq.transaction_date.between(filters.from_date, filters.to_date))
        )
        .orderby(sq.transaction_date, sqi.item_code)
    )

    if filters.get("item_code"):
        query = query.where(sqi.item_code == filters.item_code)
    if filters.get("supplier"):
        query = query.where(sq.supplier.isin(filters.supplier))
    if filters.get("supplier_quotation"):
        query = query.where(sqi.parent.isin(filters.supplier_quotation))
    if filters.get("request_for_quotation"):
        query = query.where(sqi.request_for_quotation == filters.request_for_quotation)
    if not filters.get("include_expired"):
        query = query.where(sq.status != "Expired")

    return query.run(as_dict=True)


def prepare_data(supplier_quotation_data, filters):
    out = []
    group_wise_map = defaultdict(list)
    float_precision = cint(frappe.db.get_default("float_precision")) or 2
    group_by_field = "supplier_name" if filters.get("categorize_by") == "Categorize by Supplier" else "item_code"

    for data in supplier_quotation_data:
        group = data.get(group_by_field)

        row = {
            "item_code": "" if group_by_field == "item_code" else data.item_code,
            "supplier_name": "" if group_by_field == "supplier_name" else data.supplier_name,
            "quotation": data.parent,
            "qty": data.qty,
            "uom": data.uom,
            "stock_uom": data.stock_uom,
            "valid_till": data.valid_till,
            "custom_free_qty": flt(data.custom_free_qty or 0, float_precision),
            "custom_mrp": flt(data.custom_mrp or 0, float_precision),  

            # PRESERVE ORIGINAL VALUES - NO CHANGES
            "price_list_rate": flt(data.price_list_rate or 0, float_precision),
            "rate": flt(data.rate or 0, float_precision),
            "amount": flt(data.amount or 0, float_precision),
            "discount_percentage": flt(data.discount_percentage or 0, float_precision),
            "discount_amount": flt(data.discount_amount or 0, float_precision),
        }

        # Use RATE for price_per_unit comparison (standard ERPNext way)
        row["price_per_unit"] = row["rate"]

        group_wise_map[group].append(row)

    # Grouping and lowest price highlighting
    for group in group_wise_map:
        entries = group_wise_map[group]
        if entries:
            entries[0][group_by_field] = group

        if group_by_field == "item_code" or filters.get("item_code"):
            prices = [e["price_per_unit"] for e in entries if e["price_per_unit"] > 0]
            if prices:
                min_price = min(prices)
                for e in entries:
                    if abs(e["price_per_unit"] - min_price) < 0.01:
                        e["is_lowest_price"] = 1

        out.extend(entries)

    return out, []


def execute(filters=None):
    filters = filters or {}
    validate_filters(filters)

    columns = get_columns(filters)

    raw_data = get_data(filters)
    data, chart = prepare_data(raw_data, filters)
    message = get_message()

    if not data:
        return columns, [], message, chart

    # Insert custom columns
    columns.insert(0, {"label": "Select", "fieldname": "select_row", "fieldtype": "Check", "width": 60})
    columns.insert(1, {"label": "Row ID", "fieldname": "row_id", "fieldtype": "Data", "hidden": 1})
    columns.append({"label": "Free Qty", "fieldname": "custom_free_qty", "fieldtype": "Float", "width": 100})

    
    columns.append({
        "label": "MRP",
        "fieldname": "custom_mrp",
        "fieldtype": "Currency",
        "width": 120,
        "precision": 2
    })

    # Fill missing item_code in grouped view
    current_item = None
    for row in data:
        if row.get("item_code"):
            current_item = row["item_code"]
        elif current_item:
            row["item_code"] = current_item

    # Mark lowest price rows
    item_prices = defaultdict(list)
    for idx, row in enumerate(data):
        price = row.get("price_per_unit") or row.get("rate") or 0
        item = row.get("item_code")
        if item and price:
            item_prices[item].append((price, idx))

    lowest_indices = set()
    for prices in item_prices.values():
        if prices:
            min_price = min(p[0] for p in prices)
            lowest_indices.update(idx for p, idx in prices if abs(p - min_price) < 0.01)

    # Final clean rows
    final_data = []
    for idx, row in enumerate(data):
        row = row.copy()
        row.update({
            "select_row": 0,
            "row_id": f"row_{idx}",
            "is_lowest_price": idx in lowest_indices,
            "supplier_name": row.get("supplier_name") or "",
            "item_code": row.get("item_code") or "",
            "qty": row.get("qty") or 1,
            "quotation": row.get("quotation") or "",
            "custom_free_qty": row.get("custom_free_qty") or 0,
            "custom_mrp": row.get("custom_mrp") or 0,  
        })
        final_data.append(row)

    return columns, final_data, message, chart