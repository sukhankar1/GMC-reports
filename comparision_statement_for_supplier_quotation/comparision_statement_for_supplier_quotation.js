// // Comparison Statement For Tender
// // Only "Price per Unit" cell highlighted in green for lowest price

// frappe.query_reports["Comparision Statement For Supplier Quotation"] = {
//     filters: [
//         {
//             fieldtype: "Link",
//             label: "Company",
//             options: "Company",
//             fieldname: "company",
//             default: frappe.defaults.get_user_default("Company"),
//             reqd: 1,
//         },
//         { fieldname: "from_date", label: "From Date", fieldtype: "Date", reqd: 1, default: frappe.datetime.add_months(frappe.datetime.get_today(), -1) },
//         { fieldname: "to_date",   label: "To Date",   fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
//         { fieldname: "item_code", label: "Item", fieldtype: "Link", options: "Item" },
//         { fieldname: "supplier", label: "Supplier", fieldtype: "MultiSelectList", get_data: txt => frappe.db.get_link_options("Supplier", txt) },
//         { fieldname: "supplier_quotation", label: "Supplier Quotation", fieldtype: "MultiSelectList", get_data: txt => frappe.db.get_link_options("Supplier Quotation", txt, { docstatus: ["<", 2] }) },
//         { fieldname: "request_for_quotation", label: "Request for Quotation", fieldtype: "Link", options: "Request for Quotation" },
//         { fieldname: "categorize_by", label: "Categorize by", fieldtype: "Select", options: ["Categorize by Supplier", "Categorize by Item"], default: "Categorize by Supplier" },
//         { fieldname: "include_expired", label: "Include Expired", fieldtype: "Check", default: 0 },
//     ],

//     // FORMATTER: Only highlight "Price per Unit" cell in green
//     formatter: function (value, row, column, data, default_formatter) {
//         value = default_formatter(value, row, column, data);

//         // Checkbox column
//         if (column.fieldname === "select_row") {
//             return `<input type="checkbox" class="row-select" data-row-id="${data.row_id}" ${data.select_row ? "checked" : ""}>`;
//         }

        

//         // Fallback: if is_lowest_price not set but min=1 exists
//         if (column.fieldname === "price_per_unit" && data.min === 1) {
//             return `<span style="color:green;font-weight:bold">${value}</span>`;
//         }

//         // Valid Till color coding
//         if (column.fieldname === "valid_till" && data.valid_till) {
//             const days = frappe.datetime.get_diff(data.valid_till, frappe.datetime.nowdate());
//             if (days <= 1) return `<span style="color:red;font-weight:bold">${value} (Expired)</span>`;
//             if (days <= 7) return `<span style="color:orange;font-weight:bold">${value}</span>`;
//         }

//         return value;
//     },

//     onload: function (report) {
//         // Wait for report to fully render
//         setTimeout(() => {
//             report.page.clear_primary_action();

//             // BIG BLUE BUTTON - Always visible
//             report.page.add_button("Generate Purchase Order", function () {
//                 const selected = report.data.filter(r => r.select_row === 1);

//                 if (!selected.length) {
//                     return frappe.msgprint({
//                         title: "No Selection",
//                         message: "Please select at least one row to create a Purchase Order.",
//                         indicator: "orange"
//                     });
//                 }

//                 const suppliers = [...new Set(selected.map(r => r.supplier_name).filter(Boolean))];

//                 if (suppliers.length === 0) {
//                     return frappe.msgprint("No supplier found in selected rows.");
//                 }
//                 if (suppliers.length > 1) {
//                     return frappe.msgprint({
//                         title: "Multiple Suppliers",
//                         message: "All selected items must belong to the same supplier.",
//                         indicator: "red"
//                     });
//                 }

//                 const supplierName = suppliers[0];

//                 frappe.confirm(
//                     `Create Draft Purchase Order for <b>${supplierName}</b> with <b>${selected.length}</b> item(s)?`,
//                     () => {
//                         frappe.call({
//                             method: "quantbit_hims_integration.api_for_report.generate_po_from_comparison",
//                             args: {
//                                 selected_items: selected,
//                                 company: report.get_filter_value("company")
//                             },
//                             freeze: true,
//                             freeze_message: "Creating Draft Purchase Order...",
//                             callback: function (r) {
//                                 if (r.message && !r.exc) {
//                                     frappe.show_alert({
//                                         message: `Draft PO Created: <a href="/app/purchase-order/${r.message}" style="font-weight:bold;color:green;">${r.message}</a>`,
//                                         indicator: "green"
//                                     }, 15);
//                                     frappe.set_route("Form", "Purchase Order", r.message);
//                                 }
//                             },
//                             error: function (err) {
//                                 frappe.msgprint({
//                                     title: "Error",
//                                     message: err.message || "Failed to create Purchase Order",
//                                     indicator: "red"
//                                 });
//                             }
//                         });
//                     }
//                 );
//             }, {
//                 icon: "fa-truck",
//                 btn_class: "btn-primary"
//             });

//         }, 1000);

//         // Live checkbox handler
//         $(document).off("change", ".row-select").on("change", ".row-select", function () {
//             const row_id = $(this).data("row-id");
//             const checked = this.checked ? 1 : 0;
//             const row = report.data.find(r => r.row_id === row_id);
//             if (row) {
//                 row.select_row = checked;
//             }
//         });
//     }
// };


