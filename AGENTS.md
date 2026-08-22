# AGENTS.md

# STA Transport — Telegram Invoice Automation

Dokumen ini berisi aturan kerja permanen untuk AI Agent yang bekerja pada
proyek otomasi invoice STA Transport.

Seluruh agent WAJIB membaca dokumen ini sebelum melakukan analisis,
perubahan kode, instalasi, konfigurasi, atau pengujian.

---

## 1. Project Identity

Project:

STA Transport — Telegram Invoice Automation

Workspace utama:

`/home/heden/projects/n8n_invoice`

Environment development:

- Windows 11
- WSL Ubuntu
- Tanpa Docker

Target deployment setelah local development stabil:

- Linux VPS
- Tanpa Docker

---

## 2. Tujuan Sistem

Sistem digunakan untuk membuat invoice STA Transport melalui percakapan
Telegram menggunakan bahasa natural.

User tidak diwajibkan menggunakan format input yang kaku.

Sistem harus mendukung minimal:

1. format input panjang;
2. format input singkat;
3. revisi data invoice melalui percakapan;
4. approval sebelum invoice final dibuat.

Flow utama WAJIB:

Telegram
→ Hermes Agent
→ Parse input
→ Normalisasi data
→ Validasi
→ Hitung ulang
→ Preview invoice
→ User approval
→ Generate PDF
→ Simpan MySQL
→ Kirim PDF ke Telegram

Dilarang melewati tahap approval untuk invoice final kecuali requirement
tersebut secara eksplisit diubah oleh user.

---

# 3. Architecture Decisions

Keputusan arsitektur berikut dianggap APPROVED dan menjadi default proyek.

## AI Agent

Gunakan:

**Hermes Agent — Nous Research**

Jangan mengganti Hermes dengan:

- n8n
- LangChain
- custom Telegram framework
- platform automation lainnya

tanpa persetujuan eksplisit user.

n8n bukan bagian dari arsitektur aktif meskipun nama workspace saat ini:

`n8n_invoice`

Nama folder tidak boleh dijadikan alasan untuk mengganti arsitektur.

---

## 4. Docker Policy

Project berjalan:

**TANPA Docker**

Berlaku untuk:

- local development;
- testing;
- production VPS.

Jangan membuat:

- Dockerfile;
- docker-compose.yml;
- container architecture;

kecuali diminta secara eksplisit oleh user.

Gunakan native Linux/WSL environment.

---

# 5. Telegram Architecture

Gunakan Telegram sebagai interface utama.

Mode Telegram:

**Long Polling**

Bukan webhook.

Alasan:

- local development tidak membutuhkan public endpoint;
- tidak membutuhkan domain;
- tidak membutuhkan SSL;
- deployment VPS lebih sederhana.

Jangan mengganti polling menjadi webhook tanpa persetujuan user.

Telegram token tidak boleh disimpan dalam Git repository.

Gunakan environment variable/configuration rahasia.

---

# 6. Hermes Skill

Skill utama proyek:

`invoice-sta`

Lokasi runtime yang ditargetkan:

`~/.hermes/skills/invoice-sta/`

Skill bertanggung jawab terhadap:

- parsing percakapan;
- normalisasi data;
- validasi;
- kalkulasi invoice;
- preview;
- approval state;
- rendering invoice;
- penyimpanan database;
- response Telegram.

Jika source skill disimpan di repository project, runtime copy dan source
harus dijaga konsisten.

Jangan mengedit runtime skill tanpa memastikan source project juga
terdokumentasi.

---

# 7. Natural Language Input

Bot harus menerima input menggunakan bahasa manusia/bahasa bebas.

Contoh informasi yang dapat muncul:

- nama pemesan/perusahaan;
- tanggal perjalanan;
- jumlah kendaraan;
- jenis kendaraan;
- lokasi jemput;
- tujuan;
- harga per unit;
- jumlah hari;
- fasilitas yang termasuk;
- biaya yang tidak termasuk;
- DP;
- pelunasan;
- catatan;
- informasi tambahan.

Urutan informasi tidak boleh diasumsikan tetap.

Agent harus melakukan ekstraksi berdasarkan arti/semantik,
bukan posisi teks semata.

---

# 8. Input Modes

Minimal dua pola penggunaan harus didukung.

## Format panjang

User memberikan informasi invoice secara lengkap dalam beberapa kalimat
atau paragraf.

