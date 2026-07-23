# TMJ Production Restore Runbook (frappe_docker, single server, HTTPS)

This runbook restores a **PT. Tunas Mitra Jaya** ERPNext site onto a **Docker production deployment** built on the official [`frappe/frappe_docker`](https://github.com/frappe/frappe_docker), running on a **single server** with **HTTPS terminated by Traefik (Let's Encrypt)**.

The source was a local Frappe **bench v16 dev site** named `tmj.localhost`. The handover is **not** a fresh install: it is a **full database + files restore** (the `20260615_231534-tmj_localhost-*` backup set) into a **custom Docker image** that bakes in `frappe`, `erpnext`, and the custom **`tmj`** app (module label "Hicom System"). All versions are pinned to **Frappe 16.22.0 / ERPNext 16.22.0**. The placeholder production domain throughout is `erp.example.com` — the client picks the real one.

> **Note on doc paths:** `frappe_docker` reorganized its docs into numbered folders (`docs/02-setup/…`, `docs/03-production/…`, `docs/04-operations/…`). Old flat paths (`docs/custom-apps.md`, etc.) now 404. Citations below use the current `main` paths.

---

## 1. Why a full restore (not a fresh install)

The client's real value lives in the **database and files**, not in the app's Python code. Installing the `tmj` app onto a fresh site reproduces almost none of it, because **the app's patches are not registered in `patches.txt`** — they do not self-bootstrap on install.

| Customization | Where it lives | Reproduced by fresh `install-app tmj`? |
| --- | --- | --- |
| 4 custom Reports | Database | No |
| Client Script | Database | No |
| Server Script ("Website Settings Setup") | Database | No |
| Custom Print Format | Database | No |
| ~289 Property Setters | Database | No |
| Number Cards & Dashboard Charts (workspace renders these) | Database | No |
| Custom DocPerms (hide unused doctypes) | Database | No |
| All business data | Database | No |
| Branding logo + splash images | **Public files** (`-files.tar`) | No |
| `tmj` app code + desk assets (`desk_overrides.bundle.js`, `custom.css`) | **App code in image** | Yes (this is why we still bake the app in) |

**Conclusion:** the handover requires **both** — the `tmj` app **code present in the image** AND a **DB + files restore** of the backup into that site. One without the other is incomplete.

---

## 2. What lives where

| Layer | Contents | How it gets onto production |
| --- | --- | --- |
| **App code** | `frappe`, `erpnext`, `tmj` Python/JS, built assets (`desk_overrides.bundle.js`, `custom.css`) | Baked into the **custom Docker image** at build time (`bench init` compiles assets) |
| **DB-only** | Reports, Client/Server Scripts, Print Format, ~289 Property Setters, Number Cards, Dashboard Charts, Custom DocPerms, business data | **`bench restore`** of `…-database.sql.gz` |
| **Files** | Branding logo, splash images (public); private uploads | **`bench restore --with-public-files / --with-private-files`** |

---

## 3. Prerequisites

- A **Linux server** (x86_64 / amd64 — `frappe_docker`'s `compose.yaml` pins `platform: linux/amd64` on every service).
- **Docker Engine v23.0+** (BuildKit is the default builder — required for the `--secret` build mechanism) and **Docker Compose v2**.
- A **domain** (`erp.example.com`) with a **DNS A-record pointing at the server's public IP**, set up **before** bringing up the HTTPS stack (Let's Encrypt HTTP-01 validation needs it reachable).
- **Ports 80 and 443** open/free on the host (Traefik publishes both; ACME + HTTP→HTTPS redirect).
- The **four backup files** (all share the `20260615_231534` timestamp prefix):
  - `20260615_231534-tmj_localhost-database.sql.gz` — the database (~1.4M)
  - `20260615_231534-tmj_localhost-files.tar` — public files, **includes branding logo + splash images** (~286K)
  - `20260615_231534-tmj_localhost-private-files.tar` — private files (~3.5K)
  - `20260615_231534-tmj_localhost-site_config_backup.json` — source db name/password + `installed_apps` snapshot (`["frappe","erpnext","tmj"]`). **Not fed to `bench restore`** (the restore does not consume it). **⚠️ SECRET-BEARING:** this JSON contains the source site's **cleartext DB password** (`"db_password": "<REDACTED>"`) and `"developer_mode": 1`. Treat the whole handover bundle as a secret-bearing artifact — do **not** email it, drop it in shared storage, or commit it unredacted. Either **exclude this file from the handover** (it is not needed for restore) or **redact** `db_password`/`db_name`/`db_user` before transfer, and **destroy** the source bundle once the restore is verified. The source DB password **must NOT be reused on production** — production's MariaDB root password is the new strong `.env` `DB_PASSWORD`, and per-site db passwords are regenerated automatically by `bench new-site` / `bench restore`.
- Exact target versions: **Frappe `16.22.0`**, **ERPNext `16.22.0`**.
- **MariaDB compatibility:** the restore lands in a containerized MariaDB (`overrides/compose.mariadb.yaml`). ERPNext v16 expects **MariaDB 10.6+** with **`utf8mb4` / `utf8mb4_unicode_ci`**. Confirm/pin the bundled `db` service to a v16-supported release (frappe_docker's mariadb override currently uses a compatible tag); if `bench restore` errors on collation, set the dump/db charset to `utf8mb4` before retrying. See also §6.
- The public custom-app repo: **`https://github.com/Bryantant/TMJ`**, branch **`main`** (declares `name = "tmj"`). Public → clones over HTTPS with **no token**. (If it is ever made private, see §5's PAT note.)

---

## 4. Step 1 — Get frappe_docker

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
mkdir -p ~/gitops   # holds the generated compose file + env files (keep private — secrets inside)
```

---

## 5. Step 2 — Build the custom image (frappe + erpnext + tmj)

### 5.1 Create `apps.json` in the `frappe_docker` repo root

`apps.json` is a JSON **array of `{url, branch}` objects**. **Do NOT list `frappe`** here — frappe comes from the `FRAPPE_PATH` / `FRAPPE_BRANCH` build-args. List **erpnext + tmj**:

```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-16"
  },
  {
    "url": "https://github.com/Bryantant/TMJ",
    "branch": "main"
  }
]
```

> **The `tmj` repo is public** → the plain `https://github.com/Bryantant/TMJ` URL works with no token.
>
> **Private-repo fallback (only if `TMJ` is ever made private):** embed a fine-grained, read-only, single-repo GitHub **PAT** in the clone URL inside `apps.json`:
> `{ "url": "https://<github-username>:<PAT>@github.com/Bryantant/TMJ", "branch": "main" }`
> Because `apps.json` is passed as a **BuildKit secret** (next step), the token never lands in `docker image history` or any image layer. Rotate the PAT after the build. *(In-URL PAT form is the standard git/bench convention; `frappe_docker`'s `docs/02-setup/02-build-setup.md` documents the secret mechanism generically — confirm the exact form against frappe_docker main.)*

### 5.2 apps.json is a SECRET, not base64

> **Heads-up:** older `frappe_docker` checkouts and most blog tutorials used `--build-arg APPS_JSON_BASE64=$(base64 -w 0 apps.json)`. **That mechanism has been removed from current `main`** — `apps.json` is now passed as a BuildKit **secret** (`--secret=id=apps_json,src=apps.json`), and the docs warn: *"Do not use `--build-arg` for `apps.json` — build arguments are permanently visible via `docker image history`."* If you ever pin `frappe_docker` to a pre-2025 ref, use the base64 idiom below; otherwise it is silently ignored and you get a frappe+erpnext-only image with **no tmj**.
>
> **Legacy-only base64 idiom** (only when you pin `frappe_docker` to an older ref that still reads `APPS_JSON_BASE64`):
> ```bash
> # Linux
> export APPS_JSON_BASE64=$(base64 -w 0 apps.json)
> # macOS (no -w flag; strip newlines)
> export APPS_JSON_BASE64=$(base64 apps.json | tr -d '\n')
> ```

### 5.3 Build the image (current `main`, secret-based, pinned to 16.22.0)

Use the **layered** Containerfile (`images/layered/Containerfile`) — it builds `FROM frappe/build:${FRAPPE_BRANCH}` + `frappe/base:${FRAPPE_BRANCH}`, inheriting the Python/Node/yarn that are guaranteed compatible with v16. (The self-contained `images/custom/Containerfile` defaults to Python 3.14.2 / Node 24.13.0, which may be ahead of v16's official support — prefer `layered`.)

```bash
# RECOMMENDED (strategy a): branch-pin frappe+erpnext to version-16,
# then assert the exact version in §5.4. apps.json uses "branch": "version-16" for erpnext.
docker build \
  --no-cache \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --platform=linux/amd64 \
  --secret=id=apps_json,src=apps.json \
  --tag=tmj-erpnext:v16.22.0 \
  --file=images/layered/Containerfile .
```

**Two pinning strategies:**

- **(a) Branch pin — `version-16` — RECOMMENDED PRIMARY PATH** (in `apps.json` and `FRAPPE_BRANCH=version-16`): the fully-documented, fully-supported path. Resolves to the newest 16.x at build time (today: 16.22.0). The catch is that a rebuild next week could pull 16.23.0 — which is exactly why the **mandatory §5.4 version assertion** gates this path: it proves the built image is exactly 16.22.0 with `tmj` baked in. **Ground-truth note:** as of this backup the `v16.22.0` tag sits on `version-16` HEAD in both `frappe` and `erpnext` (`git branch --contains v16.22.0` → `version-16`), so branch-pin yields exactly **16.22.0** today.
- **(b) Exact-pin — `v16.22.0` forever — EXPERIMENTAL / NOT EXPLICITLY DOCUMENTED:** set `FRAPPE_BRANCH=v16.22.0` **and** the erpnext `branch` to `"v16.22.0"` in `apps.json` (below). `bench init` clones with `git clone --branch <ref>`, which *does* accept tags, so today this resolves to the **identical commit** as strategy (a). However, passing a tag where a branch field is expected is **supported but not explicitly documented** in frappe_docker/bench — a future bench/frappe_docker version could reject a tag in that field. **Use (b) only as a deliberate, verified experiment:** confirm against frappe_docker `main` and check the build log shows `v16.22.0` checked out. The `tmj` repo has no version tags, so it is always pinned by `branch: "main"` (optionally pin a commit SHA in that field for full reproducibility).

`apps.json` for the experimental exact pin (strategy b only):
```json
[
  { "url": "https://github.com/frappe/erpnext", "branch": "v16.22.0" },
  { "url": "https://github.com/Bryantant/TMJ",   "branch": "main" }
]
```

> **`--platform=linux/amd64`:** the build host here is Apple Silicon (Darwin/arm64). `compose.yaml` pins every service to `linux/amd64`, so build for amd64 (via emulation) or the x86 prod server will refuse the image. For arm servers, build `--platform=linux/arm64` and override `platform:` in compose to match. See `docs/07-troubleshooting/03-arm64-apple-silicon.md`.

> **Assets are compiled at build time.** The layered builder is `frappe/build` (ships Node + yarn). `bench init` runs the framework asset build for every app present, including tmj's `desk_overrides.bundle.js` and `custom.css` (declared in `tmj/hooks.py`: `app_include_js = ["desk_overrides.bundle.js"]`, `app_include_css = ["/assets/tmj/css/custom.css"]`). The Containerfile then moves `sites/assets` into an image layer. **No runtime `bench build` is needed — and you must NOT run `bench build` inside a running container** (it desyncs `assets.json` and breaks the UI; recovery requires *recreating*, not restarting, containers). To change assets, rebuild the image.

### 5.4 Post-build verification (MANDATORY for strategy a)

This step is **required**, not optional — it is what makes branch-pin (strategy a) safe by proving the built image is exactly 16.22.0.

```bash
# Confirm you actually got 16.22.0 + tmj by reading the pinned versions straight
# from the app source. (`bench version` is fragile in a freshly-built image with no
# site/configurator and depends on cwd — read __init__.py instead; do `bench version`
# as the post-deploy check inside the running backend container in §12 where it works.)
docker run --rm tmj-erpnext:v16.22.0 \
  cat apps/frappe/frappe/__init__.py \
      apps/erpnext/erpnext/__init__.py \
      apps/tmj/tmj/__init__.py | grep __version__
# expect:  frappe 16.22.0,  erpnext 16.22.0,  tmj 0.0.1
# If frappe/erpnext is NOT 16.22.0, the branch-pin drifted — rebuild before proceeding.

# Confirm tmj assets compiled into the image
docker run --rm tmj-erpnext:v16.22.0 \
  ls -la /home/frappe/frappe-bench/assets/tmj/
# expect a hashed `desk_overrides.bundle.<hash>.js` (the hash is build-dependent and
# will DIFFER from the dev build — do not expect a specific hash) and a plain
# `css/custom.css` (custom.css is a non-bundled file served at /assets/tmj/css/custom.css,
# it does not go through the JS bundler).

# Optional: assert the asset map resolves the bundle
docker run --rm tmj-erpnext:v16.22.0 \
  cat sites/assets/assets.json | grep desk_overrides
```

### 5.5 Registry push vs. local build

- **Build on the prod server (single VM):** keep the image local and set `PULL_POLICY=never` (§6) so compose uses the local image and never tries to pull. *(frappe_docker's env-variables doc lists the allowed values as `always`, `never`, `if-not-present` — `never` is the documented choice for the build-on-server case. Docker Compose also accepts `missing` as a synonym of `if-not-present`, but it is **not** in the frappe_docker vocabulary, so prefer `never` here for doc-alignment.)*
- **Build elsewhere → push to a registry (recommended for clean handover/CI):**
  ```bash
  docker tag tmj-erpnext:v16.22.0 <registry>/<namespace>/tmj-erpnext:v16.22.0
  docker push <registry>/<namespace>/tmj-erpnext:v16.22.0
  ```
  Then on the server set `CUSTOM_IMAGE=<registry>/<namespace>/tmj-erpnext`, `CUSTOM_TAG=v16.22.0`, `PULL_POLICY=always`. **The build host's architecture must match the server's** unless you built multi-arch (`--platform linux/amd64,linux/arm64 … --push`; multi-arch manifests can only be pushed, not loaded into the local daemon).

> **CI note:** for automated rebuilds drop `--no-cache` and pass `--build-arg=CACHE_BUST="$(sha256sum apps.json | awk '{print $1}')"` (or `$GITHUB_SHA`). Secret contents are NOT part of the layer cache key, so an `apps.json` change won't invalidate cache on its own (`docs/03-production/06-automated-builds-and-deployment.md`).

---

## 6. Step 3 — Configure the environment (.env)

```bash
cp example.env ~/gitops/tmj.env
```

`compose.yaml`'s shared anchor is `image: ${CUSTOM_IMAGE:-frappe/erpnext}:${CUSTOM_TAG:-$ERPNEXT_VERSION}` with `pull_policy: ${PULL_POLICY:-always}`. Point these at the baked image. Minimum keys to set in `~/gitops/tmj.env`:

```dotenv
# --- pin version (example.env on main already ships ERPNEXT_VERSION=v16.22.0) ---
ERPNEXT_VERSION=v16.22.0          # required even when CUSTOM_* is set; it's the CUSTOM_TAG fallback

# --- use the custom image instead of frappe/erpnext ---
CUSTOM_IMAGE=tmj-erpnext          # or <registry>/<namespace>/tmj-erpnext if pushed
CUSTOM_TAG=v16.22.0
PULL_POLICY=never                 # use the local build; don't try to pull. (registry/CI: always)
                                  # frappe_docker docs list always | never | if-not-present.
                                  # Docker Compose's `missing` is a synonym of if-not-present but
                                  # is NOT in the frappe_docker vocabulary — use `never` here.

# --- DB (containerized MariaDB via overrides/compose.mariadb.yaml) ---
# ERPNext v16 needs MariaDB 10.6+ with utf8mb4 / utf8mb4_unicode_ci. Confirm the bundled
# `db` image tag is a v16-supported MariaDB release (the override currently uses a compatible tag).
DB_PASSWORD=<strong-db-root-password>   # THIS is the MariaDB root password used by every bench restore/new-site below
# DB_HOST / DB_PORT left BLANK for the bundled db service (defaults to service name `db`, port 3306)

# --- HTTPS / Traefik (overrides/compose.https.yaml) ---
LETSENCRYPT_EMAIL=admin@erp.example.com
SITES_RULE=Host(`erp.example.com`)      # Traefik v3 syntax — backticks, NOT quotes. `SITES` is deprecated.
```

> **Secrets stay out of git.** `example.env` ships placeholder `DB_PASSWORD=123` — replace it with a **new strong** root password (do **NOT** reuse the source DB password from the handover bundle — see §3). Keep `~/gitops/*.env` out of any public repo (or commit only to a **private** gitops repo). The site admin password is set at site-create time, never hardcoded in committed files.
>
> **Prefer a Docker secrets file over an inline password.** Set `DB_PASSWORD_SECRETS_FILE=` (documented in `example.env`) to point at a Docker secrets file. This also lets `bench` read the root password from the secret rather than from a `--db-root-password` CLI flag — CLI-passed passwords are exposed via the container process list (`ps`/`/proc`) and the operator's shell history (`~/.zsh_history`), and may surface in `docker compose`/CI logs (see §8/§9).

---

## 7. Step 4 — Generate compose + bring up the stack

Generate the production compose (Traefik HTTPS + MariaDB + Redis). **The override order is load-bearing:**

```bash
docker compose --env-file ~/gitops/tmj.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  config > ~/gitops/docker-compose.yml

docker compose --project-name tmj -f ~/gitops/docker-compose.yml up -d
```

- `compose.mariadb.yaml` — adds the `db` (MariaDB) service on an internal network. **Do not add a host `ports:` mapping** — MariaDB must stay reachable only inside the Docker network.
- `compose.redis.yaml` — adds `redis-cache` + `redis-queue`.
- `compose.https.yaml` — runs **`traefik:v3.6`** as the `proxy` service on `:80`/`:443`, auto-redirects HTTP→HTTPS, uses an ACME httpChallenge resolver, stores certs in the **`cert-data`** volume at `/letsencrypt/acme.json`. Requires `SITES_RULE` + `LETSENCRYPT_EMAIL`.

**Containers you should see** (`docker compose -p tmj ps`):

| Service | Role |
| --- | --- |
| `configurator` | One-shot init — writes `db_host`, `db_port`, `redis_*` into `common_site_config.json`, then **exits 0**. Wait for it to exit before any site/restore command. |
| `backend` | Gunicorn — **the container you `exec` into for all bench commands** (user `frappe`, bench path `/home/frappe/frappe-bench`). |
| `frontend` | nginx — serves the site, proxies to `backend:8000` + `websocket:9000`. |
| `websocket` | node socket.io. |
| `queue-short` | `bench worker --queue short,default`. |
| `queue-long` | `bench worker --queue long,default,short`. |
| `scheduler` | `bench schedule`. |
| `db` | MariaDB (from `compose.mariadb.yaml`). |
| `redis-cache`, `redis-queue` | Redis (from `compose.redis.yaml`). |
| `proxy` | Traefik (from `compose.https.yaml`) — owns `:80`/`:443` + Let's Encrypt. |

> Commit `~/gitops/docker-compose.yml` (and the env file) to a **private** gitops repo — that generated YAML is the deploy artifact. Regenerate + re-commit it whenever you bump `CUSTOM_TAG`/`ERPNEXT_VERSION` or change overrides.

---

## 8. Step 5 — Create the production site

The site name **must equal the host in `SITES_RULE`** (`erp.example.com`) so Traefik routes to it. Create the empty site first, then restore over it — `bench restore` needs an existing site dir + `site_config.json`. (Do **not** pass `--install-app tmj`; the restore brings the DB's `installed_apps`, and the tmj **code** is already in the image.)

```bash
# Prefer omitting --admin-password so bench prompts interactively (keeps it out of
# the process list and shell history). It is reset to a strong unique value post-restore
# in §10 anyway. If you must pass it, prefix the command with a space to skip history.
docker compose -p tmj exec -it backend \
  bench new-site --mariadb-user-host-login-scope=% \
  erp.example.com
```

> **Credential exposure — read before running.** Both the MariaDB root password and the admin password, when passed as CLI args, are visible in the container process list (`ps`/`/proc`) to anyone who can `exec` in, and they land in the operator's shell history and may surface in `docker compose`/CI logs. Mitigations:
> - **Root password:** prefer `DB_PASSWORD_SECRETS_FILE` (§6) so bench reads it from the Docker secret instead of `--db-root-password`. If you must pass `--db-root-password <…>`, it **= the `.env` `DB_PASSWORD`**.
> - **Admin password:** omit `--admin-password` to be prompted (used above), or reset it post-restore in §10. Do not bake a shared/weak "temp" password into a public HTTPS site.
> - For the session: prefix sensitive commands with a leading space, or `unset HISTFILE`, and scrub history afterward.

> `--mariadb-user-host-login-scope=%` is the modern replacement for the deprecated `--no-mariadb-socket` (current bench warns on the old flag). If you hit `Access denied`, test connectivity inside the backend container with `mysql -uroot -p -hdb` (interactive password prompt — don't inline it) and see `docs/07-troubleshooting/01-troubleshoot.md`.

> **Encryption-key note:** `bench new-site` generates a **fresh** `encryption_key` here. The source has none, so this fresh key won't decrypt source secrets — see the prominent callout in §10.

---

## 9. Step 6 — Transfer & restore the backup

`docker cp` cannot take a compose service name — it needs a concrete container name. **Derive it** instead of hardcoding `tmj-backend-1` (that is only the default `<project>-<service>-<index>` name and breaks if the backend was scaled/renamed):

```bash
docker compose -p tmj ps   # confirm the backend container name
BACKEND=$(docker compose -p tmj ps -q backend)   # resolve the container regardless of naming
```

Copy the three restore artifacts into the backend container's sites volume (the `…-site_config_backup.json` is **not** restored — and per §3 it carries a cleartext DB password, so don't copy it in):

```bash
# Run these from the directory that holds the four backup files, OR set SRC to its absolute path.
SRC=/path/to/backups                 # absolute path to the directory containing the backup files
BK=20260615_231534-tmj_localhost
DEST=/home/frappe/frappe-bench/sites/erp.example.com/private/backups

docker compose -p tmj exec backend mkdir -p "$DEST"
docker cp "$SRC/${BK}-database.sql.gz"   "$BACKEND:${DEST}/"
docker cp "$SRC/${BK}-files.tar"         "$BACKEND:${DEST}/"
docker cp "$SRC/${BK}-private-files.tar" "$BACKEND:${DEST}/"
```

Restore the DB + public files + private files. The DB `sql.gz` is the **positional argument**; the two tar archives are flags. Prefer reading the root password from `DB_PASSWORD_SECRETS_FILE` (§6) over the `--db-root-password` flag (which is exposed via process list/history — see §8); if you do pass it, it **= the `.env` `DB_PASSWORD`**:

```bash
docker compose -p tmj exec backend \
  bench --site erp.example.com --force restore \
  ${DEST}/${BK}-database.sql.gz \
  --with-public-files  ${DEST}/${BK}-files.tar \
  --with-private-files ${DEST}/${BK}-private-files.tar
  # add --db-root-password <…> here only if you are NOT using DB_PASSWORD_SECRETS_FILE
```

> The restore-specific flags (`--with-public-files`, `--with-private-files`, `--force`, `--db-root-password`) are standard core-`bench` options — frappe_docker defers `restore` to the upstream bench guide. Confirm with `bench restore --help` inside the container. The restore **overwrites** the freshly created DB, so `installed_apps` becomes `["frappe","erpnext","tmj"]` from the dump — which is exactly why the tmj code had to be in the image.

```bash
# Confirm the app list lines up with the image's app code
docker compose -p tmj exec backend bench --site erp.example.com list-apps
# expect: frappe  erpnext  tmj
```

---

## 10. Step 7 — Post-restore configuration

```bash
# 1. Run framework/erpnext patches + apply any DB-registered schema for the v16.22.0 image.
#    NOTE: tmj ships patch scripts under patches/v0_0 that are intentionally NOT in patches.txt,
#    so `migrate` does NOT run them — the workspace, Number Cards, Property Setters, etc. all come
#    from the DB restore, not from migrate. (This is the whole reason for the full-restore approach.)
docker compose -p tmj exec backend bench --site erp.example.com migrate

# 2. Production hardening: developer_mode OFF (source had it = 1; prod MUST be 0).
#    Use -p so ast.literal_eval("0") yields the integer 0 (falsy). WITHOUT -p the value is
#    stored as the JSON string "0", and Frappe reads developer_mode as a direct bool where
#    bool("0") is True — i.e. developer mode would stay effectively ON. Verify afterward that
#    site_config.json shows  "developer_mode": 0  (no quotes), not "0".
docker compose -p tmj exec backend bench --site erp.example.com set-config -p developer_mode 0

# 3. Keep Server Scripts ENABLED (the "Website Settings Setup" Server Script depends on it).
#    Use -p with a value ast.literal_eval accepts: `1` (or `True` with a capital T).
#    Do NOT use lowercase `true` — ast.literal_eval("true") raises ValueError and the command
#    CRASHES, leaving Server Scripts disabled.
docker compose -p tmj exec backend bench --site erp.example.com set-config -p server_script_enabled 1

# 4. Force-reset the Administrator password to a strong, UNIQUE production value (the §8 temp
#    password — or whatever the backup carried — must not survive to go-live on a public site).
#    Omit the value to be prompted interactively (keeps it out of process list / shell history).
docker compose -p tmj exec -it backend bench --site erp.example.com set-admin-password

# 5. Enable the scheduler (new/restored sites start with it OFF → no scheduled jobs/emails/backups)
docker compose -p tmj exec backend bench --site erp.example.com enable-scheduler

# 6. Clear maintenance mode if the restore left it on (users would see "Updating, please wait")
docker compose -p tmj exec backend bench --site erp.example.com set-maintenance-mode off

# 7. Make it the default site
docker compose -p tmj exec backend bench use erp.example.com

# 8. Clear caches
docker compose -p tmj exec backend bench --site erp.example.com clear-cache
```

> **Administrator account hardening:** after step 4, confirm the §8 temp password no longer works (re-verify in §12). For go-live, also create a **named admin user** for day-to-day administration and restrict/audit the built-in `Administrator` account rather than sharing it.

> `bench build` is **NOT** in this list on purpose. Assets are baked into the image at build time (§5.3); running `bench build` in a live container is the unsupported anti-pattern that desyncs `assets.json`. If desk assets 404 after restore, recreate (not restart) containers: `docker compose -p tmj -f ~/gitops/docker-compose.yml up -d --force-recreate` so the entrypoint re-links the image-layer assets. *(`enable-scheduler`, `set-maintenance-mode`, `bench use`, `set-config` are standard bench commands — confirm with `bench <cmd> --help` in-container.)*

### 🔑 ENCRYPTION KEY CAVEAT — read this before going live

> **There is NO `encryption_key` in the source `site_config.json` or in the backup snapshot.** `bench new-site` (§8) generated a **fresh, random** key. That key will **NOT** decrypt anything that was encrypted at the source. After restore:
>
> - **Encrypted fields will fail to decrypt and must be RE-ENTERED by hand in the desk UI:** Email Account passwords, integration API keys/secrets, OAuth / connected-app / social-login tokens, and any `Password`-fieldtype value. Budget time for this.
> - **Persist and back up the new site's `encryption_key` immediately — treat it as a TOP-TIER secret:**
>   ```bash
>   docker compose -p tmj exec backend \
>     bench --site erp.example.com show-config | grep encryption_key
>   # or read sites/erp.example.com/site_config.json
>   ```
>   **Handle with care:** avoid echoing it to shared or logged terminals (it lands in scrollback/terminal logs and shell history). Store it **only** in your secrets manager. It must be available to restore every future backup of THIS production site, or the same decrypt failure recurs — but do **NOT** store it unencrypted next to the backups it decrypts (that defeats encryption-at-rest). If the key must travel with backups, the backups themselves must be encrypted (§13), so the key stays protected independently. Losing it after secrets are re-entered makes them **unrecoverable**.
> - `bench restore` also accepts `--encryption-key <key>` if you ever DO have the original source key — supply it to decrypt-and-restore in one step. Here there is none, so omit it and plan to re-enter.
>
> *(encryption_key behavior is core-Frappe, not a frappe_docker doc point, but it is a hard requirement for this handover.)*

After config changes, recreate so all workers pick up the new config:
```bash
docker compose -p tmj -f ~/gitops/docker-compose.yml up -d --force-recreate
```

---

## 11. Step 8 — HTTPS / domain

The `compose.https.yaml` override already wired Traefik + Let's Encrypt when you brought the stack up (§7). To get a valid cert:

1. **DNS:** an **A-record for `erp.example.com` → server public IP** must exist **before** `up -d` (Let's Encrypt HTTP-01 validation hits the domain).
2. **Ports:** **80 and 443** must be open/free on the host. Traefik publishes both and redirects HTTP→HTTPS. (Override with `HTTP_PUBLISH_PORT` / `HTTPS_PUBLISH_PORT` only if those host ports are taken.)
3. **Routing:** Traefik routes by `SITES_RULE=Host(\`erp.example.com\`)`. The **site name must equal that host** (created in §8 as `erp.example.com`). If you access by a name that differs from `$host`, set `FRAPPE_SITE_NAME_HEADER=erp.example.com` (default `$host`).
4. **Certs persist** in the `cert-data` volume (`/letsencrypt/acme.json`) — do **not** delete it between retries.

> **Let's Encrypt rate limit:** 5 certs/week per registered domain. Get DNS correct **before** the first `up -d`; use the LE **staging** resolver while testing, then switch to production, so failed runs don't burn the quota.

---

## 12. Verification checklist

### CLI

```bash
docker compose -p tmj exec backend bench version
# expect: frappe 16.22.0, erpnext 16.22.0, tmj <version>

docker compose -p tmj exec backend bench --site erp.example.com list-apps
# expect: frappe  erpnext  tmj   (matches backup snapshot installed_apps)

docker compose -p tmj ps          # all services Up; configurator Exited 0
docker compose -p tmj logs backend # no tracebacks
```

### `bench console` assertions (paste into `bench --site erp.example.com console`)

```python
import frappe

# tmj app installed
assert "tmj" in frappe.get_installed_apps(), "tmj app missing"

# The PT. Tunas Mitra Jaya workspace exists (the landing the client uses)
assert frappe.db.exists("Workspace", "PT. Tunas Mitra Jaya"), "workspace missing"

# Number Cards & Dashboard Charts the workspace renders
print("Number Cards:", frappe.db.count("Number Card"))
print("Dashboard Charts:", frappe.db.count("Dashboard Chart"))
assert frappe.db.count("Number Card") > 0, "no Number Cards"
assert frappe.db.count("Dashboard Chart") > 0, "no Dashboard Charts"

# The 4 custom Reports
print("Custom Reports:", frappe.get_all("Report", filters={"is_standard": "No"}, pluck="name"))

# Server Script automation present
assert frappe.db.exists("Server Script", "Website Settings Setup"), "Server Script missing"

# ~289 Property Setters + Custom DocPerms restored
print("Property Setters:", frappe.db.count("Property Setter"))   # expect ~289
print("Custom DocPerms:", frappe.db.count("Custom DocPerm"))

# Production-critical site config
print("developer_mode:", repr(frappe.conf.get("developer_mode")))         # expect 0 (int) or None — NOT the string "0"
print("server_script_enabled:", frappe.conf.get("server_script_enabled")) # expect True / 1
print("has encryption_key:", bool(frappe.conf.get("encryption_key")))     # expect True (freshly generated)
```

> Cross-check `sites/erp.example.com/site_config.json` directly: it must show `"developer_mode": 0` and `"server_script_enabled": 1` (or `true`) as **unquoted** values — a quoted `"0"`/`"true"` means the `-p` flag was missed (see §10) and the hardening is ineffective.

### Human UI checks

- **Workspace landing:** logging in lands on / shows the **"PT. Tunas Mitra Jaya"** workspace with its Number Cards and Dashboard Charts populated.
- **Branding logo:** the custom logo + splash render (these came from `-files.tar` public files).
- **"Submitted" statuses:** payment-derived invoice statuses display the neutral **"Submitted"** label (the relabel customization).
- **Non-admin scoping:** a **non-admin** user sees only the PT. Tunas Mitra Jaya sidebar/workspace and the unused doctypes stay hidden (Custom DocPerms); no "Edit DocType" affordances (developer_mode off).
- **Admin password rotated:** the §8 temp Administrator password **no longer works**; the new strong unique password (set in §10 step 4) does. The built-in `Administrator` is restricted/audited and a named admin user exists.
- **Re-entered secrets:** any Email Account / integration that you re-keyed (§10) actually connects.

---

## 13. Production backups

Backups land in the `sites` volume at `sites/<site>/private/backups/` and produce the same four-file shape as the handover set (`-database.sql.gz`, `-files.tar`, `-private-files.tar`, `-site_config_backup.json`).

> **⚠️ These backups are secret-bearing.** The DB dump is the full business DB, and (as in the handover set) the generated `…-site_config_backup.json` embeds the site's **cleartext db password**. So:
> - Ensure `sites/<site>/private/backups/` is **not world-readable** on the host (e.g. `chmod 700` the dir / `600` the files).
> - **Encrypt backups at rest** before they leave the host (see restic below) and do not commit or share them unredacted.

**Host cron — every 6h, DB + files** (`docs/03-production/02-backup-strategy.md`):

```cron
0 */6 * * * docker compose -p tmj exec backend bench --site all backup --with-files > /dev/null
```

**Offsite (restic → S3, RECOMMENDED — restic encrypts the repo)** — `restic` and `gpg` are baked into the image. Prefer restic over plain `push_backup.py` because restic encrypts the whole repo with `RESTIC_PASSWORD`. Pass all credentials via **env / secret files, never CLI flags** (CLI args leak via the process list and shell history — same exposure as §8). Use the repo's `backup-job.yml` pattern:

```bash
# Credentials come from the environment (or a Docker secret file), NOT command-line flags.
export RESTIC_REPOSITORY=s3:https://<endpoint>/<bucket>
export RESTIC_PASSWORD=<strong-restic-repo-password>   # or RESTIC_PASSWORD_FILE=/run/secrets/restic
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
restic backup sites
restic forget --keep-last=30 --prune
```

> If you must use the `push_backup.py` helper instead, supply the S3 credentials via environment variables rather than `--aws-access-key-id` / `--aws-secret-access-key` CLI flags, and enable **bucket-side encryption (SSE)** plus a **least-privilege bucket policy** on the destination.

> **Store the new site's `encryption_key` (§10) so it is available for these backups, but do NOT colocate it unencrypted in the same bucket/folder as the ciphertext** — `bench backup` does NOT include it in `site_config_backup.json`, so a future restore without it repeats the decrypt-failure problem. Keep the key in your secrets manager; the encrypted backup repo (restic) protects the data independently of the key.

---

## 14. Updating the tmj app later (immutable-image model)

Installing apps into a running container is **not supported** (`docs/01-getting-started/02-docker-immutability.md`). The loop is **rebuild image → bump tag → redeploy → migrate → clear-cache**:

```bash
# 1. Push new tmj code to https://github.com/Bryantant/TMJ

# 2. Rebuild with a NEW tag (never reuse a tag). CACHE_BUST forces a fresh clone of the tmj layer.
docker build --no-cache \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=v16.22.0 \
  --build-arg=CACHE_BUST="$(date +%s)" \
  --platform=linux/amd64 \
  --secret=id=apps_json,src=apps.json \
  --tag=<registry>/<namespace>/tmj-erpnext:<tag> \
  --file=images/layered/Containerfile .
# docker push <registry>/<namespace>/tmj-erpnext:<tag>   # if using a registry

# 3. Bump CUSTOM_TAG in ~/gitops/tmj.env (e.g. CUSTOM_TAG=<tag>)

# 4. Regenerate the compose file
docker compose --env-file ~/gitops/tmj.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  config > ~/gitops/docker-compose.yml

# 5. Redeploy onto the new image (the `sites` volume — DB + files — persists)
docker compose -p tmj -f ~/gitops/docker-compose.yml up -d

# 6. Migrate + clear caches
docker compose -p tmj exec backend bench --site erp.example.com migrate
docker compose -p tmj exec backend bench --site erp.example.com clear-cache
```

> **Do NOT run `bench build` in the container** — changed `desk_overrides.bundle.js` / `custom.css` ship inside the new image from step 2's `bench init`. If you think you need `bench build` at runtime, the supported answer is: rebuild the image.

---

## 15. Troubleshooting & pitfalls

| Symptom | Cause / Fix |
| --- | --- |
| Image won't run on the prod server (`exec format error`) | **Platform mismatch.** Built arm64 on Apple Silicon for an amd64 server. Rebuild with `--platform=linux/amd64`. See `docs/07-troubleshooting/03-arm64-apple-silicon.md`. |
| Build "succeeds" but image has no tmj | You used `--build-arg APPS_JSON_BASE64=…` on current `main` (removed). Use `--secret=id=apps_json,src=apps.json`. Verify with `docker run --rm <image> bench version`. |
| Desk UI broken / assets 404 after deploy | Someone ran `bench build` in a running container, or assets didn't relink. **Recreate** (not restart) containers: `up -d --force-recreate`. Never `bench build` at runtime. |
| Traefik returns 404 for the domain | `SITES_RULE` `Host(...)` doesn't match the created site name. The site must be named `erp.example.com`. Or set `FRAPPE_SITE_NAME_HEADER`. |
| No cert / Let's Encrypt failing | DNS A-record not pointing to the server before `up -d`, or ports 80/443 blocked. Fix DNS/ports; use LE staging while testing; don't delete the `cert-data` / `acme.json` volume between retries (rate limit: 5/week/domain). |
| `Access denied` on new-site/restore | `--db-root-password` ≠ MariaDB root password. It must equal the `.env` `DB_PASSWORD`. Test: `mysql -uroot -p -hdb` (interactive prompt — don't inline the password) inside `backend`. See `docs/07-troubleshooting/01-troubleshoot.md` (and the `mysql.global_priv` grant fix). |
| `bench restore` errors on collation / unknown charset | MariaDB version/charset mismatch. ERPNext v16 needs **MariaDB 10.6+** with **`utf8mb4` / `utf8mb4_unicode_ci`**. Pin the `db` service to a v16-supported MariaDB tag and ensure the db/dump charset is `utf8mb4` before retrying (§3/§6). |
| Bench command fails right after `up -d` | `configurator` hasn't exited / `db` not healthy yet. Wait for `configurator` to exit 0 and `db` healthy (~10s). |
| Scheduled jobs / emails / backups never fire | Scheduler not enabled on the restored site. Run `bench --site erp.example.com enable-scheduler`; confirm the `scheduler` service is Up. |
| Site stuck on "Updating, please wait" | Restore left maintenance mode on. `bench --site erp.example.com set-maintenance-mode off`. |
| `developer_mode` still effectively ON in prod | You ran `set-config developer_mode 0` **without `-p`**, storing the string `"0"` (and `bool("0")` is `True`). Re-run with `-p`: `set-config -p developer_mode 0`; verify `site_config.json` shows `"developer_mode": 0` (unquoted). |
| `set-config server_script_enabled true` crashes (`ValueError: malformed node or string`) | With `-p`, bench runs `ast.literal_eval(value)`, which rejects lowercase `true`. Use `set-config -p server_script_enabled 1` (or `True` with a capital T); verify the value type in `site_config.json`. |
| `server_script_enabled` stored as string `"true"` | You set it without `-p`. Re-run with `set-config -p server_script_enabled 1` (or `True`) to store a real boolean/int — **not** lowercase `true`, which crashes. Verify the value type in `site_config.json`. |
| Encrypted secrets blank / "decrypt failed" | Expected — fresh `encryption_key` (§10). Re-enter Email Account passwords, integration keys/secrets, OAuth tokens. Back up the new key (as a top-tier secret, not next to the backups). |
| Source DB password leaked / temp admin password still works | The handover `…-site_config_backup.json` carries a cleartext db password (§3) and §8's admin password is temporary. Never reuse the source db password on prod; rotate the Administrator password in §10 step 4 and destroy/secure the source bundle. |
| Build cache reuses an old tmj layer | `apps.json` is a secret (not part of the cache key). Use `--no-cache` for one-offs, or `--build-arg=CACHE_BUST=…` for CI. |
| Update didn't take effect | You reused a `CUSTOM_TAG`. Always bump the tag (immutability); then regenerate compose + `up -d`. |
