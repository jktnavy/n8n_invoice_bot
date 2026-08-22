# RENCANA DEPLOY VPS — Hermes + invoice-sta + MySQL invoice_bot

- Tanggal: 14 Agustus 2026
- VPS: `nakatara-server` (103.150.191.235) — Ubuntu 24.04.4 LTS, 4 vCPU, 3.8 GB RAM
- Status: ✅ **DIEXSEKUSI — bot LIVE production di VPS (14-08-2026, 20:57 WIB)**
- Prinsip: TIDAK menyentuh/mengganggu aplikasi production yang sudah live.

---

## 0. Hasil Eksekusi (14-08-2026)

Deploy selesai & **bot LIVE di production** (`@statrans_invoice_bot` dijalankan dari VPS `nakatara-server`).

| #   | Langkah                          | Hasil                                                               |
| --- | -------------------------------- | ------------------------------------------------------------------- |
| 1   | User OS `invoicebot`             | ✅ dibuat (uid 1002, home `/home/invoicebot`)                       |
| 2   | DB + user MySQL `invoice_bot`    | ✅ DB + user (grant hanya `invoice_bot.*`) + `.env` (600)           |
| A   | Schema                           | ✅ `invoices` + `invoice_items`                                     |
| B   | Hermes v0.20.1                   | ✅ (venv hermes-agent, launcher bash diperbaiki)                    |
| 3   | LLM + Telegram env               | ✅ auth.json Nous + config model + token + group allowlist          |
| 4   | Skill deps                       | ✅ venv skill (weasyprint 69 + libpango + pymysql + pillow)         |
| 5   | Skill                            | ✅ tersalin + `invoice-sta` enabled                                 |
| 6   | Systemd `hermes-gateway.service` | ✅ active, Restart=always, enabled                                  |
| 7   | Cutover                          | ✅ gateway lokal WSL distop; VPS **Connected (polling mode)** 20:57 |

**Kendala yang diatasi:** env `VIRTUAL_ENV` warisan (install ulang `sudo -iu`),
launcher symlink salah (→ script bash venv), error `Any cannot be
instantiated`, polling conflict (gateway lokal masih jalan → distop),
ownership `skills/` root (→ chown invoicebot).

## 1. Kondisi VPS Saat Ini (hasil audit 14-08-2026)

| Komponen      | Status                                                                                                         |
| ------------- | -------------------------------------------------------------------------------------------------------------- |
| OS            | Ubuntu 24.04.4 LTS, kernel 6.8                                                                                 |
| CPU / RAM     | 4 vCPU / 3.8 GB (sisa ~1.7 GB)                                                                                 |
| Disk          | 58 GB, **terpakai 79%** (sisa ~13 GB)                                                                          |
| nginx         | aktif (port 80/443) — web app live                                                                             |
| php8.4-fpm    | aktif                                                                                                          |
| MariaDB       | 11.4.12, hanya listen `127.0.0.1:3306`                                                                         |
| redis         | aktif (localhost:6379)                                                                                         |
| supervisor    | aktif (dipakai app lain — JANGAN disentuh)                                                                     |
| fail2ban      | aktif                                                                                                          |
| Web apps live | `denytrans.co.id`, `indobuswisata.com`, `nfc.web.id`, `travelcianjur.co.id` (WordPress), `travelcianjur-order` |
| Hermes        | **belum terpasang**                                                                                            |

**Kebijakan keamanan:**

- JANGAN restart/stop nginx, php-fpm, mariadb, redis, supervisor, fail2ban.
- JANGAN ubah config app lain.
- JANGAN buka port inbound baru (Hermes pakai polling → koneksi keluar saja).
- Semua perubahan hanya untuk komponen baru milik proyek invoice STA.

---

## 2. Arsitektur Target (VPS, non-Docker)

