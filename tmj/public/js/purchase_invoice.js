frappe.ui.form.on("Purchase Invoice", {
	refresh: function (frm) {
		// Status is payment-derived and not tracked here; hide the raw read-only field so the
		// collapsed "More Information" section never shows "Unpaid"/"Overdue". The header reads "Submitted".
		frm.set_df_property("status", "hidden", 1);
	},
});
