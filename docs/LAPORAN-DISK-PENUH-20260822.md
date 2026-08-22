# LAPORAN — DISK VPS 100% PENUH (22 Agustus 2026)

- VPS: `nakatara-server` (103.150.191.235)
- Tanggal deteksi: 22 Agustus 2026
- Gejala: error **"No space left on device"**

---

## 1. Status Disk

| Item            | Nilai                    |
| --------------- | ------------------------ |
| Total kapasitas | 58 GB                    |
| Terpakai        | 58 GB                    |
| **Sisa**        | **0 byte (100%)**        |
| Inode           | 6% (aman, bukan masalah) |

---

## 2. Breakdown Penggunaan (siapa yang makan disk)

| Direktori                           | Ukuran    | Keterangan                        |
| ----------------------------------- | --------- | --------------------------------- |
| **`/home`**                         | **43 GB** | ⚠️ SUMBER MASALAH                 |
| ├─ `/home/denjaka/backups`          | **37 GB** | 🔴 **PENYEBAB UTAMA**             |
| ├─ `/home/denjaka/.vscode-server`   | 4,6 GB    | VS Code Server (bisa dibersihkan) |
| ├─ `/home/denjaka/backup-denytrans` | 0,6 GB    | backup lama denytrans             |
| └─ `/home/invoicebot` (Hermes)      | 1,3 GB    | normal — bukan masalah            |
| **`/var`**                          | **11 GB** | data asli aplikasi                |
| ├─ `/var/www`                       | 7,6 GB    | file web app (JANGAN dihapus)     |
| ├─ `/var/lib`                       | 1,7 GB    | data MySQL dsb. (JANGAN dihapus)  |
| ├─ `/var/log`                       | 1,1 GB    | log sistem                        |
| └─ `/var/cache`                     | 0,15 GB   | cache                             |
| `/usr`                              | 2,6 GB    | sistem                            |
| `/boot`                             | 0,12 GB   | sistem                            |

**Kesimpulan:** 37 GB dari 58 GB (64% disk) dipakai folder backup
`/home/denjaka/backups` — itulah yang membuat disk penuh.

---

## 3. Isi Folder Backup (detail masalah)

Folder: `/home/denjaka/backups/indobuswisata` = **36 GB**

### 3a. Arsip FILE website (`files-*.tar`) — ini yang membengkak

| Tanggal           | Ukuran    | Status     |
| ----------------- | --------- | ---------- |
| 18 Agu            | 2,1 GB    | ✅ terbaru |
| 17 Agu            | 2,9 GB    | ✅         |
| 16 Agu            | 2,9 GB    | ✅         |
| 15 Agu            | 2,9 GB    | ✅         |
| 14 Agu            | 2,9 GB    | ✅         |
| 13 Agu            | 2,9 GB    | ⏳ lama    |
| 12 Agu            | 2,9 GB    | ⏳ lama    |
| 11 Agu            | 2,9 GB    | ⏳ lama    |
| 10 Agu            | 2,9 GB    | ⏳ lama    |
| 09 Agu            | 2,9 GB    | ⏳ lama    |
| 08 Agu            | 2,9 GB    | ⏳ lama    |
| 07 Agu            | 2,6 GB    | ⏳ lama    |
| 06 Agu            | 2,5 GB    | ⏳ lama    |
| **Total 13 file** | **36 GB** |            |

**Masalah:** 13 arsip `files-*.tar` ~2,9 GB/file **tidak pernah dirotasi**.
Setiap hari bertambah ~2,9 GB → disk penuh.

### 3b. Backup DATABASE (`db-*.sql.gz`) — ada yang GAGAL

| Tanggal | Ukuran     | Status                |
| ------- | ---------- | --------------------- |
| 22 Agu  | **0 byte** | 🔴 GAGAL (disk penuh) |
| 21 Agu  | **0 byte** | 🔴 GAGAL (disk penuh) |
| 20 Agu  | **0 byte** | 🔴 GAGAL (disk penuh) |
| 19 Agu  | **0 byte** | 🔴 GAGAL (disk penuh) |
| 18 Agu  | 18 MB      | ✅ valid (terakhir)   |
| 17 Agu  | 16 MB      | ✅                    |
| 16 Agu  | 14 MB      | ✅                    |
| 15 Agu  | 12 MB      | ✅                    |
| 14 Agu  | 11 MB      | ✅                    |
| 13 Agu  | 8,6 MB     | ✅                    |
| 12 Agu  | 8,5 MB     | ✅                    |
| 11 Agu  | 8,3 MB     | ✅                    |
| 10 Agu  | 7,6 MB     | ✅                    |
| 09 Agu  | 7,5 MB     | ✅                    |
| 08 Agu  | 7,0 MB     | ✅                    |
| 07 Agu  | 5,4 MB     | ✅                    |
| 06 Agu  | 3,8 MB     | ✅                    |

**Masalah:** DB backup 19–22 Agustus = 0 byte. **Tidak ada backup DB valid
lebih baru dari 18 Agustus.** Backup harian gagal diam-diam.

---

## 4. Ringkasan: MASALAH vs BUKAN MASALAH

| Item                                     | Ukuran               | Masalah?                              |
| ---------------------------------------- | -------------------- | ------------------------------------- |
| `backups/indobuswisata/files-*.tar` lama | ~25,5 GB (6–13 Agu)  | 🔴 YA — penyebab penuh, boleh dihapus |
| `backups/indobuswisata/files-*.tar` baru | ~13,7 GB (14–18 Agu) | 🟡 backup terbaru — pertahankan       |
| `backups/*/db-*.sql.gz` (0 byte)         | 0                    | 🟡 bukti kegagalan, tidak makan ruang |
| `.vscode-server`                         | 4,6 GB               | 🟡 bisa dibersihkan (cache)           |
| `/var/www`                               | 7,6 GB               | 🟢 data app asli — JANGAN             |
| `/var/lib` (MySQL)                       | 1,7 GB               | 🟢 data DB production — JANGAN        |
| `/home/invoicebot` (Hermes)              | 1,3 GB               | 🟢 normal — bukan masalah             |

---

## 5. Rencana Pemulihan (butuh persetujuan user)

### Langkah 1 — Bebaskan ruang

Hapus **9 file** `files-*.tar` tanggal **6–13 Agustus**:

```
files-20260806 … files-20260813  (≈ 25,5 GB)
```

→ Disk dari 100% turun ke **±55%** (sisa ~13 GB).

### Langkah 2 — Backup valid hari ini

Jalankan ulang backup manual `indobuswisata` → dapat `db-20260822` + `files-20260822` valid.

### Langkah 3 — Perbaiki skrip backup (cegah terulang)

Tambahkan **rotasi/retensi**: simpan N hari terakhir (mis. 7), hapus otomatis yang lebih tua.
Contoh tambahan di akhir skrip backup:

```bash
find /home/denjaka/backups/indobuswisata -name "files-*.tar" -mtime +7 -delete
find /home/denjaka/backups/indobuswisata -name "db-*.sql.gz" -size 0 -delete
```

### Langkah 4 — Verifikasi

- `df -h` → ada sisa ruang
- Backup baru valid (bukan 0 byte)
- Service `invoice_bot` & web app lain normal

---

## 6. Dampak ke Proyek Invoice

- Install Hermes/invoicebot HANYA ±1,3 GB — **bukan** penyebab disk penuh.
- Selama disk 100%, gateway tetap berjalan, tapi sistem rentan (log/PDF baru
  bisa gagal ditulis). Setelah pembersihan, semuanya aman.
