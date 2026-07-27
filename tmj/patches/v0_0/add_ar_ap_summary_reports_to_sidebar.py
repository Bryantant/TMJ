"""Add the standard ERPNext "Accounts Receivable Summary" and "Accounts
Payable Summary" reports to the PT. Tunas Mitra Jaya sidebar's Reports
section, next to the existing (detail-level) Accounts Receivable / Accounts
Payable links.

Mutates the live Workspace Sidebar document directly (not the fixture JSON):
tmj/workspace_sidebar/ isn't nested under a Module Def folder, so `bench
migrate` has no fixture-sync path for it — developer_mode re-exports the
fixture to match once this saves. Idempotent: skips any label already present.

    bench --site tmj.localhost execute tmj.patches.v0_0.add_ar_ap_summary_reports_to_sidebar.execute
"""

import frappe

WORKSPACE_SIDEBAR = "PT. Tunas Mitra Jaya"
NEW_REPORTS = [
	"Accounts Receivable Summary",
	"Accounts Payable Summary",
]


def execute():
	sb = frappe.get_doc("Workspace Sidebar", WORKSPACE_SIDEBAR)
	existing_labels = {i.label for i in sb.items}

	added = []
	for label in NEW_REPORTS:
		if label in existing_labels:
			continue
		sb.append("items", {
			"type": "Link", "label": label, "link_type": "Report",
			"link_to": label, "icon": "-", "child": 1, "collapsible": 1,
			"indent": 0, "keep_closed": 0, "show_arrow": 0,
		})
		added.append(label)

	sb.flags.ignore_links = True
	sb.save(ignore_permissions=True)
	frappe.db.commit()
	print(f"Added {added} to '{WORKSPACE_SIDEBAR}' sidebar.")
