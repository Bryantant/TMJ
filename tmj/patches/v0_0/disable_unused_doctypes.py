import frappe


DOCTYPES = [
	# Buying flow
	"Purchase Receipt",
	"Purchase Order",
	"Request for Quotation",
	"Supplier Quotation",
	# Selling flow
	"Delivery Note",
	"Sales Order",
	"Quotation",
	# Stock/quality
	"Pick List",
	"Landed Cost Voucher",
	"Packing Slip",
	"Quality Inspection",
	# Pricing / promotions
	"Pricing Rule",
	"Promotional Scheme",
	"Coupon Code",
	"Blanket Order",
	"Shipping Rule",
	# CRM / marketing
	"Campaign",
	"Sales Person",
	"Sales Partner",
	"UTM Source",
	"UTM Medium",
	"UTM Campaign",
	# Finance config
	"Monthly Distribution",
	"Terms and Conditions",
	# Tax templates
	"Item Tax Template",
	"Purchase Taxes and Charges Template",
	"Sales Taxes and Charges Template",
	"Tax Category",
	"Tax Rule",
	"Tax Withholding Category",
	# POS
	"POS Closing Entry",
	"POS Customer Group",
	"POS Field",
	"POS Invoice",
	"POS Invoice Merge Log",
	"POS Item Group",
	"POS Opening Entry",
	"POS Payment Method",
	"POS Profile",
	"POS Search Fields",
	"POS Settings",
	# Supplier scorecard
	"Supplier Scorecard",
	"Supplier Scorecard Criteria",
	"Supplier Scorecard Period",
	"Supplier Scorecard Standing",
	"Supplier Scorecard Variable",
]


def execute():
	for doctype in DOCTYPES:
		frappe.db.delete("Custom DocPerm", {"parent": doctype})

		doc = frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": doctype,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": "System Manager",
				"permlevel": 0,
				"read": 1,
				"write": 1,
				"create": 1,
				"delete": 1,
				"submit": 1,
				"cancel": 1,
				"amend": 1,
				"report": 1,
				"export": 1,
				"import": 1,
				"share": 1,
				"print": 1,
				"email": 1,
			}
		)
		doc.insert(ignore_permissions=True)

	frappe.db.commit()
	print(f"Done — applied System Manager-only Custom DocPerm to {len(DOCTYPES)} doctypes.")
