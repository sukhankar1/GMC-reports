# File: quantbit_hims_integration/reports/comparision_statement_for_tender/comparision_statement_for_tender.py

import frappe
from frappe import _
from collections import OrderedDict  # Ensures order preservation

# Import original
from erpnext.buying.report.supplier_quotation_comparison.supplier_quotation_comparison import execute as original_execute

def execute(filters=None):
    if not filters:
        filters = {}

    # Call original — it returns 4 values correctly
    result = original_execute(filters)
    columns = result[0]
    data = result[1] if len(result) > 1 else []
    message = result[2] if len(result) > 2 else None
    chart = result[3] if len(result) > 3 else None

    if not data:
        return columns, [], message, chart

    # Add columns FIRST (before processing data)
    columns.insert(0, {
        "label": _("Select"),
        "fieldname": "select_row",
        "fieldtype": "Check",
        "width": 60,
        "align": "center"
    })

    columns.insert(1, {
        "label": "Row ID",
        "fieldname": "row_id",
        "fieldtype": "Data",
        "hidden": 1,
        "width": 10
    })

    # FIXED: Convert to dicts WITHOUT sorting — preserve ORIGINAL order
    new_data = []
    fieldnames = [col.get("fieldname") for col in columns[2:]]  # Original fields only

    for idx, original_row in enumerate(data):  # enumerate preserves order
        # Use OrderedDict to maintain insertion order (Python 3.7+ dicts do too, but safe)
        new_row = OrderedDict.fromkeys(["select_row", "row_id"] + fieldnames, None)

        # Set our fields FIRST (they stay at beginning)
        new_row["select_row"] = 0
        new_row["row_id"] = f"row_{idx}"

        # Map original data (by index for lists, by key for dicts)
        if isinstance(original_row, (list, tuple)):
            # Original is list — map by position (skipping our new columns)
            for i, fname in enumerate(fieldnames):
                if i < len(original_row):
                    new_row[fname] = original_row[i]
        else:
            # Original is dict — copy directly
            for fname in fieldnames:
                new_row[fname] = original_row.get(fname)

        # Ensure key fields for PO generation
        new_row["supplier_name"] = new_row.get("supplier_name") or new_row.get("supplier", "")
        new_row["item_code"] = new_row.get("item_code", "")
        new_row["qty"] = new_row.get("qty", 1)
        new_row["price_per_unit"] = new_row.get("price_per_unit", new_row.get("rate", 0))
        new_row["quotation"] = new_row.get("quotation", new_row.get("parent", ""))
        new_row["uom"] = new_row.get("uom", new_row.get("stock_uom", ""))

        new_data.append(dict(new_row))  # Convert back to regular dict

    # Return — order preserved exactly as original
    return columns, new_data, message, chart