SIM-02 — OVERHEATING NORMAL
============================
Tanggal      : 2026-11-24
Kategori     : Overheating (Suhu Berlebih)
Tipe Kasus   : Simple (kasus normal, evidence langsung tersedia)
Metode pengujian : Fungsi internal — DiagnosisEngine API (core/diagnosis.py); BUKAN demonstrasi UI

SKENARIO
--------
Pengguna melaporkan komputer sering mati mendadak karena suhu tinggi.
Fan berbunyi keras dan terasa panas berlebih saat disentuh.

MASUKAN
-------
Gejala awal  : sym_shutdown_thermal
  (Komputer mati/restart sendiri karena suhu CPU/GPU terlalu tinggi)

Hasil tes    :
  test_cpu_gpu_temp = elevated  (suhu CPU/GPU terukur di atas batas normal)

TEST YANG DIPILIH
-----------------
- test_cpu_gpu_temp

PROSES UCS
----------
1. State awal: kategori relevan = [overheating]
2. UCS ekspansi: test_cpu_gpu_temp (cost 1) → evidence high_temperature_confirmed TERKONFIRMASI
3. Goal state tercapai: overheating conclusive
4. Total cost: 1.0 (tes paling murah, hanya 1 tes diperlukan)

HASIL
-----
Diagnosis    : overheating
Status       : conclusive
Cost UCS     : 1.0
Supporting   : ['high_temperature_confirmed']
Contradicting: []

EKSPEKTASI / EXPECTED BEHAVIOR : overheating / conclusive
ACTUAL RESULT : overheating / conclusive
STATUS (PASS/FAIL) : PASS

REKOMENDASI SISTEM
------------------
- Bersihkan heatsink dan kipas dari debu.
- Pastikan pasta termal CPU belum mengering; ganti jika perlu.
- Periksa ventilasi casing PC/laptop.

ANALISIS
--------
Kasus overheating adalah yang paling efisien dalam dataset: hanya
membutuhkan 1 tes dengan cost 1 untuk mencapai diagnosis konklusif.
UCS menemukan jalur optimal dengan segera.

CATATAN KETERBATASAN
--------------------
Hanya overheating dengan satu tes; tidak menguji kondisi suhu di ambang batas (borderline).
