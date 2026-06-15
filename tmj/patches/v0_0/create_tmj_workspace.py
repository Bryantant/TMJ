"""Create the consolidated "PT. Tunas Maju Jaya" workspace + sidebar.

A single Frappe Books-style workspace that surfaces only the ACTIVE (not
System-Manager-only) doctypes and reports, so the client has one simple entry
point instead of jumping between Buying / Selling / Stock / Invoicing /
Financial Reports.

Idempotent: deletes any existing copy first, then recreates. Re-runnable via
    bench --site tmj.localhost execute tmj.patches.v0_0.create_tmj_workspace.execute
Always follow with `bench --site tmj.localhost clear-cache`.
"""

from json import dumps

import frappe

WS = "PT. Tunas Maju Jaya"
MODULE = "Hicom System"

# --- Dashboard landing content (blocks reference shortcuts/charts/number cards) ---
CONTENT = [
	{"id": "qa_hdr", "type": "header", "data": {"text": '<span class="h4"><b>Quick Actions</b></span>', "col": 12}},
	{"id": "sc_si", "type": "shortcut", "data": {"shortcut_name": "New Sales Invoice", "col": 3}},
	{"id": "sc_pi", "type": "shortcut", "data": {"shortcut_name": "New Purchase Invoice", "col": 3}},
	{"id": "sc_pay", "type": "shortcut", "data": {"shortcut_name": "New Payment", "col": 3}},
	{"id": "sc_sb", "type": "shortcut", "data": {"shortcut_name": "Stock Balance", "col": 3}},
	{"id": "sp1", "type": "spacer", "data": {"col": 12}},
	{"id": "ov_hdr", "type": "header", "data": {"text": '<span class="h4"><b>Overview</b></span>', "col": 12}},
	{"id": "ch_out", "type": "chart", "data": {"chart_name": "Outgoing Bills (Sales Invoice)", "col": 6}},
	{"id": "ch_in", "type": "chart", "data": {"chart_name": "Incoming Bills (Purchase Invoice)", "col": 6}},
	{"id": "nc_out", "type": "number_card", "data": {"number_card_name": "Total Outgoing Bills", "col": 6}},
	{"id": "nc_in", "type": "number_card", "data": {"number_card_name": "Total Incoming Bills", "col": 6}},
]

SHORTCUTS = [
	{"type": "DocType", "label": "New Sales Invoice", "link_to": "Sales Invoice", "doc_view": "New", "color": "#29CD42"},
	{"type": "DocType", "label": "New Purchase Invoice", "link_to": "Purchase Invoice", "doc_view": "New", "color": "#5E64FF"},
	{"type": "DocType", "label": "New Payment", "link_to": "Payment Entry", "doc_view": "New", "color": "#00BCD4"},
	{"type": "Report", "label": "Stock Balance", "link_to": "Stock Balance", "color": "#FF8C00"},
]

CHARTS = ["Outgoing Bills (Sales Invoice)", "Incoming Bills (Purchase Invoice)"]
NUMBER_CARDS = ["Total Outgoing Bills", "Total Incoming Bills"]

# --- Sidebar layout: (Section, icon, keep_closed, [ (label, link_type, link_to, filters, icon) ... ]) ---
# Icons use the modern Frappe icon set; ERPNext-standard icons where they exist.
SECTIONS = [
	("Sales", "sell", 0, [
		("Sales Invoice", "DocType", "Sales Invoice", None, "receipt"),
		("Customer", "DocType", "Customer", None, "customer"),
		("Sales Payments", "DocType", "Payment Entry", [["Payment Entry", "payment_type", "=", "Receive"]], "banknote-arrow-down"),
	]),
	("Purchases", "buying", 0, [
		("Purchase Invoice", "DocType", "Purchase Invoice", None, "liabilities"),
		("Supplier", "DocType", "Supplier", None, "truck"),
		("Purchase Payments", "DocType", "Payment Entry", [["Payment Entry", "payment_type", "=", "Pay"]], "banknote-arrow-up"),
	]),
	("Stock", "stock", 0, [
		("Stock Entry", "DocType", "Stock Entry", None, "stock"),
		("Stock Reconciliation", "DocType", "Stock Reconciliation", None, "clipboard-list"),
		("Warehouse", "DocType", "Warehouse", None, "warehouse"),
	]),
	("Items", "tag", 0, [
		("Item", "DocType", "Item", None, "box"),
		("Item Group", "DocType", "Item Group", None, "boxes"),
		("Price List", "DocType", "Price List", None, "tags"),
		("Item Price", "DocType", "Item Price", None, "tag"),
		("Unit of Measure (UOM)", "DocType", "UOM", None, "ruler"),
	]),
	("Accounting", "accounting", 0, [
		("Journal Entry", "DocType", "Journal Entry", None, "book"),
		("Payment Entry", "DocType", "Payment Entry", None, "payments"),
		("Chart of Accounts", "DocType", "Account", None, "list-tree"),
	]),
	("Financial Reports", "reports", 0, [
		("General Ledger", "Report", "General Ledger", None, "book-open-text"),
		("Accounts Receivable", "Report", "Accounts Receivable", None, "banknote-arrow-down"),
		("Accounts Payable", "Report", "Accounts Payable", None, "banknote-arrow-up"),
		("Profit and Loss Statement", "Report", "Profit and Loss Statement", None, "trending-up"),
		("Balance Sheet", "Report", "Balance Sheet", None, "scale"),
		("Trial Balance", "Report", "Trial Balance", None, "calculator"),
		("Cash Flow", "Report", "Cash Flow", None, "arrow-left-right"),
		("Gross Profit", "Report", "Gross Profit", None, "percent"),
		("Customer Ledger Summary", "Report", "Customer Ledger Summary", None, "customer"),
		("Supplier Ledger Summary", "Report", "Supplier Ledger Summary", None, "truck"),
		("Sales Register", "Report", "Sales Register", None, "table-view"),
		("Purchase Register", "Report", "Purchase Register", None, "table-view"),
	]),
	("Stock Reports", "reports", 1, [
		("Stock Ledger", "Report", "Stock Ledger", None, "book-open-text"),
		("Stock Balance", "Report", "Stock Balance", None, "package"),
		("Stock Projected Qty", "Report", "Stock Projected Qty", None, "trending-up"),
		("Stock Ageing", "Report", "Stock Ageing", None, "calendar-clock"),
		("Stock Analytics", "Report", "Stock Analytics", None, "chart"),
		("Item Shortage Report", "Report", "Item Shortage Report", None, "clipboard-list"),
		("Warehouse Wise Stock Balance", "Report", "Warehouse Wise Stock Balance", None, "warehouse"),
	]),
	("Sales & Purchase Reports", "reports", 1, [
		("Sales Analytics", "Report", "Sales Analytics", None, "chart"),
		("Item-wise Sales History", "Report", "Item-wise Sales History", None, "table-view"),
		("Purchase Analytics", "Report", "Purchase Analytics", None, "chart"),
		("Item-wise Purchase History", "Report", "Item-wise Purchase History", None, "table-view"),
	]),
	("Setup", "settings", 1, [
		("Company", "DocType", "Company", None, "organization"),
		("Mode of Payment", "DocType", "Mode of Payment", None, "credit-card"),
		("Payment Term", "DocType", "Payment Term", None, "calendar"),
		("Accounts Settings", "DocType", "Accounts Settings", None, "accounting"),
		("Selling Settings", "DocType", "Selling Settings", None, "sell"),
		("Buying Settings", "DocType", "Buying Settings", None, "settings"),
		("Stock Settings", "DocType", "Stock Settings", None, "stock"),
	]),
]


