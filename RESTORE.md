# PT. Tunas Maju Jaya — Backup & Restore Runbook

How to stand up the `tmj.localhost` site on a client machine. Most of the
client's customization lives **in the site database**, not in this app's code, so
a working handover is **full-site-backup restore + this app installed** — *not* a
fresh `bench install-app tmj` (that alone reproduces almost none of it).

## What lives where

| Layer | Carried by |
|---|---|
| Desk CSS/JS overrides, sidebar boot filter, invoice-status relabel JS | this app (git) |
| "PT. Tunas Maju Jaya" workspace + sidebar + desktop icon | app fixtures **and** DB |
| Number Cards / Dashboard Charts the workspace renders | **DB only** |
| Hidden doctypes (Custom DocPerm), custom Reports, Client/Server Scripts, Print Format, Property Setters, custom field | **DB only** |
| Branding images (App Logo, Splash) | **DB-linked files** (in the `-files.tar`) |
| All business data (companies, customers, invoices, items, …) | **DB only** |

## Environment parity (must match the source)

- Frappe **v16.22.0**
- ERPNext **v16.22.0**
- `tmj` app — https://github.com/Bryantant/TMJ , branch `main`
- MariaDB (same major version as source)

## Backup artifacts

Produced by `bench --site tmj.localhost backup --with-files`, found under
`sites/tmj.localhost/private/backups/`. A complete set is four files sharing a
timestamp prefix (e.g. `20260615_231534-tmj_localhost-…`):

- `…-database.sql.gz` — the database
- `…-files.tar` — public files (**includes the branding images**)
- `…-private-files.tar` — private files
- `…-site_config_backup.json` — original db name/password + installed_apps

> Always hand over the **whole timestamped set**, and confirm the config snapshot
> reads `"installed_apps": ["frappe", "erpnext", "tmj"]`. Backups predating the
> June 2026 `hicom16 → tmj` rename say `hicom16` and must **not** be used.

## Restore on the client machine

```bash
# 1. Bench with matching Frappe (init pins the version-16 branch; verify 16.22.0)
bench init --frappe-branch version-16 benchv16
cd benchv16

# 2. Pull the two apps into the bench (code only)
bench get-app --branch version-16 erpnext
bench get-app https://github.com/Bryantant/TMJ tmj
#   Confirm versions match the source before restoring:
#   cat apps/frappe/frappe/__init__.py | grep __version__   # 16.22.0
#   cat apps/erpnext/erpnext/__init__.py | grep __version__ # 16.22.0

# 3. Create an empty target site
bench new-site tmj.localhost            # set Administrator + MariaDB root password when prompted

# 4. Restore DB + files over it (point paths at the handed-over backup set)
bench --site tmj.localhost --force restore \
  /path/to/20260615_231534-tmj_localhost-database.sql.gz \
  --with-public-files  /path/to/20260615_231534-tmj_localhost-files.tar \
  --with-private-files /path/to/20260615_231534-tmj_localhost-private-files.tar

# 5. Apply schema, rebuild assets, clear cache
bench --site tmj.localhost migrate
bench build
bench --site tmj.localhost clear-cache
```

## Post-restore verification

```bash
bench --site tmj.localhost list-apps          # expect: frappe, erpnext, tmj
bench --site tmj.localhost console <<'PY'
import frappe
print("Workspace:", frappe.db.exists("Workspace", "PT. Tunas Maju Jaya"))
print("Sidebar:",   frappe.db.exists("Workspace Sidebar", "PT. Tunas Maju Jaya"))
print("Charts:",    frappe.db.exists("Dashboard Chart", "Outgoing Bills (Sales Invoice)"))
print("Cards:",     frappe.db.exists("Number Card", "Total Outgoing Bills"))
PY
```

Then log in and confirm: the **PT. Tunas Maju Jaya** workspace is the landing page
with its Quick Actions + Overview charts, non-admin users see only that workspace,
the company **logo** shows on the home tile and sidebar header, and Sales/Purchase
Invoice statuses display as **"Submitted"**.

## Production hardening (optional, recommended on client site)

```bash
bench --site tmj.localhost set-config developer_mode 0
bench --site tmj.localhost clear-cache
```

Turning `developer_mode` off stops accidental DocType edits and fixture re-exports
on the production machine.

## Rebuilding from scratch (NOT the handover path — reference only)

This app's `patches/v0_0/` generators (hide doctypes, build the workspace, restrict
roles) are **not** registered in `patches.txt`; they run manually via
`bench --site <site> execute tmj.patches.v0_0.<module>.execute`. They recreate the
*structure* but **not** the DB-only assets above or any business data. Use the
backup-restore path for handover.
