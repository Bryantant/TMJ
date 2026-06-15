import frappe

WORKSPACES = ["Buying", "Selling", "Stock"]
LABELS = ["Home", "Dashboard"]


def execute():
	for workspace in WORKSPACES:
		frappe.db.delete(
			"Workspace Sidebar Item",
			{"parent": workspace, "label": ["in", LABELS]},
		)
	frappe.db.commit()
	print(f"Removed {LABELS} from {WORKSPACES} sidebars.")
