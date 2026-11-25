RINGKASAN EVALUASI — KOMPARASI UCS VS CHECKLIST
=================================================

Dokumen ini meringkas performa algoritma **Uniform Cost Search (UCS)** dibandingkan dengan
**Fixed-Order Checklist** pada tiga dataset: Baseline, Extended, dan Combined.
Data bersumber dari `../../../evaluation/results/summary_metrics.csv`.

====================================================================
TABEL PERBANDINGAN PERFORMA
====================================================================

| Dataset | Kategori | Label Concl. | Label Inconcl. | Correct Concl. | Correct Inconcl. | Coverage | Overall Correct |
|---------|----------|--------------|----------------|----------------|------------------|----------|-----------------|
| Baseline| UCS      | 15           | 5              | 15             | 5                | 75.00%   | 100.00%         |
| Baseline| Checkl.  | 15           | 5              | 15             | 5                | 75.00%   | 100.00%         |
| Exten.  | UCS      | 93           | 87             | 92             | 57               | 67.78%   | 82.78%          |
| Exten.  | Checkl.  | 93           | 87             | 92             | 57               | 67.78%   | 82.78%          |
| Combined| UCS      | 108          | 92             | 107            | 62               | 68.50%   | 84.50%          |
| Combined| Checkl.  | 108          | 92             | 107            | 62               | 68.50%   | 84.50%          |

| Dataset | Kategori | Missed Concl. | False Pos. | Obs.-Limited | Avg Cost | Avg Test |
|---------|----------|---------------|------------|--------------|----------|----------|
| Baseline| UCS      | 0             | 0          | 0            | 2.80     | 1.25     |
| Baseline| Checkl.  | 0             | 0          | 0            | 2.90     | 1.30     |
| Exten.  | UCS      | 1             | 0          | 30           | 6.83     | 2.82     |
| Exten.  | Checkl.  | 1             | 0          | 30           | 6.69     | 2.68     |
| Combined| UCS      | 1             | 0          | 30           | 6.425    | 2.66     |
| Combined| Checkl.  | 1             | 0          | 30           | 6.31     | 2.54     |

====================================================================
ANALISIS HASIL
====================================================================

1. **Efektivitas Klasifikasi**:
   UCS dan Checklist menunjukkan hasil klasifikasi yang IDENTIK pada seluruh dataset.
   Ini mengindikasikan bahwa keterbatasan performa diagnosis (missed/inconclusive)
   disebabkan oleh desain basis pengetahuan, bukan pada strategi pemilihan tes.

2. **Efisiensi (Cost & Test Count)**:
   - Baseline: UCS lebih efisien (avg cost 2.80 vs 2.90).
   - Extended/Combined: Checklist lebih efisien (misalnya Combined avg cost 6.31 vs 6.425).
   Checklist menunjukkan overhead yang lebih kecil pada kasus-kasus yang lebih kompleks
   dan panjang dalam dataset extended.

3. **Keterbatasan Teramati**:
   - 30 kasus pada dataset extended/combined berakhir sebagai 'observation-limited_conclusive'.
     UCS berhenti lebih awal sebelum mencapai tes kontradiktif (memenuhi goal state
     dengan bukti yang ada). Ini efisien namun melewatkan bukti kontradiktif yang
     ada dalam daftar tes (tapi tidak diakses).
   - Akurasi 'among evaluable conclusive' konsisten di 100% pada semua dataset (keduanya).
   - False positive: 0 (sistem aman).

====================================================================
REFERENSI GRAFIK & CSV (LOKAL)
====================================================================

Bagan visual (Matplotlib):
- Grafik Cost rata-rata : `../../../evaluation/results/chart_average_cost.png`
- Grafik Test rata-rata : `../../../evaluation/results/chart_average_test_count.png`
- Grafik Outcome        : `../../../evaluation/results/chart_outcomes.png`
- Grafik Cost per Kasus : `../../../evaluation/results/chart_cost_per_case.png`

CSV Sumber:
- Kanonik Utama : `../../../evaluation/results/summary_metrics.csv`
- Log Baseline  : `../01-log-eksekusi/evaluation-baseline.txt`
- Log Extended  : `../01-log-eksekusi/evaluation-extended.txt`
- Log Combined  : `../01-log-eksekusi/evaluation-combined.txt`
