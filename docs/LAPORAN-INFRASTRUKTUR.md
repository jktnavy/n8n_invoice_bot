# LAPORAN INFRASTRUKTUR — Otomasi Invoice Telegram STA Transport

| Field   | Nilai                                                                       |
| ------- | --------------------------------------------------------------------------- |
| Disusun | 14 Agustus 2026                                                             |
| Versi   | 1.0                                                                         |
| Status  | 🟢 Deploy VPS LIVE — bot production di nakatara-server (14-08-2026)         |
| Lingkup | Audit environment, arsitektur, komponen, setup lokal & VPS, biaya, keamanan |

---

## 1. Ringkasan Eksekutif

Proyek membangun **bot Telegram pembuat invoice otomatis** untuk STA Transport.
User cukup chat ke bot (format bebas bahasa Indonesia, panjang atau singkat),
bot mem-parse data, menampilkan **pratinjau**, meminta **persetujuan**, lalu
membuat **PDF invoice** dengan template STA dan menyimpan record ke **MySQL**.

Solusi terpilih: **Hermes Agent** (Nous Research) — AI agent dengan gateway
Telegram bawaan, sistem skills, dan berjalan **tanpa Docker** (cocok VPS kecil).

Fase saat ini: **Sprint 1 selesai — termasuk deploy VPS (LIVE production)**.
Bot berjalan dari VPS `nakatara-server` (systemd, polling Telegram), DB
`invoice_bot` terisolasi dengan user MySQL khusus (`invoice_bot`), tanpa
menyentuh aplikasi web yang sudah live.

---

## 2. Hasil Audit Environment (14-08-2026)

Dilakukan pada WSL Ubuntu via SSH:

| Komponen  | Status                                | Keterangan                                      |
| --------- | ------------------------------------- | ----------------------------------------------- |
| OS        | ✅                                    | WSL Ubuntu (Windows 11 host)                    |
| Node.js   | ✅ v22.18.0                           | via nvm (`~/.nvm`)                              |
| ngrok     | ✅                                    | via snap (opsional, tidak wajib — mode polling) |
| Chromium  | ✅                                    | via snap (fallback HTML→PDF)                    |
| Docker    | ❌ Tidak ada                          | Sesuai keputusan: tidak dipakai                 |
| n8n       | ❌ Tidak ada                          | Tidak dipakai (pilihan: Hermes)                 |
| MySQL     | ⚠️ Ada (milik user)                   | Untuk DB baru `invoice_bot`                     |
| Python    | ✅                                    | via miniforge3 / uv (dipakai Hermes)            |
| Workspace | 📁 `/home/heden/projects/n8n_invoice` | Berisi `docs/`                                  |

> **Catatan penting:** Aplikasi lama `bus_invoice_app` memakai **SQL Server**
> (`bus_invoice_db`, port 1433) — BUKAN MySQL. Data tenant asli STA ada di
> sana (atau diinput manual). Seed database hanya berisi tenant demo
> (PT Bus Wisata Nusantara / PT Pariwisata Sejahtera), bukan STA Transport.

### 2b. Audit VPS Production (14-08-2026)

| Komponen | Hasil                                                                                         |
| -------- | --------------------------------------------------------------------------------------------- |
| Host     | `nakatara-server` — 103.150.191.235 (SSH user `denjaka`)                                      |
| OS       | Ubuntu 24.04.4 LTS, 4 vCPU, RAM 3.8 GB (sisa ~1.7 GB)                                         |
| Disk     | 58 GB, terpakai 79% (sisa ~13 GB)                                                             |
| Service  | nginx, php8.4-fpm, mariadb 11.4.12, redis, supervisor, fail2ban                               |
| MySQL    | listen 127.0.0.1:3306; 6 DB production; tiap app punya user sendiri                           |
| Web apps | denytrans.co.id, indobuswisata.com, nfc.web.id, travelcianjur.co.id (WP), travelcianjur-order |
| Hermes   | sebelumnya belum ada → kini diinstall untuk user `invoicebot`                                 |
| Deploy   | ✅ bot LIVE 14-08-2026 20:57 WIB (gateway lokal distop)                                       |

---

## 3. Arsitektur

```
[Telegram]  ── pesan bebas ──▶  [Bot STA Invoice (@BotFather)]
                                     │ token
                                     ▼
                          [Hermes Gateway]  (daemon, tanpa Docker)
                                     │
                                     ▼
                          [Skill: invoice-sta]   ~/.hermes/skills/
                                     │
        ┌────────────────────────────┼───────────────────────────┐
        ▼                            ▼                           ▼
   Parse & hitung               Pratinjau +              Render PDF
   (qty×price, terbilang)       Persetujuan             (weasyprint/
                                 (via chat)              chromium)
        │                            │                           │
        │                            └──────────┬────────────────┘
        │                                       ▼
        │                          [MySQL: invoice_bot]
        │                          invoices + invoice_items
        │                                       │
        └──────────▶ Kirim PDF ke Telegram ◀────┘
                          (path file + [[as_document]])
```