```
[Telegram] ── polling ──▶ [Hermes Gateway (systemd)]
                              │ user: invoicebot (khusus)
                              ▼
                    [Skill: invoice-sta]
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
   Parse & hitung        Pratinjau +            Render PDF
   (qty×price)           Persetujuan           (weasyprint)
                              │                      │
                              └──────────┬───────────┘
                                         ▼
                              [MySQL: invoice_bot]
                              user khusus: invoice_bot
                              (hanya grant DB ini)
                                         ▼
                        Kirim PDF ke Telegram ([[as_document]])
```

## 3. Isolasi — Komponen Baru, Terpisah dari App Live

| Aspek            | Keputusan                                                                        |
| ---------------- | -------------------------------------------------------------------------------- |
| User OS          | User baru **`invoicebot`** (bukan `denjaka`, bukan `root`)                       |
| Direktori        | `/home/invoicebot/.hermes/` (runtime) + skill di `~/.hermes/skills/invoice-sta/` |
| MySQL DB         | DB baru **`invoice_bot`** + user MySQL **`invoice_bot`**                         |
| Grant MySQL      | HANYA `invoice_bot.*` (SELECT/INSERT/UPDATE/DELETE) — TIDAK akses DB lain        |
| Service          | systemd unit **`hermes-gateway.service`** milik `invoicebot`                     |
| Port             | TIDAK ada port inbound baru (polling = koneksi keluar ke Telegram)               |
| Nginx/supervisor | TIDAK disentuh                                                                   |
| Backup           | cron user `invoicebot`: `mysqldump invoice_bot` + folder `~/.hermes/invoices`    |

## 4. Langkah Eksekusi (menunggu persetujuan per langkah)

> Urutan dirancang agar app live tidak pernah terdampak.

### Langkah 0 — Prasyarat (persetujuan user)

- Pastikan disk cukup (sisa ~13 GB; Hermes ~2.3 GB — aman).
- Pastikan kredensial LLM tersedia (Nous Portal / OpenRouter) di VPS.

### Langkah 1 — Buat user OS `invoicebot` (tidak menyentuh apa pun)

```bash
sudo useradd -m -s /bin/bash invoicebot
sudo passwd invoicebot   # password diketik user sendiri (bukan via chat)
```

### Langkah 2 — Buat DB & user MySQL khusus

Dijalankan via `sudo mysql` (root socket lokal):

```sql
CREATE DATABASE IF NOT EXISTS invoice_bot
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'invoice_bot'@'localhost' IDENTIFIED BY '<password_user>';
GRANT SELECT, INSERT, UPDATE, DELETE ON invoice_bot.* TO 'invoice_bot'@'localhost';
FLUSH PRIVILEGES;
```

- User MySQL **`invoice_bot`** hanya punya akses ke DB `invoice_bot` — aman dari DB production lain.
- Password diketik user sendiri di terminal, tidak lewat chat.

### Langkah 3 — Install Hermes sebagai user `invoicebot`

```bash
sudo -u invoicebot bash -lc 'curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash'
```

- Hermes tidak menyentuh app lain (self-contained di `~/.hermes/`).

### Langkah 4 — Setup LLM + Telegram

```bash
sudo -u invoicebot hermes setup          # login LLM provider
sudo -u invoicebot hermes gateway setup  # token bot @statrans_invoice_bot
```

- Token di `~/.hermes/.env` (bukan di repo).

### Langkah 5 — Dependensi PDF (weasyprint)

```bash
sudo apt install -y libpango-1.0-0 libpangocairo-1.0-0   # sistem, aman (tidak mengganti app)
sudo -u invoicebot bash -lc 'source ~/.hermes/... ; uv pip install weasyprint pymysql pillow'
```

### Langkah 6 — Salin skill `invoice-sta`

```bash
sudo mkdir -p /home/invoicebot/.hermes/skills/invoice-sta
sudo cp -r /home/heden/projects/n8n_invoice/skills/invoice-sta/* /home/invoicebot/.hermes/skills/invoice-sta/
sudo chown -R invoicebot:invoicebot /home/invoicebot/.hermes/skills/
```

- Pastikan path interpreter di SKILL.md diubah ke `/home/invoicebot/.hermes/venvs/...` (bukan `/home/heden/...`).

