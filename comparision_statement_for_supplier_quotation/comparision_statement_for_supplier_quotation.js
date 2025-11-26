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

        // Render checkbox with stored state - read from global storage
        if (column.fieldname === "select_row") {
            if (!window.report_selected_rows) {
                window.report_selected_rows = new Set();
            }
            
            // Create unique identifier for this row
            const row_identifier = data.row_id || `${data.supplier_name || data.supplier}_${data.item_code}_${data.quotation}_${row}`;
            
            // Store it back to data so we can use it later
            if (!data.row_id) {
                data.row_id = row_identifier;
            }
            
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
        // Initialize global storage for selected rows
        if (!window.report_selected_rows) {
            window.report_selected_rows = new Set();
        }

        // Function to restore all checkboxes from storage
        function restoreCheckboxes() {
            $(".row-select").each(function() {
                const row_id = $(this).data("row-id");
                if (row_id && window.report_selected_rows.has(row_id)) {
                    $(this).prop("checked", true);
                }
            });
        }

        // Watch for any changes to the report table and restore checkboxes
        const observer = new MutationObserver(function(mutations) {
            restoreCheckboxes();
        });

        // Start observing the report wrapper for DOM changes
        const reportWrapper = report.page.wrapper.find(".report-wrapper, .datatable, .dt-scrollable")[0];
        if (reportWrapper) {
            observer.observe(reportWrapper, {
                childList: true,
                subtree: true
            });
        }

        // Also restore after any report refresh
        const originalRefresh = report.refresh.bind(report);
        report.refresh = function() {
            originalRefresh();
            setTimeout(restoreCheckboxes, 100);
        };

        setTimeout(() => {
            report.page.clear_primary_action();

            report.page.add_button(__("Generate Purchase Order"), function() {
                // Filter selected rows from current data
                const selected = report.data.filter(r => {
                    const row_id = r.row_id || `${r.supplier_name || r.supplier}_${r.item_code}_${r.quotation}`;
                    return window.report_selected_rows.has(row_id);
                });

                if (!selected.length) {
                    frappe.msgprint("Please select at least one row.");
                    return;
                }

                const suppliers = [...new Set(selected.map(r => r.supplier_name || r.supplier).filter(Boolean))];
                if (suppliers.length > 1) {
                    frappe.msgprint("All selected items must belong to the same supplier.");
                    return;
                }

                frappe.confirm(
                    `Create new Purchase Order for ${suppliers[0]} with ${selected.length} items?`,
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

                                            // Header
                                            frm.set_value("company", data.company);
                                            frm.set_value("supplier", data.supplier);
                                            frm.set_value("transaction_date", data.transaction_date || frappe.datetime.get_today());
                                            frm.set_value("schedule_date", data.schedule_date || frappe.datetime.get_today());
                                            frm.set_value("currency", data.currency || "INR");
                                            frm.set_value("buying_price_list", data.buying_price_list || "Standard Buying");
                                            frm.set_value("ignore_pricing_rule", 1);

                                            // Clear and add items safely
                                            frm.clear_table("items");
                                            data.items.forEach(item => {
                                                let row = frm.add_child("items");
                                                frappe.model.set_value(row.doctype, row.name, {
                                                    item_code: item.item_code,
                                                    item_name: item.item_name || item.item_code,
                                                    description: item.description || item.item_name || item.item_code,
                                                    qty: item.qty,
                                                    uom: item.uom,
                                                    stock_uom: item.stock_uom || item.uom,
                                                    conversion_factor: item.conversion_factor || 1,
                                                    rate: item.rate,
                                                    amount: item.amount,
                                                    price_list_rate: item.rate,
                                                    schedule_date: item.schedule_date || frappe.datetime.get_today(),
                                                    supplier_quotation: item.supplier_quotation || "",
                                                    supplier_quotation_item: item.supplier_quotation_item || ""
                                                });
                                            });

                                            frm.refresh_field("items");

                                            // FORCE ALL TOTALS TO APPEAR
                                            frm.trigger("items");
                                            frm.trigger("total");
                                            frm.trigger("calculate_taxes_and_totals");

                                            // LOCK RATE FOREVER
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

        // Use event delegation on the parent wrapper for better persistence
        report.page.wrapper.off("change", ".row-select").on("change", ".row-select", function() {
            const row_id = $(this).data("row-id");
            const checked = this.checked;

            if (!window.report_selected_rows) {
                window.report_selected_rows = new Set();
            }

            // Update the global Set for persistence
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