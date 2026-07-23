# TMJ Backup (Mac) → Restore on Client's Windows PC (local, Docker Desktop/WSL2)

This is a **companion** to [`RESTORE.md`](RESTORE.md), not a replacement. Use this guide when the target is the **client's own Windows PC** — the site runs **locally** on that machine (accessed as `http://tmj.localhost:8080`), with **no public domain and no HTTPS/Traefik**. If the client instead wants the site reachable over the internet from a Linux VPS with a real domain, follow `RESTORE.md` instead.

Like `RESTORE.md`, this is a **full database + files restore**, not a fresh `bench install-app tmj` — almost all of PT. Tunas Mitra Jaya's customization (4 custom Reports, Client/Server Scripts, Print Format, ~289 Property Setters, Number Cards, Dashboard Charts, Custom DocPerms, business data, branding images) lives in the **database and files**, not in the app's Python code. The `tmj` app's `patches/v0_0/` are not registered in `patches.txt`, so they never self-run on install — only a real restore reproduces them.

Confirmed on this Mac (2026-07-13): **Frappe 16.22.0 / ERPNext 16.22.0 / tmj 0.0.1**, site `tmj.localhost`, app repo `https://github.com/Bryantant/TMJ` branch `main`.

---

## 0. Shape of the job

| | Mac (this computer) | Client's Windows PC |
| --- | --- | --- |
| Role | Source — produce the backup | Target — restore into a local Docker stack |
| What you do | `bench backup --with-files`, push app code to GitHub | Install Docker Desktop, build the image, restore the backup |
| Transport | — | The 3 backup files, carried over on a USB drive or encrypted transfer |

Because the `tmj` repo is **public**, the Windows machine builds its own image straight from GitHub — you do **not** need to export/transfer a multi-GB Docker image from the Mac. Only the small backup files travel.

### 0.5 Remote access via AnyDesk

This whole restore is done on the client's PC over **AnyDesk**, not in person. A few things to set up/know before starting:

- **Unattended Access must already be configured** on the client's PC before you begin (client installs AnyDesk once, sets a fixed access password, and enables *Security → Unattended Access* in AnyDesk's settings). Without this you cannot reconnect after the reboots in Part B, and you cannot approve Windows UAC/elevation prompts remotely — both are required by this guide.
- **UAC/elevation prompts** (e.g. "Run PowerShell as Administrator", the Docker Desktop installer) render on the remote screen through Unattended Access and can be clicked normally from your side — the client does not need to be physically present to approve them.
- **Reboots disconnect the AnyDesk session, not the remote PC.** `wsl --install` and the Docker Desktop installer both trigger a restart. AnyDesk will show "disconnected" — wait ~1–3 minutes for Windows to come back up, then reconnect with the same unattended-access credentials. Nothing needs to happen on the client's end.
- **Enable clipboard synchronization** (AnyDesk toolbar → clipboard icon, or `Ctrl+Shift+C`/`Ctrl+Shift+V`) so you can paste the multi-line bash commands below into the Ubuntu (WSL2) terminal instead of retyping them.
- **Long-running steps (the `docker build` in Part C) keep running even if AnyDesk briefly drops** — unlike an SSH session, an AnyDesk session is a real remote desktop login, not a shell attached to your connection, so a dropped viewer connection doesn't kill the build. Just reconnect and check on it.

---

## PART A — On the Mac: take the backup

### A.1 Push app code

The image is built from the GitHub repo, not from this Mac's working copy — anything uncommitted/unpushed will be missing from the restored site's app code (though not from the DB, which carries the rest).

```bash
cd /Users/bryantantonio/Dev/benchv16/apps/tmj
git status                     # make sure nothing important is uncommitted
git push origin main
```

### A.2 Take a fresh backup

> ⚠️ The backup already sitting in `sites/tmj.localhost/private/backups/` is dated **2026-06-15** — almost a month stale relative to today. Don't hand that one over; take a new one.

```bash
cd /Users/bryantantonio/Dev/benchv16
bench --site tmj.localhost backup --with-files
```

`--with-files` is required — a DB-only backup misses the branding images (App Logo / Splash Image) that live under `public/files`.

This produces four files under `sites/tmj.localhost/private/backups/`, named with a fresh timestamp `YYYYMMDD_HHMMSS`:

