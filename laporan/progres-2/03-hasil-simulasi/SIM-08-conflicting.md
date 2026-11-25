SIM-08 — CONFLICTING (KONTRADIKTIF DRIVER)
===========================================
Tanggal      : 2026-11-24
Kategori     : Driver & Perangkat Lunak Sistem
Tipe Kasus   : Contradictory (bukti yang saling bertentangan)
Metode pengujian : Fungsi internal — DiagnosisEngine API (core/diagnosis.py); BUKAN demonstrasi UI

SKENARIO
--------
Pengguna melaporkan BSOD driver. Namun dua tes berbeda memberikan hasil
yang saling bertolak belakang: Device Manager melaporkan error driver,
sementara riwayat kode error menyatakan tidak ada masalah driver.

MASUKAN
-------
Gejala awal  :
  sym_bsod_driver
  sym_bsod_generic

Hasil tes    :
  test_driver_status         = yellow_bang       (MENDUKUNG driver_issue_confirmed)
  test_error_code_history    = no_driver_errors  (MENOLAK driver_issue_confirmed)
  test_smart_disk            = inconclusive
  test_disk_system_error_logs = inconclusive
  test_memory_diagnostic     = inconclusive
  test_ram_usage_snapshot    = inconclusive

TEST YANG DIPILIH
-----------------
- test_smart_disk
- test_driver_status
- test_disk_system_error_logs
- test_error_code_history
- test_memory_diagnostic
- test_ram_usage_snapshot

PROSES UCS
----------
1. State awal: kategori relevan = [driver_software, storage_disk, ram_memory]
2. Hasil tes diproses:
   - test_driver_status: supports ['driver_issue_confirmed']
   - test_error_code_history: contradicts ['driver_issue_confirmed']
3. Evidence driver_issue_confirmed berada dalam kondisi KONFLIK:
   tercatat sekaligus di supporting dan contradicting
4. Kategori driver_software ditandai sebagai conflicting
5. Tidak ada kategori lain yang memiliki bukti valid
6. Status: inconclusive
7. Total cost akumulasi: 16.0 (2+3+2+3+5+1)

HASIL
-----
Diagnosis    : None
Status       : inconclusive
Cost UCS     : 16.0
Supporting   : ['driver_issue_confirmed']
Contradicting: ['driver_issue_confirmed']

EKSPEKTASI / EXPECTED BEHAVIOR : observation_limited_conclusive / inconclusive (kontradiksi teramati)
ACTUAL RESULT : None / inconclusive
STATUS (PASS/FAIL) : PASS

REKOMENDASI SISTEM
------------------
- Terdeteksi ketidakkonsistenan bukti untuk kategori Driver.
- Periksa minidump crash terbaru secara manual menggunakan WinDbg.
- Pastikan tidak ada konflik driver tersembunyi antar perangkat.

ANALISIS
--------
UCS berhasil mendeteksi kontradiksi bukti secara eksplisit.
Sistem menolak memberikan diagnosis konklusif yang tidak dapat dipercaya
karena ada bukti yang menentang. Ini mencegah false positive berbahaya.

CATATAN KETERBATASAN
--------------------
Sistem mendeteksi kontradiksi tetapi tidak dapat menentukan bukti mana yang benar; perlu verifikasi manual.
