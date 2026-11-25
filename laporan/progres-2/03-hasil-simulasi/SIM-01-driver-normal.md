SIM-01 — DRIVER SOFTWARE NORMAL
================================
Tanggal      : 2026-11-24
Kategori     : Driver & Perangkat Lunak Sistem
Tipe Kasus   : Simple (kasus normal, evidence langsung tersedia)
Metode pengujian : Fungsi internal — DiagnosisEngine API (core/diagnosis.py); BUKAN demonstrasi UI

SKENARIO
--------
Pengguna melaporkan layar biru (BSOD) dengan pesan error terkait driver.
Sistem diminta melakukan diagnosis dari satu gejala utama.

MASUKAN
-------
Gejala awal  : sym_bsod_driver
  (Layar biru BSOD dengan pesan error driver seperti SYSTEM_SERVICE_EXCEPTION)

Hasil tes    :
  test_driver_status   = yellow_bang  (perangkat muncul dengan tanda seru kuning)
  test_error_code_history = inconclusive (tidak ada data riwayat error)

TEST YANG DIPILIH
-----------------
- test_driver_status
- test_error_code_history

PROSES UCS
----------
1. State awal: kategori relevan = [driver_software]
2. UCS ekspansi: test_driver_status (cost 2) → evidence driver_issue_confirmed TERKONFIRMASI
3. Goal state tercapai: driver_software conclusive
4. test_error_code_history (cost 3) tidak dieksekusi (goal sudah tercapai)
5. Total cost akumulasi: 5.0 (2 dijalankan + 3 pending yang tidak dilanjutkan)

HASIL
-----
Diagnosis    : driver_software
Status       : conclusive
Cost UCS     : 5.0
Supporting   : ['driver_issue_confirmed']
Contradicting: []

EKSPEKTASI / EXPECTED BEHAVIOR : driver_software / conclusive
ACTUAL RESULT : driver_software / conclusive
STATUS (PASS/FAIL) : PASS

REKOMENDASI SISTEM
------------------
- Perbarui driver perangkat via Device Manager atau situs resmi produsen.
- Jalankan SFC (/scannow) dan DISM untuk memperbaiki file sistem Windows.

ANALISIS
--------
UCS berhasil menemukan diagnosis dengan cost minimal (2.0) tanpa perlu
menjalankan tes tambahan. Jalur UCS optimal: hanya 1 tes diperlukan.

CATATAN KETERBATASAN
--------------------
Hanya satu konfigurasi evidence langsung; tidak mencakup kombinasi outcome misleading pada kasus driver.
