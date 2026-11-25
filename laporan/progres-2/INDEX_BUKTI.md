# INDEX BUKTI PROGRES KE-2

Navigasi lengkap untuk dosen, reviewer, dan mahasiswa. Semua path bersifat relatif terhadap root proyek `AI-Computer-Diagnosis/`.

**Panduan utama:** [`PANDUAN_PENELUSURAN_HASIL.md`](../../PANDUAN_PENELUSURAN_HASIL.md)  
**Laporan utama:** [`LAPORAN_PROGRES_2.md`](LAPORAN_PROGRES_2.md) — path lengkap: `laporan/progres-2/LAPORAN_PROGRES_2.md`

Tanggal audit dokumentasi: 2026-11-25.

---

## Kunci Status

| Status | Arti |
| :--- | :--- |
| **AVAILABLE** | File benar-benar ada dan isi dapat dibaca. |
| **NOT YET CAPTURED** | File wajib belum dibuat; screenshot masih harus diambil manual. |
| **NOT FOUND** | File tidak ditemukan di lokasi yang terdokumentasi. |
| **NEEDS VERIFICATION** | File ada, tetapi perlu dicek ulang terhadap data/CSV/log terbaru. |

---

## Daftar Isi

- [A. Log Eksekusi](#a-log-eksekusi)
- [B. Hasil 10 Simulasi Fungsional](#b-hasil-10-simulasi-fungsional)
- [C. Hasil Evaluasi Komparatif](#c-hasil-evaluasi-komparatif)
- [D. Screenshot Progres ke-2](#d-screenshot-progres-ke-2)
- [E. Dokumentasi dan Kode Utama](#e-dokumentasi-dan-kode-utama)
- [F. Status Kelengkapan](#f-status-kelengkapan)
- [G. Perintah Verifikasi Cepat](#g-perintah-verifikasi-cepat)

---

## A. Log Eksekusi

Lokasi folder: `laporan/progres-2/01-log-eksekusi/`

| Kategori | File | Status | Dibuktikan |
| :--- | :--- | :--- | :--- |
| Lingkungan | `laporan/progres-2/01-log-eksekusi/environment.txt` | AVAILABLE | Windows 11 build 26300; Python 3.14.10; Streamlit 1.67.0; Pytest 9.2.0; Matplotlib 3.11.2 |
| Unit test | `laporan/progres-2/01-log-eksekusi/pytest.txt` | AVAILABLE | 108 test lulus (`108 passed in 1.84s`) |
| Validasi baseline | `laporan/progres-2/01-log-eksekusi/dataset-validation-baseline.txt` | AVAILABLE | 20 kasus valid, 0 error |
| Validasi extended | `laporan/progres-2/01-log-eksekusi/dataset-validation-extended.txt` | AVAILABLE | 180 kasus valid, 0 error |
| Validasi combined | `laporan/progres-2/01-log-eksekusi/dataset-validation-combined.txt` | AVAILABLE | 200 kasus valid, 0 error |
| Validasi semua (agregat) | `laporan/progres-2/01-log-eksekusi/dataset-validation.txt` | AVAILABLE | Ringkasan baseline + extended + combined |
| Evaluasi baseline | `laporan/progres-2/01-log-eksekusi/evaluation-baseline.txt` | AVAILABLE | Ringkasan metrik + 20 hasil per kasus |
| Evaluasi extended | `laporan/progres-2/01-log-eksekusi/evaluation-extended.txt` | AVAILABLE | Ringkasan metrik + 180 hasil per kasus |
| Evaluasi combined | `laporan/progres-2/01-log-eksekusi/evaluation-combined.txt` | AVAILABLE | Ringkasan metrik + 200 hasil per kasus |
| Streamlit smoke test | `laporan/progres-2/01-log-eksekusi/streamlit-run.txt` | AVAILABLE | Server aktif 12 detik, tidak crash |
| Troubleshooting | `laporan/progres-2/01-log-eksekusi/TROUBLESHOOTING.md` | AVAILABLE | 4 isu dan penyelesaiannya |

---

## B. Hasil 10 Simulasi Fungsional

Metode eksekusi: **API internal `DiagnosisEngine`** (`core/diagnosis.py`), bukan demonstrasi UI Streamlit manual.

Ringkasan: `laporan/progres-2/03-hasil-simulasi/RINGKASAN_SIMULASI.md` — AVAILABLE

| ID | File | Status | Dibuktikan |
| :--- | :--- | :--- | :--- |
| SIM-01 | `laporan/progres-2/03-hasil-simulasi/SIM-01-driver-normal.md` | AVAILABLE | Driver software terdiagnosis conclusively, cost 5.0 |
| SIM-02 | `laporan/progres-2/03-hasil-simulasi/SIM-02-overheating-normal.md` | AVAILABLE | Overheating terdiagnosis, cost 1.0 (UCS pilih tes termurah) |
| SIM-03 | `laporan/progres-2/03-hasil-simulasi/SIM-03-storage-normal.md` | AVAILABLE | Storage disk terdiagnosis, cost 5.0 |
| SIM-04 | `laporan/progres-2/03-hasil-simulasi/SIM-04-ram-normal.md` | AVAILABLE | RAM memory terdiagnosis, cost 6.0 |
| SIM-05 | `laporan/progres-2/03-hasil-simulasi/SIM-05-ambiguous.md` | AVAILABLE | Ambiguitas multi-kategori tidak dipaksakan, in_progress, cost 3.0 |
| SIM-06 | `laporan/progres-2/03-hasil-simulasi/SIM-06-uncertain.md` | AVAILABLE | Semua outcome uncertain → in_progress, cost 10.0 |
| SIM-07 | `laporan/progres-2/03-hasil-simulasi/SIM-07-misleading.md` | AVAILABLE | Misleading false-negative RAM → inconclusive, cost 6.0 |
| SIM-08 | `laporan/progres-2/03-hasil-simulasi/SIM-08-conflicting.md` | AVAILABLE | Kontradiksi teramati → inconclusive, cost 16.0 |
| SIM-09 | `laporan/progres-2/03-hasil-simulasi/SIM-09-inconclusive.md` | AVAILABLE | Tanpa evidence → in_progress, cost 10.0 |
| SIM-10 | `laporan/progres-2/03-hasil-simulasi/SIM-10-reset-session.md` | AVAILABLE | Reset sesi bersih, diagnosis ulang conclusive, cost 2.0 |

---

## C. Hasil Evaluasi Komparatif

### Ringkasan Naratif

| File | Status | Isi |
| :--- | :--- | :--- |
| `laporan/progres-2/04-hasil-evaluasi/RINGKASAN_EVALUASI.md` | AVAILABLE | Perbandingan UCS vs Checklist pada 20/180/200 kasus |
| `laporan/progres-2/04-hasil-evaluasi/README.md` | AVAILABLE | Penjelasan folder ringkasan dan lokasi artefak kanonik |

### Artefak Kanonik

| Tipe | Baseline (20) | Extended (180) | Combined (200) | Status |
| :--- | :--- | :--- | :--- | :--- |
| Summary Metrics | `evaluation/results/baseline/summary_metrics.csv` | `evaluation/results/extended/summary_metrics.csv` | `evaluation/results/summary_metrics.csv` | AVAILABLE |
| Laporan JSON | `evaluation/results/baseline/evaluation_report.json` | `evaluation/results/extended/evaluation_report.json` | `evaluation/results/evaluation_report.json` | AVAILABLE |
| CSV per Kasus | `evaluation/results/baseline/results_per_case.csv` | `evaluation/results/extended/results_per_case.csv` | `evaluation/results/results_per_case.csv` | AVAILABLE |

> `evaluation/results/combined/` berisi salinan artefak combined yang identik. Semua angka di panduan ini bersumber dari `evaluation/results/summary_metrics.csv` dan log teks aktual.

### Grafik Evaluasi

| File | Status | Isi |
| :--- | :--- | :--- |
| `evaluation/results/chart_average_cost.png` | AVAILABLE | Rata-rata total cost UCS vs Checklist |
| `evaluation/results/chart_average_test_count.png` | AVAILABLE | Rata-rata jumlah pemeriksaan |
| `evaluation/results/chart_outcomes.png` | AVAILABLE | Distribusi 6 bucket outcome |
| `evaluation/results/chart_cost_per_case.png` | AVAILABLE | Total cost per kasus |
| `evaluation/results/chart_cost_per_category.png` | AVAILABLE | Rata-rata cost per kategori |

### Angka Kunci Combined (200 Kasus)

Bersumber dari `evaluation/results/summary_metrics.csv`:

| Metrik | UCS | Checklist |
| :--- | ---: | ---: |
| Total kasus | 200 | 200 |
| Label konklusif / inkonklusif | 108 / 92 | 108 / 92 |
| Correct conclusive | 107 | 107 |
| Incorrect conclusive | 0 | 0 |
| Correct inconclusive | 62 | 62 |
| Missed conclusive | 1 | 1 |
| False negative (turunan) | 1 | 1 |
| False positive (teramati) | 0 | 0 |
| Observation-limited conclusive | 30 | 30 |
| Coverage | 68.50% | 68.50% |
| Overall correct rate | 84.50% | 84.50% |
| Accuracy among evaluable conclusive | 100.00% | 100.00% |
| Rata-rata cost | 6.425 (log: 6.42) | 6.31 |
| Rata-rata jumlah tes | 2.66 | 2.54 |

---

## D. Screenshot Progres ke-2

Lokasi checklist: `laporan/progres-2/02-screenshot/DAFTAR_SCREENSHOT_YANG_HARUS_DIAMBIL.md` — AVAILABLE

Folder `laporan/progres-2/02-screenshot/` saat ini **hanya berisi checklist**, belum ada file PNG.

| No | Nama File | Status | Tampilan yang Dibuktikan |
| :--- | :--- | :--- | :--- |
| 1 | `laporan/progres-2/02-screenshot/01-halaman-utama.png` | NOT YET CAPTURED | Halaman utama tanpa input |
| 2 | `laporan/progres-2/02-screenshot/02-pilih-gejala.png` | NOT YET CAPTURED | Gejala BSOD driver dipilih |
| 3 | `laporan/progres-2/02-screenshot/03-rekomendasi-tes.png` | NOT YET CAPTURED | Rekomendasi tes UCS + biaya |
| 4 | `laporan/progres-2/02-screenshot/04-form-hasil-tes.png` | NOT YET CAPTURED | Form hasil observasi (tanpa opsi misleading) |
| 5 | `laporan/progres-2/02-screenshot/05-hasil-conclusive.png` | NOT YET CAPTURED | Diagnosis konklusif |
| 6 | `laporan/progres-2/02-screenshot/06-hasil-kontradiksi.png` | NOT YET CAPTURED | Evidence kontradiktif |
| 7 | `laporan/progres-2/02-screenshot/07-hasil-inconclusive.png` | NOT YET CAPTURED | Status inkonklusif |
| 8 | `laporan/progres-2/02-screenshot/08-riwayat-state.png` | NOT YET CAPTURED | Riwayat langkah & biaya |
| 9 | `laporan/progres-2/02-screenshot/09-reset-sesi.png` | NOT YET CAPTURED | Sesi setelah reset |

**Aturan integritas:** Jangan mengubah status menjadi `CAPTURED` sebelum file PNG benar-benar ada. Screenshot lama di folder `screenshots/` tidak boleh dipakai sebagai pengganti tanpa verifikasi.

---

## E. Dokumentasi dan Kode Utama

| Kategori | File | Status | Fungsi |
| :--- | :--- | :--- | :--- |
| Panduan utama | `PANDUAN_PENELUSURAN_HASIL.md` | AVAILABLE | Peta navigasi seluruh hasil proyek |
| Halaman depan | `README.md` | AVAILABLE | Deskripsi, fitur, instalasi, cara menjalankan, hasil evaluasi |
| Dokumentasi teknis | `DOKUMENTASI_TEKNIS_FINAL.md` | AVAILABLE | Detail arsitektur/UCS/K evaluasi; (Catatan: mengandung snapshot awal 8 gejala/6 uji, data aktual 13/7) |
| Laporan Progres ke-2 | `laporan/progres-2/LAPORAN_PROGRES_2.md` | AVAILABLE | Laporan resmi Progres ke-2 |
| Indeks bukti | `laporan/progres-2/INDEX_BUKTI.md` | AVAILABLE | File ini |

### Kode dan Knowledge Base

| File | Status | Fungsi |
| :--- | :--- | :--- |
| `app.py` | AVAILABLE | Antarmuka Streamlit + filter `EXCLUDED_UI_OUTCOMES` |
| `core/ucs.py` | AVAILABLE | Algoritma Uniform Cost Search generik |
| `core/diagnosis.py` | AVAILABLE | DiagnosisEngine, state, evidence, replanning |
| `core/knowledge_base.py` | AVAILABLE | Loader + validator skema JSON |
| `core/symptom_matcher.py` | AVAILABLE | Pencocokan teks + validasi BSOD |
| `core/exceptions.py` | AVAILABLE | Eksepsi kustom sistem |
| `data/symptoms.json` | AVAILABLE | 4 kategori + 13 gejala standar |
| `data/diagnostic_tests.json` | AVAILABLE | 7 uji, cost, outcome, evidence mapping |
| `data/test_cases.json` | AVAILABLE | Skenario integrasi dasar |
| `data/extended_dataset.json` | AVAILABLE | 180 kasus extended |
| `evaluation/evaluation_dataset.json` | AVAILABLE | 20 kasus baseline |
| `evaluation/run_evaluation.py` | AVAILABLE | Mesin evaluasi & klasifikasi outcome |
| `evaluation/run_evaluation_all.py` | AVAILABLE | Runner baseline/extended/combined |
| `evaluation/checklist.py` | AVAILABLE | Metode pembanding Fixed-Order Checklist |
| `evaluation/validate_dataset.py` | AVAILABLE | Validator dataset |
| `evaluation/generate_extended_dataset.py` | AVAILABLE | Generator dataset extended |
| `evaluation/visualize.py` | AVAILABLE | Pembuat grafik evaluasi |
| `tests/test_ucs.py` | AVAILABLE | 9 test UCS |
| `tests/test_diagnosis.py` | AVAILABLE | 60 test mesin diagnosis |
| `tests/test_symptom_matcher.py` | AVAILABLE | 13 test symptom matcher |
| `tests/test_user_symptoms.py` | AVAILABLE | 13 test gejala kustom |
| `tests/test_reset.py` | AVAILABLE | 13 test reset sesi |
| `screenshots/` | AVAILABLE | 15 screenshot antarmuka multi-resolusi (bukan bukti Progres ke-2) |
| `assets/` | AVAILABLE | Folder aset statis (kosong; placeholder) |

---

## F. Status Kelengkapan Progres ke-2

| Bagian | Status |
| :--- | :--- |
| Log eksekusi (11 file: environment, pytest, validasi, evaluasi, streamlit, troubleshooting) | ✅ LENGKAP — AVAILABLE |
| 10 simulasi fungsional (SIM-01 … SIM-10) | ✅ LENGKAP — 10/10 AVAILABLE |
| Ringkasan simulasi | ✅ LENGKAP — AVAILABLE |
| Evaluasi baseline / extended / combined + ringkasan | ✅ LENGKAP — AVAILABLE |
| Artefak CSV & JSON kanonik | ✅ LENGKAP — AVAILABLE |
| 5 grafik evaluasi Matplotlib | ✅ LENGKAP — AVAILABLE |
| Laporan utama `LAPORAN_PROGRES_2.md` | ✅ AVAILABLE |
| Panduan penelusuran hasil | ✅ AVAILABLE |
| Indeks bukti (file ini) | ✅ AVAILABLE |
| Screenshot UI Progres ke-2 (9 file) | ❌ NOT YET CAPTURED — tindakan manual diperlukan |
| File yang tidak ditemukan | TIDAK ADA (semua file yang disebut tersedia, kecuali screenshot yang memang belum diambil) |

---

## G. Perintah Verifikasi Cepat

```powershell
# Masuk ke root proyek
cd D:\Kuliah\PROJECT\Web\AI-Computer-Diagnosis

# 1. Verifikasi unit test (harus 108 passed)
.venv\Scripts\python.exe -m pytest -q

# 2. Verifikasi validasi dataset
.venv\Scripts\python.exe -m evaluation.validate_dataset --baseline
.venv\Scripts\python.exe -m evaluation.validate_dataset --extended
.venv\Scripts\python.exe -m evaluation.validate_dataset --combined

# 3. Verifikasi evaluasi combined (harus: 200 kasus, coverage 68.50%, overall 84.50%)
.venv\Scripts\python.exe -m evaluation.run_evaluation_all --mode combined

# 4. Verifikasi angka kanonik
type evaluation\results\summary_metrics.csv

# 5. Verifikasi streamlit aktif
.venv\Scripts\python.exe -m streamlit run app.py
# Buka http://localhost:8501

# 6. Baca laporan utama dan panduan
type laporan\progres-2\LAPORAN_PROGRES_2.md
type PANDUAN_PENELUSURAN_HASIL.md
```

---

## Catatan Konsistensi

- Seluruh angka pada indeks ini cocok dengan `evaluation/results/summary_metrics.csv` dan log `01-log-eksekusi/`.
- Nilai `average_cost` UCS combined di CSV adalah `6.425`; log mencetak `6.42` (pembulatan).
- `false_positive` dan `false_negative` tetap ada di Knowledge Base dan evaluator, tetapi tidak ditampilkan di UI observasi (`app.py` → `EXCLUDED_UI_OUTCOMES`).
- Perubahan dokumen ini tidak mengubah kode, dataset, hasil evaluasi, atau konfigurasi aplikasi.
