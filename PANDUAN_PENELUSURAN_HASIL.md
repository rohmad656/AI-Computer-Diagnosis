# PANDUAN PENELUSURAN HASIL
## Proyek AI Computer Diagnosis

Dokumen ini adalah peta navigasi tunggal untuk menemukan seluruh hasil, bukti, dan implementasi proyek. Ketika dosen bertanya "hasil ini ada di file mana?", buka halaman ini dan ikuti tabel yang sesuai.

Semua path relatif terhadap root proyek (`AI-Computer-Diagnosis/`). Semua angka numerik dicocokkan langsung dari file log dan CSV aktual.

---

## Daftar Isi

- [A. Informasi Proyek](#a-informasi-proyek)
- [B. Peta Struktur Folder](#b-peta-struktur-folder)
- [C. Lokasi Implementasi Algoritma](#c-lokasi-implementasi-algoritma)
- [D. Lokasi Data dan Knowledge Base](#d-lokasi-data-dan-knowledge-base)
- [E. Lokasi Hasil Pengujian](#e-lokasi-hasil-pengujian)
- [F. Lokasi Hasil Simulasi](#f-lokasi-hasil-simulasi)
- [G. Lokasi Hasil Evaluasi](#g-lokasi-hasil-evaluasi)
- [H. Lokasi Screenshot](#h-lokasi-screenshot)
- [I. Cara Menjalankan Proyek](#i-cara-menjalankan-proyek)
- [J. Panduan Menjawab Pertanyaan Dosen](#j-panduan-menjawab-pertanyaan-dosen)

---

## A. Informasi Proyek

| Atribut | Nilai |
| :--- | :--- |
| **Nama Proyek** | AI Computer Diagnosis |
| **Jenis** | Sistem pakar diagnosis awal masalah komputer berbasis web |
| **Platform** | Windows (Python + Streamlit) |
| **Algoritma Utama** | Uniform Cost Search (UCS) berbasis biaya kumulatif minimum |
| **Pembanding** | Fixed-Order Troubleshooting Checklist |
| **Lingkup Diagnosis** | 4 kategori: Driver & Software, Overheating, Storage/Disk, RAM/Memori |
| **Pemeriksaan Diagnostik** | 7 uji diagnostik dengan rentang cost 1–5 |
| **Gejala** | 13 gejala standar di `data/symptoms.json`; gejala kustom dari deskripsi bebas/kode BSOD hanya disimpan di `st.session_state` |
| **Dataset Evaluasi** | Baseline 20 kasus + Extended 180 kasus = Combined 200 kasus |
| **Unit Test** | 108 test (100% pass) |
| **Repositori** | https://github.com/rohmad656/AI-Computer-Diagnosis.git |
| **Python** | 3.14.10 |
| **Streamlit** | 1.67.0 |
| **Pytest** | 9.2.0 |
| **Matplotlib** | 3.11.2 |

### Gambaran Singkat Cara Kerja Sistem

1. **Pemilihan gejala**: Pengguna memilih gejala awal dari 13 gejala standar atau memasukkan deskripsi bebas/kode BSOD.
2. **Inisialisasi state**: `initialize_diagnosis()` di `core/diagnosis.py` membangun `DiagnosisState` dengan `possible_categories` yang dipetakan dari gejala.
3. **Rekomendasi pemeriksaan**: UCS (`core/ucs.py`) menjalankan `uniform_cost_search()` dari state saat ini untuk menemukan pemeriksaan berikutnya dengan biaya kumulatif terendah.
4. **Input hasil pengguna**: Pengguna memasukkan hasil observasi aktual. `apply_test_result()` memperbarui `supporting_evidence`, `trusted_support`, `contradicting_evidence`, dan `possible_categories`.
5. **Evaluasi**: `evaluate_diagnosis()` menentukan apakah diagnosis sudah `conclusive`, `inconclusive`, atau `in_progress`.
6. **Online replanning**: Jika belum konklusif, UCS dijalankan ulang dari state terbaru.

Sistem **tidak** memaksakan diagnosis; jika bukti tidak cukup atau bertentangan, diagnosis dinyatakan `inconclusive` secara aman.

---

## B. Peta Struktur Folder

```
AI-Computer-Diagnosis/           ← Root proyek
├── app.py                       ← Entry point Streamlit (antarmuka web)
├── requirements.txt             ← Dependensi (streamlit, pytest, matplotlib)
├── README.md                    ← Halaman depan dokumentasi proyek
├── DOKUMENTASI_TEKNIS_FINAL.md  ← Dokumentasi teknis komprehensif
├── PANDUAN_PENELUSURAN_HASIL.md ← Peta navigasi hasil (file ini)
├── .streamlit/
│   └── config.toml              ← Konfigurasi tema Streamlit
│
├── core/                        ← Logika inti Classical AI
│   ├── ucs.py                   ← Implementasi Uniform Cost Search
│   ├── diagnosis.py             ← DiagnosisState, mesin inferensi, evaluasi
│   ├── knowledge_base.py        ← Loader + validator skema JSON
│   ├── symptom_matcher.py       ← Pencocokan teks + validasi kode BSOD
│   └── exceptions.py            ← Eksepsi kustom (NoPathFoundError, dll.)
│
├── data/                        ← Basis pengetahuan (Knowledge Base) + dataset
│   ├── symptoms.json            ← 4 kategori + 13 gejala awal
│   ├── diagnostic_tests.json    ← 7 uji diagnostik, cost, pemetaan bukti
│   ├── test_cases.json          ← 4 skenario integrasi dasar
│   └── extended_dataset.json    ← 180 kasus simulasi extended
│
├── evaluation/                  ← Modul evaluasi eksperimental
│   ├── evaluation_dataset.json  ← Dataset baseline 20 kasus
│   ├── checklist.py             ← Implementasi Fixed-Order Checklist
│   ├── run_evaluation.py        ← Mesin evaluasi & klasifikasi outcome
│   ├── run_evaluation_all.py    ← Runner baseline / extended / combined
│   ├── validate_dataset.py      ← Validator integritas dataset
│   ├── generate_extended_dataset.py ← Generator dataset extended
│   ├── visualize.py             ← Pembuat grafik Matplotlib
│   └── results/                 ← Artefak hasil evaluasi
│       ├── evaluation_report.json  ← Laporan JSON lengkap (combined)
│       ├── results_per_case.csv    ← Data per kasus (combined)
│       ├── summary_metrics.csv     ← Ringkasan metrik (combined)
│       ├── chart_average_cost.png
│       ├── chart_average_test_count.png
│       ├── chart_outcomes.png
│       ├── chart_cost_per_case.png
│       ├── chart_cost_per_category.png
│       ├── baseline/            ← Artefak evaluasi 20 kasus
│       │   ├── evaluation_report.json
│       │   ├── results_per_case.csv
│       │   └── summary_metrics.csv
│       ├── extended/            ← Artefak evaluasi 180 kasus
│       │   ├── evaluation_report.json
│       │   ├── results_per_case.csv
│       │   └── summary_metrics.csv
│       └── combined/            ← Artefak evaluasi 200 kasus
│           ├── evaluation_report.json
│           ├── results_per_case.csv
│           └── summary_metrics.csv
│
├── tests/                       ← 108 unit test otomatis
│   ├── test_ucs.py              ← 9 test algoritma UCS
│   ├── test_diagnosis.py        ← 60 test mesin diagnosis & evidence
│   ├── test_symptom_matcher.py  ← 13 test pencocokan teks & BSOD
│   ├── test_user_symptoms.py    ← 13 test gejala kustom & sesi
│   └── test_reset.py            ← 13 test reset sesi & flag UI
│
├── screenshots/                 ← 15 tangkapan layar antarmuka (multi-resolusi)
│   ├── align_1920x1080.png
│   ├── align_1366x768.png
│   ├── align_1024x768.png
│   ├── align_1536x864.png
│   ├── align_768x1024.png
│   ├── align_390x844.png
│   ├── mobile_drawer_open.png
│   └── screen_*.png             ← 8 screenshot resolusi tambahan
│
├── assets/                      ← Aset statis (placeholder; saat ini kosong)
│
└── laporan/                     ← Laporan progres akademik (untracked)
    └── progres-2/               ← Laporan Progres ke-2
        ├── LAPORAN_PROGRES_2.md
        ├── INDEX_BUKTI.md
        ├── 01-log-eksekusi/     ← Log aktual 10 file
        ├── 02-screenshot/       ← Checklist screenshot UI
        ├── 03-hasil-simulasi/   ← 10 file skenario simulasi
        └── 04-hasil-evaluasi/   ← Ringkasan evaluasi komparatif
```

---

## C. Lokasi Implementasi Algoritma

| Komponen | File | Fungsi / Kelas | Bagian yang Dibuka |
| :--- | :--- | :--- | :--- |
| **Uniform Cost Search (UCS)** | `core/ucs.py` | `uniform_cost_search()` | Bagian fungsi: priority queue `heapq`, tiebreaker deterministik, explored set |
| **UCS dengan batas biaya** | `core/ucs.py` | `uniform_cost_search_with_limit()` | Bagian fungsi dengan parameter `max_cost` |
| **Search Node (priority queue)** | `core/ucs.py` | `SearchNode` (dataclass) | Deklarasi dataclass dengan `total_cost` sebagai pembanding utama |
| **Rekonstruksi jalur** | `core/ucs.py` | `reconstruct_path()` | Bagian fungsi yang menelusuri `parent` hingga state awal |
| **State diagnosis** | `core/diagnosis.py` | `DiagnosisState` (dataclass) | Deklarasi field state: evidence, kategori, biaya |
| **Goal test** | `core/diagnosis.py` | `is_goal_state()` | Bagian fungsi yang memakai `trusted_support` |
| **Fungsi ekspansi state** | `core/diagnosis.py` | `expand_state()` | Bagian fungsi yang menghasilkan pasangan `(next_state, step_cost, action)` |
| **Rekomendasi pemeriksaan berikutnya** | `core/diagnosis.py` | `get_next_recommended_test()` | Bagian fungsi yang memanggil `uniform_cost_search()` |
| **Inisialisasi diagnosis** | `core/diagnosis.py` | `initialize_diagnosis()` | Bagian fungsi yang mengisi `possible_categories` |
| **Aplikasi hasil pemeriksaan** | `core/diagnosis.py` | `apply_test_result()` | Bagian fungsi yang memperbarui evidence |
| **Evaluasi status diagnosis** | `core/diagnosis.py` | `evaluate_diagnosis()` | Bagian fungsi yang menghasilkan `conclusive`/`inconclusive`/`in_progress` |
| **Konfirmasi kategori (trusted_support)** | `core/diagnosis.py` | `is_category_confirmed()` | Bagian fungsi yang hanya memakai `trusted_support` |
| **Kategori berkonflik** | `core/diagnosis.py` | `is_category_conflicting()` | Bagian fungsi yang membandingkan dukungan dan kontradiksi |
| **Pemeriksaan tersedia** | `core/diagnosis.py` | `get_available_tests()` | Bagian fungsi yang menyaring tes relevan & belum dilakukan |
| **Online replanning** | `core/diagnosis.py` | `get_next_recommended_test()` | Memanggil UCS dari state terbaru setelah setiap `apply_test_result()` |
| **Mesin diagnosis terpadu** | `core/diagnosis.py` | `DiagnosisEngine` | Deklarasi kelas wrapper API |
| **Loader Knowledge Base** | `core/knowledge_base.py` | `load_symptoms()`, `load_diagnostic_tests()` | Bagian fungsi loader JSON |
| **Validator skema JSON** | `core/knowledge_base.py` | `validate_knowledge_base()` | Bagian fungsi validasi struktur |
| **Pencocokan gejala teks** | `core/symptom_matcher.py` | `match_free_text()` | Bagian fungsi pencocokan kata kunci |
| **Validasi kode BSOD** | `core/symptom_matcher.py` | `validate_bsod_code()`, `match_bsod_code()` | Bagian fungsi validasi dan pemetaan kode BSOD |
| **Pembuatan gejala kustom** | `core/symptom_matcher.py` | `create_user_defined_symptom()` | Bagian fungsi pembuatan gejala dari deskripsi pengguna |
| **Antarmuka Streamlit** | `app.py` | `main()` | Fungsi utama entry point aplikasi |
| **Form pilihan hasil observasi** | `app.py` | `render_process_section()` | Bagian yang merakit `choice_options` |
| **Filter opsi UI (EXCLUDED_UI_OUTCOMES)** | `app.py` | `EXCLUDED_UI_OUTCOMES` | Konstanta di bagian atas file |
| **Label outcome** | `app.py` | `OUTCOME_LABELS`, `outcome_label()` | Konstanta dan fungsi di bagian atas file |
| **Fixed-Order Checklist (pembanding)** | `evaluation/checklist.py` | Seluruh file | Urutan pemeriksaan tetap: cpu_temp→driver→smart→disk_logs→error_history→memory |
| **Runner evaluasi** | `evaluation/run_evaluation.py` | `run_evaluation()`, `classify_outcome()` | Bagian fungsi runner dan klasifikasi bucket |
| **Klasifikasi outcome evaluasi** | `evaluation/run_evaluation.py` | `classify_outcome()` | Bagian fungsi dengan 6 konstanta bucket outcome |
| **Visualisasi grafik** | `evaluation/visualize.py` | `main()`, tiap `plot_*()` | Input: `evaluation/results/evaluation_report.json` |

### Aturan `trusted_support` vs `misleading_support`

| Tipe Outcome | `supporting_evidence` | `trusted_support` | `misleading_support` |
| :--- | :---: | :---: | :---: |
| `normal` | ✓ | ✓ | — |
| `abnormal` | ✓ | ✓ | — |
| `misleading` | ✓ | — | ✓ |
| `uncertain` | — | — | — |

Sumber: `core/diagnosis.py` → `apply_test_result()`. Goal test `is_goal_state()` hanya memeriksa `trusted_support`, bukan `supporting_evidence`.

---

## D. Lokasi Data dan Knowledge Base

| Data | File | Kunci JSON | Isi |
| :--- | :--- | :--- | :--- |
| **4 Kategori diagnosis** | `data/symptoms.json` | `categories` | `driver_software`, `overheating`, `storage_disk`, `ram_memory` |
| **13 Gejala awal** | `data/symptoms.json` | `symptoms` | 13 gejala standar beserta field `related_categories` |
| **7 Pemeriksaan diagnostik** | `data/diagnostic_tests.json` | `tests` | ID, name, cost (1–5), `possible_outcomes`, `outcome_types`, `evidence_mapping` |
| **Pemetaan bukti (evidence mapping)** | `data/diagnostic_tests.json` | `tests[i].evidence_mapping` | Per outcome: `supports`, `contradicts` |
| **4 Skenario integrasi** | `data/test_cases.json` | `test_cases` | Skenario dasar untuk `tests/test_diagnosis.py` |
| **Dataset baseline (20 kasus)** | `evaluation/evaluation_dataset.json` | `test_cases` | 20 kasus: driver×5, mixed×1, overheating×5, ram×3, storage×6 |
| **Dataset extended (180 kasus)** | `data/extended_dataset.json` | `cases` | 180 kasus: 45×4 kategori; tipe: simple, cross_category, uncertain, contradictory, misleading |
| **Dataset combined** | Gabungan dua file di atas | — | 200 kasus via `run_evaluation_all.py --mode combined` |

### Daftar 7 Pemeriksaan Diagnostik

| ID Tes | Nama | Kategori | Cost | Outcomes (UI) |
| :--- | :--- | :--- | :---: | :--- |
| `test_cpu_gpu_temp` | Cek suhu CPU/GPU | `overheating` | 1 | normal, elevated, critical, inconclusive |
| `test_smart_disk` | Cek SMART disk | `storage_disk` | 2 | healthy, warning, bad, inconclusive |
| `test_driver_status` | Cek status driver | `driver_software` | 2 | all_ok, yellow_bang, error_code, inconclusive |
| `test_disk_system_error_logs` | Cek log error disk/sistem | `storage_disk` | 3 | no_errors, disk_errors_present, inconclusive |
| `test_error_code_history` | Cek riwayat kode error | `driver_software` | 3 | no_driver_errors, driver_errors_found, inconclusive |
| `test_memory_diagnostic` | Tes memori (butuh restart) | `ram_memory` | 5 | no_errors, errors_found, inconclusive |
| `test_ram_usage_snapshot` | Cek Penggunaan RAM | `ram_memory` | 1 | normal, high_usage, inconclusive |

> Catatan: `false_positive` dan `false_negative` terdaftar di `possible_outcomes` JSON untuk keperluan dataset simulasi. Di antarmuka pengguna (UI), keduanya disaring oleh `EXCLUDED_UI_OUTCOMES` di `app.py` (konstanta `EXCLUDED_UI_OUTCOMES`) dan tidak pernah ditampilkan sebagai pilihan observasi.

---

## E. Lokasi Hasil Pengujian

| Pengujian | Hasil Aktual | Lokasi Log | Cara Menjalankan Ulang |
| :--- | :--- | :--- | :--- |
| **108 Unit Test** | `108 passed in 1.84s` (log) / `2.59s` (run terbaru) | `laporan/progres-2/01-log-eksekusi/pytest.txt` | `.venv\Scripts\python.exe -m pytest -q` |
| **Detail tiap test** | — | — | `.venv\Scripts\python.exe -m pytest -v` |
| **Validasi Dataset Baseline** | 20 kasus valid, 0 error | `laporan/progres-2/01-log-eksekusi/dataset-validation-baseline.txt` | `.venv\Scripts\python.exe -m evaluation.validate_dataset --baseline` |
| **Validasi Dataset Extended** | 180 kasus valid, 0 error | `laporan/progres-2/01-log-eksekusi/dataset-validation-extended.txt` | `.venv\Scripts\python.exe -m evaluation.validate_dataset --extended` |
| **Validasi Dataset Combined** | 200 kasus valid, 0 error | `laporan/progres-2/01-log-eksekusi/dataset-validation-combined.txt` | `.venv\Scripts\python.exe -m evaluation.validate_dataset --combined` |
| **Validasi semua dataset** | — | `laporan/progres-2/01-log-eksekusi/dataset-validation.txt` | `.venv\Scripts\python.exe -m evaluation.validate_dataset` |
| **Streamlit Smoke Test** | Server aktif setelah 12 detik, tidak crash | `laporan/progres-2/01-log-eksekusi/streamlit-run.txt` | `.venv\Scripts\python.exe -m streamlit run app.py` |

### Distribusi 108 Unit Test

| File Test | Jumlah Test | Fokus |
| :--- | :---: | :--- |
| `tests/test_ucs.py` | 9 | Algoritma UCS: heapq, tiebreaker, jalur minimum, explored set |
| `tests/test_diagnosis.py` | 60 | DiagnosisState, evidence, misleading, goal test, inkonklusif |
| `tests/test_symptom_matcher.py` | 13 | Pencocokan teks, BSOD map, alias map |
| `tests/test_user_symptoms.py` | 13 | Gejala kustom, ID stabil, integrasi sesi |
| `tests/test_reset.py` | 13 | Reset sesi, flag UI, isolasi antar sesi |
| **Total** | **108** | |

---

## F. Lokasi Hasil Simulasi

Semua simulasi dijalankan melalui **API internal `DiagnosisEngine`** (`core/diagnosis.py`), **bukan** melalui antarmuka UI Streamlit secara manual.

| ID | Skenario | File Hasil | Gejala Utama | Status Akhir | Cost | Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| SIM-01 | Driver Software Normal | `laporan/progres-2/03-hasil-simulasi/SIM-01-driver-normal.md` | `sym_bsod_driver` | conclusive (`driver_software`) | 5.0 | ✅ PASS |
| SIM-02 | Overheating Normal | `laporan/progres-2/03-hasil-simulasi/SIM-02-overheating-normal.md` | `sym_shutdown_thermal` | conclusive (`overheating`) | 1.0 | ✅ PASS |
| SIM-03 | Storage Disk Normal | `laporan/progres-2/03-hasil-simulasi/SIM-03-storage-normal.md` | `sym_disk_slow_freeze` | conclusive (`storage_disk`) | 5.0 | ✅ PASS |
| SIM-04 | RAM Memory Normal | `laporan/progres-2/03-hasil-simulasi/SIM-04-ram-normal.md` | `sym_app_crash_random` | conclusive (`ram_memory`) | 6.0 | ✅ PASS |
| SIM-05 | Ambiguous (Multi-Kategori) | `laporan/progres-2/03-hasil-simulasi/SIM-05-ambiguous.md` | `sym_bsod_generic` + lain | in_progress (tidak dipaksakan) | 3.0 | ✅ PASS |
| SIM-06 | Uncertain (Semua Inconclusive) | `laporan/progres-2/03-hasil-simulasi/SIM-06-uncertain.md` | `sym_system_crash` | in_progress | 10.0 | ✅ PASS |
| SIM-07 | Misleading (False Negative RAM) | `laporan/progres-2/03-hasil-simulasi/SIM-07-misleading.md` | `sym_app_crash_random` | inconclusive | 6.0 | ✅ PASS |
| SIM-08 | Conflicting (Kontradiktif) | `laporan/progres-2/03-hasil-simulasi/SIM-08-conflicting.md` | `sym_bsod_driver` + generic | inconclusive | 16.0 | ✅ PASS |
| SIM-09 | Inconclusive (No Evidence) | `laporan/progres-2/03-hasil-simulasi/SIM-09-inconclusive.md` | `sym_bsod_generic` | in_progress | 10.0 | ✅ PASS |
| SIM-10 | Reset Session & Diagnosis Ulang | `laporan/progres-2/03-hasil-simulasi/SIM-10-reset-session.md` | `sym_bsod_driver` | conclusive (`driver_software`) | 2.0 | ✅ PASS |

**Ringkasan**: `laporan/progres-2/03-hasil-simulasi/RINGKASAN_SIMULASI.md`  
**Tingkat keberhasilan**: 10/10 (100% PASS)

---

## G. Lokasi Hasil Evaluasi

### Script Evaluasi

| Perintah | Fungsi | Output |
| :--- | :--- | :--- |
| `.venv\Scripts\python.exe -m evaluation.run_evaluation_all --mode baseline` | Evaluasi 20 kasus | `evaluation/results/baseline/` |
| `.venv\Scripts\python.exe -m evaluation.run_evaluation_all --mode extended` | Evaluasi 180 kasus | `evaluation/results/extended/` |
| `.venv\Scripts\python.exe -m evaluation.run_evaluation_all --mode combined` | Evaluasi 200 kasus | `evaluation/results/` |
| `.venv\Scripts\python.exe -m evaluation.visualize` | Buat grafik PNG | `evaluation/results/chart_*.png` |
| `.venv\Scripts\python.exe -m evaluation.validate_dataset` | Validasi 3 dataset | stdout |

### Lokasi Artefak Kanonik

| Tipe Artefak | Baseline (20) | Extended (180) | Combined (200) |
| :--- | :--- | :--- | :--- |
| **Summary Metrics CSV** | `evaluation/results/baseline/summary_metrics.csv` | `evaluation/results/extended/summary_metrics.csv` | `evaluation/results/summary_metrics.csv` |
| **Laporan JSON Lengkap** | `evaluation/results/baseline/evaluation_report.json` | `evaluation/results/extended/evaluation_report.json` | `evaluation/results/evaluation_report.json` |
| **CSV Per Kasus** | `evaluation/results/baseline/results_per_case.csv` | `evaluation/results/extended/results_per_case.csv` | `evaluation/results/results_per_case.csv` |
| **Log teks Progres ke-2** | `laporan/progres-2/01-log-eksekusi/evaluation-baseline.txt` | `laporan/progres-2/01-log-eksekusi/evaluation-extended.txt` | `laporan/progres-2/01-log-eksekusi/evaluation-combined.txt` |

### Grafik Evaluasi (Matplotlib)

| File | Isi |
| :--- | :--- |
| `evaluation/results/chart_average_cost.png` | Rata-rata total cost UCS vs Checklist |
| `evaluation/results/chart_average_test_count.png` | Rata-rata jumlah pemeriksaan per kasus |
| `evaluation/results/chart_outcomes.png` | Distribusi 6 bucket outcome (correct, incorrect, missed, fp, obs-limited) |
| `evaluation/results/chart_cost_per_case.png` | Total cost per kasus (200 kasus) |
| `evaluation/results/chart_cost_per_category.png` | Rata-rata cost per kategori |

### Hasil Utama (Combined 200 Kasus)

Sumber: `evaluation/results/summary_metrics.csv` dan `laporan/progres-2/01-log-eksekusi/evaluation-combined.txt`

| Metrik | UCS | Checklist |
| :--- | :---: | :---: |
| Total kasus | 200 | 200 |
| Kasus label konklusif | 108 | 108 |
| Kasus label inkonklusif | 92 | 92 |
| Correct conclusive | 107 | 107 |
| Incorrect conclusive | 0 | 0 |
| Correct inconclusive | 62 | 62 |
| Missed conclusive (false negative) | 1 | 1 |
| False positive (bukti teramati) | 0 | 0 |
| Observation-limited conclusive | 30 | 30 |
| Coverage | 68.50% | 68.50% |
| Accuracy among conclusive (label) | 78.10% | 78.10% |
| Accuracy among evaluable conclusive | 100.00% | 100.00% |
| Overall correct rate | 84.50% | 84.50% |
| Overall correct rate (evaluable) | 99.41% | 99.41% |
| Rata-rata total cost | **6.425** | 6.31 |
| Rata-rata jumlah pemeriksaan | **2.66** | 2.54 |

> Catatan: Log mencetak `6.42` (pembulatan tampilan); CSV menyimpan `6.425` (nilai presisi penuh).

### Definisi 6 Bucket Outcome Evaluasi

| Bucket | Kondisi | Arti |
| :--- | :--- | :--- |
| `correct_conclusive` | Label konklusif, hasil konklusif, diagnosis sama | Diagnosis benar |
| `incorrect_conclusive` | Label konklusif, hasil konklusif, diagnosis berbeda | Diagnosis salah kategori |
| `correct_inconclusive` | Label inkonklusif, hasil inkonklusif | Sistem tepat menolak menyimpulkan |
| `missed_conclusive` | Label konklusif, hasil inkonklusif | Sistem gagal sampai pada diagnosis |
| `false_positive` | Label inkonklusif, hasil konklusif, bukti kontradiktif teramati | Sistem salah menyimpulkan |
| `observation_limited_conclusive` | Label inkonklusif, hasil konklusif, bukti kontradiktif tidak teramati | Early stopping; bukan false positive sejati |

> `false_negative` di CSV adalah nilai yang sama dengan `missed_conclusive` (diturunkan; bukan bucket tersendiri). Lihat `evaluation/run_evaluation.py` pada bagian `build_confusion_matrix()`.

### Perbedaan Simulasi vs Evaluasi

| Aspek | Simulasi (SIM-01 s.d. SIM-10) | Evaluasi (Baseline/Extended/Combined) |
| :--- | :--- | :--- |
| **Tujuan** | Membuktikan perilaku sistem pada skenario tertentu | Mengukur performa agregat UCS vs Checklist |
| **Skala** | 10 skenario terkurasi | 20 / 180 / 200 kasus otomatis |
| **Metode eksekusi** | `DiagnosisEngine` API (`core/diagnosis.py`) secara langsung | `run_evaluation.py` memanggil `initialize_diagnosis()` + `apply_test_result()` secara berulang |
| **Output** | File Markdown naratif per skenario | CSV, JSON, grafik PNG |
| **Kegunaan** | Demonstrasi perilaku kualitatif | Metrik kuantitatif komparatif |

---

## H. Lokasi Screenshot

### Screenshots di `screenshots/` (tersedia)

| File | Resolusi | Keterangan | Status |
| :--- | :--- | :--- | :--- |
| `screenshots/align_1920x1080.png` | 1920×1080 | Desktop full HD | AVAILABLE |
| `screenshots/align_1366x768.png` | 1366×768 | Laptop standar | AVAILABLE |
| `screenshots/align_1024x768.png` | 1024×768 | Monitor lama | AVAILABLE |
| `screenshots/align_1536x864.png` | 1536×864 | Laptop layar tinggi | AVAILABLE |
| `screenshots/align_768x1024.png` | 768×1024 | Tablet portrait | AVAILABLE |
| `screenshots/align_390x844.png` | 390×844 | Mobile (iPhone) | AVAILABLE |
| `screenshots/mobile_drawer_open.png` | mobile | Sidebar terbuka di mobile | AVAILABLE |
| `screenshots/screen_1920x1080.png` | 1920×1080 | — | AVAILABLE |
| `screenshots/screen_1366x768.png` | 1366×768 | — | AVAILABLE |
| `screenshots/screen_1280x800.png` | 1280×800 | — | AVAILABLE |
| `screenshots/screen_1440x900.png` | 1440×900 | — | AVAILABLE |
| `screenshots/screen_1024x768.png` | 1024×768 | — | AVAILABLE |
| `screenshots/screen_768x1024.png` | 768×1024 | — | AVAILABLE |
| `screenshots/screen_390x844.png` | 390×844 | — | AVAILABLE |
| `screenshots/screen_360x800.png` | 360×800 | — | AVAILABLE |

### Screenshots Spesifik UI Progres ke-2 (belum diambil)

Checklist: `laporan/progres-2/02-screenshot/DAFTAR_SCREENSHOT_YANG_HARUS_DIAMBIL.md`

| No | Nama File | Tampilan | Status |
| :--- | :--- | :--- | :--- |
| 1 | `01-halaman-utama.png` | Halaman awal tanpa input | NOT YET CAPTURED |
| 2 | `02-pilih-gejala.png` | Gejala BSOD driver dipilih | NOT YET CAPTURED |
| 3 | `03-rekomendasi-tes.png` | Rekomendasi UCS + biaya | NOT YET CAPTURED |
| 4 | `04-form-hasil-tes.png` | Form pilihan hasil observasi | NOT YET CAPTURED |
| 5 | `05-hasil-conclusive.png` | Diagnosis konklusif | NOT YET CAPTURED |
| 6 | `06-hasil-kontradiksi.png` | Evidence kontradiktif | NOT YET CAPTURED |
| 7 | `07-hasil-inconclusive.png` | Diagnosis inkonklusif | NOT YET CAPTURED |
| 8 | `08-riwayat-state.png` | Riwayat langkah & cost | NOT YET CAPTURED |
| 9 | `09-reset-sesi.png` | Sesi setelah reset | NOT YET CAPTURED |

**Cara mengambil screenshot UI:**
```powershell
# 1. Jalankan Streamlit
.venv\Scripts\python.exe -m streamlit run app.py

# 2. Buka browser ke http://localhost:8501
# 3. Ambil screenshot sesuai checklist dengan Win+Shift+S
# 4. Simpan ke laporan/progres-2/02-screenshot/
```

---

## I. Cara Menjalankan Proyek

### Pra-Syarat

```powershell
# Windows PowerShell, dari root proyek
# Virtual environment sudah dibuat dan terdapat .venv/

# Jika belum ada venv:
python -m venv .venv
pip install -r requirements.txt
```

### Menjalankan Aplikasi Streamlit

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
# Buka http://localhost:8501 di browser
```

### Menjalankan Unit Test

```powershell
# Semua test, ringkas
.venv\Scripts\python.exe -m pytest -q

# Semua test, nama test ditampilkan
.venv\Scripts\python.exe -m pytest -v

# JANGAN gunakan: pytest -q  (gagal dengan ModuleNotFoundError: No module named 'core')
# Alasan: pytest dari PATH tidak memasukkan CWD ke sys.path; selalu gunakan python -m pytest
```

### Menjalankan Validasi Dataset

```powershell
# Validasi semua dataset
.venv\Scripts\python.exe -m evaluation.validate_dataset

# Per mode
.venv\Scripts\python.exe -m evaluation.validate_dataset --baseline
.venv\Scripts\python.exe -m evaluation.validate_dataset --extended
.venv\Scripts\python.exe -m evaluation.validate_dataset --combined
```

### Menjalankan Evaluasi

```powershell
# 20 kasus baseline
.venv\Scripts\python.exe -m evaluation.run_evaluation_all --mode baseline

# 180 kasus extended
.venv\Scripts\python.exe -m evaluation.run_evaluation_all --mode extended

# 200 kasus combined
.venv\Scripts\python.exe -m evaluation.run_evaluation_all --mode combined

# Dengan output direktori kustom
.venv\Scripts\python.exe -m evaluation.run_evaluation_all --mode combined --output-dir evaluation/results/combined
```

### Menjalankan Visualisasi Grafik

```powershell
.venv\Scripts\python.exe -m evaluation.visualize
# Membaca: evaluation/results/evaluation_report.json
# Menulis: evaluation/results/chart_*.png
```

---

## J. Panduan Menjawab Pertanyaan Dosen

| Pertanyaan Dosen | Jawaban Singkat | File / Bagian yang Dibuka |
| :--- | :--- | :--- |
| **Di mana implementasi UCS?** | Di `core/ucs.py`, fungsi `uniform_cost_search()`. Priority queue menggunakan `heapq`, tiebreaker integer deterministik, explored dict. | `core/ucs.py` → fungsi `uniform_cost_search()` |
| **Di mana proses diagnosis dilakukan?** | Di `core/diagnosis.py`. Alur: `initialize_diagnosis()` → `get_next_recommended_test()` (memanggil UCS) → `apply_test_result()` → `evaluate_diagnosis()` | `core/diagnosis.py` →fungsi-fungsi tersebut |
| **Di mana Knowledge Base?** | File JSON di `data/`: `symptoms.json` (kategori & gejala), `diagnostic_tests.json` (uji, cost, evidence mapping). Loader di `core/knowledge_base.py`. | `data/diagnostic_tests.json`, `data/symptoms.json` |
| **Di mana daftar gejala?** | `data/symptoms.json` → kunci `symptoms` (13 gejala standar beserta `related_categories`). Gejala tambahan pengguna hanya disimpan di `session_state`. | `data/symptoms.json` |
| **Di mana dataset evaluasi?** | Baseline: `evaluation/evaluation_dataset.json` (20 kasus). Extended: `data/extended_dataset.json` (180 kasus). | Lihat bagian D dokumen ini |
| **Mana bukti 108 unit test berhasil?** | Log aktual di `laporan/progres-2/01-log-eksekusi/pytest.txt` menampilkan `108 passed in 1.84s`. Jalankan ulang: `.venv\Scripts\python.exe -m pytest -q` | `laporan/progres-2/01-log-eksekusi/pytest.txt` |
| **Mana bukti aplikasi berhasil dijalankan?** | Log smoke test di `laporan/progres-2/01-log-eksekusi/streamlit-run.txt`: server aktif, tidak crash setelah 12 detik. | `laporan/progres-2/01-log-eksekusi/streamlit-run.txt` |
| **Mana hasil 10 simulasi?** | Folder `laporan/progres-2/03-hasil-simulasi/`: 10 file Markdown (SIM-01 s.d. SIM-10), ringkasan di `RINGKASAN_SIMULASI.md`. | `laporan/progres-2/03-hasil-simulasi/` |
| **Mana hasil evaluasi 200 kasus?** | Log teks: `laporan/progres-2/01-log-eksekusi/evaluation-combined.txt`. CSV: `evaluation/results/summary_metrics.csv`. Grafik: `evaluation/results/chart_*.png` | `evaluation/results/summary_metrics.csv` |
| **Bagaimana membuktikan hasil evaluasi?** | Jalankan ulang: `.venv\Scripts\python.exe -m evaluation.run_evaluation_all --mode combined`. Output harus identik dengan log. Periksa CSV kanonik di `evaluation/results/combined/summary_metrics.csv` | Bagian G dokumen ini |
| **Apa perbedaan simulasi dan evaluasi?** | Simulasi: 10 skenario kualitatif via `DiagnosisEngine` API. Evaluasi: metrik kuantitatif UCS vs Checklist pada 200 kasus otomatis. | Bagian F & G dokumen ini |
| **Bagaimana menangani hasil pemeriksaan yang bertentangan?** | `apply_test_result()` menambahkan bukti ke `contradicting_evidence`. Kategori dengan bukti kontradiktif dihapus dari `possible_categories`. Jika ada konflik, `evaluate_diagnosis()` mengembalikan `inconclusive`. | `core/diagnosis.py` → `apply_test_result()`, `is_category_conflicting()` |
| **Bagaimana sistem menentukan pemeriksaan berikutnya?** | `get_next_recommended_test()` memanggil `uniform_cost_search()` dari state saat ini. UCS mengeksplorasi semua kombinasi tes + outcome yang mungkin, memilih jalur dengan biaya kumulatif terkecil menuju goal state. | `core/diagnosis.py` → `get_next_recommended_test()`, `core/ucs.py` → `uniform_cost_search()` |
| **Bagaimana sistem menangani hasil yang tidak pasti?** | Outcome `inconclusive` bertipe `uncertain` → dicatat di `neutral_evidence`, tidak menambah `trusted_support` atau `contradicting_evidence`. Sistem melanjutkan ke pemeriksaan relevan berikutnya. | `core/diagnosis.py` → `apply_test_result()`, tipe `uncertain` di `data/diagnostic_tests.json` → `outcome_types` |
| **Di mana implementasi Fixed-Order Checklist?** | `evaluation/checklist.py`. Urutan tetap: `test_cpu_gpu_temp` (cost 1) → `test_driver_status` (2) → `test_smart_disk` (2) → `test_disk_system_error_logs` (3) → `test_error_code_history` (3) → `test_memory_diagnostic` (5). | `evaluation/checklist.py` |
| **Mengapa 30 kasus dikategorikan observation-limited?** | UCS berhenti (*early stopping*) saat goal state tercapai sebelum tes kontradiktif dieksekusi. Bukti kontradiktif ada dalam dataset, tetapi tidak diakses oleh UCS. Ini bukan false positive; dikategorikan `observation_limited_conclusive`. | `evaluation/run_evaluation.py` → `classify_outcome()`, `laporan/progres-2/01-log-eksekusi/TROUBLESHOOTING.md` |
| **Mengapa 1 kasus missed_conclusive (EXT_DRV_045)?** | Kasus misleading: outcome `false_positive` pada `test_driver_status` menambah `misleading_support` tetapi tidak `trusted_support`. UCS tidak mencapai goal state karena tidak ada bukti konfirmasi sejati. Ini keterbatasan yang didokumentasikan. | `laporan/progres-2/01-log-eksekusi/TROUBLESHOOTING.md`, `evaluation/results/extended/results_per_case.csv` (ID `EXT_DRV_045`) |
| **Bagaimana `false_positive`/`false_negative` dipakai di sistem ini?** | Di KB (JSON): sebagai jenis outcome tes untuk dataset simulasi. Di evaluasi: sebagai bucket klasifikasi performa. Di UI: **tidak** ditampilkan (disaring oleh `EXCLUDED_UI_OUTCOMES` di `app.py`). | `app.py` → `EXCLUDED_UI_OUTCOMES`, `data/diagnostic_tests.json`, `evaluation/run_evaluation.py` → `classify_outcome()` |

---

## Referensi Silang Dokumen

| Dokumen | Lokasi | Isi |
| :--- | :--- | :--- |
| Panduan navigasi (file ini) | `PANDUAN_PENELUSURAN_HASIL.md` | Peta hasil, algoritma, data, evaluasi |
| Halaman depan proyek | `README.md` | Deskripsi, fitur, cara install, hasil evaluasi ringkas |
| Dokumentasi teknis | `DOKUMENTASI_TEKNIS_FINAL.md` | Arsitektur, formulasi UCS, Knowledge Base, metodologi evaluasi |
| Laporan Progres ke-2 | `laporan/progres-2/LAPORAN_PROGRES_2.md` | Laporan resmi per bagian |
| Indeks bukti Progres ke-2 | `laporan/progres-2/INDEX_BUKTI.md` | Navigasi seluruh file bukti |
| Ringkasan simulasi | `laporan/progres-2/03-hasil-simulasi/RINGKASAN_SIMULASI.md` | Tabel 10 skenario |
| Ringkasan evaluasi | `laporan/progres-2/04-hasil-evaluasi/RINGKASAN_EVALUASI.md` | Perbandingan UCS vs Checklist per dataset |
| Troubleshooting | `laporan/progres-2/01-log-eksekusi/TROUBLESHOOTING.md` | 4 isu yang diselesaikan selama Progres ke-2 |
| Lingkungan pengembangan | `laporan/progres-2/01-log-eksekusi/environment.txt` | OS, Python version, dependensi |
