import frappe

# Relabel app titles shown in the desk workspace sidebar (the small subtitle
# under each workspace name, e.g. "ERPNext" beneath "Assets").
# Key = installed app_name, value = the title to display instead.
# Edit the value to rebrand; add more entries to relabel other apps.
APP_TITLE_OVERRIDES = {
	"erpnext": "Hicom System",
	"frappe": "Hicom Core",
}


def boot_session(bootinfo):
	"""Extend the boot payload without touching core files.

	Wired via the `extend_bootinfo` hook, which runs in frappe.sessions.get()
	*after* frappe.boot has populated app_data and desktop_icons, on every
	request (including cached boots).
	"""
	for app in bootinfo.get("app_data") or []:
		new_title = APP_TITLE_OVERRIDES.get(app.get("app_name"))
		if new_title:
			app["app_title"] = new_title

	_hide_role_restricted_workspace_icons(bootinfo)


def _hide_role_restricted_workspace_icons(bootinfo):
	"""Hide Desktop Icons whose target Workspace's own `roles` table excludes
	the current user — e.g. the "Assets" workspace has roles=[System Manager].

	Core's own desktop-icon permission check (get_desktop_icons in
	frappe/desk/doctype/desktop_icon/desktop_icon.py) only verifies that the
	icon's linked Workspace *Sidebar* has >=1 permitted item. A restricted
	workspace's sidebar can still contain generic items (e.g. "Item",
	"Accounts Settings") that the user can read via unrelated roles, so the
	icon survives core's filter and the workspace keeps appearing in the
	"Workspaces" dropdown (ui/sidebar/sidebar_header.js sibling_workspaces)
	even though opening it is blocked by Workspace.roles. This mirrors
	Workspace.roles directly instead of duplicating a hand-maintained
	allowlist, so it stays correct as roles are edited via the UI.
	"""
	icons = bootinfo.get("desktop_icons") or []
	if not icons:
		return

	user_roles = set(frappe.get_roles())
	if "System Manager" in user_roles:
		return

	kept = []
	for icon in icons:
		if icon.get("icon_type") == "Folder" or icon.get("link_type") != "Workspace Sidebar":
			kept.append(icon)
			continue

		ws_roles = frappe.get_all(
			"Has Role",
			filters={"parenttype": "Workspace", "parent": icon.get("link_to")},
			pluck="role",
		)
		if ws_roles and not (set(ws_roles) & user_roles):
			continue

		kept.append(icon)

	bootinfo.desktop_icons = kept
