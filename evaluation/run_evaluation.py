"""Menjalankan perbandingan eksperimental UCS vs Fixed-Order Checklist.

Skrip ini:
1. Memuat dataset evaluasi 20 kasus simulasi.
2. Memvalidasi kelengkapan dataset terhadap Knowledge Base.
3. Menjalankan UCS melalui core.diagnosis.
4. Menjalankan Fixed-Order Checklist melalui evaluation.checklist.
5. Menghitung metrik perbandingan.
6. Menyimpan hasil ke JSON dan CSV.

Tidak ada hasil yang ditulis manual. Seluruh angka dihitung dari eksekusi.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from core.diagnosis import (
    apply_test_result,
    evaluate_diagnosis,
    get_available_tests,
    get_next_recommended_test,
    initialize_diagnosis,
    is_goal_state,
)
from core.knowledge_base import get_categories, get_test_by_id
from evaluation.checklist import ChecklistResult, run_checklist_all_cases

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DATASET_PATH = Path(__file__).resolve().parent / "evaluation_dataset.json"


def load_evaluation_dataset(path: str | Path = DATASET_PATH) -> dict[str, Any]:
    """Muat dataset evaluasi dari JSON."""
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def validate_dataset(cases: list[dict[str, Any]]) -> None:
    """Validasi konsistensi dataset terhadap Knowledge Base.

    Memastikan:
    - case_id unik.
    - gejala awal valid.
    - seluruh pemeriksaan yang relevan memiliki hasil simulasi.
    - outcome valid untuk pemeriksaan terkait.
    - expected diagnosis merujuk kategori yang ada.

    Raises:
        ValueError: Jika dataset tidak lengkap atau tidak konsisten.
    """
    issues: list[str] = []
    seen_ids: set[str] = set()
    valid_categories = {category["id"] for category in get_categories()}
    required_keys = {
        "case_id",
        "category",
        "name",
        "initial_symptoms",
        "simulated_results",
        "expected_supporting_evidence",
        "expected_contradicting_evidence",
        "expected_diagnosis",
        "expected_status",
    }

    for index, case in enumerate(cases):
        case_id = case.get("case_id", f"index_{index}")
        missing_keys = required_keys - set(case)
        if missing_keys:
            issues.append(f"{case_id}: kunci hilang: {sorted(missing_keys)}")
            continue

        if case_id in seen_ids:
            issues.append(f"{case_id}: case_id duplikat")
        seen_ids.add(case_id)

        if case["expected_status"] not in {"conclusive", "inconclusive"}:
            issues.append(f"{case_id}: expected_status tidak valid")
        if (
            case["expected_diagnosis"] is not None
            and case["expected_diagnosis"] not in valid_categories
        ):
            issues.append(f"{case_id}: expected_diagnosis tidak dikenal")

        try:
            state = initialize_diagnosis(case["initial_symptoms"])
        except Exception as exc:  # noqa: BLE001 - dikumpulkan sebagai issue dataset
            issues.append(f"{case_id}: gejala awal tidak valid: {exc}")
            continue

        available_ids = {test["id"] for test in get_available_tests(state)}
        result_ids = set(case["simulated_results"])
        missing_results = available_ids - result_ids
        if missing_results:
            issues.append(
                f"{case_id}: hasil pemeriksaan belum lengkap untuk {sorted(missing_results)}"
            )

        for test_id, outcome in case["simulated_results"].items():
            test = get_test_by_id(test_id)
            if test is None:
                issues.append(f"{case_id}: test tidak dikenal: {test_id}")
            elif outcome not in test["possible_outcomes"]:
                issues.append(
                    f"{case_id}: outcome '{outcome}' tidak valid untuk '{test_id}'"
                )

    if issues:
        raise ValueError("Dataset evaluasi tidak valid:\n- " + "\n- ".join(issues))


def run_ucs_for_case(case: dict[str, Any]) -> dict[str, Any]:
    """Jalankan UCS untuk satu kasus menggunakan mesin diagnosis yang ada."""
    state = initialize_diagnosis(case["initial_symptoms"])
    simulated_results = case["simulated_results"]
    route: list[dict[str, Any]] = []

    while True:
        next_test = get_next_recommended_test(state)
        if next_test is None:
            break

        test_id = next_test["id"]
        if test_id not in simulated_results:
            raise ValueError(
                f"{case['case_id']}: UCS meminta '{test_id}' tetapi hasilnya tidak tersedia"
            )

        outcome = simulated_results[test_id]
        state = apply_test_result(state, test_id, outcome)
        route.append(
            {
                "step": len(route) + 1,
                "test_id": test_id,
                "test_name": next_test["name"],
                "outcome": outcome,
                "cost": next_test["cost"],
                "cumulative_cost": state.cumulative_cost,
            }
        )

        if is_goal_state(state):
            break

    evaluation = evaluate_diagnosis(state)
    total_cost = sum(step["cost"] for step in route)
    if abs(total_cost - state.cumulative_cost) > 1e-9:
        raise ValueError(f"{case['case_id']}: perhitungan cost UCS tidak konsisten")

    return {
        "route": route,
        "total_cost": total_cost,
        "test_count": len(route),
        "diagnosis": evaluation.get("diagnosed_category"),
        "status": evaluation["status"],
        "evidence_sufficiency": evaluation.get("evidence_sufficiency", "partial"),
        "supporting_evidence": sorted(evaluation.get("supporting_evidence", [])),
        "contradicting_evidence": sorted(evaluation.get("contradicting_evidence", [])),
    }


def checklist_result_to_dict(result: ChecklistResult) -> dict[str, Any]:
    """Konversi ChecklistResult ke struktur yang sama dengan hasil UCS."""
    total_cost = sum(step["cost"] for step in result.performed_tests)
    if abs(total_cost - result.total_cost) > 1e-9:
        raise ValueError(f"{result.case_id}: perhitungan cost checklist tidak konsisten")

    return {
        "route": result.performed_tests,
        "total_cost": total_cost,
        "test_count": result.test_count,
        "diagnosis": result.diagnosis,
        "status": result.status,
        "evidence_sufficiency": result.evidence_sufficiency,
        "supporting_evidence": sorted(result.final_state.supporting_evidence) if result.final_state else [],
        "contradicting_evidence": sorted(result.final_state.contradicting_evidence) if result.final_state else [],
    }


def classify_outcome(
    actual_diagnosis: str | None,
    actual_status: str,
    expected_diagnosis: str | None,
    expected_status: str,
) -> str:
    """Klasifikasikan hasil terhadap label kasus.

    Returns:
        correct, correct_inconclusive, wrong_diagnosis, false_negative, atau
        false_positive.
    """
    if expected_status == "conclusive":
        if actual_status == "conclusive" and actual_diagnosis == expected_diagnosis:
            return "correct"
        if actual_status == "inconclusive":
            return "false_negative"
        return "wrong_diagnosis"

    if actual_status == "inconclusive":
        return "correct_inconclusive"
    return "false_positive"


def evidence_is_consistent(
    actual_supporting: list[str],
    actual_contradicting: list[str],
    expected_supporting: list[str],
    expected_contradicting: list[str],
) -> bool:
    """Periksa apakah bukti aktual konsisten dengan label kasus.

    Bukti pendukung harus sama persis. Bukti bertentangan boleh berupa subset
    karena metode dapat berhenti sebelum semua pemeriksaan dijalankan.
    """
    if set(actual_supporting) != set(expected_supporting):
        return False
    return set(actual_contradicting).issubset(set(expected_contradicting))


def summarize_method(
    records: list[dict[str, Any]],
    method: str,
) -> dict[str, Any]:
    """Hitung metrik ringkasan untuk satu metode."""
    results = [record[method] for record in records]
    outcomes = {
        "correct": 0,
        "correct_inconclusive": 0,
        "wrong_diagnosis": 0,
        "false_negative": 0,
        "false_positive": 0,
    }
    for result in results:
        outcomes[result["outcome"]] += 1

    total_cases = len(results)
    correct_total = outcomes["correct"] + outcomes["correct_inconclusive"]
    actual_inconclusive = sum(1 for result in results if result["status"] == "inconclusive")

    conclusive_costs = [
        result["total_cost"]
        for record, result in zip(records, results)
        if record["expected_status"] == "conclusive"
    ]
    conflict_records = [
        record for record in records if record["expected_contradicting_evidence"]
    ]
    conflict_correct = sum(
        1
        for record in conflict_records
        if record[method]["outcome"] in {"correct", "correct_inconclusive"}
    )
    evidence_consistent = sum(
        1 for record in records if record["evidence_consistent"][method]
    )

    return {
        "cases_total": total_cases,
        "correct_conclusive": outcomes["correct"],
        "correct_inconclusive": outcomes["correct_inconclusive"],
        "correct_total": correct_total,
        "accuracy": correct_total / total_cases if total_cases else 0.0,
        "wrong_diagnosis": outcomes["wrong_diagnosis"],
        "false_negative": outcomes["false_negative"],
        "false_positive": outcomes["false_positive"],
        "actual_inconclusive": actual_inconclusive,
        "average_cost": mean(result["total_cost"] for result in results) if results else 0.0,
        "average_conclusive_cost": mean(conclusive_costs) if conclusive_costs else 0.0,
        "average_test_count": mean(result["test_count"] for result in results) if results else 0.0,
        "conflict_cases": len(conflict_records),
        "conflict_cases_correct": conflict_correct,
        "evidence_consistent_cases": evidence_consistent,
        "outcomes": outcomes,
    }


def write_per_case_csv(records: list[dict[str, Any]], path: Path) -> None:
    """Tulis tabel hasil per kasus ke CSV."""
    fieldnames = [
        "case_id",
        "category",
        "name",
        "expected_diagnosis",
        "expected_status",
        "ucs_diagnosis",
        "ucs_status",
        "ucs_outcome",
        "ucs_test_count",
        "ucs_total_cost",
        "checklist_diagnosis",
        "checklist_status",
        "checklist_outcome",
        "checklist_test_count",
        "checklist_total_cost",
        "ucs_evidence_consistent",
        "checklist_evidence_consistent",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "case_id": record["case_id"],
                    "category": record["category"],
                    "name": record["name"],
                    "expected_diagnosis": record["expected_diagnosis"] or "",
                    "expected_status": record["expected_status"],
                    "ucs_diagnosis": record["ucs"]["diagnosis"] or "",
                    "ucs_status": record["ucs"]["status"],
                    "ucs_outcome": record["ucs"]["outcome"],
                    "ucs_test_count": record["ucs"]["test_count"],
                    "ucs_total_cost": record["ucs"]["total_cost"],
                    "checklist_diagnosis": record["checklist"]["diagnosis"] or "",
                    "checklist_status": record["checklist"]["status"],
                    "checklist_outcome": record["checklist"]["outcome"],
                    "checklist_test_count": record["checklist"]["test_count"],
                    "checklist_total_cost": record["checklist"]["total_cost"],
                    "ucs_evidence_consistent": record["evidence_consistent"]["ucs"],
                    "checklist_evidence_consistent": record["evidence_consistent"]["checklist"],
                }
            )


def write_summary_csv(summary: dict[str, Any], path: Path) -> None:
    """Tulis tabel ringkasan metrik ke CSV."""
    metrics = [
        ("cases_total", "Jumlah kasus"),
        ("correct_conclusive", "Diagnosis konklusif benar"),
        ("correct_inconclusive", "Inkonklusif sesuai label"),
        ("correct_total", "Total hasil sesuai label"),
        ("accuracy", "Akurasi terhadap label"),
        ("wrong_diagnosis", "Diagnosis salah"),
        ("false_negative", "False negative"),
        ("false_positive", "False positive"),
        ("actual_inconclusive", "Hasil inkonklusif"),
        ("average_cost", "Rata-rata total cost"),
        ("average_conclusive_cost", "Rata-rata cost kasus konklusif"),
        ("average_test_count", "Rata-rata jumlah pemeriksaan"),
        ("conflict_cases", "Kasus dengan bukti bertentangan"),
        ("conflict_cases_correct", "Kasus bertentangan yang benar"),
        ("evidence_consistent_cases", "Kasus dengan bukti konsisten"),
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "label", "ucs", "checklist"])
        for key, label in metrics:
            writer.writerow([key, label, summary["ucs"][key], summary["checklist"][key]])


def print_summary(summary: dict[str, Any], records: list[dict[str, Any]]) -> None:
    """Cetak ringkasan ke stdout."""
    print("\n=== RINGKASAN ===")
    for method_name in ("ucs", "checklist"):
        method = summary[method_name]
        print(f"\n{method_name.upper()}")
        print(f"  Total kasus              : {method['cases_total']}")
        print(f"  Diagnosis benar          : {method['correct_conclusive']}")
        print(f"  Inkonklusif sesuai label : {method['correct_inconclusive']}")
        print(f"  Salah diagnosis          : {method['wrong_diagnosis']}")
        print(f"  False negative           : {method['false_negative']}")
        print(f"  False positive           : {method['false_positive']}")
        print(f"  Akurasi terhadap label   : {method['accuracy']:.2%}")
        print(f"  Rata-rata total cost     : {method['average_cost']:.2f}")
        print(f"  Rata-rata jumlah tes     : {method['average_test_count']:.2f}")
        print(
            f"  Kasus bukti bertentangan : {method['conflict_cases_correct']}/"
            f"{method['conflict_cases']} benar"
        )
        print(
            f"  Bukti konsisten          : {method['evidence_consistent_cases']}/"
            f"{method['cases_total']}"
        )

    print("\n=== HASIL PER KASUS ===")
    header = (
        f"{'Case ID':<14} {'Kategori':<16} {'Expected':<24} "
        f"{'UCS':<20} {'Checklist':<20} {'Cost U':>7} {'Cost C':>7}"
    )
    print(header)
    print("-" * len(header))
    for record in records:
        expected = f"{record['expected_diagnosis'] or '-'}/{record['expected_status']}"
        ucs = f"{record['ucs']['diagnosis'] or '-'}/{record['ucs']['status']}/{record['ucs']['outcome']}"
        checklist = (
            f"{record['checklist']['diagnosis'] or '-'}/"
            f"{record['checklist']['status']}/{record['checklist']['outcome']}"
        )
        print(
            f"{record['case_id']:<14} {record['category']:<16} {expected:<24} "
            f"{ucs:<20} {checklist:<20} "
            f"{record['ucs']['total_cost']:>7.1f} {record['checklist']['total_cost']:>7.1f}"
        )


def main() -> None:
    """Jalankan seluruh eksperimen."""
    dataset = load_evaluation_dataset()
    cases = dataset["test_cases"]
    validate_dataset(cases)

    print(f"Dataset valid: {len(cases)} kasus.")
    print("Menjalankan UCS...")
    ucs_results = [run_ucs_for_case(case) for case in cases]

    print("Menjalankan Fixed-Order Checklist...")
    checklist_raw = run_checklist_all_cases(cases)
    checklist_results = [
        checklist_result_to_dict(result) for result in checklist_raw
    ]

    records: list[dict[str, Any]] = []
    for case, ucs, checklist in zip(cases, ucs_results, checklist_results):
        ucs["outcome"] = classify_outcome(
            ucs["diagnosis"],
            ucs["status"],
            case["expected_diagnosis"],
            case["expected_status"],
        )
        checklist["outcome"] = classify_outcome(
            checklist["diagnosis"],
            checklist["status"],
            case["expected_diagnosis"],
            case["expected_status"],
        )

        records.append(
            {
                "case_id": case["case_id"],
                "category": case["category"],
                "name": case["name"],
                "expected_diagnosis": case["expected_diagnosis"],
                "expected_status": case["expected_status"],
                "expected_supporting_evidence": case["expected_supporting_evidence"],
                "expected_contradicting_evidence": case["expected_contradicting_evidence"],
                "ucs": ucs,
                "checklist": checklist,
                "evidence_consistent": {
                    "ucs": evidence_is_consistent(
                        ucs["supporting_evidence"],
                        ucs["contradicting_evidence"],
                        case["expected_supporting_evidence"],
                        case["expected_contradicting_evidence"],
                    ),
                    "checklist": evidence_is_consistent(
                        checklist["supporting_evidence"],
                        checklist["contradicting_evidence"],
                        case["expected_supporting_evidence"],
                        case["expected_contradicting_evidence"],
                    ),
                },
            }
        )

    summary = {
        "ucs": summarize_method(records, "ucs"),
        "checklist": summarize_method(records, "checklist"),
    }

    category_distribution: dict[str, int] = {}
    status_distribution = {"conclusive": 0, "inconclusive": 0}
    for case in cases:
        category_distribution[case["category"]] = (
            category_distribution.get(case["category"], 0) + 1
        )
        status_distribution[case["expected_status"]] += 1

    report = {
        "metadata": {
            "total_cases": len(cases),
            "category_distribution": category_distribution,
            "expected_status_distribution": status_distribution,
            "dataset": str(DATASET_PATH.name),
            "note": (
                "Hasil hanya berlaku untuk skenario simulasi yang disiapkan. "
                "Tidak mengklaim akurasi terhadap kerusakan komputer nyata."
            ),
        },
        "summary": summary,
        "cases": records,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS_DIR / "evaluation_report.json"
    per_case_path = RESULTS_DIR / "results_per_case.csv"
    summary_path = RESULTS_DIR / "summary_metrics.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
    write_per_case_csv(records, per_case_path)
    write_summary_csv(summary, summary_path)

    print_summary(summary, records)
    print(f"\nHasil JSON : {json_path}")
    print(f"Hasil CSV  : {per_case_path}")
    print(f"Ringkasan  : {summary_path}")


if __name__ == "__main__":
    main()