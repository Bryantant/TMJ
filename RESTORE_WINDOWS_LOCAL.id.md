# Backup Mac → Restore ke PC Windows Client (via AnyDesk)

Panduan singkat buat mindahin site `tmj.localhost` dari Mac ini ke PC Windows client, jalan lokal di situ (bukan server publik, jadi nggak perlu domain/HTTPS). Ini restore penuh (DB + files), bukan install app dari kosong — soalnya hampir semua kustomisasi (Report, Property Setter, Number Card, dll) cuma ada di database, bukan di kode.

Versi: Frappe/ERPNext 16.22.0, tmj 0.0.1. Repo: `github.com/Bryantant/TMJ` branch `main`.

Kalau nanti butuh deploy ke VPS beneran (domain + HTTPS), itu ada di [`RESTORE.md`](RESTORE.md) — bukan panduan ini.

**Sebelum mulai:** pastikan AnyDesk di PC client sudah di-set **Unattended Access** (password tetap). Tanpa ini kamu nggak bisa approve prompt UAC dari jauh dan nggak bisa reconnect setelah PC-nya restart (2x restart bakal kejadian: install WSL2 dan install Docker Desktop). Kalau AnyDesk sempat disconnect pas restart, tenang aja — itu wajar, tunggu 1-2 menit lalu connect lagi, proses di PC-nya nggak kepotong.

---

## 1. Di Mac: buat backup

```bash
cd /Users/bryantantonio/Dev/benchv16/apps/tmj
git push origin main            # pastikan kode app sudah ke-push

cd /Users/bryantantonio/Dev/benchv16
bench --site tmj.localhost backup --with-files
```

Hasilnya 4 file di `sites/tmj.localhost/private/backups/` dengan timestamp baru. Zip **3 file ini saja** (skip yang `-site_config_backup.json`, isinya password DB dalam bentuk plain text dan nggak kepake buat restore):

```bash
cd sites/tmj.localhost/private/backups
zip tmj-handover.zip <ts>-tmj_localhost-database.sql.gz <ts>-tmj_localhost-files.tar <ts>-tmj_localhost-private-files.tar
```

Kirim `tmj-handover.zip` ke PC client lewat **File Transfer AnyDesk** (ikon di toolbar sesi) ke folder `C:\Users\<user>\Downloads\`.

---

## 2. Di PC Windows: install Docker

1. PowerShell (Admin) → `wsl --install` → restart PC (approve UAC-nya, tunggu restart selesai, reconnect AnyDesk).
2. Buat username/password Ubuntu waktu diminta (bebas, catat).
3. Install **Docker Desktop** dari docker.com → restart lagi kalau diminta.
4. Docker Desktop → Settings → Resources → WSL Integration → aktifkan untuk Ubuntu.
5. Buka app **Ubuntu** dari Start menu — dari sini semua perintah bash sama persis kayak di Mac.

---

## 3. Build image tmj di PC itu

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
mkdir -p ~/gitops

cat > apps.json <<'EOF'
[
  { "url": "https://github.com/frappe/erpnext", "branch": "version-16" },
  { "url": "https://github.com/Bryantant/TMJ",   "branch": "main" }
]
EOF

docker build --no-cache \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=apps.json \
  --tag=tmj-erpnext:v16.22.0 \
  --file=images/layered/Containerfile .
```

Ini nge-clone langsung dari GitHub, jadi nggak perlu transfer image gede-gede dari Mac. Tunggu aja sampai selesai (agak lama, ada compile assets juga) — kalau AnyDesk kepotong di tengah jalan, build-nya tetap lanjut, reconnect aja lagi nanti.

---

## 4. Setup & jalankan stack (lokal, tanpa HTTPS)

```bash
cp example.env ~/gitops/tmj.env
```

Edit `~/gitops/tmj.env`, isi seperti ini:

```dotenv
ERPNEXT_VERSION=v16.22.0
CUSTOM_IMAGE=tmj-erpnext
CUSTOM_TAG=v16.22.0
PULL_POLICY=never
DB_PASSWORD=<password-kuat-bebas>
HTTP_PUBLISH_PORT=8080
FRAPPE_SITE_NAME_HEADER=tmj.localhost
```

