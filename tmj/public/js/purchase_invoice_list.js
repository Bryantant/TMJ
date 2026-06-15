// Relabel payment-derived statuses to a neutral "Submitted" (client posts no payments).
// Loaded AFTER erpnext core purchase_invoice_list.js (see frappe/desk/form/meta.py), so this
// overrides get_indicator only, preserving core add_fields / onload.
frappe.listview_settings["Purchase Invoice"] = frappe.listview_settings["Purchase Invoice"] || {};

(function () {
	// Keep return / debit-note documents distinct; collapse all payment statuses
	// (Paid, Unpaid, Overdue, Partly Paid, On Hold, Internal Transfer) to "Submitted".
	const KEEP = { "Debit Note Issued": "gray", Return: "gray" };

	frappe.listview_settings["Purchase Invoice"].get_indicator = function (doc) {
		if (KEEP[doc.status]) {
			return [__(doc.status), KEEP[doc.status], "status,=," + doc.status];
		}
		// Only reached for docstatus == 1 (Draft/Cancelled handled by frappe.get_indicator).
		return [__("Submitted"), "blue", "docstatus,=,1"];
	};
})();
