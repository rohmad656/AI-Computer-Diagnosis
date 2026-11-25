SIM-06 — UNCERTAIN (SEMUA INCONCLUSIVE)
========================================
Tanggal      : 2026-11-24
Kategori     : Uncertain (Ketidakpastian Penuh)
Tipe Kasus   : Uncertain (semua tes menghasilkan netral)
Metode pengujian : Fungsi internal — DiagnosisEngine API (core/diagnosis.py); BUKAN demonstrasi UI

SKENARIO
--------
Pengguna melaporkan crash sistem tanpa kode error spesifik.
Semua pemeriksaan diagnostik yang dijalankan tidak menemukan indikasi
masalah pada perangkat manapun (semua inconclusive).

MASUKAN
-------
Gejala awal  : sym_system_crash
  (Sistem crash tanpa kode error atau minidump yang jelas)

Hasil tes    :
  test_cpu_gpu_temp      = inconclusive
  test_smart_disk        = inconclusive
  test_driver_status     = inconclusive
  test_memory_diagnostic = inconclusive

TEST YANG DIPILIH
-----------------
- test_cpu_gpu_temp
- test_smart_disk
- test_driver_status
- test_memory_diagnostic

PROSES UCS
----------
1. State awal: kategori relevan = [overheating, storage_disk, driver_software, ram_memory]
2. Semua tes dieksekusi berdasarkan urutan cost:
   - test_cpu_gpu_temp (cost 1) → inconclusive, evidence = []
   - test_smart_disk (cost 2) → inconclusive, evidence = []
   - test_driver_status (cost 2) → inconclusive, evidence = []
   - test_memory_diagnostic (cost 5) → inconclusive, evidence = []
3. Tidak ada evidence yang mendukung atau menolak kategori manapun.
4. Total cost akumulasi: 10.0 (1+2+2+5)

HASIL
-----
Diagnosis    : None
Status       : in_progress (tidak ada kesimpulan karena evidence kosong)
Cost UCS     : 10.0
Supporting   : []
Contradicting: []

EKSPEKTASI / EXPECTED BEHAVIOR : inconclusive (tidak ada kesimpulan definitif)
ACTUAL RESULT : None / in_progress (evidence tidak cukup)
STATUS (PASS/FAIL) : PASS

REKOMENDASI SISTEM
------------------
- Catat kode error atau gejala baru jika crash terjadi kembali.
- Pertimbangkan kemungkinan masalah power supply (PSU) atau motherboard
  yang belum tercakup dalam kategori diagnostik sistem.
- Konsultasikan dengan teknisi hardware profesional.

ANALISIS
--------
UCS menunjukkan perilaku aman: sistem tidak mengarang diagnosis jika
semua tes netral. Prinsip keselamatan ini penting untuk mencegah tindakan
perbaikan yang tidak tepat.

CATATAN KETERBATASAN
--------------------
Kategori di luar knowledge base (mis. PSU/motherboard) tidak dapat didiagnosis meski gejala persist.