Baris terakhir itu yang bikin site bisa jalan tanpa domain asli — nginx-nya dipaksa selalu arahkan ke `tmj.localhost` apapun yang diketik di browser.

```bash
docker compose --env-file ~/gitops/tmj.env \
  -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml \
  config > ~/gitops/docker-compose.yml

docker compose -p tmj -f ~/gitops/docker-compose.yml up -d
docker compose -p tmj ps        # tunggu configurator "Exited (0)" dan db "healthy"
```

---

## 5. Buat site & restore backup

```bash
docker compose -p tmj exec -it backend bench new-site --mariadb-user-host-login-scope=% tmj.localhost
```

Salin backup ke container, lalu restore (sesuaikan `SRC` & `BK` dengan file yang tadi dikirim lewat AnyDesk):

```bash
SRC=/mnt/c/Users/<user>/Downloads      # tempat tmj-handover.zip di-unzip
BK=<ts>-tmj_localhost                  # prefix nama file backup
DEST=/home/frappe/frappe-bench/sites/tmj.localhost/private/backups

docker compose -p tmj exec backend mkdir -p "$DEST"
BACKEND=$(docker compose -p tmj ps -q backend)
docker cp "$SRC/${BK}-database.sql.gz"   "$BACKEND:${DEST}/"
docker cp "$SRC/${BK}-files.tar"         "$BACKEND:${DEST}/"
docker cp "$SRC/${BK}-private-files.tar" "$BACKEND:${DEST}/"

docker compose -p tmj exec backend bench --site tmj.localhost --force restore \
  ${DEST}/${BK}-database.sql.gz \
  --with-public-files  ${DEST}/${BK}-files.tar \
  --with-private-files ${DEST}/${BK}-private-files.tar
```

---

## 6. Beres-beres setelah restore

```bash
docker compose -p tmj exec backend bench --site tmj.localhost migrate
docker compose -p tmj exec backend bench --site tmj.localhost set-config -p developer_mode 0
docker compose -p tmj exec backend bench --site tmj.localhost set-config -p server_script_enabled 1
docker compose -p tmj exec -it backend bench --site tmj.localhost set-admin-password
docker compose -p tmj exec backend bench --site tmj.localhost enable-scheduler
docker compose -p tmj exec backend bench --site tmj.localhost set-maintenance-mode off
docker compose -p tmj exec backend bench use tmj.localhost
docker compose -p tmj exec backend bench --site tmj.localhost clear-cache

docker compose -p tmj -f ~/gitops/docker-compose.yml up -d --force-recreate
```

**Penting:** password Email Account, API key, dan token OAuth di source **nggak akan kebawa jalan** (encryption key-nya baru) — harus dimasukin ulang manual lewat desk UI kalau memang dipakai.

---

## 7. Buka di browser

```
http://tmj.localhost:8080
```

Kalau nggak bisa kebuka, edit `C:\Windows\System32\drivers\etc\hosts` (Notepad as Admin) tambahin baris `127.0.0.1 tmj.localhost`.

Cek: landing di workspace "PT. Tunas Mitra Jaya" dengan Number Card/Chart terisi, logo branding muncul, password admin yang baru berfungsi.

---

## Kalau ada masalah

| Gejala | Solusi |
| --- | --- |
| AnyDesk disconnect pas restart | Wajar, tunggu 1-2 menit lalu connect lagi |
| `docker: command not found` di Ubuntu | Docker Desktop → Resources → WSL Integration → aktifkan Ubuntu |
| Image ke-build tapi nggak ada tmj-nya | Pastikan pakai `--secret=id=apps_json,...` bukan flag base64 lama |
| Port 8080 sudah kepakai | Ganti `HTTP_PUBLISH_PORT` di `tmj.env`, generate ulang compose, `up -d` lagi |
| `Access denied` waktu restore | Password root DB harus sama dengan `DB_PASSWORD` di `tmj.env` |
| Login/integrasi gagal setelah restore | Encryption key baru — masukin ulang password/API key itu manual |
