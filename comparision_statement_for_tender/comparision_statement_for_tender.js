frappe.query_reports["Comparision Statement For Tender"] = {
    filters: [
        {
            fieldtype: "Link",
            label: __("Company"),
            options: "Company",
            fieldname: "company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
        },
        { fieldname: "from_date", label: __("From Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.add_months(frappe.datetime.get_today(), -1) },
        { fieldname: "to_date",   label: __("To Date"),   fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
        { fieldname: "item_code", label: __("Item"), fieldtype: "Link", options: "Item" },
        { fieldname: "supplier", label: __("Supplier"), fieldtype: "MultiSelectList", get_data: txt => frappe.db.get_link_options("Supplier", txt) },
        { fieldname: "supplier_quotation", label: __("Supplier Quotation"), fieldtype: "MultiSelectList", get_data: txt => frappe.db.get_link_options("Supplier Quotation", txt, { docstatus: ["<", 2] }) },
        { fieldname: "request_for_quotation", label: __("Request for Quotation"), fieldtype: "Link", options: "Request for Quotation" },
        { fieldname: "categorize_by", label: __("Categorize by"), fieldtype: "Select", options: ["Categorize by Supplier", "Categorize by Item"], default: "Categorize by Supplier" },
        { fieldname: "include_expired", label: __("Include Expired"), fieldtype: "Check", default: 0 },
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "select_row") {
            return `<input type="checkbox" class="row-select" data-row-id="${data.row_id}" ${data.select_row ? "checked" : ""}>`;
        }

        if (column.fieldname === "price_per_unit" && data.min === 1) {
            value = `<span style="color:green;font-weight:bold">${value}</span>`;
        }

        if (column.fieldname === "valid_till" && data.valid_till) {
            const days = frappe.datetime.get_diff(data.valid_till, frappe.datetime.nowdate());
            if (days <= 1) value = `<span style="color:red">${value}</span>`;
            else if (days <= 7) value = `<span style="color:orange">${value}</span>`;
        }

        return value;
    },

    onload: function (report) {
        // Wait for full render — this guarantees the button appears
        setTimeout(() => {
            // Clear any old buttons
            report.page.clear_primary_action();

            // BIG VISIBLE PRIMARY BUTTON (Top-right, next to Print/Export)
            report.page.add_button(__("Generate Purchase Order"), function () {
                const selected = report.data.filter(r => r.select_row === 1);

                if (!selected.length) {
                    return frappe.msgprint({
                        title: __("No Selection"),
                        message: __("Please select at least one row to generate Purchase Order."),
                        indicator: "orange"
                    });
                }

                // Extract supplier safely — uses supplier_name (the actual field in report)
                const suppliers = [...new Set(
                    selected.map(r => r.supplier_name).filter(Boolean)
                )];

                if (suppliers.length === 0) {
                    return frappe.msgprint("No supplier found in selected rows.");
                }

                if (suppliers.length > 1) {
                    return frappe.msgprint({
                        title: __("Invalid Selection"),
                        message: __("All selected items must belong to the same supplier."),
                        indicator: "red"
                    });
                }

                const supplier_display = suppliers[0];

                frappe.confirm(
                    __("Create Purchase Order for <b>{0}</b> with <b>{1}</b> item(s)?", [supplier_display, selected.length]),
                    () => {
                        frappe.call({
                            method: "quantbit_hims_integration.api_for_report.generate_po_from_comparison",
                            args: {
                                selected_items: selected,
                                company: report.get_filter_value("company")
                            },
                            freeze: true,
                            freeze_message: __("Creating Purchase Order..."),
                            callback: function (r) {
                                if (r.message && !r.exc) {
                                    frappe.show_alert({
                                        message: __("Purchase Order Created Successfully: ") 
                                            + `<a href="/app/purchase-order/${r.message}" style="font-weight:bold;">${r.message}</a>`,
                                        indicator: "green"
                                    }, 10);

                                    // Redirect to new PO
                                    frappe.set_route("Form", "Purchase Order", r.message);
                                }
                            },
                            error: function (err) {
                                frappe.msgprint({
                                    title: __("Error"),
                                    message: err.message || __("Failed to create Purchase Order"),
                                    indicator: "red"
                                });
                            }
                        });
                    }
                );
            }, {
                icon: "fa fa-truck",
                btn_class: "btn-primary"
            });

        }, 1000); // 1 second delay = 100% button visibility

        // Live checkbox handler — updates report.data instantly
        $(document).off("change", ".row-select").on("change", ".row-select", function () {
            const row_id = $(this).data("row-id");
            const checked = this.checked ? 1 : 0;
            const row = report.data.find(r => r.row_id === row_id);
            if (row) {
                row.select_row = checked;
            }
        });
    }
};