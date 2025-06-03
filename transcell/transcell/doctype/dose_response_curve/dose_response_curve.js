frappe.ui.form.on('Dose Response Curve', {
    onload: function(frm) {
        if (!cur_frm.is_new()){
            frm.x50_params = null;
    
            // Retrieve the params (4PL coefficients) after document load
            frappe.call({
                method: 'get_preview_plot',
                doc: frm.doc,
                callback: function(r) {
                    if (r.message) {
                        frm.x50_params = r.message.params; // Store params for calculation
                    }
                }
            });

        }
    },
    refresh: function(frm) {
        frm.add_custom_button('Generate Preview', () => {
            frappe.call({
                method: 'get_preview_plot',
                doc: frm.doc,
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('x50', r.message.x50);
                        frm.set_value('equation', r.message.equation);

                        // Create image field and HTML viewer dynamically
                        frm.set_df_property('output_view', 'options', `
                            <div>
                                <p><strong>X50:</strong> ${r.message.x50}</p>
                                <p><strong>Equation:</strong> ${r.message.equation}</p>
                                <img src="${r.message.plot}" style="max-width: 100%; border: 1px solid #ccc; padding: 8px; border-radius: 6px;">
                            </div>
                        `);
                        frm.refresh_field('output_view');
                    }
                }
            });
        });
    }
});

frappe.ui.form.on('X50 Regression Entry', {
    x(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.x && !row.y) {
            frappe.call({
                method: "calculate_y_from_x",
                doc: frm.doc,
                args: {
                  
                    x: row.x
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, "y", r.message);
                    }
                }
            });
        }
    },
    y(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.y && !row.x) {
            frappe.call({
                method: "calculate_x_from_y",
                doc: frm.doc,
                args: {
                    y: row.y
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, "x", r.message);
                    }
                }
            });
        }
    }
});