| File | Contents | Needed for restore? |
| --- | --- | --- |
| `<ts>-tmj_localhost-database.sql.gz` | Full DB — all customization + business data | Yes |
| `<ts>-tmj_localhost-files.tar` | Public files (incl. branding logo/splash) | Yes |
| `<ts>-tmj_localhost-private-files.tar` | Private uploads | Yes |
| `<ts>-tmj_localhost-site_config_backup.json` | Source `db_name`/`db_password` snapshot | **No — do not carry this one over** |

### A.3 Transfer only the 3 needed files

**Do not include `…-site_config_backup.json` in the transfer.** It contains the source site's DB password in cleartext (confirmed above: this Mac's site config has real `db_password`/`db_name` values redacted from the excerpt shown to you, but present in the raw file) and isn't consumed by `bench restore` anyway.

```bash
cd sites/tmj.localhost/private/backups
zip tmj-handover-<date>.zip \
  <ts>-tmj_localhost-database.sql.gz \
  <ts>-tmj_localhost-files.tar \
  <ts>-tmj_localhost-private-files.tar
```

Since you're connected to the client's PC over AnyDesk, send it through AnyDesk's built-in **File Transfer** feature rather than email/Slack (this is the entire business database) or a physical USB drive (you're remote, there's no drive to plug in):