Komponen produksi (VPS, non-Docker):

- `hermes gateway` (systemd) → LLM API (OpenRouter/OpenAI)
- Python + weasyprint → HTML → PDF
- MySQL (sudah ada) → record invoice
- Mode polling Telegram → tanpa domain/SSL/webhook

---

## 4. Komponen & Persyaratan

### 4.1 Hermes Agent

- Install: `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`
- Butuh: **API key LLM** (OpenRouter / OpenAI / Nous Portal) → biaya per pesan
- Gateway: Telegram, Discord, Slack, WhatsApp, Signal, dll (20+ platform)
- Skills: folder `SKILL.md` (standar agentskills.io), lokasi `~/.hermes/skills/`
- Skill otomatis jadi slash command `/invoice-sta` di Telegram & CLI

### 4.2 Skill `invoice-sta`

Struktur:

```
~/.hermes/skills/invoicing/invoice-sta/
├── SKILL.md                  # instruksi + frontmatter + config
├── templates/invoice_template.html
└── scripts/
    ├── format_indonesia.py   # rupiah, tanggal panjang, terbilang
    └── render_invoice.py     # HTML→PDF + insert MySQL
```

Alur skill: parse → hitung ulang → terbilang → **pratinjau** → **persetujuan**
→ render PDF → simpan MySQL → kirim ke Telegram.

### 4.3 Database MySQL — `invoice_bot`

- DB baru: `invoice_bot` (utf8mb4) — lihat `schema-mysql.sql`
- Tabel `invoices`: nomor, customer, tanggal, tipe bayar, DP, subtotal, diskon,
  pajak, grand total, terbilang, termasuk/tidak, status, pdf_path, raw_request
- Tabel `invoice_items`: detail perjalanan (tanggal, jenis kendaraan, qty,
  jemput, tujuan, harga, subtotal) — FK ke `invoices`, ON DELETE CASCADE

### 4.4 PDF Generation (tanpa Docker)

- **Utama:** weasyprint (Python; butuh `libpango` di sistem)
- **Fallback:** Chromium headless (sudah terpasang via snap):
  `chromium --headless --no-sandbox --print-to-pdf=out.pdf file.html`
- Template: HTML statis hasil konversi `invoice.blade.php` + logo
  `docs/images/Logo STA Trans.png` (di-embed base64)
- **Cap & tanda tangan tumpang tindih:** file `Cap STA Trans.gif` dan
  `Tanda Tangan Suhendi.gif` dikonversi ke PNG (weasyprint tidak mendukung
  GIF), lalu digabung menjadi satu gambar: **tanda tangan di bawah, cap di
  atas** (seperti dokumen yang ditandatangani dulu baru dicap). Pola ini
  meniru `TenantBrandingService` (merge stamp+signature) di `bus_invoice_app`.

### 4.5 Data Perusahaan (dari `docs/info-perusahaan.md`)

```
Nama   : STA Transport
Alamat : Jl. Akses Tol Cimanggis No. 73, Leuwinanggung, Tapos, Depok 16456
HP     : 0811-800-8613
WA     : 0812-840-21376
Email  : statransdotcom@gmail.com
Web    : www.statransport.co.id  |  www.statranswisata.com
Logo   : docs/images/Logo STA Trans.png
Bank   : BCA — 406 061 5352 — a.n. Suhendi
TTD    : Suhendi — Marketing Executive
Cap    : docs/images/Cap STA Trans.gif
TTD img: docs/images/Tanda Tangan Suhendi.gif
```

---

## 5. Setup Lokal (WSL) — Langkah Eksekusi

> ⚠️ Belum dieksekusi — menunggu persetujuan user.

```bash
# 1. Install Hermes
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.bashrc

# 2. Setup provider LLM (pilih OpenRouter/OpenAI/Nous Portal)
hermes setup

# 3. Bot Telegram: chat @BotFather → /newbot → simpan token
hermes gateway setup     # masukkan token
hermes gateway start

# 4. Dependensi PDF + MySQL (di env Hermes)
uv pip install weasyprint pymysql
sudo apt install -y libpango-1.0-0 libpangocairo-1.0-0   # jika perlu

# 5. Database — jalankan docs/schema-mysql.sql

# 6. Skill
mkdir -p ~/.hermes/skills/invoicing/invoice-sta/{scripts,templates}
# salin SKILL.md, scripts/*, templates/invoice_template.html

# 7. Env/config skill (bank, penandatangan, DB)
#    set di ~/.hermes/.env : INVOICE_DB_* + config skill sta.*

# 8. Uji
hermes    # CLI: /invoice-sta buat invoice a.n. PT Nusa Horizon Wisata...
```

