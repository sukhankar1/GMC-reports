frappe.query_reports["Re-Order Level Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group",
        },
        {
            fieldname: "brand",
            label: __("Brand"),
            fieldtype: "Link",
            options: "Brand",
        },
        {
            fieldname: "custom_category",
            label: __("Category"),
            fieldtype: "Link",
            options: "Item Category",
        },
    ],
};