1. In the AnyDesk session, open **File Transfer** (toolbar icon, or the session's side menu).
2. Left pane = this Mac → browse to `sites/tmj.localhost/private/backups/` and select `tmj-handover-<date>.zip`.
3. Right pane = the client's PC → navigate to `C:\Users\<client-user>\Downloads\` and send it across.

AnyDesk's file transfer is TLS-encrypted end-to-end, so the zip doesn't need a separate encryption layer for the trip — just don't leave a copy sitting in a shared/public folder on either machine afterward. Total size is small (last backup was ~1.7 MB combined).

Once it lands in `C:\Users\<client-user>\Downloads\`, unzip it from the Ubuntu (WSL2) terminal — Windows drives are mounted under `/mnt/c/...`:

```bash
cd /mnt/c/Users/<client-user>/Downloads
unzip tmj-handover-<date>.zip -d tmj-handover
```

> If AnyDesk's File Transfer panel is greyed out, check *Security → File Transfer* is enabled in the client's AnyDesk settings — it's a separate permission from Unattended Access.

---

## PART B — On the Windows PC: prepare Docker

### B.1 Prerequisites

- **Windows 10 (2004+) or Windows 11**, 64-bit, admin rights on the account doing the install.
- Virtualization enabled in BIOS/UEFI (usually already on for a modern business PC).
- At least ~10 GB free disk for the image + containers.

### B.2 Install WSL2 + Docker Desktop

1. Open **PowerShell as Administrator** (the UAC prompt renders through AnyDesk's Unattended Access — see Part 0.5 — approve it directly) and run:
   ```powershell
   wsl --install
   ```
   This installs WSL2 and a default Ubuntu distro. **Restart the PC** when prompted.
   > This drops your AnyDesk session, not the client's account. Wait ~1–3 minutes for Windows to finish rebooting, then reconnect with the unattended-access credentials — no action needed from the client.
2. On reboot, Ubuntu finishes setup and asks you to create a UNIX username/password for that WSL2 distro (separate from the Windows login — pick anything, write it down).
3. Download and install **Docker Desktop for Windows**: https://www.docker.com/products/docker-desktop/ — this installer also triggers a restart; expect the same AnyDesk disconnect/reconnect as step 1.
4. During/after install, open Docker Desktop → **Settings → General** → confirm **"Use the WSL 2 based engine"** is checked. Settings → Resources → WSL Integration → make sure it's enabled for the Ubuntu distro.
5. Start Docker Desktop and wait for the whale icon in the system tray to show "Docker Desktop is running."

### B.3 Do everything else from the Ubuntu (WSL2) terminal

Open the **Ubuntu** app from the Start menu (search "Ubuntu"). This gives a normal bash shell with the `docker` and `docker compose` CLIs already wired to Docker Desktop — every command below is the **same bash syntax used on the Mac**, no PowerShell translation needed.

```bash
docker version          # confirm client + server both respond
docker compose version
```

If `docker` isn't found inside Ubuntu, re-check Docker Desktop → Settings → Resources → WSL Integration.

---

## PART C — Build the image (frappe + erpnext + tmj) on the Windows PC

This mirrors `RESTORE.md` §5, but built natively (Windows PCs are x86_64, same as the target — **no `--platform=linux/amd64` cross-emulation needed**, unlike building on this Apple Silicon Mac).

### C.1 Get frappe_docker

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
mkdir -p ~/gitops
```

### C.2 Create `apps.json`

```bash
cat > apps.json <<'EOF'
[
  { "url": "https://github.com/frappe/erpnext", "branch": "version-16" },
  { "url": "https://github.com/Bryantant/TMJ",   "branch": "main" }
]
EOF
```

The `tmj` repo is public, so this plain URL works with no token.

### C.3 Build

```bash
docker build \
  --no-cache \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=apps.json \
  --tag=tmj-erpnext:v16.22.0 \
  --file=images/layered/Containerfile .
```

(No `--platform` flag: this builds for the machine's own architecture. If the client's PC is ARM — very unlikely for a business desktop/laptop — add `--platform=linux/arm64`.)

### C.4 Verify the build

```bash
docker run --rm tmj-erpnext:v16.22.0 \
  cat apps/frappe/frappe/__init__.py \
      apps/erpnext/erpnext/__init__.py \
      apps/tmj/tmj/__init__.py | grep __version__
# expect: frappe 16.22.0, erpnext 16.22.0, tmj 0.0.1

docker run --rm tmj-erpnext:v16.22.0 \
  ls -la /home/frappe/frappe-bench/assets/tmj/
# expect a hashed desk_overrides.bundle.<hash>.js and css/custom.css
```

If frappe/erpnext isn't `16.22.0`, the branch pin drifted since this doc was written — rebuild with `FRAPPE_BRANCH=v16.22.0` and `"branch": "v16.22.0"` for erpnext in `apps.json` instead.

---

## PART D — Configure for local access (no HTTPS, no domain)

This is the main way this setup differs from `RESTORE.md`: **skip the `compose.https.yaml` override entirely** — no Traefik, no Let's Encrypt, no `SITES_RULE`. The `frontend` service in the base `compose.yaml` already publishes a plain HTTP port directly.

### D.1 `.env`

```bash
cp example.env ~/gitops/tmj.env
```

Edit `~/gitops/tmj.env`:

```dotenv
ERPNEXT_VERSION=v16.22.0

CUSTOM_IMAGE=tmj-erpnext
CUSTOM_TAG=v16.22.0
PULL_POLICY=never                 # use the local build

DB_PASSWORD=<pick-a-strong-local-password>

# Local access — no domain, no HTTPS
HTTP_PUBLISH_PORT=8080
FRAPPE_SITE_NAME_HEADER=tmj.localhost
```

`FRAPPE_SITE_NAME_HEADER` is what makes this work without a real domain: it pins the nginx `frontend` service to always route to the `tmj.localhost` site regardless of what Host header the browser sends, instead of the default `$host`-based multi-tenant routing that `SITES_RULE`/Traefik would otherwise handle.

### D.2 Generate compose (DB + Redis only — no `compose.https.yaml`)

```bash
docker compose --env-file ~/gitops/tmj.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  config > ~/gitops/docker-compose.yml

docker compose --project-name tmj -f ~/gitops/docker-compose.yml up -d
```

Wait for `configurator` to exit (0) and `db` to be healthy before the next step:

```bash
docker compose -p tmj ps
```

---

## PART E — Create the site and restore

```bash
BACKEND=$(docker compose -p tmj ps -q backend)

docker compose -p tmj exec -it backend \
  bench new-site --mariadb-user-host-login-scope=% \
  tmj.localhost
# omit --admin-password to be prompted interactively
```

Copy the 3 backup files in (this is where the zip unzipped to in Part A.3, over `/mnt/c/` from the AnyDesk file transfer):

```bash
SRC=/mnt/c/Users/<client-user>/Downloads/tmj-handover
BK=<ts>-tmj_localhost                  # the timestamp prefix from Part A.2
DEST=/home/frappe/frappe-bench/sites/tmj.localhost/private/backups

docker compose -p tmj exec backend mkdir -p "$DEST"
docker cp "$SRC/${BK}-database.sql.gz"   "$BACKEND:${DEST}/"
docker cp "$SRC/${BK}-files.tar"         "$BACKEND:${DEST}/"
docker cp "$SRC/${BK}-private-files.tar" "$BACKEND:${DEST}/"
```

Restore:

```bash
docker compose -p tmj exec backend \
  bench --site tmj.localhost --force restore \
  ${DEST}/${BK}-database.sql.gz \
  --with-public-files  ${DEST}/${BK}-files.tar \
  --with-private-files ${DEST}/${BK}-private-files.tar
  # add --db-root-password <value from tmj.env DB_PASSWORD> if prompted
```

```bash
docker compose -p tmj exec backend bench --site tmj.localhost list-apps
# expect: frappe  erpnext  tmj
```

---

## PART F — Post-restore configuration

Same hardening as `RESTORE.md` §10, run against `tmj.localhost` instead of a public domain:

```bash
# Apply framework/erpnext migrations for this image (tmj's own patches deliberately do
# NOT run here — they're not in patches.txt; the restore already brought that state).
docker compose -p tmj exec backend bench --site tmj.localhost migrate

# developer_mode: decide per client preference. The source Mac site has it ON (1) for
# dev convenience. For a client's day-to-day machine, OFF (0) is safer — it hides
# "Customize Form"/"Edit DocType" affordances from end users. Use -p so it's stored as
# a real int, not the string "0" (which Python treats as truthy).
docker compose -p tmj exec backend bench --site tmj.localhost set-config -p developer_mode 0

# Keep Server Scripts enabled — the "Website Settings Setup" Server Script depends on it.
docker compose -p tmj exec backend bench --site tmj.localhost set-config -p server_script_enabled 1

# Reset the Administrator password to something the client will actually use.
docker compose -p tmj exec -it backend bench --site tmj.localhost set-admin-password

# New/restored sites start with the scheduler OFF.
docker compose -p tmj exec backend bench --site tmj.localhost enable-scheduler

# Clear maintenance mode if the restore left it on.
docker compose -p tmj exec backend bench --site tmj.localhost set-maintenance-mode off

docker compose -p tmj exec backend bench use tmj.localhost
docker compose -p tmj exec backend bench --site tmj.localhost clear-cache
```

```bash
docker compose -p tmj -f ~/gitops/docker-compose.yml up -d --force-recreate
```

> **Encryption key caveat (same as `RESTORE.md`):** `bench new-site` generated a fresh `encryption_key` here — it will **not** decrypt anything encrypted at the source. Any Email Account password, integration API key/secret, or OAuth token must be **re-entered by hand** in the desk UI after restore. Back up the new key immediately:
> ```bash
> docker compose -p tmj exec backend bench --site tmj.localhost show-config | grep encryption_key
> ```
> Store it in a password manager — not next to the backup files.

---

## PART G — Make `tmj.localhost` resolve in the browser

Modern Windows (10 build 17093+/1803 and all of Windows 11) resolves any `*.localhost` hostname to `127.0.0.1` automatically — no hosts-file edit needed on a normal up-to-date PC. Try it first:

```
http://tmj.localhost:8080
```

If that doesn't load (some locked-down corporate DNS/network stacks override it), add it manually:

1. Open **Notepad as Administrator**.
2. Open `C:\Windows\System32\drivers\etc\hosts`.
3. Add a line: `127.0.0.1 tmj.localhost`
4. Save, then retry the URL.

This only makes the site reachable **from this PC**. If the client wants other machines on their office LAN to reach it too, that's a separate step (open the Windows Firewall for port 8080 and use this PC's LAN IP instead of `tmj.localhost`) — not covered here since it wasn't asked for.

