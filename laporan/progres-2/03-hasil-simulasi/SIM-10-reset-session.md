SIM-10 — RESET SESSION LALU DIAGNOSIS ULANG
============================================
Tanggal      : 2026-11-24
Kategori     : Siklus Hidup Sesi (Reset & Inisialisasi Ulang)
Tipe Kasus   : Behavioral / Session Management
Metode pengujian : Fungsi internal — DiagnosisEngine API (core/diagnosis.py); BUKAN demonstrasi UI

SKENARIO
--------
Pengguna melakukan diagnosis driver software hingga selesai.
Kemudian pengguna menekan tombol "Mulai Diagnosis Baru" (Reset).
Sistem harus membersihkan seluruh state (gejala, hasil tes, evidence, cost)
dan siap menerima sesi diagnosis baru yang independen.

MASUKAN SESI 1
--------------
Gejala awal  : sym_bsod_driver
Hasil tes    : test_driver_status = yellow_bang
Hasil Sesi 1 : driver_software / conclusive (cost: 2.0)

AKSI RESET
----------
Engine diinisialisasi ulang:
  - state._performed_tests dibersihkan
  - state._supporting_evidence dibersihkan
  - state._contradicting_evidence dibersihkan
  - state._cumulative_cost di-reset ke 0

MASUKAN SESI 2 (Setelah Reset)
------------------------------
Gejala awal  : sym_bsod_driver
Hasil tes    : test_driver_status = yellow_bang

TEST YANG DIPILIH
-----------------
- test_driver_status

PROSES SESI 2
-------------
1. State awal bersih: hanya memuat gejala baru sym_bsod_driver
2. apply_result('test_driver_status', 'yellow_bang')
3. Evaluasi menghasilkan driver_software / conclusive
4. Cumulative cost tepat 2.0 (tidak ada kebocoran cost dari Sesi 1)

HASIL
-----
Diagnosis    : driver_software
Status       : conclusive
Cost UCS     : 2.0
Supporting   : ['driver_issue_confirmed']
Contradicting: []

EKSPEKTASI / EXPECTED BEHAVIOR : driver_software / conclusive (hasil identik, state bersih)
ACTUAL RESULT : driver_software / conclusive (cost tepat 2.0)
STATUS (PASS/FAIL) : PASS

CATATAN VERIFIKASI RESET
-------------------------
- Cumulative cost di Sesi 2 = 2.0 (bukan 4.0). Membuktikan cost tidak bocor.
- Supporting evidence hanya 1 item. Membuktikan evidence tidak terduplikasi.
- Sesi 2 berperilaku identik dengan eksekusi pertama dari kondisi bersih.

ANALISIS
--------
Fungsionalitas reset bekerja dengan sempurna: tidak ada state leakage,
tidak ada akumulasi cost yang salah antar sesi. Sistem siap untuk
penggunaan multi-sesi di antarmuka web Streamlit.

CATATAN KETERBATASAN
--------------------
Reset disimulasikan lewat inisialisasi ulang engine; belum diuji melalui klik tombol UI Streamlit.
