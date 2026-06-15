import frappe

DOCTYPES = [
	"Serial No",
	"Batch",
	"Serial and Batch Bundle",
	"Inventory Dimension",
	"Item Alternative",
	"Quality Inspection Template",
	"Delivery Trip",
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