---

## PART H — Verification checklist

### CLI

```bash
docker compose -p tmj exec backend bench version
# expect: frappe 16.22.0, erpnext 16.22.0, tmj 0.0.1

docker compose -p tmj exec backend bench --site tmj.localhost list-apps
docker compose -p tmj ps                    # all Up; configurator Exited 0
docker compose -p tmj logs backend          # no tracebacks
```

### `bench console` (`docker compose -p tmj exec -it backend bench --site tmj.localhost console`)

```python
import frappe
assert "tmj" in frappe.get_installed_apps()
assert frappe.db.exists("Workspace", "PT. Tunas Mitra Jaya")
assert frappe.db.count("Number Card") > 0
assert frappe.db.count("Dashboard Chart") > 0
assert frappe.db.exists("Server Script", "Website Settings Setup")
print("Property Setters:", frappe.db.count("Property Setter"))   # expect ~289
print("developer_mode:", repr(frappe.conf.get("developer_mode")))          # expect 0, not "0"
print("server_script_enabled:", frappe.conf.get("server_script_enabled")) # expect True/1
```

### In the browser (`http://tmj.localhost:8080`)

- Login lands on the **"PT. Tunas Mitra Jaya"** workspace with Number Cards/Dashboard Charts populated.
- Branding logo + splash image render.
- Payment-derived invoice statuses show the neutral **"Submitted"** label.
- A non-admin user only sees the PT. Tunas Mitra Jaya sidebar; unused doctypes stay hidden.
- Any re-entered Email Account/integration (Part F caveat) actually connects.