// Inside your report .js file (e.g. comparision_statement_for_supplier_quotation.js)

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
        { fieldname: "from_date", label: "From Date", fieldtype: "Date", reqd: 1, default: frappe.datetime.add_months(frappe.datetime.get_today(), -1) },
        { fieldname: "to_date",   label: "To Date",   fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
        { fieldname: "item_code", label: "Item", fieldtype: "Link", options: "Item" },
        { fieldname: "supplier", label: "Supplier", fieldtype: "MultiSelectList", get_data: txt => frappe.db.get_link_options("Supplier", txt) },
        { fieldname: "supplier_quotation", label: "Supplier Quotation", fieldtype: "MultiSelectList", get_data: txt => frappe.db.get_link_options("Supplier Quotation", txt, { docstatus: ["<", 2] }) },
        { fieldname: "request_for_quotation", label: "Request for Quotation", fieldtype: "Link", options: "Request for Quotation" },
        { fieldname: "categorize_by", label: "Categorize by", fieldtype: "Select", options: ["Categorize by Supplier", "Categorize by Item"], default: "Categorize by Supplier" },
        { fieldname: "include_expired", label: "Include Expired", fieldtype: "Check", default: 0 },
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "select_row") {
            return `<input type="checkbox" class="row-select" data-row-id="${data.row_id}" ${data.select_row ? "checked" : ""}>`;
        }

        if (column.fieldname === "price_per_unit" && data.min === 1) {
            return `<span style="color:green !important;font-weight:bold">${value}</span>`;
        }

        if (column.fieldname === "valid_till" && data.valid_till) {
            const days = frappe.datetime.get_diff(data.valid_till, frappe.datetime.nowdate());
            if (days <= 0) return `<span style="color:red;font-weight:bold">${value} (Expired)</span>`;
            if (days <= 7) return `<span style="color:orange;font-weight:bold">${value}</span>`;
        }

        return value;
    },

    onload: function(report) {
        setTimeout(() => {
            report.page.clear_primary_action();

            report.page.add_button(__("Generate Purchase Order"), function() {
                const selected = report.data.filter(r => r.select_row === 1);
                if (!selected.length) {
                    frappe.msgprint("Please select at least one row.");
                    return;
                }

                const suppliers = [...new Set(selected.map(r => r.supplier_name).filter(Boolean))];
                if (suppliers.length > 1) {
                    frappe.msgprint("All selected items must belong to the same supplier.");
                    return;
                }

                frappe.confirm(
                    `Create new <strong>Purchase Order</strong> for <strong>${suppliers[0]}</strong> with <strong>${selected.length}</strong> items?<br><small style="color:#fff;">It will open as "Not Saved" – you can fill warehouse, department, etc.</small>`,
                    () => {
                        frappe.call({
                            method: "quantbit_hims_integration.api_for_report.generate_po_from_comparison",
                            args: {
                                selected_items: selected,
                                company: report.get_filter_value("company")
                            },
                            freeze: true,
                            freeze_message: __("Preparing Purchase Order..."),
                            callback: function(r) {
                                if (r.message && !r.exc) {
                                    const data = r.message;

                                    // THE ONLY CORRECT WAY – Use frappe.run_serially
                                    frappe.run_serially([
                                        () => frappe.new_doc("Purchase Order", true),  // true = open form immediately
                                        () => {
                                            const frm = cur_frm;
                                            if (!frm) return;

                                            // Header fields
                                            frm.set_value("company", data.company);
                                            frm.set_value("supplier", data.supplier);
                                            frm.set_value("transaction_date", data.transaction_date);
                                            frm.set_value("schedule_date", data.schedule_date);
                                            frm.set_value("currency", data.currency);
                                            frm.set_value("buying_price_list", data.buying_price_list);

                                            // Clear & add items – THIS WORKS 100%
                                            frm.clear_table("items");
                                            data.items.forEach(item => {
                                                let row = frm.add_child("items");
                                                row.item_code = item.item_code;
                                                row.item_name = item.item_name || item.item_code;
                                                row.description = item.description || item.item_name;
                                                row.qty = item.qty;
                                                row.rate = item.rate;
                                                row.amount = item.amount;
                                                row.uom = item.uom;
                                                row.stock_uom = item.stock_uom;
                                                row.schedule_date = item.schedule_date;
                                                row.supplier_quotation = item.supplier_quotation || "";
                                            });
                                            frm.refresh_field("items");

                                            // Trigger calculations
                                            frm.trigger("calculate_taxes_and_totals");
                                        }
                                    ]).then(() => {
                                        frappe.show_alert({
                                            message: __("Purchase Order ready! Fill warehouse & Save."),
                                            indicator: "green"
                                        }, 8);
                                    });
                                }
                            }
                        });
                    }
                );
            }, { icon: "fa-truck", btn_class: "btn-primary" });

        }, 1000);

        // Checkbox handler
        $(document).off("change", ".row-select").on("change", ".row-select", function() {
            const row_id = $(this).data("row-id");
            const checked = this.checked;
            const row = report.data.find(r => r.row_id === row_id);
            if (row) row.select_row = checked ? 1 : 0;
        });
    }
};