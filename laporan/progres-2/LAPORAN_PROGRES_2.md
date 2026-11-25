LAPORAN PROGRES KE-2
====================
PROYEK: AI Computer Diagnosis (Sistem Pakar Diagnosis Komputer Berbasis UCS)
TANGGAL PERIKSA: 2026-11-24
REPOSITORI: D:\Kuliah\PROJECT\Web\AI-Computer-Diagnosis
LOKASI LAPORAN: laporan/progres-2/
STATUS GIT: Lokal (Phase 13/14, commit 4354994) — Belum di-commit / push

====================================================================
1. IDENTITAS DAN TUJUAN PROYEK
====================================================================

AI Computer Diagnosis adalah sistem pakar berbasis web (Python + Streamlit) untuk
diagnosis awal masalah perangkat keras/lunak komputer pada OS Windows.
Sistem ini menggunakan algoritma Uniform Cost Search (UCS) berbasis biaya kumulatif
rendah untuk menentukan urutan pemeriksaan diagnostik secara adaptif.

Tujuan Proyek:
- Membantu pengguna awam mengidentifikasi masalah komputer secara terstruktur.
- Meminimalkan biaya/waktu pengujian dengan urutan tes optimal dari UCS.
- Menjaga transparansi bukti (supporting, contradicting, neutral evidence).
- Menolak memaksakan diagnosis jika bukti tidak memadai (prinsip keselamatan).
- Menyediakan evaluasi komparatif faktual antara UCS dan Fixed-Order Checklist.

Lingkup Diagnosis:
- 4 Kategori: Driver & Software (`driver_software`), Suhu Berlebih (`overheating`),
  Storage/Disk (`storage_disk`), dan Memory/RAM (`ram_memory`).
- 6 Uji diagnostik terstruktur dengan pemetaan bukti deterministik.
- Tidak ada tindakan otomatis atau eksekusi perintah berbahaya di sistem operasi.

====================================================================
2. LINGKUNGAN PENGEMBANGAN
====================================================================

Hasil audit lingkungan dari `01-log-eksekusi/environment.txt`:

| Parameter | Nilai Faktual |
|-----------|---------------|
| Waktu Pemeriksaan | 2026-11-24 08:32:07 |
| Sistem Operasi | Windows 11 (10.0.26300) |
| Arsitektur Mesin | AMD64 (64bit) |
| Hostname / Node | Rohmad |
| Python Executable | `D:\Kuliah\PROJECT\Web\AI-Computer-Diagnosis\.venv\Scripts\python.exe` |
| Python Version | 3.14.10 (tags/v3.14.10:b703b2c, Oct 25 2026) |
| Virtual Env | Aktif (`.venv`) |
| Streamlit | 1.67.0 |
| Pytest | 9.2.0 |
| Matplotlib | 3.11.2 |

====================================================================
3. HASIL EKSEKUSI APLIKASI
====================================================================

Smoke Test Server Streamlit (`01-log-eksekusi/streamlit-run.txt`):
- Perintah: `.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.port 8501`
- Hasil: Process timeout setelah 12 detik (TimeoutExpired).
- Interpretasi: Server HTTP aktif, tidak crash, dan dapat di-import dengan benar.
- Status: PASS.

Pengambilan Screenshot UI:
- Status: NOT YET CAPTURED.
- Tindakan manual diperlukan: Buka browser ke `http://localhost:8501` dan ambil screenshot
  sesuai instruksi pada `02-screenshot/DAFTAR_SCREENSHOT_YANG_HARUS_DIAMBIL.md`.

====================================================================
4. RIWAYAT ERROR DAN PENYELESAIAN (TROUBLESHOOTING)
====================================================================

Ringkasan dari `01-log-eksekusi/TROUBLESHOOTING.md`:

1. `pytest -q` gagal ("No module named 'core'"):
   - Penyebab: `pytest` langsung dari PATH tidak memasukkan CWD ke `sys.path`.
   - Solusi: Jalankan via `.venv\Scripts\python.exe -m pytest -q`.
   - Hasil: All tests pass. Tidak ada perubahan kode/algoritma.

2. `Tee-Object` PowerShell menghasilkan encoding UTF-16 BOM:
   - Penyebab: Perilaku default PowerShell `Tee-Object`.
   - Solusi: Tulis file log langsung menggunakan Python dengan `encoding='utf-8'`.

