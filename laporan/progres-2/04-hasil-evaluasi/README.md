HASIL EVALUASI — FOLDER RINGKASAN
==================================

Folder ini HANYA berisi ringkasan naratif Progres ke-2.
Hasil evaluasi kanonik (laporan JSON, CSV per kasus, ringkasan metrik,
dan grafik) tetap berada di:

    evaluation/results/

File di folder ini:

  - RINGKASAN_EVALUASI.md
      Ringkasan yang disusun dari:
        1. Log eksekusi aktual di `../01-log-eksekusi/evaluation-*.txt`
        2. `../../../evaluation/results/summary_metrics.csv`
        3. `../../../evaluation/results/{baseline,extended,combined}/summary_metrics.csv`

TIDAK ada evaluasi baru yang dijalankan di folder ini.
TIDAK ada angka yang dihitung ulang atau diubah.
TIDAK ada salinan JSON/CSV penuh yang dibuat ulang di sini, agar tidak
terjadi perbedaan dengan artefak asli.

====================================================================
LOKASI ARTEFAK KANONIK
====================================================================

Ringkasan metrik (combined, default):
  evaluation/results/summary_metrics.csv
  evaluation/results/combined/summary_metrics.csv

Ringkasan metrik per mode:
  evaluation/results/baseline/summary_metrics.csv
  evaluation/results/extended/summary_metrics.csv

Laporan lengkap:
  evaluation/results/evaluation_report.json
  evaluation/results/baseline/evaluation_report.json
  evaluation/results/extended/evaluation_report.json
  evaluation/results/combined/evaluation_report.json

CSV per kasus:
  evaluation/results/results_per_case.csv
  evaluation/results/baseline/results_per_case.csv
  evaluation/results/extended/results_per_case.csv
  evaluation/results/combined/results_per_case.csv

Grafik (Matplotlib):
  evaluation/results/chart_average_cost.png
  evaluation/results/chart_average_test_count.png
  evaluation/results/chart_outcomes.png
  evaluation/results/chart_cost_per_case.png
  evaluation/results/chart_cost_per_category.png

Log eksekusi teks Progres ke-2:
  laporan/progres-2/01-log-eksekusi/evaluation-baseline.txt
  laporan/progres-2/01-log-eksekusi/evaluation-extended.txt
  laporan/progres-2/01-log-eksekusi/evaluation-combined.txt

====================================================================
ATURAN
====================================================================

- Jika angka di ringkasan ini perlu dikoreksi, koreksi dari log/CSV
  kanonik, lalu perbarui ringkasan. Jangan mengubah CSV asli.
- Jangan menjalankan evaluate dengan output-dir ke folder ini; itu akan
  membuat duplikat artefak yang membingungkan.
- Navigasi lengkap: `../INDEX_BUKTI.md`
