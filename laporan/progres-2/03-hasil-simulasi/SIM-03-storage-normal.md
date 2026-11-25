SIM-03 — STORAGE DISK NORMAL
=============================
Tanggal      : 2026-11-24
Kategori     : Storage / Disk
Tipe Kasus   : Simple (kasus normal, evidence langsung tersedia)
Metode pengujian : Fungsi internal — DiagnosisEngine API (core/diagnosis.py); BUKAN demonstrasi UI

SKENARIO
--------
Pengguna melaporkan hard drive sangat lambat dan sistem sering freeze
saat membuka file. Dicurigai ada masalah pada storage.

MASUKAN
-------
Gejala awal  : sym_disk_slow_freeze
  (Hard disk sangat lambat, sistem freeze saat akses file)

Hasil tes    :
  test_smart_disk         = warning  (SMART melaporkan sektor buruk / peringatan)
  test_disk_system_error_logs = inconclusive (log tidak menunjukkan error disk)

TEST YANG DIPILIH
-----------------
- test_smart_disk
- test_disk_system_error_logs

PROSES UCS
----------
1. State awal: kategori relevan = [storage_disk]
2. UCS ekspansi: test_smart_disk (cost 2) → evidence disk_issue_confirmed TERKONFIRMASI
3. Goal state tercapai: storage_disk conclusive
4. test_disk_system_error_logs (cost 3) sudah diinput tapi tidak mengubah hasil
5. Total cost akumulasi: 5.0

HASIL
-----
Diagnosis    : storage_disk
Status       : conclusive
Cost UCS     : 5.0
Supporting   : ['disk_issue_confirmed']
Contradicting: []

EKSPEKTASI / EXPECTED BEHAVIOR : storage_disk / conclusive
ACTUAL RESULT : storage_disk / conclusive
STATUS (PASS/FAIL) : PASS

REKOMENDASI SISTEM
------------------
- Backup data segera sebelum disk mengalami kegagalan total.
- Jalankan chkdsk /r untuk memeriksa dan memperbaiki bad sector.
- Pertimbangkan penggantian HDD/SSD.

ANALISIS
--------
test_smart_disk adalah indikator kuat untuk storage_disk.
UCS menemukan diagnosis dengan cost 2 (1 tes utama) secara efisien.

CATATAN KETERBATASAN
--------------------
Bergantung pada akurasi SMART; kegagalan disk tanpa peringatan SMART tidak tercakup.
