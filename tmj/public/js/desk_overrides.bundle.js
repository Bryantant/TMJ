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

// Make "Custom Report" sidebar links open in the Script Report (query-report) view.
// Bug: frappe.ui.sidebar_item.TypeLink.get_path() (sidebar_item.js) sets is_query_report
// only when report_type is "Query Report" or "Script Report" — it omits "Custom Report".
// A Custom Report based on a script report (e.g. "Sales Report Summary", whose
// reference_report is "Sales Register") therefore gets the report-builder route
// (<doctype>/view/report/<name>) and opens as a list view instead of the query report.
// Frappe's own desk module/desktop logic (desktop.py) DOES treat "Custom Report" as a
// query report; we mirror that by briefly normalizing report_type so the original
// get_path() builds the query-report route, then restoring it.
(function fixCustomReportSidebarRoute() {
	if (!frappe.ui || !frappe.ui.sidebar_item || !frappe.ui.sidebar_item.TypeLink) return;
	var proto = frappe.ui.sidebar_item.TypeLink.prototype;
	if (proto.__tmj_custom_report_patch) return;
	var orig = proto.get_path;
	proto.get_path = function () {
		var rep = this.item && this.item.report;
		if (
			rep &&
			this.item.type === "Link" &&
			this.item.link_type === "Report" &&
			rep.report_type === "Custom Report"
		) {
			var real = rep.report_type;
			rep.report_type = "Script Report"; // makes orig compute is_query_report = true
			try {
				return orig.call(this);
			} finally {
				rep.report_type = real;
			}
		}
		return orig.call(this);
	};
	proto.__tmj_custom_report_patch = true;
})();

// Remove the "Company" filter from the Item-wise Sales History report.
// The report JS is lazy-loaded when the user navigates to it, so we intercept
// the property assignment on frappe.query_reports rather than patching after load.
(function removeCompanyFilterItemwiseSalesHistory() {
	frappe.provide("frappe.query_reports");
	var _stored = frappe.query_reports["Item-wise Sales History"];
	Object.defineProperty(frappe.query_reports, "Item-wise Sales History", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) {
			if (def && Array.isArray(def.filters)) {
				def.filters = def.filters.map(function (f) {
					if (f.fieldname === "company") {
						f.hidden = 1;
						f.default = frappe.defaults.get_default("company");
					}
					return f;
				});
			}
			_stored = def;
		},
	});
	// Handle the unlikely case it was already loaded
	if (_stored && Array.isArray(_stored.filters)) {
		_stored.filters = _stored.filters.map(function (f) {
			if (f.fieldname === "company") {
				f.hidden = 1;
				f.default = frappe.defaults.get_default("company");
			}
			return f;
		});
	}
})();

// Hide Company, Mode of Payment, Cost Center, Warehouse, and Show Ledger View filters
// from the Sales Register report. Company must stay with a default (Python crashes on None);
// the rest are safe to hide with no value.
(function hideSalesRegisterFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = { company: 1, mode_of_payment: 1, cost_center: 1, warehouse: 1, include_payments: 1, owner: 1 };
	var _stored = frappe.query_reports["Sales Register"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}
	}

	Object.defineProperty(frappe.query_reports, "Sales Register", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it), Mode of Payment, Warehouse, and Income Account
// filters from the Item-wise Sales Register report. Company must stay with a
// default (the server query requires one); the rest are safe to hide with no value.
(function hideItemwiseSalesRegisterFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = { company: 1, mode_of_payment: 1, warehouse: 1, income_account: 1 };
	var _stored = frappe.query_reports["Item-wise Sales Register"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}
	}

	Object.defineProperty(frappe.query_reports, "Item-wise Sales Register", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it), Mode of Payment, Cost Center, Warehouse, and
// Show Ledger View filters from the Purchase Register report. Company must keep
// a default (the server query requires one); the rest are safe to hide.
(function hidePurchaseRegisterFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = { company: 1, mode_of_payment: 1, cost_center: 1, warehouse: 1, include_payments: 1 };
	var _stored = frappe.query_reports["Purchase Register"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}
	}

	Object.defineProperty(frappe.query_reports, "Purchase Register", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it) and Mode of Payment filters from the
// Item-wise Purchase Register report.
(function hideItemwisePurchaseRegisterFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = { company: 1, mode_of_payment: 1 };
	var _stored = frappe.query_reports["Item-wise Purchase Register"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}
	}

	Object.defineProperty(frappe.query_reports, "Item-wise Purchase Register", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it), Warehouses, Batch No, Project, and
// Enable Serial / Batch Bundle filters from the Stock Ledger report.
// Also hide the Item, Warehouse, Project, and Company display columns.
(function hideStockLedgerFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = { company: 1, warehouse: 1, batch_no: 1, project: 1, segregate_serial_batch_bundle: 1 };
	var HIDDEN_COLS = { item_code: 1, warehouse: 1, project: 1, company: 1 };
	var _stored = frappe.query_reports["Stock Ledger"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}

		var prevGetOpts = def && def.get_datatable_options;
		if (def) {
			def.get_datatable_options = function (options) {
				if (typeof prevGetOpts === "function") {
					options = prevGetOpts(options) || options;
				}
				if (options && Array.isArray(options.columns)) {
					options.columns = options.columns.filter(function (c) {
						return !HIDDEN_COLS[c.fieldname];
					});
				}
				return options;
			};
		}
	}

	Object.defineProperty(frappe.query_reports, "Stock Ledger", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it), Warehouses, Warehouse Type, Show Variant Attributes,
