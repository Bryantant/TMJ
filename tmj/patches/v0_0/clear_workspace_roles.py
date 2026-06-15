import frappe


def execute():
	frappe.db.delete("Has Role", {"parenttype": "Workspace"})
	frappe.db.commit()
	print("Cleared all Workspace Role restrictions.")
