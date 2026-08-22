---
name: invoice-sta
description: Membuat invoice penagihan STA Transport dari pesan bahasa Indonesia
  (format panjang maupun singkat). Parse data pemesan dan rincian perjalanan,
  hitung ulang total, tampilkan pratinjau, minta persetujuan, lalu render PDF
  template STA (cap & ttd tumpang tindih) dan simpan ke MySQL. Gunakan saat
  user minta "buat invoice", "buatkan invoice", atau "invoice a.n. ...".
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [invoice, sta, transport, billing, tagihan]
    category: invoicing
    config:
      - key: sta.company_name
        description: Nama perusahaan penerbit
        default: "STA Transport"
      - key: sta.company_address
        description: Alamat perusahaan penerbit
        default: "Jl. Akses Tol Cimanggis No. 73, Leuwinanggung, Tapos, Depok 16456"
      - key: sta.company_email
        description: Email perusahaan penerbit
        default: "statransdotcom@gmail.com"
      - key: sta.company_phone
        description: Telepon perusahaan penerbit
        default: "0811-800-8613"
      - key: sta.bank_name
        description: Nama bank tujuan pembayaran
        default: "BCA"
      - key: sta.bank_account_number
        description: Nomor rekening tujuan pembayaran
        default: "406 061 5352"
      - key: sta.bank_account_holder
        description: Pemilik rekening tujuan pembayaran
        default: "Suhendi"
      - key: sta.signatory_name
        description: Nama penandatangan invoice
        default: "Suhendi"
      - key: sta.signatory_position
        description: Jabatan penandatangan invoice
        default: "Marketing Executive"
      - key: sta.signatory_city
        description: Kota pada kolom tanda tangan
        default: "Jakarta"
required_environment_variables:
  - name: INVOICE_DB_HOST
    prompt: Host MySQL
    default: "127.0.0.1"
  - name: INVOICE_DB_PORT
    prompt: Port MySQL
    default: "3306"
  - name: INVOICE_DB_USER
    prompt: User MySQL
    default: "root"
  - name: INVOICE_DB_PASSWORD
    prompt: Password MySQL (kosongkan bila root lokal tanpa password)
    default: ""
  - name: INVOICE_DB_NAME
    prompt: Nama database MySQL
    default: "invoice_bot"
---

# Invoice STA Transport

## When to Use

Gunakan saat user meminta pembuatan invoice/tagihan STA Transport dengan
deskripsi bebas bahasa Indonesia (format panjang maupun singkat), atau meminta
revisi/preview invoice yang sedang dibuat.

## Data Default

- Termasuk: Unit kendaraan, Pengemudi, BBM
- Tidak termasuk: Tol, Parkir, Tips pengemudi
- Penerbit, bank & tanda tangan: dari config skill `sta.*`
- Cap & tanda tangan digabung **tumpang tindih** otomatis oleh render script
  (ttd di bawah, cap di atas — seperti ditandatangani dulu lalu dicap).

## Procedure

1. **Parse** pesan menjadi struktur JSON (template desain baru):

   ```json
   {
     "invoice_date": "2026-08-14",
     "payment_status": "LUNAS",
     "payment_type": "FULL_PAYMENT",
     "customer": {
       "name": "PT Nusa Horizon Wisata",
       "address": "",
       "phone": "",
       "email": ""
     },
     "trip_summary": {
       "vehicle_type": "Medium Bus",
       "total_units": 2,
       "departure_date": "2026-08-15",
       "return_date": "2026-08-17",
       "pickup_address": "Harapan Indah, Bekasi",
       "destination": "Cisarua, Puncak",
       "duration": "3 hari"
     },
     "items": [
       {
         "description": "Harapan Indah, Bekasi ke Cisarua, Puncak – 15 Agustus 2026",
         "vehicle_type": "Medium Bus",
         "quantity": 2,
         "unit_price": 2800000,
         "subtotal": 5600000
       }
     ],
     "subtotal": 10800000,
     "discount": 0,
     "additional_fee": 0,
     "grand_total": 10800000,
     "paid_amount": 10800000,
     "remaining_balance": 0,
     "amount_in_words": "sepuluh juta delapan ratus ribu rupiah",
     "notes": [
       "Harga termasuk unit kendaraan, pengemudi, dan BBM.",
       "Harga belum termasuk tol, parkir, dan tips pengemudi."
     ]
   }
   ```

   - `invoice_date` default = hari ini bila tidak disebut.
   - `payment_status` (LUNAS / BELUM LUNAS / DP DITERIMA / DRAFT / DIBATALKAN):
     - `LUNAS` hanya bila `paid_amount >= grand_total`.
     - `DRAFT` → PDF diberi watermark transparan (badge abu-abu).
   - `payment_type`: `FULL_PAYMENT` (langsung lunas, tanpa bagian DP) atau
     teks DP/pelunasan.
   - `notes` (array) = baris catatan (termasuk/tidak termasuk).
   - Sertakan `source_chat` = ID chat Telegram (untuk kolom audit di MySQL).
   - Field kosong TIDAK ditampilkan di template.
   - Jika informasi kritis tidak ada, TANYAKAN — jangan mengarang data.

