import frappe

# DocTypes unique to the "Assets" workspace sidebar (see Workspace Sidebar "Assets").
# Excludes shared doctypes also used by the client-facing tmj workspace or ERPNext
# internals — Item, Accounts Settings, Location — restricting those would break
# unrelated flows (e.g. Item lookup on Sales/Purchase Invoice).
DOCTYPES = [
	"Asset",
	"Asset Category",
	"Asset Depreciation Schedule",
	"Asset Capitalization",
	"Asset Movement",
	"Asset Maintenance Team",
	"Asset Maintenance",
	"Asset Maintenance Log",
	"Asset Value Adjustment",
	"Asset Repair",
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
