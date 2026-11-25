SIM-07 — MISLEADING (FALSE NEGATIVE RAM)
=========================================
Tanggal      : 2026-11-24
Kategori     : RAM / Memory
Tipe Kasus   : Misleading (hasil tes menyesatkan — false negative)
Metode pengujian : Fungsi internal — DiagnosisEngine API (core/diagnosis.py); BUKAN demonstrasi UI

SKENARIO
--------
Pengguna mengalami aplikasi crash acak karena kerusakan RAM. Namun alat
uji memori (test_memory_diagnostic) memberikan hasil 'false_negative'
(melaporkan normal padahal ada masalah). Sistem terancam salah mendiagnosis.

MASUKAN
-------
Gejala awal  : sym_app_crash_random
  (Aplikasi crash secara acak)

Hasil tes    :
  test_memory_diagnostic = false_negative  (tes salah lapor: tidak ada error)
  test_ram_usage_snapshot = inconclusive

TEST YANG DIPILIH
-----------------
- test_memory_diagnostic
- test_ram_usage_snapshot

PROSES UCS
----------
1. State awal: kategori relevan = [ram_memory, driver_software]
2. Hasil tes diproses:
   - test_memory_diagnostic=false_negative memetakan ke:
     contradicts: ['memory_issue_confirmed']
   - Evidence memory_issue_confirmed DITOLAK
3. Kategori ram_memory dieliminasi karena bukti kunci ditolak
4. Tidak ada bukti pendukung lain untuk kategori yang tersisa
5. Status: inconclusive
6. Total cost: 6.0 (5 + 1)

HASIL
-----
Diagnosis    : None
Status       : inconclusive
Cost UCS     : 6.0
Supporting   : []
Contradicting: ['memory_issue_confirmed']

EKSPEKTASI / EXPECTED BEHAVIOR : inconclusive (RAM tidak terdeteksi — risiko false negative)
ACTUAL RESULT : None / inconclusive
STATUS (PASS/FAIL) : PASS

REKOMENDASI SISTEM
------------------
- Hasil tes menunjukkan tidak ada error memori, namun gejala masih berlanjut.
- Coba gunakan alat uji memori alternatif seperti MemTest86 via USB boot.
- Periksa log aplikasi individual untuk melihat pola error tertentu.

ANALISIS & CATATAN KETERBATASAN
--------------------------------
Ini adalah simulasi risiko false negative dunia nyata:
- Alat diagnostik software terkadang gagal mendeteksi kerusakan RAM intermiten
- Sistem AI tidak memiliki kemampuan supranatural untuk mendeteksi bahwa tes berbohong
- Sistem bertindak konsisten dengan data yang diterima: mengeliminasi kategori
- Keterbatasan ini didokumentasikan secara transparan, bukan disembunyikan
