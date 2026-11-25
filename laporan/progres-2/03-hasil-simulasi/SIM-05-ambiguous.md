SIM-05 — AMBIGUOUS (MULTI-KATEGORI)
=====================================
Tanggal      : 2026-11-24
Kategori     : Multi-Kategori (Overheating + Storage)
Tipe Kasus   : Cross-Category / Ambiguous
Metode pengujian : Fungsi internal — DiagnosisEngine API (core/diagnosis.py); BUKAN demonstrasi UI

SKENARIO
--------
Pengguna melaporkan kombinasi gejala yang luas: BSOD umum dan penurunan
kinerja secara bertahap. Dua tes berbeda menunjukkan masalah pada dua
komponen yang berbeda (CPU/GPU panas DAN disk bermasalah).

MASUKAN
-------
Gejala awal  :
  sym_bsod_generic             (BSOD umum, relevan: driver, ram, storage)
  sym_performance_degradation  (penurunan performa, relevan: overheating, storage, ram)

Hasil tes    :
  test_cpu_gpu_temp = elevated  (mendukung: high_temperature_confirmed)
  test_smart_disk   = warning   (mendukung: disk_issue_confirmed)

TEST YANG DIPILIH
-----------------
- test_cpu_gpu_temp
- test_smart_disk

PROSES UCS
----------
1. State awal: kategori relevan = [overheating, storage_disk, driver_software, ram_memory]
2. Hasil tes memberikan evidence pendukung untuk DUA kategori sekaligus:
   - high_temperature_confirmed → overheating
   - disk_issue_confirmed → storage_disk
3. Terjadi ambiguitas / multi-evidence: sistem tidak dapat menyimpulkan
   satu kategori tunggal tanpa tes lanjutan untuk membedakan prioritas.
4. Status evaluasi: in_progress / inconclusive
5. Total cost: 3.0 (1 untuk temp + 2 untuk disk)

HASIL
-----
Diagnosis    : None (belum ada kesimpulan tunggal)
Status       : in_progress (memerlukan tes lanjutan)
Cost UCS     : 3.0
Supporting   : ['disk_issue_confirmed', 'high_temperature_confirmed']
Contradicting: []

EKSPEKTASI / EXPECTED BEHAVIOR : inconclusive / in_progress (multi-evidence konflik)
ACTUAL RESULT : None / in_progress
STATUS (PASS/FAIL) : PASS

REKOMENDASI SISTEM
------------------
- Selesaikan masalah termal terlebih dahulu (lebih mendesak).
- Lakukan backup data dari disk sebelum melakukan pengujian lanjutan.
- Jalankan tes lanjutan untuk memverifikasi kategori primer.

ANALISIS
--------
UCS menangani ambiguitas dengan benar: tidak terburu-buru mengambil
keputusan jika ada dua bukti yang saling bersaing. Ini mencegah false
positive pada kasus kompleks.

CATATAN KETERBATASAN
--------------------
Sistem tidak menyelesaikan ambiguitas tanpa tes lanjutan; memerlukan keputusan prioritas pengguna/teknisi.