## Format singkat

User dapat memberikan input seperti:

`PT ABC | 2 medium | 15 Agu | Harapan Indah-Puncak | 2.8jt/unit`

Agent harus mencoba mengubah input tersebut menjadi struktur invoice yang
sama dengan format panjang.

Jika informasi kritis tidak tersedia, jangan mengarang data.

Tanyakan hanya informasi yang benar-benar dibutuhkan.

---

# 9. Invoice Processing Rules

Semua nilai invoice harus dihitung ulang oleh aplikasi.

Jangan mempercayai total yang diketik user tanpa verifikasi.

Contoh:

quantity = 2
unit_price = 2,800,000

maka:

subtotal = quantity × unit_price
subtotal = 5,600,000

Jika total dari input user berbeda dengan hasil perhitungan sistem,
gunakan hasil kalkulasi sistem dan tampilkan perbedaannya pada preview.

Semua kalkulasi keuangan dilakukan menggunakan tipe numeric/decimal,
bukan floating point bila berpotensi menyebabkan rounding error.

---

# 10. Approval Workflow

State minimum invoice:

- DRAFT
- PREVIEW
- APPROVED
- GENERATED

Opsional bila dibutuhkan:

- CANCELLED
- REVISED
- SENT

Invoice PDF final hanya boleh dibuat setelah:

`APPROVED`

Contoh approval natural language yang dapat diterima:

- setuju
- oke
- ok
- lanjut
- buat invoice
- generate
- sudah benar

Tetap perhatikan konteks percakapan.

Jangan menganggap semua kata "ok" sebagai approval jika konteksnya tidak
jelas berkaitan dengan preview terakhir.

---

# 11. Revision Workflow

Sebelum approval, user dapat melakukan revisi melalui percakapan.

Contoh:

`alamat jemput ganti Harapan Indah Bekasi`

atau:

`tidak usah DP, langsung pelunasan`

Agent harus:

1. mengambil draft invoice aktif;
2. mengubah field terkait saja;
3. mempertahankan field lainnya;
4. menghitung ulang bila diperlukan;
5. menampilkan preview baru;
6. meminta approval kembali.

Jangan membuat invoice baru hanya karena user melakukan koreksi kecil
terhadap draft aktif.

---

# 12. Invoice Number

Format nomor invoice:

`INV-XXXX/STA/BULAN_ROMawi/TAHUN`

Contoh:

`INV-0001/STA/VIII/2026`

- `XXXX` = urutan 4 digit dari database.
- `STA` = kode perusahaan.
- `BULAN_ROMawi` = bulan (I–XII) sesuai tanggal invoice.
- `TAHUN` = tahun.

Sequence diambil dari database.

Nomor invoice tidak boleh dibuat berdasarkan tebakan agent.

Sequence harus aman terhadap duplicate invoice number.

Database menjadi source of truth nomor invoice.

---

# 13. Database

Database engine:

**MySQL**

Database:

`invoice_bot`

Minimum entities:

- invoices
- invoice_items

Gunakan schema resmi proyek:

`schema-mysql.sql`

Jangan mengganti database menjadi:

- PostgreSQL
- SQLite
- SQL Server

tanpa persetujuan user.

Aplikasi lama `bus_invoice_app` dapat digunakan sebagai referensi
template/business rule, tetapi database aplikasi tersebut bukan database
utama sistem invoice Telegram.

---

# 14. Database Persistence

Database harus menyimpan minimal informasi header invoice dan item
perjalanan.

Hubungan:

`invoices 1:N invoice_items`

Jangan menyimpan seluruh invoice hanya sebagai text/blob jika informasi
tersebut seharusnya dapat dinormalisasi.

Raw user message boleh disimpan sebagai audit/reference tambahan.

Jika relevan, pertimbangkan menyimpan:

- raw_input;
- parsed payload;
- status;
- timestamps;
- Telegram chat/user reference;
- generated PDF path.

Tetapi perubahan schema harus tetap mengikuti schema resmi proyek.

---

# 15. PDF Generation

Renderer utama:

**WeasyPrint**

Fallback:

**Chromium Headless**

Jangan mengganti renderer utama tanpa alasan teknis yang jelas dan
persetujuan user.

PDF harus menggunakan template STA Transport yang sudah disetujui.

---

# 16. Invoice Template Policy

