"""Add the 4 client-specific Custom Reports (is_standard=No) to the PT. Tunas
Mitra Jaya sidebar's Reports section: Sales Report Summary, Sales Report
Detail, Purchase Report Summary, Purchase Report Detail.

These reports only exist as DB records (Report Builder / Custom Report type),
never as app fixtures, so editing the committed Workspace Sidebar JSON alone
does not reach the live site — `bench migrate` has no fixture-sync path for
tmj/workspace_sidebar/ (it isn't nested under a Module Def folder). This patch
mutates the live document directly instead; developer_mode then re-exports the
fixture JSON to match. Idempotent: skips any label already present.

    bench --site tmj.localhost execute tmj.patches.v0_0.add_custom_reports_to_sidebar.execute
"""

import frappe

WORKSPACE_SIDEBAR = "PT. Tunas Mitra Jaya"
NEW_REPORTS = [
	"Sales Report Summary",
	"Sales Report Detail",
	"Purchase Report Summary",
	"Purchase Report Detail",
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
