import frappe
from collections import defaultdict
from erpnext.buying.report.supplier_quotation_comparison.supplier_quotation_comparison import execute as original_execute

def execute(filters=None):
    if not filters:
        filters = {}

    columns, data, message, chart = original_execute(filters)
    if not data:
        return columns, [], message, chart

    # Add Select & Row ID columns
    columns.insert(0, {
        "label": "Select",
        "fieldname": "select_row",
        "fieldtype": "Check",
        "width": 60
    })
    columns.insert(1, {
        "label": "Row ID",
        "fieldname": "row_id",
        "fieldtype": "Data",
        "hidden": 1
    })

    # Fill missing item_code (so every row has it)
    current_item = None
    for row in data:
        if isinstance(row, dict):
            if row.get("item_code"):
                current_item = row["item_code"]
            elif current_item:
                row["item_code"] = current_item
        else:
            item_idx = next((i for i, col in enumerate(columns[2:]) if col.get("fieldname") == "item_code"), None)
            if item_idx is not None:
                if row[item_idx]:
                    current_item = row[item_idx]
                elif current_item:
                    row[item_idx] = current_item

    # Find lowest price per item
    item_price_map = defaultdict(list)
    for idx, row in enumerate(data):
        item_code = row.get("item_code") if isinstance(row, dict) else row[
            next((i for i, c in enumerate(columns[2:]) if c.get("fieldname") == "item_code"), None)
        ] if len(row) > 0 else None

        price = row.get("price_per_unit") or row.get("rate") or 0
        if isinstance(row, list):
            price_idx = next((i for i, c in enumerate(columns[2:]) if c.get("fieldname") == "price_per_unit"), None)
            price = row[price_idx] if price_idx is not None and price_idx < len(row) else 0

        if item_code and price:
            item_price_map[item_code].append((float(price), idx))

    lowest_rows = set()
    for prices in item_price_map.values():
        if prices:
            min_price = min(p[0] for p in prices)
            lowest_rows.update(idx for price, idx in prices if abs(price - min_price) < 0.01)

    # Build final data
    new_data = []
    for idx, row in enumerate(data):
        row_dict = {
            "select_row": 0,
            "row_id": f"row_{idx}",
            "is_lowest_price": idx in lowest_rows
        }

        if isinstance(row, dict):
            row_dict.update(row)
        else:
            for i, col in enumerate(columns[2:]):
                if i < len(row):
                    row_dict[col["fieldname"]] = row[i]

        # Ensure required fields
        row_dict["supplier_name"] = row_dict.get("supplier_name") or row_dict.get("supplier", "")
        row_dict["item_code"] = row_dict.get("item_code", "")
        row_dict["qty"] = row_dict.get("qty") or row_dict.get("quantity") or 1
        row_dict["price_per_unit"] = row_dict.get("price_per_unit") or row_dict.get("rate") or 0
        row_dict["quotation"] = row_dict.get("quotation") or row_dict.get("parent", "")

        new_data.append(row_dict)

    return columns, new_data, message, chart