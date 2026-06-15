"""Restore the standard Home & Dashboard items to the Buying/Selling/Stock sidebars.

Reverts remove_home_dashboard_from_sidebars.py. Prepends the two ERPNext-default
top-level items (positions 0 and 1) while preserving every other sidebar item and
its order. Idempotent: any existing Home/Dashboard rows are dropped first.

    bench --site tmj.localhost execute tmj.patches.v0_0.restore_home_dashboard_to_sidebars.execute
"""

import frappe

WORKSPACES = ["Buying", "Selling", "Stock"]
KEEP = [
	"type", "label", "link_type", "link_to", "icon", "child",
	"indent", "collapsible", "keep_closed", "show_arrow",
	"url", "filters", "route_options",
]


def execute():
	for ws in WORKSPACES:
		sb = frappe.get_doc("Workspace Sidebar", ws)

		existing = [
			{k: i.get(k) for k in KEEP}
			for i in sb.items
			if i.label not in ("Home", "Dashboard")
		]

		sb.set("items", [])
		sb.append("items", {
			"type": "Link", "label": "Home", "link_type": "Workspace",
			"link_to": ws, "icon": "home", "child": 0,
		})
		sb.append("items", {
			"type": "Link", "label": "Dashboard", "link_type": "Dashboard",
			"link_to": ws, "icon": "chart", "child": 0,
		})
		for row in existing:
			sb.append("items", row)

		# Skip link validation: some standard fixture rows (e.g. certain Report
		# links) don't pass strict Dynamic-Link checks, and we aren't changing them.
		sb.flags.ignore_links = True
		sb.save(ignore_permissions=True)

	frappe.db.commit()
	print(f"Restored Home & Dashboard to {WORKSPACES} sidebars.")
