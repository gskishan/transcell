
frappe.ui.form.on('Dose Response Curve', {
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
