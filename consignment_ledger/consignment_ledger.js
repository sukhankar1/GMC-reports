// Copyright (c) 2026, Quantbit Technologies Pvt Ltd and Contributers and contributors
// For license information, please see license.txt

frappe.query_reports["Consignment Ledger"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_end(),
            reqd: 1
        },
        {
            fieldname: "supplier",
            label: __("Supplier"),
            fieldtype: "Link",
            options: "Supplier"
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "Link",
            options: "Department"
        },
        {
            fieldname: "item_code",
            label: __("Item"),
            fieldtype: "Link",
            options: "Item"
        },
        {
            fieldname: "batch_no",
            label: __("Batch No"),
            fieldtype: "Link",
            options: "Batch"
        },
        {
            fieldname: "include_cancelled",
            label: __("Include Cancelled"),
            fieldtype: "Check",
            default: 0
        }
    ],

    formatter: function (value, row, column, data) {
        if (column.fieldname === "running_balance" && data) {
            if (data.running_balance < 0) {
                return `<span style="color:red;font-weight:bold">${value}</span>`;
            }
        }
        return value;
    }
};