Template existing STA Transport berasal dari referensi:

`bus_invoice_app`

Referensi utama sebelumnya:

`invoice.blade.php`

Helper referensi:

- IndonesianFormat
- Terbilang

Template tersebut digunakan sebagai baseline desain invoice.

Jangan melakukan redesign besar terhadap:

- layout;
- logo;
- posisi informasi;
- typography;
- struktur tabel;
- rekening;
- tanda tangan;
- cap/stempel;

tanpa permintaan user.

Perubahan teknis untuk tokenisasi/dynamic data diperbolehkan selama
hasil visual tetap konsisten.

---

# 17. Indonesian Formatting

Gunakan format Indonesia untuk nilai uang.

Contoh:

`Rp2.800.000`

atau mengikuti format visual template resmi STA Transport.

Gunakan format tanggal Indonesia bila sesuai template.

Terbilang harus menggunakan Bahasa Indonesia.

Contoh:

`Lima Juta Enam Ratus Ribu Rupiah`

Format harus konsisten di seluruh invoice.

---

# 18. Company Information

Source of truth informasi perusahaan:

`docs/info-perusahaan.md`

Logo:

`docs/images/Logo STA Trans.png`

Jangan hardcode ulang informasi perusahaan ke banyak file jika dapat
menggunakan satu configuration/source of truth.

Jika informasi perusahaan berubah, prioritaskan perubahan pada config
atau source yang terpusat.

---

# 19. Secrets & Credentials

DILARANG memasukkan secret berikut ke repository:

- Telegram bot token;
- LLM API key;
- MySQL password;
- SSH credential;
- VPS credential;
- secret lainnya.

Gunakan environment variable.

Contoh:

`.env`

Pastikan `.env` masuk `.gitignore`.

Boleh menyediakan:

`.env.example`

tetapi hanya dengan placeholder.

Contoh:

TELEGRAM_BOT_TOKEN=
MYSQL_HOST=
MYSQL_PORT=
MYSQL_DATABASE=invoice_bot
MYSQL_USER=
MYSQL_PASSWORD=
LLM_API_KEY=

---

# 20. Security Rules

Semua input Telegram dianggap untrusted input.

Lakukan:

- validation;
- sanitization;
- type validation;
- numeric validation;
- SQL parameter binding.

Dilarang membuat SQL query dengan string concatenation dari input user.

Gunakan prepared statement/parameterized query.

Jangan menjalankan shell command berdasarkan isi Telegram tanpa whitelist
dan validation yang sangat ketat.

---

# 21. Error Handling

Error internal tidak boleh langsung dilempar mentah ke Telegram.

Jangan mengirim:

- stack trace;
- database password;
- API key;
- filesystem sensitive path;
- internal configuration.

User Telegram cukup menerima pesan yang dapat dimengerti.

Detail teknis dapat ditulis ke local log.

---

# 22. Logging

Logging harus membantu troubleshooting tetapi tidak menyimpan secret.

Boleh log:

- invoice ID;
- invoice number;
- processing stage;
- Telegram chat identifier;
- status;
- error category.

Hindari mencatat:

- API key;
- bot token;
- password;
- full credential.

---

# 23. Source of Truth

Gunakan dokumen berikut sesuai kebutuhannya.

## Permanent agent rules

`AGENTS.md`

## Sprint progress

`docs/SPRINT-1.md`

## Infrastructure

`docs/LAPORAN-INFRASTRUKTUR.md`

## Company information

`docs/info-perusahaan.md`

## Database

`schema-mysql.sql`

## Company logo

`docs/images/Logo STA Trans.png`

Jika terjadi konflik:

1. instruksi terbaru user;
2. AGENTS.md;
3. decision/architecture documentation;
4. sprint documentation;
5. existing implementation.

Instruksi terbaru user selalu memiliki prioritas tertinggi.

---

# 24. Change Control — VERY IMPORTANT

Agent TIDAK BOLEH langsung melakukan tindakan yang mengubah environment
atau source code jika user belum memberikan persetujuan eksplisit.

Tindakan berikut membutuhkan approval user:

- install package;
- uninstall package;
- mengubah source code;
- membuat/mengubah database;
- menjalankan migration;
- mengubah config;
- mengubah `.env`;
- menjalankan Hermes setup;
- mengubah Telegram gateway;
- deploy;
- restart production service;
- push Git;
- commit Git;
- membuat Pull Request;
- menghapus file/data;
- melakukan perubahan irreversible.