2. **Hitung ulang** (jangan percaya total yang diketik user):
   - `subtotal` per item = `quantity * unit_price`
   - `subtotal` = Σ per item
   - `grand_total = subtotal - discount + additional_fee`
   - `remaining_balance = grand_total - paid_amount`
   - Jika total user berbeda dari hasil hitung sistem, tampilkan selisihnya di
     preview dan gunakan hasil hitung sistem.

3. **Terbilang**: jalankan
   `/home/heden/.hermes/venvs/invoice-sta/bin/python scripts/format_indonesia.py terbilang <grand_total>`
   lalu set `amount_in_words`. Format rupiah baru: `Rp10.800.000` (tanpa spasi,
   tanpa ',-').

4. **PRATINJAU** — kirim ringkasan dan MINTA PERSETUJUAN. Contoh:

   ```
   📄 PRATINJAU INVOICE — STA TRANSPORT
   Status : LUNAS (badge hijau) | No: INV-XXXX/STA/VIII/2026 (ditetapkan saat generate)
   Kepada : PT Nusa Horizon Wisata
   Tanggal: 14 Agustus 2026 | Pembayaran: FULL_PAYMENT
   Ringkasan: Medium Bus, 2 unit, 15-17 Agustus 2026, 3 hari
   Rute   : Harapan Indah, Bekasi → Cisarua, Puncak
   1. Medium Bus — Harapan Indah, Bekasi ke Cisarua, Puncak – 15 Agustus 2026
      @Rp2.800.000 × 2 = Rp5.600.000
   2. Medium Bus — Jemput Cisarua, Puncak, drop Jakarta – 17 Agustus 2026
      @Rp2.600.000 × 2 = Rp5.200.000
   Subtotal  : Rp10.800.000
   Total     : Rp10.800.000
   Terbilang : Sepuluh juta delapan ratus ribu rupiah.
   Setuju? (setuju / revisi ...)
   ```

   JANGAN membuat PDF sebelum persetujuan (AGENTS.md §10).

5. **Revisi**: jika user mengoreksi, ubah field terkait saja, hitung ulang,
   tampilkan preview baru, minta persetujuan lagi. Jangan buat invoice baru
   hanya karena koreksi kecil (AGENTS.md §11).

6. Setelah **disetujui**, tulis JSON ke file sementara (sertakan `request_id` random
   dan `source_chat` = ID numerik chat dari konteks gateway) lalu jalankan dengan
   `--chat <ID_NUMERIK_CHAT>` (WAJIB; contoh grup `-5483961981`, DM `1301178833`):

   ```
   /home/invoicebot/.hermes/venvs/invoice-sta/bin/python scripts/render_invoice.py /tmp/invoice_draft.json --chat -5483961981
   ```

   Script akan: menentukan nomor invoice dari DB (`INV-0001/STA/VIII/2026`), render
   PDF, simpan ke MySQL, LALU **mengirim PDF langsung ke chat** lewat Bot API.
   Script mencetak status yang HARUS diperiksa:
   - `TELEGRAM_SEND_OK=true/false`
   - `TELEGRAM_CHAT_ID=...`
   - `TELEGRAM_MESSAGE_ID=<angka>` (hanya jika ok)
   - `INVOICE_RESULT=OK` atau `INVOICE_RESULT=FAILED (...)`
   - exit code: `0` = sukses penuh, `20` = Telegram delivery gagal.

