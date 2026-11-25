DAFTAR SCREENSHOT YANG HARUS DIAMBIL — PROGRES KE-2
=====================================================
Lokasi penyimpanan : `laporan/progres-2/02-screenshot/`
Status saat ini    : **BELUM ADA SCREENSHOT YANG DIAMBIL**
Kunci status       : `NOT YET CAPTURED`

Dokumen ini adalah **checklist**, bukan bukti. Semua entri di bawah
berstatus `NOT YET CAPTURED`. Tidak ada screenshot yang dibuat,
disimulasikan, atau direkayasa dalam laporan Progres ke-2 ini.

====================================================================
CARA MENJALANKAN UI (PRA-SYARAT)
====================================================================

1. Buka terminal di direktori proyek:
   `D:\Kuliah\PROJECT\Web\AI-Computer-Diagnosis`
2. Jalankan:
   `.venv\Scripts\python.exe -m streamlit run app.py`
3. Buka browser ke:
   `http://localhost:8501`
4. Ambil gambar dengan `Win + Shift + S` / Snipping Tool.
5. Simpan ke `laporan/progres-2/02-screenshot/` dengan nama file
   persis seperti di tabel.
6. Ubah status baris terkait dari `NOT YET CAPTURED` menjadi
   `CAPTURED` hanya setelah file benar-benar ada.

Catatan: smoke test server sudah tercatat di
`01-log-eksekusi/streamlit-run.txt` (STATUS: PASS). Itu **bukan**
bukti tampilan visual; screenshot tetap wajib diambil manual.

====================================================================
CHECKLIST
====================================================================

| No | Nama file | Tampilan / Aksi yang harus terlihat | Langkah singkat | Status |
|----|-----------|--------------------------------------|-----------------|--------|
| 1 | `01-halaman-utama.png` | Judul aplikasi, sidebar, dan kondisi awal sesi | Buka `http://localhost:8501` tanpa input | NOT YET CAPTURED |
| 2 | `02-pilih-gejala.png` | Gejala `sym_bsod_driver` (atau setara) telah dipilih | Pilih gejala BSOD driver pada form awal | NOT YET CAPTURED |
| 3 | `03-rekomendasi-tes.png` | Daftar pemeriksaan yang disarankan UCS beserta biaya | Setelah gejala dipilih, tampilkan rekomendasi tes | NOT YET CAPTURED |
| 4 | `04-form-hasil-tes.png` | Form input hasil pemeriksaan | Buka/form isi hasil `test_driver_status = yellow_bang` | NOT YET CAPTURED |
| 5 | `05-hasil-conclusive.png` | Diagnosis `driver_software`, status `conclusive`, evidence pendukung, rekomendasi | Kirim hasil tes lalu evaluasi | NOT YET CAPTURED |
| 6 | `06-hasil-kontradiksi.png` | Evidence kontradiktif untuk kategori driver (supporting dan contradicting) | Reproduksi SIM-08 di UI | NOT YET CAPTURED |
| 7 | `07-hasil-inconclusive.png` | Status `inconclusive` / tidak ada diagnosis dipaksakan | Reproduksi SIM-07 di UI | NOT YET CAPTURED |
| 8 | `08-riwayat-state.png` | Riwayat langkah, outcome, dan biaya kumulatif | Gulir ke bagian riwayat/state pada hasil | NOT YET CAPTURED |
| 9 | `09-reset-sesi.png` | Kondisi sesi setelah tombol reset/mulai diagnosis baru ditekan | Klik reset, tunjukkan form bersih | NOT YET CAPTURED |

====================================================================
ATURAN INTEGRITAS
====================================================================

- Dilarang mengganti status menjadi `CAPTURED` sebelum file ada.
- Dilarang memakai screenshot lama dari folder `screenshots/` sebagai
  pengganti tanpa verifikasi bahwa tampilannya masih sesuai Progres ke-2.
- Dilarang mengarang nama file atau membuat file kosong.
- Jika một tampilan tidak tersedia di UI versi saat ini, tulis
  `NOT AVAILABLE IN UI` pada kolom Status dan jelaskan di catatan,
  jangan mengganti dengan `CAPTURED`.

====================================================================
RELASI DENGAN BUKTI LAIN
====================================================================

- Eksekusi server: `../01-log-eksekusi/streamlit-run.txt`
- Skenario yang bisa direproduksi di UI:
  `../03-hasil-simulasi/RINGKASAN_SIMULASI.md`
- Navigasi keseluruhan: `../INDEX_BUKTI.md`
