

import frappe
from collections import defaultdict

# Import the ORIGINAL report 
from erpnext.buying.report.supplier_quotation_comparison.supplier_quotation_comparison import execute as original_execute


def execute(filters=None):
    if not filters:
        filters = {}

    # 1. Run the ORIGINAL report → perfect columns + data + ORDER
    columns, data, message, chart = original_execute(filters)

    if not data:
        return columns, [], message, chart

    # 2. Add our two custom columns at the front
    columns.insert(0, {
        "label": "Select",
        "fieldname": "select_row",
        "fieldtype": "Check",
        "width": 60,
        "align": "center"
    })
    columns.insert(1, {
        "label": "Row ID",
        "fieldname": "row_id",
        "fieldtype": "Data",
        "hidden": 1
    })

    # 3. Find which rows have the lowest price per item (for green highlight)
    item_price_map = defaultdict(list)
    for idx, row in enumerate(data):
        if isinstance(row, dict):
            item_code = row.get("item_code")
            price = row.get("price_per_unit")
        else:
            # Find column positions in original columns (before we added ours)
            item_idx = next((i for i, c in enumerate(columns[2:]) if c.get("fieldname") == "item_code"), None)
            price_idx = next((i for i, c in enumerate(columns[2:]) if c.get("fieldname") == "price_per_unit"), None)
            item_code = row[item_idx] if item_idx is not None and item_idx < len(row) else None
            price = row[price_idx] if price_idx is not None and price_idx < len(row) else None

        if item_code and price is not None:
            item_price_map[item_code].append((float(price), idx))

    lowest_rows = set()
    for prices in item_price_map.values():
        if not prices:
            continue
        min_price = min(p[0] for p in prices)
        lowest_rows.update(idx for price, idx in prices if price == min_price)

    # 4. Build new data → SAME ORDER as original (enumerate keeps exact sequence)
    new_data = []
    for idx, original_row in enumerate(data):
        row_dict = {
            "select_row": 0,
            "row_id": f"row_{idx}",
            "is_lowest_price": idx in lowest_rows          
        }

        # Copy all original fields
        if isinstance(original_row, dict):
            row_dict.update(original_row)
        else:
            # Map list → dict using original column fieldnames
            for i, col in enumerate(columns[2:]):
                if i < len(original_row):
                    row_dict[col["fieldname"]] = original_row[i]

        # Ensure fields needed for PO creation exist
        row_dict["supplier_name"] = row_dict.get("supplier_name") or row_dict.get("supplier", "")
        row_dict["item_code"]     = row_dict.get("item_code", "")
        row_dict["qty"]           = row_dict.get("qty") or 1
        row_dict["price_per_unit"]= row_dict.get("price_per_unit") or row_dict.get("rate", 0)
        row_dict["quotation"]     = row_dict.get("quotation") or row_dict.get("parent", "")

        new_data.append(row_dict)

    return columns, new_data, message, chart