# SPRINT 1 — Persiapan & Setup Otomasi Invoice Telegram (STA Transport)

| Field          | Nilai                                         |
| -------------- | --------------------------------------------- |
| Proyek         | Otomasi Invoice via Telegram — STA Transport  |
| Lokasi         | `/home/heden/projects/n8n_invoice`            |
| Sprint         | Sprint 1 — Persiapan, Keputusan & Setup Lokal |
| Tanggal Mulai  | 14 Agustus 2026                               |
| Target Selesai | 19 Agustus 2026                               |
| Status         | � Berjalan — deploy VPS LIVE (14-08-2026)     |
| Tool utama     | Hermes Agent (Nous Research) — TANPA Docker   |
| DB Record      | MySQL baru: `invoice_bot`                     |

---

## 1. Tujuan Sprint 1

1. Audit environment lokal (WSL Ubuntu) ✅
2. Keputusan arsitektur & tool ✅
3. Template invoice STA Transport disetujui ✅
4. Setup Hermes + gateway Telegram di lokal
5. Skill `invoice-sta` terpasang & teruji (parse → pratinjau → persetujuan → PDF → MySQL)
6. Uji 2 format input (panjang & singkat)
7. Dokumentasi lengkap

---

## 2. Konteks Permintaan

User (STA Transport) ingin membuat **invoice secara otomatis melalui chat Telegram**.
Cara pakai:

- User chat ke bot dengan **bahasa bebas** (format panjang atau singkat).
- Bot mem-parse data, menghitung ulang, menampilkan **pratinjau**.
- Setelah **disetujui**, bot membuat **PDF invoice** (template STA Transport)
  dan mengirimnya kembali ke Telegram.
- Seluruh record tersimpan di **MySQL** (`invoice_bot`).

Prioritas: **uji coba di lokal dulu (WSL)**. Setelah sesuai dan bisa dipakai,
baru **deploy ke VPS**.

---

## 3. Keputusan Penting (Decision Log)

| #   | Tanggal    | Keputusan                                                         | Alasan                                                                                                            |
| --- | ---------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| D1  | 14-08-2026 | Pakai **Hermes Agent**, bukan n8n                                 | Input bahasa natural (2 format), Telegram gateway bawaan, tanpa Docker, jalan di VPS kecil                        |
| D2  | 14-08-2026 | **Tanpa Docker** (local & VPS)                                    | Menghindari beban virtualisasi di VPS                                                                             |
| D3  | 14-08-2026 | **MySQL** untuk record invoice (DB & tabel baru: `invoice_bot`)   | Sudah ada MySQL; tidak perlu Postgres                                                                             |
| D4  | 14-08-2026 | Template **STA Transport** (dari `bus_invoice_app`) **disetujui** | Desain sesuai invoice lama, tinggal tokenisasi                                                                    |
| D5  | 14-08-2026 | Alur **pratinjau → persetujuan → PDF final**                      | Kontrol kualitas sebelum dokumen keluar                                                                           |
| D6  | 14-08-2026 | PDF via **weasyprint** (fallback Chromium headless)               | Murni Python tanpa Docker; Chromium sudah terpasang (snap)                                                        |
| D7  | 14-08-2026 | **Mode polling** Telegram (bukan webhook)                         | Tidak butuh domain/SSL di local maupun VPS                                                                        |
| D8  | 14-08-2026 | Nomor invoice: `INV-YYYY-MM-###`                                  | Konsisten & auto-sequence dari DB                                                                                 |
| D9  | 14-08-2026 | Cap & tanda tangan **tumpang tindih** (ttd dulu, cap di atas)     | Menyerupai dokumen asli yang ditandatangani lalu dicap; mengikuti pola `TenantBrandingService` di bus_invoice_app |

---

## 4. Activity Log

> Waktu dicatat WIB (sesuaikan jika perlu).