def execute():
	for di in frappe.get_all("Desktop Icon", filters={"link_to": WS}, pluck="name"):
		frappe.delete_doc("Desktop Icon", di, force=True, ignore_permissions=True)
	frappe.delete_doc_if_exists("Workspace Sidebar", WS)
	frappe.delete_doc_if_exists("Workspace", WS)

	_create_workspace()
	_create_sidebar()
	_create_desktop_icon()

	# Per-user Desktop Layout records are snapshots of the home icon grid taken
	# when the user last arranged it; they do NOT auto-include icons added later.
	# Clear them so every user's grid regenerates from frappe.boot.desktop_icons
	# (admin: all icons + the new one; client: boot.py filters to just this one).
	frappe.db.delete("Desktop Layout")

	frappe.db.commit()
	print(f"Created workspace + sidebar + desktop icon: {WS} (reset Desktop Layouts)")


def _create_workspace():
	ws = frappe.new_doc("Workspace")
	ws.title = WS
	ws.label = WS
	ws.type = "Workspace"
	ws.public = 1
	ws.app = "tmj"
	ws.module = MODULE
	ws.icon = "getting-started"
	ws.indicator_color = "blue"
	ws.content = dumps(CONTENT)

	for sc in SHORTCUTS:
		ws.append("shortcuts", sc)
	for chart in CHARTS:
		ws.append("charts", {"chart_name": chart, "label": chart})
	for nc in NUMBER_CARDS:
		ws.append("number_cards", {"number_card_name": nc, "label": nc})

	ws.insert(ignore_permissions=True)


def _create_sidebar():
	sb = frappe.new_doc("Workspace Sidebar")
	sb.title = WS
	sb.header_icon = "getting-started"
	sb.standard = 0
	sb.app = "tmj"

	# Dashboard landing link (top level)
	sb.append("items", {
		"type": "Link", "label": "Dashboard", "link_type": "Workspace",
		"link_to": WS, "icon": "dashboard", "child": 0,
	})

	for label, icon, keep_closed, children in SECTIONS:
		sb.append("items", {
			"type": "Section Break", "label": label, "icon": icon,
			"collapsible": 1, "keep_closed": keep_closed, "child": 0,
		})
		for clabel, link_type, link_to, filters, child_icon in children:
			row = {
				"type": "Link", "label": clabel, "link_type": link_type,
				"link_to": link_to, "icon": child_icon, "child": 1,
			}
			if filters:
				row["filters"] = dumps(filters)
			sb.append("items", row)

	sb.insert(ignore_permissions=True)


def _create_desktop_icon():
	"""Surface the workspace in the home grid / switcher (frappe.boot.desktop_icons).

	Creating a Workspace + Sidebar does NOT auto-create this; desktop_icons is
	backed by the Desktop Icon doctype. standard=1 so it shows for all users
	(the boot.py OPEN_WORKSPACES filter then scopes it to non-admins).
	"""
	icon = frappe.new_doc("Desktop Icon")
	icon.label = WS
	icon.icon_type = "Link"
	icon.link_type = "Workspace Sidebar"
	icon.link_to = WS
	icon.icon = "getting-started"
	icon.standard = 1
	icon.app = "tmj"
	icon.idx = 0
	icon.insert(ignore_permissions=True, ignore_if_duplicate=True)
