"""Membuat visualisasi hasil evaluasi UCS vs Fixed-Order Checklist.

Semua nilai dibaca dari evaluation/results/evaluation_report.json yang
dihasilkan oleh run_evaluation.py. Tidak ada angka yang ditulis manual.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
REPORT_PATH = RESULTS_DIR / "evaluation_report.json"

COLORS = {
    "ucs": "#2563eb",
    "checklist": "#059669",
    "grid": "#e5e7eb",
    "text": "#1f2937",
}


def load_report(path: Path = REPORT_PATH) -> dict[str, Any]:
    """Muat laporan evaluasi JSON."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def style_axes(ax: plt.Axes, title: str, ylabel: str) -> None:
    """Terapkan gaya konsisten pada grafik."""
    ax.set_title(title, fontsize=13, fontweight="bold", color=COLORS["text"], pad=12)
    ax.set_ylabel(ylabel, color=COLORS["text"])
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(colors=COLORS["text"])


def annotate_bars(ax: plt.Axes, bars: Any, fmt: str = "{:.2f}") -> None:
    """Tambahkan nilai di atas setiap batang."""
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            fmt.format(height),
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            color=COLORS["text"],
        )


def plot_average_cost(report: dict[str, Any], output: Path) -> None:
    """Grafik perbandingan rata-rata total cost."""
    summary = report["summary"]
    labels = ["UCS", "Checklist"]
    values = [summary["ucs"]["average_cost"], summary["checklist"]["average_cost"]]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(labels, values, color=[COLORS["ucs"], COLORS["checklist"]], width=0.5)
    annotate_bars(ax, bars)
    style_axes(ax, "Rata-rata Total Cost per Kasus", "Total cost")
    ax.set_ylim(0, max(values) * 1.25 if max(values) else 1)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_average_test_count(report: dict[str, Any], output: Path) -> None:
    """Grafik perbandingan rata-rata jumlah pemeriksaan."""
    summary = report["summary"]
    labels = ["UCS", "Checklist"]
    values = [
        summary["ucs"]["average_test_count"],
        summary["checklist"]["average_test_count"],
    ]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(labels, values, color=[COLORS["ucs"], COLORS["checklist"]], width=0.5)
    annotate_bars(ax, bars, fmt="{:.2f}")
    style_axes(ax, "Rata-rata Jumlah Pemeriksaan per Kasus", "Jumlah pemeriksaan")
    ax.set_ylim(0, max(values) * 1.3 if max(values) else 1)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_outcomes(report: dict[str, Any], output: Path) -> None:
    """Grafik jumlah hasil diagnosis per metode."""
    ucs = report["summary"]["ucs"]["outcomes"]
    checklist = report["summary"]["checklist"]["outcomes"]
    categories = [
        ("correct", "Benar"),
        ("correct_inconclusive", "Inkonklusif\nsesuai label"),
        ("wrong_diagnosis", "Salah\ndiagnosis"),
        ("false_negative", "False\nnegative"),
        ("false_positive", "False\npositive"),
    ]

    labels = [label for _, label in categories]
    ucs_values = [ucs[key] for key, _ in categories]
    checklist_values = [checklist[key] for key, _ in categories]

    x = range(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9, 4.8))
    bars_ucs = ax.bar(
        [i - width / 2 for i in x],
        ucs_values,
        width,
        label="UCS",
        color=COLORS["ucs"],
    )
    bars_checklist = ax.bar(
        [i + width / 2 for i in x],
        checklist_values,
        width,
        label="Checklist",
        color=COLORS["checklist"],
    )
    annotate_bars(ax, bars_ucs, fmt="{:.0f}")
    annotate_bars(ax, bars_checklist, fmt="{:.0f}")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    style_axes(ax, "Hasil Diagnosis per Metode", "Jumlah kasus")
    ax.set_ylim(0, max(ucs_values + checklist_values) * 1.3 or 1)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_cost_per_case(report: dict[str, Any], output: Path) -> None:
    """Grafik total cost setiap kasus untuk kedua metode."""
    cases = report["cases"]
    labels = [case["case_id"].replace("eval_", "") for case in cases]
    ucs_values = [case["ucs"]["total_cost"] for case in cases]
    checklist_values = [case["checklist"]["total_cost"] for case in cases]

    x = range(len(labels))
    width = 0.4

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar([i - width / 2 for i in x], ucs_values, width, label="UCS", color=COLORS["ucs"])
    ax.bar(
        [i + width / 2 for i in x],
        checklist_values,
        width,
        label="Checklist",
        color=COLORS["checklist"],
    )
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=8)
    style_axes(ax, "Total Cost per Kasus", "Total cost")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_cost_per_category(report: dict[str, Any], output: Path) -> None:
    """Grafik rata-rata cost per kategori untuk kedua metode."""
    categories: dict[str, dict[str, list[float]]] = {}
    for case in report["cases"]:
        category = case["category"]
        categories.setdefault(category, {"ucs": [], "checklist": []})
        categories[category]["ucs"].append(case["ucs"]["total_cost"])
        categories[category]["checklist"].append(case["checklist"]["total_cost"])

    labels = list(categories.keys())
    ucs_values = [
        sum(categories[c]["ucs"]) / len(categories[c]["ucs"]) for c in labels
    ]
    checklist_values = [
        sum(categories[c]["checklist"]) / len(categories[c]["checklist"])
        for c in labels
    ]

    x = range(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9, 4.8))
    bars_ucs = ax.bar(
        [i - width / 2 for i in x], ucs_values, width, label="UCS", color=COLORS["ucs"]
    )
    bars_checklist = ax.bar(
        [i + width / 2 for i in x],
        checklist_values,
        width,
        label="Checklist",
        color=COLORS["checklist"],
    )
    annotate_bars(ax, bars_ucs, fmt="{:.2f}")
    annotate_bars(ax, bars_checklist, fmt="{:.2f}")
    ax.set_xticks(list(x))
    ax.set_xticklabels([label.replace("_", " ") for label in labels], fontsize=9)
    style_axes(ax, "Rata-rata Cost per Kategori", "Total cost")
    ax.set_ylim(0, max(ucs_values + checklist_values) * 1.3 or 1)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main() -> None:
    """Buat seluruh grafik."""
    report = load_report()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    outputs = {
        "average_cost": RESULTS_DIR / "chart_average_cost.png",
        "average_test_count": RESULTS_DIR / "chart_average_test_count.png",
        "outcomes": RESULTS_DIR / "chart_outcomes.png",
        "cost_per_case": RESULTS_DIR / "chart_cost_per_case.png",
        "cost_per_category": RESULTS_DIR / "chart_cost_per_category.png",
    }

    plot_average_cost(report, outputs["average_cost"])
    plot_average_test_count(report, outputs["average_test_count"])
    plot_outcomes(report, outputs["outcomes"])
    plot_cost_per_case(report, outputs["cost_per_case"])
    plot_cost_per_category(report, outputs["cost_per_category"])

    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()