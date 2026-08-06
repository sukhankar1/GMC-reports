# Copyright (c) 2026
# License: GNU General Public License v3

import frappe
from frappe import _

from erpnext.stock.report.stock_ledger import stock_ledger as standard_report


def execute(filters=None):
    filters = frappe._dict(filters or {})

    # Execute standard Stock Ledger report
    columns, data = standard_report.execute(filters)

    # Add Classification column
    columns.insert(
        3,
        {
            "label": _("Classification"),
            "fieldname": "custom_classification",
            "fieldtype": "Link",
            "options": "Classification",
            "width": 140,
        },
    )

    # Add Department column
    columns.insert(
        4,
        {
            "label": _("Department"),
            "fieldname": "custom_department_name",
            "fieldtype": "Link",
            "options": "Department",
            "width": 140,
        },
    )


    # -------------------------
    # Item Classification
    # -------------------------

    item_codes = list(
        set(
            row.get("item_code")
            for row in data
            if row.get("item_code")
            and row.get("item_code") != _("'Opening'")
        )
    )


    classification_map = {}

    if item_codes:

        items = frappe.get_all(
            "Item",
            filters={
                "name": ["in", item_codes]
            },
            fields=[
                "name",
                "custom_classification",
            ],
        )

        classification_map = {
            item.name: item.custom_classification
            for item in items
        }


    # -------------------------
    # Stock Entry Department
    # -------------------------

    stock_entry_names = list(
        set(
            row.get("voucher_no")
            for row in data
            if row.get("voucher_type") == "Stock Entry"
            and row.get("voucher_no")
        )
    )

    department_map = {}

    if stock_entry_names:

        stock_entries = frappe.get_all(
            "Stock Entry",
            filters={
                "name": ["in", stock_entry_names]
            },
            fields=[
                "name",
                "custom_department_name",
            ],
        )

        department_map = {
            entry.name: entry.custom_department_name
            for entry in stock_entries
        }


    # -------------------------
    # Update report rows
    # -------------------------
  
    for row in data:

        # Item field
        row["custom_classification"] = classification_map.get(
            row.get("item_code")
        )


        # Stock Entry field
        if row.get("voucher_type") == "Stock Entry":

            row["custom_department_name"] = department_map.get(
                row.get("voucher_no")
            )

        else:
            row["custom_department_name"] = None



    # -------------------------
    # Filters
    # -------------------------

    if filters.get("custom_classification"):

        data = [
            row
            for row in data
            if row.get("item_code") == _("'Opening'")
            or row.get("custom_classification")
            == filters.custom_classification
        ]


    if filters.get("custom_department_name"):

        data = [
            row
            for row in data
            if row.get("custom_department_name")
            == filters.custom_department_name
        ]


    return columns, data