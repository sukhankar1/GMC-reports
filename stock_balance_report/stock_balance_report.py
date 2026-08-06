# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

# Copyright (c) 2026

import frappe
from frappe import _

from erpnext.stock.report.stock_balance import stock_balance


def execute(filters=None):

    filters = frappe._dict(filters or {})

    columns, data = stock_balance.execute(filters)


    # Add Classification Column
    columns.insert(
        2,
        {
            "label": _("Classification"),
            "fieldname": "custom_classification",
            "fieldtype": "Link",
            "options": "Classification",
            "width": 150,
        },
    )


    # Add Department Column
    columns.insert(
        3,
        {
            "label": _("Department"),
            "fieldname": "custom_department_name",
            "fieldtype": "Link",
            "options": "Department",
            "width": 150,
        },
    )


    # -------------------------
    # Get Item Classification
    # -------------------------

    item_codes = list(
        set(
            row.item_code
            for row in data
            if row.get("item_code")
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
                "custom_classification"
            ],
        )

        classification_map = {
            d.name: d.custom_classification
            for d in items
        }


    # -------------------------
    # Department from Stock Entry
    # -------------------------

    department_map = {}


    stock_entries = frappe.get_all(
        "Stock Ledger Entry",
        filters={
            "item_code": ["in", item_codes],
            "voucher_type": "Stock Entry"
        },
        fields=[
            "item_code",
            "warehouse",
            "voucher_no"
        ]
    )


    voucher_names = list(
        set(
            d.voucher_no
            for d in stock_entries
        )
    )


    if voucher_names:

        entries = frappe.get_all(
            "Stock Entry",
            filters={
                "name": ["in", voucher_names]
            },
            fields=[
                "name",
                "custom_department_name"
            ]
        )


        department_map = {
            d.name:d.custom_department_name
            for d in entries
        }



    # -------------------------
    # Update Rows
    # -------------------------

    for row in data:

        row["custom_classification"] = (
            classification_map.get(
                row.item_code
            )
        )


        # find department
        dept = None

        for se in stock_entries:

            if (
                se.item_code == row.item_code
                and se.warehouse == row.warehouse
            ):
                dept = department_map.get(
                    se.voucher_no
                )
                break


        row["custom_department_name"] = dept



    # -------------------------
    # Filters
    # -------------------------


    if filters.get("custom_classification"):

        data = [
            d for d in data
            if d.custom_classification ==
            filters.custom_classification
        ]



    if filters.get("custom_department_name"):

        data = [
            d for d in data
            if d.custom_department_name ==
            filters.custom_department_name
        ]



    return columns, data