---

## 6. Setup VPS (tanpa Docker)

| Item     | Detail                                                                      |
| -------- | --------------------------------------------------------------------------- |
| OS       | Ubuntu 22.04/24.04 minimal                                                  |
| RAM      | ≥ 1 GB (Hermes ringan, jalan idle)                                          |
| Install  | sama seperti lokal (script resmi)                                           |
| Daemon   | systemd unit `hermes-gateway.service` (Restart=always)                      |
| LLM      | API key via `~/.hermes/.env`                                                |
| MySQL    | pakai server MySQL yang sudah ada + DB `invoice_bot`                        |
| PDF      | weasyprint + libpango (apt) — tanpa container                               |
| Telegram | mode **polling** → tanpa domain/SSL/webhook                                 |
| Backup   | cron: dump MySQL `invoice_bot` + folder `~/.hermes/invoices` + config skill |

Contoh systemd:

```ini
[Unit]
Description=Hermes Gateway (STA Invoice Bot)
After=network.target mysql.service

[Service]
User=hermes
WorkingDirectory=/home/hermes
ExecStart=/home/hermes/.hermes/bin/hermes gateway start
Restart=always
RestartSec=5
EnvironmentFile=/home/hermes/.hermes/.env

[Install]
WantedBy=multi-user.target
```

---

## 7. Keamanan

- Kredensial DB & API key disimpan di `~/.hermes/.env` (bukan di repo/skill).
- Skill membatasi pengguna: gateway Telegram di-pairing hanya dengan chat/user
  tertentu (DM pairing + command approval bawaan Hermes).
- Validasi & hitung ulang total dari qty×price (jangan percaya angka mentah).
- Alur **persetujuan** wajib sebelum PDF final dibuat.
- Backup rutin DB + folder invoice.
- Tidak ada Docker → permukaan serangan lebih kecil.

---

## 8. Estimasi Biaya

| Item                              | Biaya                                               |
| --------------------------------- | --------------------------------------------------- |
| Hermes Agent                      | Gratis (MIT, self-hosted)                           |
| LLM API (OpenRouter, model murah) | ~Rp0 – Rp1.500/pesanan (tergantung model & panjang) |
| VPS 1GB (jika belum ada)          | ±Rp50–100rb/bulan                                   |
| MySQL                             | Sudah ada (Rp0)                                     |
| Domain/SSL                        | Tidak wajib (mode polling)                          |

---

## 9. Risiko & Mitigasi

| Risiko                         | Mitigasi                                                          |
| ------------------------------ | ----------------------------------------------------------------- |
| LLM salah parse angka/tanggal  | Hitung ulang dari qty×price; pratinjau + persetujuan sebelum PDF  |
| Biaya LLM membengkak           | Batasi model murah; cache; mode kaku untuk field standar          |
| PDF beda dari template lama    | Verifikasi visual vs output `bus_invoice_app`; logo + layout sama |
| Data tenant asli belum lengkap | Ambil dari SQL Server live / input manual (bank & penandatangan)  |
| Gateway mati                   | systemd auto-restart; healthcheck cron; notifikasi ke Telegram    |

---

## 10. Timeline Keseluruhan

| Fase                           | Rentang                      | Output                                       |
| ------------------------------ | ---------------------------- | -------------------------------------------- |
| Fase 1 — Persiapan & keputusan | 14-08-2026                   | ✅ Audit, keputusan, template, dokumen       |
| Fase 2 — Setup lokal + skill   | 15–16-08-2026                | Hermes jalan, bot aktif, skill terpasang     |
| Fase 3 — Uji coba & revisi     | 17–18-08-2026                | 2 format teruji, PDF sesuai, record di MySQL |
| Fase 4 — Finalisasi lokal      | 19-08-2026                   | Review sprint, dokumentasi, approval user    |
| Fase 5 — Deploy VPS            | TBD (setelah local approved) | systemd + MySQL + backup                     |

---

## LAMPIRAN

- **A — Schema MySQL** → lihat `docs/schema-mysql.sql`
- **B — File Skill** → ✅ DIREnder ke `skills/invoice-sta/` (source) dan
  `~/.hermes/skills/invoice-sta/` (runtime): SKILL.md,
  `scripts/format_indonesia.py`, `scripts/render_invoice.py`
- **C — Template Invoice** → ✅ v2 redesain: `templates/invoice_template.html`
  (font Inter lokal, warna brand, badge status, kartu info, ringkasan
  perjalanan, tabel baru, watermark DRAFT, cap & ttd tumpang tindih)
- **D — PNG render A4** → `docs/renders/` (5 variasi uji: 1 baris, contoh 2
  baris LUNAS, 5 baris, DP DITERIMA, DRAFT watermark)
