"""Re-add the 'Settings' (Website Settings) item to the Website workspace sidebar.

Frappe's standard Website sidebar originally shipped a Link "Settings" ->
"Website Settings" (icon 'settings', positioned after "Web Form"), but a later
Frappe commit removed it from the fixture. After it was accidentally deleted
here, re-importing the current fixture can't bring it back. This restores it.

Idempotent: skips if the item is already present. Run via:
    bench --site tmj.localhost execute tmj.patches.v0_0.restore_website_settings_item.execute
"""

import frappe

WS = "Website"
KEEP = [
	"type", "label", "link_type", "link_to", "icon", "child",
	"indent", "collapsible", "keep_closed", "show_arrow",
	"url", "filters", "route_options",
]

SETTINGS_ITEM = {
	"type": "Link", "label": "Settings", "link_type": "DocType",
	"link_to": "Website Settings", "icon": "settings", "child": 0,
}


def execute():
	sb = frappe.get_doc("Workspace Sidebar", WS)

	if any(i.label == "Settings" and i.link_to == "Website Settings" for i in sb.items):
		print("'Settings' item already present in Website sidebar.")
		return

	rows = [{k: i.get(k) for k in KEEP} for i in sb.items]

	out, inserted = [], False
	for r in rows:
		out.append(r)
		if not inserted and r["label"] == "Web Form":
			out.append(dict(SETTINGS_ITEM))
			inserted = True
	if not inserted:  # fallback: no "Web Form" anchor -> put it first
		out.insert(0, dict(SETTINGS_ITEM))

	sb.set("items", [])
	for r in out:
		sb.append("items", r)

	sb.flags.ignore_links = True
	sb.save(ignore_permissions=True)
	frappe.db.commit()
	print("Restored 'Settings' (Website Settings) item to Website sidebar.")
