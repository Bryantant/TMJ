// Relabel payment-derived statuses to a neutral "Submitted" (client posts no payments).
// Loaded AFTER erpnext core sales_invoice_list.js (see frappe/desk/form/meta.py), so this
// overrides get_indicator only, preserving core add_fields / onload / right_column.
frappe.listview_settings["Sales Invoice"] = frappe.listview_settings["Sales Invoice"] || {};

(function () {
	// Keep return / credit-note documents distinct; collapse all payment statuses
	// (Paid, Unpaid, Overdue, Partly Paid, *and Discounted, Internal Transfer) to "Submitted".
	const KEEP = { Return: "gray", "Credit Note Issued": "gray" };

	frappe.listview_settings["Sales Invoice"].get_indicator = function (doc) {
		if (KEEP[doc.status]) {
			return [__(doc.status), KEEP[doc.status], "status,=," + doc.status];
		}
		// Only reached for docstatus == 1 (Draft/Cancelled handled by frappe.get_indicator).
		return [__("Submitted"), "blue", "docstatus,=,1"];
	};
})();
