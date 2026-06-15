// Hide 'Help', 'About' and 'Frappe Support' from the desk dropdown / avatar menu.
// Frappe v16 renders these as `.frappe-menu .dropdown-menu-item` with a
// `.menu-item-title` span. The Help submenu (About, Frappe Support, ...) renders
// as a second `.frappe-menu` that appears on hover, so we match by title text
// across every menu rather than by position.
(function hideMenuItems() {
	var HIDDEN_LABELS = ["Help", "About", "Frappe Support"];

	function removeItems() {
		document.querySelectorAll(".frappe-menu .dropdown-menu-item").forEach(function (item) {
			var title = item.querySelector(".menu-item-title");
			if (title && HIDDEN_LABELS.indexOf(title.textContent.trim()) !== -1) {
				item.style.display = "none";
			}
		});
	}

	// The dropdown/avatar menu is rendered lazily when opened, so watch the DOM
	// rather than running once. (frappe.ready is portal-only — unavailable in desk.)
	removeItems();
	var observer = new MutationObserver(removeItems);
	observer.observe(document.body, { childList: true, subtree: true });
})();

// Restrict desktop layout editing ("Edit Layout" / "Reset Layout") to System Manager.
// Frappe v16 exposes both to every user — via the desktop right-click menu and a
// floating pencil button — with no server-side role gate (see desk/page/desktop/desktop.js,
// setup_context_menu/setup_edit_button: no role check). We suppress both on the client
// for users without the System Manager role.
(function restrictDesktopLayoutEditing() {
	function isSystemManager() {
		// frappe.user_roles is populated once boot loads; absent before then.
		return (frappe.user_roles || []).indexOf("System Manager") !== -1;
	}

	// Hide the floating pencil "Edit Layout" button (.desktop-edit, appended to <body>).
	// Gated on boot being ready so the role check is valid.
	frappe.after_ajax(function () {
		if (isSystemManager()) return;
		var style = document.createElement("style");
		style.textContent = ".desktop-edit { display: none !important; }";
		document.head.appendChild(style);
	});

	// Suppress the right-click context menu (Edit Layout / Reset Layout) on the desktop
	// icon grid. The menu binds `contextmenu` on `.desktop-container` (menu.js); a
	// capture-phase listener that stops propagation prevents it from ever opening.
	// The role is checked lazily at event time, so boot is always loaded by then.
	document.addEventListener(
		"contextmenu",
		function (e) {
			if (!isSystemManager() && e.target.closest && e.target.closest(".desktop-container")) {
				e.preventDefault();
				e.stopImmediatePropagation();
			}
		},
		true
	);
})();

// Keep the current workspace sidebar when navigating to a TREE doctype or a
// REPORT from a custom workspace sidebar.
// Bug: frappe.ui.Sidebar.entity_from_route (sidebar.js) only special-cases
// length-3 "Workspaces/private" routes. So:
//   - a tree doctype routes as ["Tree", "<DocType>"]  -> returns "Tree"
//   - a query report routes as ["query-report", "<Report>"] -> returns "query-report"
// In both cases the returned entity matches no sidebar item's link_to, so the
// desk can't keep/select our custom sidebar and falls back to the doctype's /
// report's module sidebar (clicking Warehouse or refreshing on a report jumps
// to Stock). We override entity_from_route so that when the first segment is a
// view keyword or "query-report", the real entity (route[1] = the doctype or
// report name) is returned. That makes get_workspace_sidebars() match our
// sidebar, so it is actively kept/selected. Preserves the tree view (unlike
// forcing List) and fixes every tree doctype + report generically.
(function fixTreeAndReportRouteSidebar() {
	if (!frappe.ui || !frappe.ui.Sidebar || !frappe.ui.Sidebar.prototype) return;
	var proto = frappe.ui.Sidebar.prototype;
	if (proto.__tmj_entity_patch) return;
	var orig = proto.entity_from_route;
	var ROUTE_PREFIXES = {
		List: 1, Tree: 1, Report: 1, Form: 1, Dashboard: 1,
		Kanban: 1, Calendar: 1, Gantt: 1, Image: 1, Inbox: 1, Map: 1,
		"query-report": 1,
	};
	proto.entity_from_route = function (route) {
		if (route && route.length >= 2 && ROUTE_PREFIXES[route[0]]) {
			return route[1];
		}
		return orig.call(this, route);
	};
	proto.__tmj_entity_patch = true;
})();

// Hicom16 desk overrides: start with sidebar closed on form/list pages (not workspace)
frappe.router.on("change", function () {
	setTimeout(function () {
		var route = frappe.get_route();
		// Skip workspace — its left nav should stay open
		if (!route || !route[0] || route[0] === "Workspaces") return;

		var $sidebar = $(".layout-side-section");
		if ($sidebar.is(":visible")) {
			$sidebar.hide();
			var $icon = $(".sidebar-toggle-btn .sidebar-toggle-icon");
			if ($icon.length && frappe.utils) {
				$icon.html(frappe.utils.icon("es-line-sidebar-expand", "md"));
			}
		}
	}, 300);
});