// Show Stock Ageing Data, Ignore Closing Balance, and Show Dimension Wise Stock
// filters from the Stock Balance report.
// Also hide the Item, Warehouse, Reserved Stock, and Company display columns.
(function hideStockBalanceFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = {
		company: 1,
		warehouse: 1,
		warehouse_type: 1,
		show_variant_attributes: 1,
		show_stock_ageing_data: 1,
		ignore_closing_balance: 1,
		show_dimension_wise_stock: 1,
	};
	var HIDDEN_COLS = { item_code: 1, warehouse: 1, reserved_stock: 1, company: 1 };
	var _stored = frappe.query_reports["Stock Balance"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}

		var prevGetOpts = def && def.get_datatable_options;
		if (def) {
			def.get_datatable_options = function (options) {
				if (typeof prevGetOpts === "function") {
					options = prevGetOpts(options) || options;
				}
				if (options && Array.isArray(options.columns)) {
					options.columns = options.columns.filter(function (c) {
						return !HIDDEN_COLS[c.fieldname];
					});
				}
				return options;
			};
		}
	}

	Object.defineProperty(frappe.query_reports, "Stock Balance", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it), Sales Person, Warehouse, Cost Center, and Project
// filters from the Gross Profit report. Also drop Warehouse, Territory,
// Sales Person, Project, Cost Center, and Payment Term from the Group By options.
(function hideGrossProfitFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = { company: 1, sales_person: 1, warehouse: 1, cost_center: 1, project: 1 };
	var DROP_GROUP_BY = {
		Warehouse: 1,
		Territory: 1,
		"Sales Person": 1,
		Project: 1,
		"Cost Center": 1,
		"Payment Term": 1,
	};
	var _stored = frappe.query_reports["Gross Profit"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				if (f.fieldname === "group_by" && typeof f.options === "string") {
					f.options = f.options
						.split("\n")
						.filter(function (opt) {
							return !DROP_GROUP_BY[opt];
						})
						.join("\n");
				}
				return f;
			});
		}
	}

	Object.defineProperty(frappe.query_reports, "Gross Profit", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it), Finance Book, Cost Center, Project, Sales Partner,
// Territory, Show Linked Delivery Notes, and Revaluation Journals filters from
// the Accounts Receivable report.
(function hideAccountsReceivableFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = {
		company: 1,
		finance_book: 1,
		cost_center: 1,
		project: 1,
		sales_partner: 1,
		territory: 1,
		show_delivery_notes: 1,
		for_revaluation_journals: 1,
	};
	var _stored = frappe.query_reports["Accounts Receivable"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}
	}

	Object.defineProperty(frappe.query_reports, "Accounts Receivable", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it), Finance Book, Cost Center, Project, Sales Partner,
// and Territory filters from the Accounts Receivable Summary report.
(function hideAccountsReceivableSummaryFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = {
		company: 1,
		finance_book: 1,
		cost_center: 1,
		project: 1,
		sales_partner: 1,
		territory: 1,
	};
	var _stored = frappe.query_reports["Accounts Receivable Summary"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}
	}

	Object.defineProperty(frappe.query_reports, "Accounts Receivable Summary", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it), Finance Book, Cost Center, Project, Sales Partner,
// Territory, Revaluation Journals, and Handle Employee Advances filters from
// the Accounts Payable report. (Accounts Payable has no Sales Partner /
// Territory filters, so those two entries are harmless no-ops here.)
(function hideAccountsPayableFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = {
		company: 1,
		finance_book: 1,
		cost_center: 1,
		project: 1,
		sales_partner: 1,
		territory: 1,
		for_revaluation_journals: 1,
		handle_employee_advances: 1,
	};
	var _stored = frappe.query_reports["Accounts Payable"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}
	}

	Object.defineProperty(frappe.query_reports, "Accounts Payable", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it), Finance Book, Cost Center, Project, Sales Partner,
// Territory, and Revaluation Journals filters from the Accounts Payable
// Summary report. (Accounts Payable Summary has no Sales Partner / Territory
// filters, so those two entries are harmless no-ops here.)
(function hideAccountsPayableSummaryFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = {
		company: 1,
		finance_book: 1,
		cost_center: 1,
		project: 1,
		sales_partner: 1,
		territory: 1,
		for_revaluation_journals: 1,
	};
	var _stored = frappe.query_reports["Accounts Payable Summary"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}
	}

	Object.defineProperty(frappe.query_reports, "Accounts Payable Summary", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();

// Hide Company (default it), Finance Book, Cost Center, and Project filters
// from the Cash Flow report.
(function hideCashFlowFilters() {
	frappe.provide("frappe.query_reports");
	var HIDDEN = { company: 1, finance_book: 1, cost_center: 1, project: 1 };
	var _stored = frappe.query_reports["Cash Flow"];

	function patch(def) {
		if (def && Array.isArray(def.filters)) {
			def.filters = def.filters.map(function (f) {
				if (HIDDEN[f.fieldname]) {
					f.hidden = 1;
					if (f.fieldname === "company") {
						f.default = frappe.defaults.get_default("company");
					}
				}
				return f;
			});
		}
	}

	Object.defineProperty(frappe.query_reports, "Cash Flow", {
		configurable: true,
		get: function () { return _stored; },
		set: function (def) { patch(def); _stored = def; },
	});

	if (_stored) patch(_stored);
})();
