import frappe

# Relabel app titles shown in the desk workspace sidebar (the small subtitle
# under each workspace name, e.g. "ERPNext" beneath "Assets").
# Key = installed app_name, value = the title to display instead.
# Edit the value to rebrand; add more entries to relabel other apps.
APP_TITLE_OVERRIDES = {
	"erpnext": "Hicom System",
	"frappe": "Hicom Core",
}

# Workspaces visible to all roles. Everything else is hidden from non-System
# Manager users. This drives both the home-page icon grid AND the sidebar
# dropdown "Workspaces" submenu — both read frappe.boot.desktop_icons.
# The client gets a single consolidated workspace; the old per-module
# workspaces (Buying/Selling/Stock) remain visible to System Managers only.
OPEN_WORKSPACES = {"PT. Tunas Mitra Jaya"}


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

	# Restrict workspace icons for users without System Manager.
	if "System Manager" not in frappe.get_roles():
		open_lower = {w.lower() for w in OPEN_WORKSPACES}
		icons = bootinfo.get("desktop_icons") or []
		bootinfo.desktop_icons = [i for i in icons if (i.get("name") or "").lower() in open_lower]