| Tanggal    | Waktu  | Aktivitas                     | Detail                                                                                                                                                                                                                                                                   | Oleh           |
| ---------- | ------ | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- |
| 14-08-2026 | ~10:00 | Kickoff & audit environment   | Cek workspace, Node v22.18.0 (nvm), ngrok, Chromium via snap; Docker & n8n TIDAK ada                                                                                                                                                                                     | Copilot        |
| 14-08-2026 | ~10:15 | Riset solusi                  | Bandingkan Hermes vs n8n untuk invoice Telegram; Hermes = AI agent + gateway Telegram                                                                                                                                                                                    | Copilot        |
| 14-08-2026 | ~10:30 | Riset template                | Temukan `invoice.blade.php` + helper `IndonesianFormat` & `Terbilang` di `bus_invoice_app`                                                                                                                                                                               | Copilot        |
| 14-08-2026 | ~11:00 | Keputusan tool                | User pilih **Hermes Agent**; template disetujui; MySQL DB baru                                                                                                                                                                                                           | User + Copilot |
| 14-08-2026 | ~11:15 | Temuan data tenant            | Seed `bus_invoice_app` hanya berisi tenant DEMO; app pakai SQL Server (bukan MySQL); data asli STA harus diambil dari DB live / input manual                                                                                                                             | Copilot        |
| 14-08-2026 | ~11:30 | Penyusunan skill              | Draf `SKILL.md` + `format_indonesia.py` + `render_invoice.py` + struktur `~/.hermes/skills/`                                                                                                                                                                             | Copilot        |
| 14-08-2026 | ~12:00 | Data perusahaan               | User sediakan `docs/info-perusahaan.md` + logo `docs/images/Logo STA Trans.png`                                                                                                                                                                                          | User           |
| 14-08-2026 | ~12:15 | Penyusunan dokumen            | Sprint doc + laporan infrastruktur                                                                                                                                                                                                                                       | Copilot        |
| 14-08-2026 | ~12:30 | Render dokumen                | `SPRINT-1.md`, `LAPORAN-INFRASTRUKTUR.md`, `schema-mysql.sql` ditulis ke `docs/`                                                                                                                                                                                         | Copilot        |
| 14-08-2026 | ~13:00 | Data pelengkap                | User tambahkan bank (BCA 406 061 5352 a.n. Suhendi), penandatangan Suhendi (Marketing Executive), file cap & tanda tangan di `docs/images/`                                                                                                                              | User           |
| 14-08-2026 | ~13:15 | Desain cap & ttd              | Keputusan: cap & tanda tangan tumpang tindih (ttd → cap di atas); perlu konversi GIF→PNG + merge gambar                                                                                                                                                                  | User + Copilot |
| 14-08-2026 | ~13:30 | Render skill & template       | ✅ Disetujui user. Source skill dibuat di `skills/invoice-sta/` (SKILL.md, scripts, templates, assets) & dicopy ke runtime `~/.hermes/skills/invoice-sta/`                                                                                                               | Copilot        |
| 14-08-2026 | ~14:00 | Install Hermes                | `curl ... install.sh`; uv + Python 3.11 + Node + venv terinstall; login Nous Portal (model `poolside/laguna-s-2.1:free`); 82 bundled skills; systemd user service aktif                                                                                                  | Copilot        |
| 14-08-2026 | ~14:02 | Konfig Telegram               | `TELEGRAM_BOT_TOKEN` di `~/.hermes/.env`; token valid → bot `@statrans_invoice_bot` (STA Transport Invoice)                                                                                                                                                              | Copilot        |
| 14-08-2026 | ~14:03 | Debug koneksi Telegram        | Error `Any cannot be instantiated`: PTB belum terinstall saat plugin pertama di-load (install Hermes fallback PyPI) → restart gateway → **Connected (polling mode)**                                                                                                     | Copilot        |
| 14-08-2026 | ~14:06 | DB invoice_bot                | Jalankan `docs/schema-mysql.sql` (root@127.0.0.1, tanpa password) → tabel `invoices` + `invoice_items`                                                                                                                                                                   | Copilot        |
| 14-08-2026 | ~14:08 | Dependensi skill              | venv `~/.hermes/venvs/invoice-sta` (Py3.11): pillow 12.3, weasyprint 69, pymysql 2.2                                                                                                                                                                                     | Copilot        |
| 14-08-2026 | ~14:10 | Uji pipeline (format panjang) | Draft PT Nusa Horizon Wisata → PDF `INV-2026-08-001.pdf` ✅ + record MySQL (1 invoice + 2 items) ✅; terbilang, cap+ttd merge, bank diverifikasi                                                                                                                         | Copilot        |
| 14-08-2026 | ~14:15 | Uji live Telegram             | ⏳ Menunggu user DM `@statrans_invoice_bot` → pairing code → approve → tes 2 format + revisi                                                                                                                                                                             | User           |
| 14-08-2026 | ~14:20 | Pairing Telegram              | User DM `@statrans_invoice_bot` → kode `WS3EF9MF` → approve → **Heden (1301178833)** diizinkan akses bot                                                                                                                                                                 | User + Copilot |
| 14-08-2026 | ~15:00 | Redesain UI/UX invoice (v2)   | Template baru: font Inter lokal, warna brand (biru #1769A6/navy #12324A/merah #D64045), badge status, kartu info pembayaran, ringkasan perjalanan, tabel rincian baru, watermark DRAFT, cap+ttd tumpang tindih. Struktur data baru (customer/trip_summary/items/payment) | Copilot        |
| 14-08-2026 | ~15:30 | Uji render v2                 | 1/2/5 baris perjalanan → **1 halaman A4** ✅; skenario DP (Uang Muka + Sisa Tagihan) ✅; DRAFT watermark ✅; rupiah `Rp10.800.000`; PNG render di `docs/renders/` (5 variasi)                                                                                            | Copilot        |
| 14-08-2026 | ~16:00 | Redesain v3 (3 komposisi)     | Desain v2 DITOLAK (terlihat dashboard). Audit → 3 alternatif di `docs/designs/`: Editorial Corporate, Classic Commercial, Modern Transport Manifest (PNG A4, 1 halaman). Format nomor invoice → `INV-0001/STA/VIII/2026` (bulan Romawi/tahun). Menunggu pilihan user     | User + Copilot |
| 14-08-2026 | ~16:30 | Implementasi desain terpilih  | User pilih **Modern Transport Manifest**. Template produksi + render script ditulis ulang (manifest strip navy, hero route, tabel ref TR-XX, total navy, footer 1 baris). Uji 7 variasi (1/2/5 item, DP, DRAFT, nama panjang, rute panjang) → **semua 1 halaman A4** ✅  | Copilot        |
| 14-08-2026 | ~16:45 | Persetujuan desain final      | User menyetujui desain **Modern Transport Manifest** ("ok mantab"). Siap uji live via Telegram                                                                                                                                                                           | User           |
| 14-08-2026 | ~18:55 | Akses grup Telegram           | Grup "STA TRANS" (chat `-5483961981`) di-allowlist (`TELEGRAM_GROUP_ALLOWED_CHATS`), privacy off, bot di-remove & di-add ulang. Pesan grup diterima & bot merespons ✅                                                                                                   | User + Copilot |

---

## 4b. Activity Log — Deploy VPS (14-08-2026)

| Tanggal    | Waktu  | Aktivitas                     | Detail                                                                                                                                                                                                                                                                                                                            | Oleh           |
| ---------- | ------ | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| 14-08-2026 | ~19:30 | Perbaikan konsistensi skill   | Fix path `~` → absolut di SKILL.md (source & runtime); format nomor preview; `discount_total` di MySQL (fix placeholder 16→15); regex `next_invoice_number`; uji pipeline penuh (PDF + MySQL) ✅                                                                                                                                  | Copilot        |
| 14-08-2026 | ~20:00 | Audit VPS production          | SSH `denjaka@103.150.191.235` (`nakatara-server`): Ubuntu 24.04.4, 4 vCPU, 3.8 GB RAM, disk 79% (sisa 13 GB); service nginx+php8.4+mariadb 11.4+redis+supervisor+fail2ban; 6 DB production (indobuswisata_db 200MB, nakatara_wp619/910, travelcianjur_order, passlinkdb, travelcianjurdb kosong); Hermes belum ada; app live aman | Copilot        |
| 14-08-2026 | ~20:19 | Deploy VPS — user & DB        | User OS `invoicebot` dibuat; DB `invoice_bot` + user MySQL `invoice_bot` (grant SELECT/INSERT/UPDATE/DELETE hanya DB ini) + kredensial di `.env` (600); schema `invoices`+`invoice_items` di-load                                                                                                                                 | Copilot        |
| 14-08-2026 | ~20:21 | Deploy VPS — Hermes           | Install Hermes v0.20.1 utk user invoicebot; config model Nous (`poolside/laguna-s-2.1:free`); venv skill (weasyprint 69 + libpango + pymysql + pillow); skill disalin & enabled; env Telegram + group allowlist                                                                                                                   | Copilot        |
| 14-08-2026 | ~20:34 | Deploy VPS — systemd gateway  | Unit `hermes-gateway.service` (User=invoicebot, Restart=always); kendala: `dotenv`, `Any cannot be instantiated`, polling conflict → diperbaiki (launcher bash + venv benar + stop gateway lokal)                                                                                                                                 | Copilot        |
| 14-08-2026 | ~20:57 | **CUTOVER — bot LIVE di VPS** | Gateway lokal WSL distop; VPS `hermes-gateway` **Connected (polling mode)**; skill `invoice-sta` enabled; 60 commands registered; render test PDF di VPS ✅                                                                                                                                                                       | User + Copilot |

---

## 5. Rencana Kerja (Timeline)

| Hari       | Tanggal    | Target                                                                          |
| ---------- | ---------- | ------------------------------------------------------------------------------- |
| ✅ Selesai | 14-08-2026 | Audit, keputusan, template, draf skill, dokumen sprint                          |
| ✅ Selesai | 14-08-2026 | Install Hermes + setup + gateway Telegram (maju dari jadwal)                    |
| ✅ Selesai | 14-08-2026 | Skill `invoice-sta` + dependensi venv + DB `invoice_bot` (maju dari jadwal)     |
| ✅ Selesai | 14-08-2026 | Uji pipeline format PANJANG → PDF + MySQL (maju dari jadwal)                    |
| ⏳ 4       | 18-08-2026 | Uji format SINGKAT (live Telegram); skenario revisi & DP; perbaikan             |
| ⏳ 5       | 19-08-2026 | Validasi PDF vs template lama, backup, finalisasi dokumen → **Review Sprint 1** |

---

## 6. Checklist

- [x] Install Hermes di WSL ✅
- [x] `hermes setup` (provider LLM + API key) ✅ (Nous Portal, model `poolside/laguna-s-2.1:free`)
- [x] Buat bot Telegram via @BotFather → token ✅ (`@statrans_invoice_bot`)
- [x] `hermes gateway` + start ✅ (Connected, polling mode)
- [x] Install dependensi skill di venv ✅ (`~/.hermes/venvs/invoice-sta`: pillow, weasyprint, pymysql)
- [x] Buat DB `invoice_bot` + tabel `invoices` & `invoice_items` ✅
- [x] Pasang skill `invoice-sta` ✅ (terdaftar & enabled di Hermes)
- [x] Lengkapi config skill (data perusahaan, bank, penandatangan) ✅ (default baked-in)
- [x] Uji format panjang → PDF sesuai template ✅ (`INV-2026-08-001.pdf`, konten diverifikasi)
- [ ] Uji format singkat (via Telegram live — menunggu pairing)
- [ ] Uji alur revisi & persetujuan (via Telegram live)
- [x] Record tersimpan di MySQL ✅ (1 invoice + 2 items)
- [x] Deploy VPS: user `invoicebot`, DB+user MySQL `invoice_bot`, Hermes, skill, systemd gateway ✅
- [x] Cutover: gateway lokal distop → bot LIVE di VPS (Connected polling) ✅
- [ ] Tes live via Telegram (VPS): format singkat, revisi, persetujuan → PDF + MySQL
- [ ] Dokumentasi sprint finalisasi

---

## 7. Open Items / Blocker

1. Data perusahaan untuk config skill — SUDAH ADA via `docs/info-perusahaan.md` ✅
   - Alamat: Jl. Akses Tol Cimanggis No. 73, Leuwinanggung, Tapos, Depok 16456
   - HP: 0811-800-8613 | WA: 0812-840-21376 | Email: statransdotcom@gmail.com
   - Website: www.statransport.co.id (dan www.statranswisata.com)
   - Logo: `docs/images/Logo STA Trans.png`
2. Data bank & penandatangan — ✅ SUDAH ADA
   - Bank: BCA — 406 061 5352 — a.n. Suhendi
   - Penandatangan: Suhendi — Marketing Executive
   - Cap: `docs/images/Cap STA Trans.gif` | TTD: `docs/images/Tanda Tangan Suhendi.gif`
3. Kredensial MySQL — ✅ local: `root@127.0.0.1` tanpa password. **Produksi VPS: user `invoice_bot` (password acak di `/home/invoicebot/.hermes/.env`, permission 600)** ✅
4. Akses Telegram — ✅ DM pairing selesai: **Heden (1301178833)** di-approve
5. Uji live 2 format + revisi/persetujuan — ⏳ dalam proses (user sudah bisa tes di bot)

---

## 8. Catatan Proses

- Semua eksekusi (install, konfigurasi, deploy) **hanya dilakukan setelah ada persetujuan eksplisit user**.
- Aktivitas dicatat di dokumen ini secara berkelanjutan.
- Komit/Git: hanya atas perintah eksplisit user.

---

## 9. Log Revisi

| Tanggal    | Revisi | Detail                |
| ---------- | ------ | --------------------- |
| 14-08-2026 | v1.0   | Dokumen sprint dibuat |