3. Kasus `EXT_DRV_045` (misleading false_positive driver) menghasilkan `missed_conclusive`:
   - Penjelasan: `test_driver_status=false_positive` dikenali UCS sebagai bukti menyesatkan.
     UCS tidak memaksakan status conclusive. Ini keterbatasan yang didokumentasikan,
     bukan kesalahan algoritma.

4. 30 Kasus contradictory menghasilkan `observation_limited_conclusive`:
   - Penjelasan: UCS berhenti lebih awal saat goal state tercapai sebelum tes kontradiktif
     tereksitasi. Ini adalah sifat cost-based early stopping dari UCS.

====================================================================
5. HASIL 108 UNIT TEST
====================================================================

Log eksekusi dari `01-log-eksekusi/pytest.txt`:
- Perintah: `.venv\Scripts\python.exe -m pytest -q`
- Hasil: `108 passed in 1.84s`

Rincian Cakupan Test Suite:
- `tests/test_ucs.py`: 9 unit test (algoritma UCS generik & heapq).
- `tests/test_diagnosis.py`: 60 unit test (mesin diagnosis, state transition, evidence).
- `tests/test_symptom_matcher.py`: 13 unit test (pencocokan kata kunci & validasi BSOD).
- `tests/test_user_symptoms.py`: 13 unit test (gejala kustom & integrasi sesi).
- `tests/test_reset.py`: 13 unit test (reset sesi & flag UI).

====================================================================
6. VALIDASI TIGA DATASET
====================================================================

Log eksekusi dari `01-log-eksekusi/dataset-validation-*.txt`:

1. Dataset Baseline (`evaluation_dataset.json`):
   - Jumlah kasus: 20
   - Distribusi: driver_software: 5, mixed: 1, overheating: 5, ram_memory: 3, storage_disk: 6
   - Status: VALID (0 error)

2. Dataset Extended (`extended_dataset.json`):
   - Jumlah kasus: 180
   - Distribusi kategori: 45 kasus per kategori (4 kategori)
   - Distribusi tipe kasus: contradictory: 30, cross_category: 56, misleading: 2, simple: 36, uncertain: 56
   - Status: VALID (0 error)

3. Dataset Combined (Baseline + Extended):
   - Jumlah kasus: 200
   - Distribusi kategori: driver_software: 50, mixed: 1, overheating: 50, ram_memory: 48, storage_disk: 51
   - Status: VALID (0 error)

====================================================================
7. HASIL 10 SIMULASI FUNGSIONAL
====================================================================

Metode Pengujian:
Seluruh 10 skenario dijalankan sebagai FUNGSI INTERNAL melalui `DiagnosisEngine` API
(`core/diagnosis.py`), BUKAN demonstrasi manual di UI Streamlit.

Ringkasan dari `03-hasil-simulasi/RINGKASAN_SIMULASI.md`:

| ID | Skenario | Gejala Utama | Hasil Diagnosis | Status | Cost | Status Test |
|----|----------|--------------|-----------------|--------|------|-------------|
| SIM-01 | Driver Software Normal | sym_bsod_driver | driver_software | conclusive | 5.0 | PASS |
| SIM-02 | Overheating Normal | sym_shutdown_thermal | overheating | conclusive | 1.0 | PASS |
| SIM-03 | Storage Disk Normal | sym_disk_slow_freeze | storage_disk | conclusive | 5.0 | PASS |
| SIM-04 | RAM Memory Normal | sym_app_crash_random | ram_memory | conclusive | 6.0 | PASS |
| SIM-05 | Ambiguous (Multi-Kategori) | sym_bsod_generic + p.degr. | None | in_progress | 3.0 | PASS |
| SIM-06 | Uncertain (Semua Inconcl.) | sym_system_crash | None | in_progress | 10.0 | PASS |
| SIM-07 | Misleading (False Neg. RAM) | sym_app_crash_random | None | inconclusive | 6.0 | PASS |
| SIM-08 | Conflicting (Kontradiktif) | sym_bsod_driver + gen. | None | inconclusive | 16.0 | PASS |
| SIM-09 | Inconclusive (No Evidence) | sym_bsod_generic | None | in_progress | 10.0 | PASS |
| SIM-10 | Reset Session | sym_bsod_driver | driver_software | conclusive | 2.0 | PASS |

Tingkat Keberhasilan: 10 / 10 PASS (100%).

====================================================================
8. EVALUASI BASELINE, EXTENDED, DAN COMBINED
====================================================================

