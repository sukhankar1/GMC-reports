# Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": "Voucher Type", "fieldname": "voucher_type", "width": 130},
        {"label": "Voucher No", "fieldname": "voucher_no", "fieldtype": "Link", "options": "Purchase Receipt", "width": 160},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 180},
        {"label": "Department", "fieldname": "department", "width": 150},
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
        {"label": "Batch No", "fieldname": "batch_no", "width": 120},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 90},
        {"label": "Running Balance", "fieldname": "running_balance", "fieldtype": "Float", "width": 140},
    ]


def get_data(filters):
    conditions = []
    values = filters or {}

    conditions.append("cle.docstatus = 1")

    if not filters.get("include_cancelled"):
        conditions.append("cle.is_cancelled = 0")

    if filters.get("from_date"):
        conditions.append("cle.posting_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("cle.posting_date <= %(to_date)s")

    if filters.get("supplier"):
        conditions.append("cle.supplier = %(supplier)s")

    if filters.get("department"):
        conditions.append("cle.department = %(department)s")

    if filters.get("item_code"):
        conditions.append("cli.item_code = %(item_code)s")

    if filters.get("batch_no"):
        conditions.append("cli.batch_no = %(batch_no)s")

    condition_sql = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            cle.posting_date,
            cle.voucher_type,
            cle.voucher_no,
            cle.supplier,
            cle.department,
            cli.item_code,
            cli.batch_no,
            cli.qty
        FROM `tabConsignment Ledger Entry` cle
        INNER JOIN `tabConsignment Ledger Entry Items` cli
            ON cli.parent = cle.name
        WHERE {condition_sql}
        ORDER BY
            cli.batch_no,
            cle.posting_date,
            cle.voucher_no
        """,
        values,
        as_dict=True,
    )

    # Batch-wise running balance
    batch_balance = {}
    result = []

    for row in rows:
        batch = row.batch_no

        if batch not in batch_balance:
            batch_balance[batch] = 0

        batch_balance[batch] += row.qty
        row.running_balance = batch_balance[batch]

        result.append(row)

    return result