7. **Balas konfirmasi HANYA berdasarkan bukti output script:**
   - Jika output mengandung `TELEGRAM_SEND_OK=true` DAN `TELEGRAM_MESSAGE_ID=<angka>`
     DAN `INVOICE_RESULT=OK` (exit 0), balas:
     ```
     Invoice INV-0001/STA/VIII/2026 berhasil dibuat dan PDF sudah terkirim.
     ```
   - Jika `INVOICE_RESULT=FAILED` atau `TELEGRAM_SEND_OK=false`, balas dengan JUJUR:
     ```
     Invoice berhasil dibuat, tetapi pengiriman PDF ke Telegram GAGAL.
     ```
   - Jika script memunculkan `POTENTIAL_DUPLICATE=true`, BERITAHU user bahwa invoice
     yang sama sudah ada (mis. INV-0001) dan tidak dibuat nomor baru.

   ⚠️ DILARANG mengarang status pengiriman. JANGAN menyatakan "PDF terkirim" tanpa
   bukti `TELEGRAM_MESSAGE_ID`. JANGAN menulis path file atau `[[as_document]]`.

8. Konfirmasi: nomor invoice, total, delivery status, dan bahwa record tersimpan
   di MySQL (kolom `delivery_status` = sent/failed).

## Format Input yang Harus Dikenali

- **Panjang**: "Buatkan invoice dengan data berikut: Nama pemesan: PT Nusa
  Horizon Wisata ... Rincian perjalanan 1: Tanggal 15 Agustus 2026, Jenis
  kendaraan Medium Bus, Jumlah 2 unit, Alamat jemput Harapan Indah Bekasi,
  Tujuan Cisarua Puncak, Harga per unit Rp2.800.000 ... Terbilang: Sepuluh juta
  delapan ratus ribu rupiah ... Harga termasuk: Unit kendaraan, Pengemudi, BBM
  ... Tidak termasuk: Tol, Parkir, Tips pengemudi ..."

- **Singkat**: "Buat invoice a.n. PT Nusa Horizon Wisata: 2 Medium Bus, 15
  Agustus 2026, jemput Harapan Indah Bekasi ke Cisarua Puncak, Rp2.800.000/unit;
  17 Agustus 2026, jemput Cisarua Puncak drop Jakarta, Rp2.600.000/unit. Total
  pelunasan 100% Rp10.800.000 tanpa DP. Termasuk mobil, sopir, BBM; di luar tol,
  parkir, dan tips sopir."

## Approval & State

- Status: DRAFT → PREVIEW → APPROVED → GENERATED (→ SENT).
- Kata approval yang valid: setuju, oke, ok, lanjut, buat invoice, generate,
  sudah benar — hanya jika konteksnya jelas merujuk preview terakhir
  (AGENTS.md §10).

## Nomor Invoice

- Format `INV-0001/STA/VIII/2026` (seq 4 digit / STA / bulan Romawi / tahun);
  sequence diambil dari `MAX(invoice_number)` di MySQL (source of truth).
  Jangan menebak nomor (AGENTS.md §12).

## Pitfalls

- Local dev memakai MySQL root **tanpa password** — `INVOICE_DB_PASSWORD` boleh kosong; jangan memblokir proses hanya karena kosong.
- Jangan percaya total yang diketik user — hitung ulang dari qty×price.
- Terbilang harus dari `format_indonesia.py`, jangan mengarang kata sendiri.
- Pastikan koneksi MySQL berhasil sebelum melaporkan "tersimpan".
- Jangan membocorkan kredensial DB / API key ke chat.
- Cap & ttd berupa GIF → dikonversi & digabung otomatis oleh script
  (butuh Pillow). WeasyPrint tidak mendukung GIF secara andal.

## Verification

- PDF terbuka, format sesuai template STA (header INVOICE, tabel item gelap,
  terbilang, box pembayaran, cap & ttd tumpang tindih).
- 1 baris di `invoices` + N baris di `invoice_items` di DB `invoice_bot`.
- Total di PDF = grand_total yang disetujui user.
