"""Unified evaluation runner for baseline, extended, and combined datasets.

Usage (from project root):

    python -m evaluation.run_evaluation_all                 # combined 200 cases
    python -m evaluation.run_evaluation_all --mode baseline  # 20 baseline cases
    python -m evaluation.run_evaluation_all --mode extended  # 180 extended cases
    python -m evaluation.run_evaluation_all --mode combined --output-dir evaluation/results
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluation.run_evaluation import run_evaluation

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = PROJECT_ROOT / "evaluation" / "evaluation_dataset.json"
EXTENDED_PATH = PROJECT_ROOT / "data" / "extended_dataset.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "evaluation" / "results"


def load_baseline(path: Path = BASELINE_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data["test_cases"]


def normalise_extended_case(case: dict[str, Any]) -> dict[str, Any]:
    """Map extended-dataset fields onto the baseline schema."""
    return {
        "case_id": case["id"],
        "category": case["primary_category"],
        "name": case.get("name", f"Extended case {case['id']}"),
        "initial_symptoms": case["initial_symptoms"],
        "simulated_results": case["simulated_test_results"],
        "expected_supporting_evidence": case["expected_supporting_evidence"],
        "expected_contradicting_evidence": case["expected_contradicting_evidence"],
        "expected_diagnosis": case["expected_diagnosis"],
        "expected_status": case["expected_status"],
    }


def load_extended(path: Path = EXTENDED_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    return [normalise_extended_case(case) for case in data["cases"]]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Jalankan evaluasi UCS vs Fixed-Order Checklist pada baseline, extended, atau gabungan."
    )
    parser.add_argument(
        "--mode",
        choices=("baseline", "extended", "combined"),
        default="combined",
        help="Dataset yang dievaluasi (default: combined).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Direktori keluaran. Default: evaluation/results untuk combined, subfolder untuk baseline/extended.",
    )
    args = parser.parse_args()

    baseline = load_baseline()
    extended = load_extended()

    if args.mode == "baseline":
        cases = baseline
        dataset_name = BASELINE_PATH.name
        default_dir = DEFAULT_OUTPUT_DIR / "baseline"
    elif args.mode == "extended":
        cases = extended
        dataset_name = EXTENDED_PATH.name
        default_dir = DEFAULT_OUTPUT_DIR / "extended"
    else:
        cases = baseline + extended
        dataset_name = "baseline+extended (200 kasus)"
        default_dir = DEFAULT_OUTPUT_DIR

    output_dir = args.output_dir if args.output_dir is not None else default_dir

    if args.mode == "combined" and len(cases) != 200:
        raise ValueError(
            f"Mode combined harus memuat tepat 200 kasus, ditemukan {len(cases)}"
        )

    print(f"Mode: {args.mode}")
    print(f"Kasus: {len(cases)}")
    run_evaluation(cases, dataset_name, output_dir)


if __name__ == "__main__":
    main()