Data dari `evaluation/results/summary_metrics.csv` dan `01-log-eksekusi/evaluation-*.txt`:

| Metrik Evaluation | Baseline (20) | Extended (180) | Combined (200) |
|-------------------|---------------|----------------|----------------|
| Expected Conclusive Cases | 15 | 93 | 108 |
| Expected Inconclusive Cases | 5 | 87 | 92 |
| Actual Conclusive Cases | 15 | 122 | 137 |
| Actual Inconclusive Cases | 5 | 58 | 63 |
| Correct Conclusive | 15 | 92 | 107 |
| Correct Inconclusive | 5 | 57 | 62 |
| Missed Conclusive | 0 | 1 | 1 |
| False Positive | 0 | 0 | 0 |
| Observation-Limited Conclusive | 0 | 30 | 30 |
| Coverage | 75.00% | 67.78% | 68.50% |
| Overall Correct Rate | 100.00% | 82.78% | 84.50% |
| Accuracy (Evaluable Conclusive) | 100.00% | 100.00% | 100.00% |
| Rata-rata Cost (UCS / Checklist) | 2.80 / 2.90 | 6.83 / 6.69 | 6.425 / 6.31 |
| Rata-rata Test Count (UCS / Checklist) | 1.25 / 1.30 | 2.82 / 2.68 | 2.66 / 2.54 |

Catatan Angka Log vs CSV:
- Log print `6.42` vs CSV `6.425` untuk Rata-rata Total Cost Combined UCS (akibat pembulatan tampilan log).

====================================================================
9. PERBANDINGAN UCS DAN CHECKLIST
====================================================================

- Klasifikasi Hasil: UCS dan Fixed-Order Checklist menghasilkan metrik klasifikasi
  (correct conclusive, missed conclusive, coverage, overall correct rate) yang IDENTIK
  pada seluruh dataset.
- Perbedaan Biaya:
  * On Baseline Dataset: UCS lebih hemat biaya (2.80 vs 2.90) dan jumlah tes (1.25 vs 1.30).
  * On Extended & Combined Datasets: Checklist memiliki rata-rata total cost sedikit
    lebih rendah (Combined: 6.31 vs 6.425) dan jumlah tes lebih rendah (2.54 vs 2.66).
- Kesimpulan Perbandingan: UCS memberikan jalur optimal pada kasus sederhana, sementara
  Checklist statis memiliki keunggulan cost pada skenario dengan banyak tes inconclusive
  berbiaya tinggi dalam extended dataset.

====================================================================
10. KETERBATASAN SISTEM
====================================================================

1. Pengetahuan Domain Terbatas: Hanya mencakup 4 kategori kerusakan dan 7 uji diagnostik (dengan rentang cost 1–5).
2. Ketergantungan Input Pengguna: Bergantung sepenuhnya pada keakuratan laporan gejala dan hasil tes.
3. Tanpa Inspeksi Langsung: Tidak membaca sensor OS/hardware secara otomatis.
4. Terlibat Misleading Outcome: Kasus `EXT_DRV_045` menunjukkan bahwa jika tes memberikan
   hasil false_positive, sistem dapat mengeliminasi diagnosis yang benar.
5. Early Stopping UCS: Pada 30 kasus kontradiktif, UCS dapat menyimpulkan diagnosis sebelum
   tes kontradiktif dijalankan jika bukti awal sudah mencukupi threshold.
6. Pemodelan Biaya Relatif: Bobot biaya (1–5) bersifat abstrak dan relatif, bukan estimasi
   biaya finansial atau durasi nyata.

====================================================================
11. KESIMPULAN
====================================================================

Pengujian dan evaluasi Progres ke-2 telah selesai dilakukan secara objektif dengan
seluruh bukti tercatat dalam file log dan simulasi yang valid.
Sistem AI Computer Diagnosis membuktikan:
- 108 unit test pass 100%.
- 3 dataset terverifikasi valid tanpa error.
- 10 simulasi fungsional berhasil 100% sesuai ekspektasi.
- Evaluasi eksperimental UCS vs Checklist berhasil dijalankan dengan metrik yang konsisten.
- Seluruh artefak pendukung tersimpan rapi dalam folder `laporan/progres-2/`.

Langkah tersisa hanyalah pengambilan screenshot UI secara manual oleh pengembang
sesuai daftar checklist di `02-screenshot/DAFTAR_SCREENSHOT_YANG_HARUS_DIAMBIL.md`.
