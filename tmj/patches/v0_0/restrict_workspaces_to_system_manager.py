import frappe

OPEN_TO_ALL = {"Buying", "Selling", "Stock"}


def execute():
	workspaces = frappe.get_all("Workspace", fields=["name"])

	updated = []
	skipped = []

	for ws in workspaces:
		if ws.name in OPEN_TO_ALL:
			skipped.append(ws.name)
			continue

		doc = frappe.get_doc("Workspace", ws.name)
		doc.roles = []
		doc.append("roles", {"role": "System Manager"})
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)
		updated.append(ws.name)

	frappe.db.commit()
	print(f"\nRestricted ({len(updated)}): {updated}")
	print(f"Left open  ({len(skipped)}): {skipped}")