---

## PART I — Ongoing local backups on the client's PC

Once running, the client can back itself up the same way, from the Ubuntu (WSL2) terminal:

```bash
docker compose -p tmj exec backend bench --site tmj.localhost backup --with-files
```

Backups land inside the container's `sites/tmj.localhost/private/backups/` — copy them out with `docker cp` if you want a copy outside the container/WSL2 disk (e.g. onto an external drive) for real disaster recovery.

---

## Troubleshooting

| Symptom | Cause / Fix |
| --- | --- |
| `wsl --install` fails / "virtualization not enabled" | Enable virtualization (Intel VT-x / AMD-V) in BIOS/UEFI, then retry. |
| Docker Desktop says "WSL 2 installation is incomplete" | Run `wsl --update` in PowerShell, restart Docker Desktop. |
| `docker: command not found` inside Ubuntu | Docker Desktop → Settings → Resources → WSL Integration → enable for the Ubuntu distro, then restart Docker Desktop. |
| Build "succeeds" but image has no tmj | Confirm you used `--secret=id=apps_json,src=apps.json` (not the old `--build-arg APPS_JSON_BASE64=`). Re-run Part C.4's verification. |
| `http://tmj.localhost:8080` doesn't load, hosts-file edit didn't help either | Check `docker compose -p tmj ps` — `frontend` and `backend` must be `Up`. Check `HTTP_PUBLISH_PORT` in `tmj.env` matches the URL's port. |
| Port 8080 already in use on the Windows PC | Set a different `HTTP_PUBLISH_PORT` in `tmj.env` (e.g. `8090`), regenerate compose, `up -d` again, and use that port in the URL. |
| `Access denied` on `new-site`/`restore` | `--db-root-password` must equal `tmj.env`'s `DB_PASSWORD`. Test inside `backend`: `mysql -uroot -p -hdb`. |
| Encrypted secrets blank / "decrypt failed" after restore | Expected — fresh `encryption_key` (Part F). Re-enter Email Account passwords / integration keys / OAuth tokens by hand. |
| `developer_mode` still effectively ON | You ran `set-config developer_mode 0` **without `-p`** — that stores the string `"0"`, which Python treats as truthy. Re-run with `-p`. |
| Windows Defender/antivirus flags the WSL2 Ubuntu disk or Docker VM | Add an exclusion for `\\wsl$\` and Docker Desktop's data directory (`%LOCALAPPDATA%\Docker`) if scans are slowing builds/restores — a common false-positive on VM disk files. |
| AnyDesk disconnects during `wsl --install` or the Docker Desktop restart | Expected — the restart drops the AnyDesk session, not the PC. Wait ~1–3 min, then reconnect with the unattended-access credentials (Part 0.5). |
| UAC/elevation prompt doesn't appear, or you can't click it, over AnyDesk | Unattended Access isn't enabled, or the client is on an outdated AnyDesk build. Confirm *Security → Unattended Access* is on with a fixed password set, before attempting any step that needs elevation. |
| Can't paste multi-line commands into the Ubuntu terminal | Enable clipboard synchronization in the AnyDesk toolbar, or use `Ctrl+Shift+V`. |
| AnyDesk File Transfer panel is greyed out | *Security → File Transfer* isn't enabled in the client's AnyDesk settings — it's a separate permission from Unattended Access. |
