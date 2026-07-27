"""Fix stale default filters on the 4 client Custom Reports (is_standard=No):
Sales Report Summary, Sales Report Detail, Purchase Report Summary, Purchase
Report Detail.

Their saved `json.filters` pointed at company "PT. Tunas Maju Jaya" (the
company's old name, pre-rename — no longer exists) and a from_date/to_date
stuck in 2026-05-15..2026-06-15. Result: every report opened from the sidebar
showed "No record found" regardless of real data. Repoint to the current
company and a rolling "this month to date" range. Preserves each report's
`columns` untouched — only the `filters` key of the `json` field is replaced.

    bench --site tmj.localhost execute tmj.patches.v0_0.fix_custom_report_default_filters.execute
"""

import json

import frappe

REPORTS = [
	"Sales Report Summary",
	"Sales Report Detail",
	"Purchase Report Summary",
	"Purchase Report Detail",
]
COMPANY = "PT. Tunas Mitra Jaya"


def execute():
	today = frappe.utils.nowdate()
	from_date = frappe.utils.data.get_first_day(today).strftime("%Y-%m-%d")

	for report_name in REPORTS:
		doc = frappe.get_doc("Report", report_name)
		config = json.loads(doc.json or "{}")
		config["filters"] = {
			"company": COMPANY,
			"from_date": from_date,
			"to_date": today,
		}
		doc.db_set("json", json.dumps(config), update_modified=True)

	frappe.db.commit()
	print(f"Updated default filters on {REPORTS} -> company={COMPANY}, from_date={from_date}, to_date={today}")
