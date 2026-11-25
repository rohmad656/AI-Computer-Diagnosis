HASIL SIMULASI FUNGSIONAL — RINGKASAN 10 SKENARIO
===================================================
Tanggal      : 2026-11-24
Metode       : Eksekusi langsung melalui DiagnosisEngine API (core.diagnosis.py) — FUNGSI INTERNAL, BUKAN demonstrasi UI
Sumber Data  : data/symptoms.json, data/diagnostic_tests.json, core/knowledge_base.py
Tool         : .venv\Scripts\python.exe

====================================================================
METODE PENGUJIAN
----------------
Seluruh 10 skenario dijalankan sebagai fungsi internal melalui
DiagnosisEngine API (core/diagnosis.py). Tidak ada simulasi yang
dilakukan melalui antarmuka pengguna Streamlit / manual UI.

====================================================================
TABEL RINGKASAN
====================================================================

| ID     | Skenario                  | Gejala Utama              | Hasil Diagnosis      | Status       | Cost | PASS |
|--------|---------------------------|---------------------------|----------------------|--------------|------|------|
| SIM-01 | Driver Software Normal    | sym_bsod_driver           | driver_software      | conclusive  |  5.0 | YA   |
| SIM-02 | Overheating Normal        | sym_shutdown_thermal      | overheating          | conclusive  |  1.0 | YA   |
| SIM-03 | Storage Disk Normal       | sym_disk_slow_freeze      | storage_disk         | conclusive  |  5.0 | YA   |
| SIM-04 | RAM Memory Normal         | sym_app_crash_random      | ram_memory           | conclusive  |  6.0 | YA   |
| SIM-05 | Ambiguous (Multi-Kategori)| sym_bsod_generic + others | None                 | in_progress |  3.0 | YA   |
| SIM-06 | Uncertain (Semua Inconcl.)| sym_system_crash          | None                 | in_progress | 10.0 | YA   |
| SIM-07 | Misleading (False Negative)| sym_app_crash_random     | None                 | inconclusive|  6.0 | YA   |
| SIM-08 | Conflicting (Kontradiktif)| sym_bsod_driver + generic | None                 | inconclusive| 16.0 | YA   |
| SIM-09 | Inconclusive (No Evidence)| sym_bsod_generic          | None                 | in_progress | 10.0 | YA   |
| SIM-10 | Reset Session             | sym_bsod_driver           | driver_software      | conclusive  |  2.0 | YA   |

TOTAL: 10/10 skenario lulus sesuai ekspektasi.

====================================================================
DISTRIBUSI HASIL
====================================================================

Berdasarkan diagnosis akhir:
  - Conclusive (terdiagnosis)      : 5 skenario (SIM-01,02,03,04,10)
  - Inconclusive / In Progress     : 5 skenario (SIM-05,06,07,08,09)

Berdasarkan kategori (untuk yang conclusive):
  - driver_software : 2
  - overheating     : 1
  - storage_disk    : 1
  - ram_memory      : 1

Berdasarkan tipe evidence (untuk yang non-conclusive):
  - Multi-evidence ambiguitas  : 1 (SIM-05)
  - Semua tes uncertain        : 1 (SIM-06)
  - Misleading false negative  : 1 (SIM-07)
  - Evidence kontradiktif      : 1 (SIM-08)
  - Tidak ada evidence         : 1 (SIM-09)

Rentang cost: 1.0 (SIM-02) sampai 16.0 (SIM-08)
Rata-rata cost: 6.5

====================================================================
VERIFIKASI PERILAKU KRITIS
====================================================================

1. ULC (Uniform Cost Search):
   SIM-02 membuktikan UCS memilih tes dengan cost terkecil (1) dibanding
   tes lain yang mungkin. SIM-01 menunjukkan UCS berhenti setelah mencapai
   goal state tanpa mengeksekusi tes yang tidak perlu.

2. Deteksi Kontradiksi:
   SIM-08 membuktikan sistem mendeteksi evidence yang saling menentang
   dan menolak membuat diagnosis konklusif.

3. Penanganan Misleading Evidence:
   SIM-07 membuktikan false_negative ditangani sebagai penolakan evidence,
   bukan diabaikan. Risiko false negative didokumentasikan secara transparan.

4. Keselamatan Ambiguitas:
   SIM-05 membuktikan sistem tidak terburu-buru memilih salah satu dari
   dua kategori yang sama-sama memiliki bukti pendukung.

5. Konsistensi Reset:
   SIM-10 membuktikan tidak ada state leakage antar sesi diagnosis.

====================================================================
DAFTAR FILE SIMULASI
====================================================================

  SIM-01-driver-normal.md     — Driver Software (conclusive, cost 5.0)
  SIM-02-overheating-normal.md— Overheating (conclusive, cost 1.0)
  SIM-03-storage-normal.md    — Storage Disk (conclusive, cost 5.0)
  SIM-04-ram-normal.md        — RAM Memory (conclusive, cost 6.0)
  SIM-05-ambiguous.md         — Multi-kategori ambigu (in_progress, cost 3.0)
  SIM-06-uncertain.md         — Semua tes inconclusive (in_progress, cost 10.0)
  SIM-07-misleading.md        — False negative RAM (inconclusive, cost 6.0)
  SIM-08-conflicting.md       — Kontradiksi driver (inconclusive, cost 16.0)
  SIM-09-inconclusive.md      — Tanpa evidence (in_progress, cost 10.0)
  SIM-10-reset-session.md     — Reset & diagnosis ulang (conclusive, cost 2.0)