Agent boleh tanpa approval:

- membaca file;
- melakukan audit;
- melakukan analisis;
- mencari penyebab masalah;
- menyusun rekomendasi;
- membuat rencana perubahan;
- menjelaskan command yang akan digunakan.

Jika user meminta audit saja:

**JANGAN melakukan perubahan.**

---

# 25. Git Policy

Jangan melakukan:

- git commit;
- git push;
- merge;
- rebase;
- reset;
- checkout yang berisiko menghilangkan perubahan;
- force push;

tanpa perintah eksplisit user.

Sebelum perubahan signifikan, periksa status repository bila tersedia.

Jangan menghapus perubahan milik user yang tidak berhubungan dengan
pekerjaan saat ini.

---

# 26. Existing Code Policy

Sebelum membuat implementasi baru:

1. inspect existing project;
2. cari implementation yang sudah tersedia;
3. cari helper yang sudah ada;
4. pahami flow existing;
5. reuse bila layak.

Hindari membuat duplicate helper atau duplicate business logic.

Jangan mengganti bagian sistem yang sudah bekerja hanya untuk membuat
implementasi terlihat lebih sederhana.

---

# 27. Scope Discipline

Jangan melakukan refactoring di luar scope task saat ini.

Contoh:

Jika user meminta memperbaiki parsing invoice,
jangan sekaligus:

- mengganti database;
- mengganti framework;
- redesign template;
- mengubah deployment architecture.

Jika menemukan masalah lain, laporkan sebagai temuan terpisah.

---

# 28. Testing Requirements

Minimal test yang harus dapat dilakukan pada sistem invoice:

## Scenario A — Long format

Input invoice lengkap.

Expected:

parse
→ calculation
→ preview
→ approval
→ PDF
→ database record
→ Telegram response

## Scenario B — Short format

Input invoice singkat.

Expected flow sama dengan Scenario A.

## Scenario C — Revision

Input awal
→ preview
→ user mengubah satu field
→ preview diperbarui
→ approval
→ PDF.

## Scenario D — Payment

Harus dapat menangani:

- DP;
- pelunasan;
- tanpa DP;
- invoice langsung lunas;

sesuai instruksi user.

---

# 29. Definition of Done

Fitur invoice belum dianggap selesai hanya karena PDF berhasil dibuat.

Minimum Definition of Done:

- input berhasil diparse;
- data tervalidasi;
- kalkulasi benar;
- preview tampil;
- revision bekerja;
- approval bekerja;
- PDF sesuai template;
- database tersimpan;
- invoice number benar;
- file berhasil dikirim melalui Telegram;
- tidak ada credential bocor;
- dokumentasi terkait diperbarui.

---

# 30. Agent Behaviour

Saat menerima task:

1. baca `AGENTS.md`;
2. identifikasi scope;
3. baca file yang relevan;
4. jangan membuat asumsi jika informasi tersedia di project;
5. lakukan audit terlebih dahulu;
6. jelaskan temuan;
7. jika perubahan diperlukan, jelaskan perubahan yang akan dilakukan;
8. tunggu approval apabila perubahan membutuhkan approval;
9. setelah disetujui, lakukan perubahan terfokus;
10. lakukan test;
11. laporkan hasil dan file yang berubah.

Prioritaskan:

- correctness;
- consistency;
- maintainability;
- data integrity;
- safety;

dibanding sekadar membuat fitur cepat selesai.

---

# 31. Do Not Assume

Agent tidak boleh mengarang:

- rekening bank;
- nama penandatangan;
- harga;
- alamat customer;
- tanggal perjalanan;
- DP;
- jumlah kendaraan;
- nomor invoice;
- informasi perusahaan.

Jika data tersebut sudah tersedia di source/config/database, gunakan
source tersebut.

Jika benar-benar tidak tersedia dan diperlukan untuk invoice,
minta informasi tersebut kepada user.

---

# 32. Current Project Direction

Arah proyek yang sudah disetujui:

**Local first → validation → VPS deployment**

Jangan melakukan production deployment sebelum local flow dinyatakan
sesuai oleh user.

Target local system:

Hermes

- Telegram Polling
- invoice-sta Skill
- WeasyPrint
- MySQL invoice_bot

Setelah stabil baru dilakukan deployment ke VPS.
