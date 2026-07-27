"""Add the standard ERPNext "Cash Flow" report to the PT. Tunas Mitra Jaya
sidebar's Reports section.

Mutates the live Workspace Sidebar document directly (not the fixture JSON):
tmj/workspace_sidebar/ isn't nested under a Module Def folder, so `bench
migrate` has no fixture-sync path for it — developer_mode re-exports the
fixture to match once this saves. Idempotent: skips if already present.

    bench --site tmj.localhost execute tmj.patches.v0_0.add_cash_flow_report_to_sidebar.execute
"""

import frappe

WORKSPACE_SIDEBAR = "PT. Tunas Mitra Jaya"
LABEL = "Cash Flow"


def execute():
	sb = frappe.get_doc("Workspace Sidebar", WORKSPACE_SIDEBAR)
	existing_labels = {i.label for i in sb.items}

	if LABEL in existing_labels:
		print(f"'{LABEL}' already present in '{WORKSPACE_SIDEBAR}' sidebar, skipping.")
		return

	sb.append("items", {
		"type": "Link", "label": LABEL, "link_type": "Report",
		"link_to": LABEL, "icon": "-", "child": 1, "collapsible": 1,
		"indent": 0, "keep_closed": 0, "show_arrow": 0,
	})
	sb.flags.ignore_links = True
	sb.save(ignore_permissions=True)
	frappe.db.commit()
	print(f"Added '{LABEL}' to '{WORKSPACE_SIDEBAR}' sidebar.")
