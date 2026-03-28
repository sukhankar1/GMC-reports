frappe.query_reports["Comparision Statement For Supplier Quotation"] = {
    filters: [
        {
            fieldtype: "Link",
            label: "Company",
            options: "Company",
            fieldname: "company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
        },
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.get_today()
        },
        {
            fieldname: "item_code",
            label: "Item",
            fieldtype: "Link",
            options: "Item"
        },
        {
            fieldname: "supplier",
            label: "Supplier",
            fieldtype: "MultiSelectList",
            get_data: txt => frappe.db.get_link_options("Supplier", txt)
        },
        {
            fieldname: "supplier_quotation",
            label: "Supplier Quotation",
            fieldtype: "MultiSelectList",
            get_data: txt => frappe.db.get_link_options("Supplier Quotation", txt, {
                docstatus: ["<", 2]
            })
        },
        {
            fieldname: "request_for_quotation",
            label: "Request for Quotation",
            fieldtype: "Link",
            options: "Request for Quotation"
        },
        {
            fieldname: "categorize_by",
            label: "Categorize by",
            fieldtype: "Select",
            options: ["Categorize by Supplier", "Categorize by Item"],
            default: "Categorize by Supplier"
        },
        {
            fieldname: "include_expired",
            label: "Include Expired",
            fieldtype: "Check",
            default: 0
        },
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "select_row") {
            if (!window.report_selected_rows) {
                window.report_selected_rows = new Set();
            }

            // STABLE UNIQUE ID: Supplier Quotation name + Item Code
            // This combination is unique and never changes on refresh/reorder
            const quotation = data.quotation || data.parent || "";
            const item_code = data.item_code || "";
            const row_identifier = `${quotation}_${item_code}`;

            // Assign stable ID to data for consistency
            data.row_id = row_identifier;

            const checked = window.report_selected_rows.has(row_identifier) ? 'checked' : '';
            return `<input type="checkbox" class="row-select" data-row-id="${row_identifier}" ${checked}>`;
        }

        if (column.fieldname === "price_per_unit" && data.is_lowest_price) {
            return `<span style="color: green; font-weight: bold;">${value}</span>`;
        }

        if (column.fieldname === "valid_till" && data.valid_till) {
            const days = frappe.datetime.get_diff(data.valid_till, frappe.datetime.nowdate());
            if (days <= 0) return `<span style="color: red;">${value} (Expired)</span>`;
            if (days <= 7) return `<span style="color: orange;">${value}</span>`;
        }

        return value;
    },

    onload: function(report) {
        // Initialize global storage
        if (!window.report_selected_rows) {
            window.report_selected_rows = new Set();
        }

        // Restore checkbox states after DOM updates
        function restoreCheckboxes() {
            $(".row-select").each(function() {
                const row_id = $(this).data("row-id");
                if (row_id && window.report_selected_rows.has(row_id)) {
                    $(this).prop("checked", true);
                }
            });
        }

        // Observe table changes
        const observer = new MutationObserver(restoreCheckboxes);
        const reportWrapper = report.page.wrapper.find(".report-wrapper, .datatable, .dt-scrollable")[0];
        if (reportWrapper) {
            observer.observe(reportWrapper, { childList: true, subtree: true });
        }

        // Restore after report refresh
        const originalRefresh = report.refresh.bind(report);
        report.refresh = function() {
            originalRefresh();
            setTimeout(restoreCheckboxes, 100);
        };

        // Add Generate PO button
        setTimeout(() => {
            report.page.clear_primary_action();

            report.page.add_button(__("Generate Purchase Order"), function() {
                // Use stable row identifier to find selected rows
                const selected = report.data.filter(r => {
                    const quotation = r.quotation || r.parent || "";
                    const item_code = r.item_code || "";
                    const row_id = `${quotation}_${item_code}`;
                    return window.report_selected_rows.has(row_id);
                });

                if (!selected.length) {
                    frappe.msgprint(__("Please select at least one row."));
                    return;
                }

                const suppliers = [...new Set(selected.map(r => r.supplier_name || r.supplier).filter(Boolean))];
                if (suppliers.length > 1) {
                    frappe.msgprint(__("All selected items must belong to the same supplier."));
                    return;
                }

                frappe.confirm(
                    __("Create new Purchase Order for {0} with {1} items?", [suppliers[0], selected.length]),
                    () => {
                        frappe.call({
                            method: "quantbit_hims_integration.api_for_report.generate_po_from_comparison",
                            args: {
                                selected_items: selected,
                                company: report.get_filter_value("company")
                            },
                            freeze: true,
                            freeze_message: __("Creating Purchase Order..."),
                            callback: function(r) {
                                if (r.message && !r.exc) {
                                    const data = r.message;

                                    frappe.run_serially([
                                        () => frappe.new_doc("Purchase Order", true),
                                        () => {
                                            const frm = cur_frm;
                                            if (!frm) return;

                                            frm.set_value("company", data.company);
                                            frm.set_value("supplier", data.supplier);
                                            frm.set_value("transaction_date", data.transaction_date || frappe.datetime.get_today());
                                            frm.set_value("schedule_date", data.schedule_date || frappe.datetime.get_today());
                                            frm.set_value("currency", data.currency || "INR");
                                            frm.set_value("buying_price_list", data.buying_price_list || "Standard Buying");
                                            frm.set_value("ignore_pricing_rule", 1);

                                            frm.clear_table("items");
                                            data.items.forEach(item => {
                                                let row = frm.add_child("items");
                                                row.item_code = item.item_code;
                                                row.item_name = item.item_name || item.item_code;
                                                row.description = item.description || item.item_name || item.item_code;
                                                row.qty = item.qty;
                                                row.uom = item.uom;
                                                
                                                row.stock_uom = item.stock_uom || item.uom;
                                                row.conversion_factor = item.conversion_factor || 1;
                                                row.rate = item.rate;
                                                row.amount = item.amount;
                                                row.schedule_date = item.schedule_date || frappe.datetime.get_today();
                                                row.supplier_quotation = item.supplier_quotation || "";
                                                row.supplier_quotation_item = item.supplier_quotation_item || "";
                                                row.custom_free_qty = item.custom_free_qty || 0;
                                                row.custom_mrp = item.custom_mrp || 0;
                                                row.discount_percentage = item.discount_percentage || 0;
                                                row.discount_amount = item.discount_amount || 0;
                                                row.price_list_rate = item.price_list_rate || 0;
                                            });

                                            frm.refresh_field("items");
                                            frm.fields_dict.items.grid.refresh();

                                            frm.trigger("items");
                                            frm.trigger("total");
                                            frm.trigger("calculate_taxes_and_totals");

                                            // Prevent rate changes
                                            frm.cscript.rate = function() {};

                                            frappe.show_alert({
                                                message: __("Purchase Order created!"),
                                                indicator: "green"
                                            }, 10);
                                        }
                                    ]);
                                }
                            }
                        });
                    }
                );
            }, {
                icon: "fa fa-truck",
                btn_class: "btn-primary"
            });
        }, 1000);

        // Handle checkbox changes with event delegation
        report.page.wrapper.off("change", ".row-select").on("change", ".row-select", function() {
            const row_id = $(this).data("row-id");
            const checked = this.checked;

            if (checked) {
                window.report_selected_rows.add(row_id);
            } else {
                window.report_selected_rows.delete(row_id);
            }

            console.log("Selected rows:", Array.from(window.report_selected_rows));
        });

        // Initial restore
        setTimeout(restoreCheckboxes, 500);
    }
};