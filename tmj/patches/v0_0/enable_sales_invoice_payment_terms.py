"""Unhide `due_date` and `payment_terms_template` on Sales Invoice.

Both fields were previously hidden via Property Setter, and `due_date` had a
static default of "Today" — so every invoice's due date always equalled its
posting date, regardless of the Payment Terms Template selected (or not
selected). Confirmed on site: 7 Payment Terms Templates exist (3/7/20/30/45/
60/90 Days) but no Sales Invoice has ever used one, and the Accounts
Receivable report's ageing (calculated from due_date) has been indistinguishable
from ageing-by-posting-date as a result.

Client confirmed some customers ARE given payment terms, so this was blocking
real functionality, not an intentional cash-only restriction. Unhiding lets
staff pick a Payment Terms Template (or set Due Date manually) per invoice;
ERPNext's own client JS (sales_invoice.js) already auto-calculates due_date
from the template when one is selected — that logic was always running, just
invisible. Leaves the "Today" default in place for invoices with no template
(effectively COD), and leaves `payments_tab`/`is_pos` overrides untouched.

    bench --site tmj.localhost execute tmj.patches.v0_0.enable_sales_invoice_payment_terms.execute
"""

import frappe

DOCTYPE = "Sales Invoice"
FIELDS = ["due_date", "payment_terms_template"]


def execute():
	for fieldname in FIELDS:
		frappe.db.delete(
			"Property Setter",
			{"doc_type": DOCTYPE, "field_name": fieldname, "property": "hidden"},
		)

	frappe.clear_cache(doctype=DOCTYPE)
	frappe.db.commit()
	print(f"Unhid {FIELDS} on '{DOCTYPE}'.")