### Langkah 7 — Env variabel (di `~/.hermes/.env` user invoicebot)

```bash
TELEGRAM_BOT_TOKEN=...
TELEGRAM_GROUP_ALLOWED_CHATS=-5483961981
INVOICE_DB_HOST=127.0.0.1
INVOICE_DB_PORT=3306
INVOICE_DB_USER=invoice_bot
INVOICE_DB_PASSWORD=...
INVOICE_DB_NAME=invoice_bot
LLM_API_KEY=...
```

### Langkah 8 — Systemd unit `hermes-gateway.service` (user invoicebot)

```ini
[Unit]
Description=Hermes Gateway (STA Invoice Bot)
After=network-online.target mariadb.service
Wants=network-online.target

[Service]
User=invoicebot
WorkingDirectory=/home/invoicebot
ExecStart=/home/invoicebot/.local/bin/hermes gateway start
Restart=always
RestartSec=5
EnvironmentFile=/home/invoicebot/.hermes/.env

[Install]
WantedBy=multi-user.target
```

- Tidak menyentuh service app lain; `Restart=always` + `RestartSec=5`.

### Langkah 9 — Uji (tanpa mengganggu apa pun)

- `sudo -u invoicebot hermes` → test skill `/invoice-sta` via CLI.
- Kirim test pesan ke grup Telegram → pratinjau → setuju → PDF → cek DB.
- Cek log: `journalctl -u hermes-gateway -f`.

### Langkah 10 — Backup otomatis (cron user invoicebot)

```cron
15 2 * * * mysqldump -u invoice_bot -p<pass> invoice_bot > ~/backups/invoice_bot_$(date +\%F).sql
30 2 * * * rsync -a ~/.hermes/invoices/ ~/backups/invoices/
```

---

## 5. Verifikasi Keamanan / Tidak Mengganggu

| Cek                    | Cara                                                          |
| ---------------------- | ------------------------------------------------------------- |
| App live tetap jalan   | `systemctl status nginx php8.4-fpm mariadb` sebelum & sesudah |
| Tidak ada port baru    | `ss -tlnp` (harus sama dengan sebelum)                        |
| MySQL aman             | `invoice_bot` user hanya grant DB `invoice_bot`               |
| Secret tidak bocor     | token & password hanya di `~/.hermes/.env` (permission 600)   |
| Log tidak bocor secret | cek `~/.hermes/logs/` setelah test                            |

---

## 6. Rollback

- Hapus unit systemd: `sudo systemctl disable --now hermes-gateway`
- Hapus user: `sudo userdel -r invoicebot`
- Drop DB: `sudo mysql -e "DROP DATABASE invoice_bot; DROP USER 'invoice_bot'@'localhost';"`
- Semua reversible, tidak menyentuh app lain.

---

## 7. Risiko & Mitigasi

| Risiko                  | Mitigasi                                                 |
| ----------------------- | -------------------------------------------------------- |
| Disk 79% penuh          | Hermes ~2.3 GB masih muat di sisa 13 GB; pantau `df -h`  |
| RAM sisa ~1.7 GB        | Hermes idle ringan; render PDF puncak ~200 MB — aman     |
| Salah ketik password DB | User MySQL terpisah, DB terpisah — tidak merusak DB lain |
| LLM API key hilang      | Simpan di `~/.hermes/.env` (600) + backup                |
| Bot mati diam-diam      | systemd `Restart=always` + healthcheck cron + notifikasi |

---

## 8. Catatan Tambahan

- Nomor invoice `INV-XXXX/STA/BULAN_ROMawi/TAHUN` diambil dari DB — DB VPS jadi source of truth.
- Sebelum cutover, pastikan skill & script di VPS identik dengan source (`diff`).
- Disarankan uji lokal penuh (grup Telegram) dulu sebelum aktivasi di VPS.
- Semua langkah di atas TIDAK dieksekusi tanpa persetujuan eksplisit per langkah.
