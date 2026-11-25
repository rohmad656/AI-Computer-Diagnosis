SIM-04 — RAM MEMORY NORMAL
===========================
Tanggal      : 2026-11-24
Kategori     : RAM / Memory
Tipe Kasus   : Simple (kasus normal, evidence langsung tersedia)
Metode pengujian : Fungsi internal — DiagnosisEngine API (core/diagnosis.py); BUKAN demonstrasi UI

SKENARIO
--------
Pengguna melaporkan aplikasi sering crash secara acak tanpa alasan jelas.
Komputer terkadang hang dan memerlukan restart paksa.

MASUKAN
-------
Gejala awal  : sym_app_crash_random
  (Aplikasi crash secara acak, tidak berkaitan dengan aktivitas tertentu)

Hasil tes    :
  test_memory_diagnostic = errors_found  (Memory Diagnostic menemukan error)
  test_ram_usage_snapshot = inconclusive  (snapshot penggunaan RAM tidak konklusif)

TEST YANG DIPILIH
-----------------
- test_memory_diagnostic
- test_ram_usage_snapshot

PROSES UCS
----------
1. State awal: kategori relevan = [ram_memory, driver_software]
2. UCS ekspansi berdasarkan cost:
   - test_memory_diagnostic (cost 5) → evidence memory_issue_confirmed TERKONFIRMASI
3. Goal state tercapai: ram_memory conclusive
4. Total cost akumulasi: 6.0 (5 + 1 untuk tes ram_usage_snapshot)

HASIL
-----
Diagnosis    : ram_memory
Status       : conclusive
Cost UCS     : 6.0
Supporting   : ['memory_issue_confirmed']
Contradicting: []

EKSPEKTASI / EXPECTED BEHAVIOR : ram_memory / conclusive
ACTUAL RESULT : ram_memory / conclusive
STATUS (PASS/FAIL) : PASS

REKOMENDASI SISTEM
------------------
- Jalankan Windows Memory Diagnostic atau MemTest86 untuk konfirmasi.
- Coba cabut dan pasang kembali modul RAM.
- Uji RAM satu per satu jika ada lebih dari satu slot.

ANALISIS
--------
RAM memiliki cost tes lebih tinggi (5) dibanding overheating (1) dan
storage (2). UCS tetap menemukan diagnosis optimal meskipun cost lebih
tinggi karena evidence sudah cukup dari 1 tes utama.

CATATAN KETERBATASAN
--------------------
Tidak menguji RAM intermiten yang terlewat oleh alat uji (false negative).
