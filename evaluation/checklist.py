"""Fixed-Order Troubleshooting Checklist untuk evaluasi perbandingan.

Checklist ini menggunakan urutan pemeriksaan tetap yang ditetapkan sebelum
pengujian. Urutan yang sama digunakan untuk semua kasus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.diagnosis import (
    DiagnosisState,
    apply_test_result,
    evaluate_diagnosis,
    get_available_tests,
    get_evidence_sufficiency,
    initialize_diagnosis,
)
from core.knowledge_base import get_category_by_id, get_test_by_id, load_diagnostic_tests


# Urutan checklist tetap (tetap untuk semua kasus).
# Urutan ini dirancang berdasarkan pendekatan troubleshooting umum:
# 1. Pemeriksaan termudah/termurah (cost rendah)
# 2. Pemeriksaan umum (suhu, driver status)
# 3. Pemeriksaan yang memerlukan restart (memory)
# 4. Pemeriksaan mendalam (SMART, error logs)

CHECKLIST_ORDER = [
    # Cost 1: Cek suhu - paling cepat dan non-invasif
    "test_cpu_gpu_temp",
    # Cost 2: Cek status driver - umum untuk BSOD
    "test_driver_status",
    # Cost 2: Cek SMART disk - non-invasif untuk storage
    "test_smart_disk",
    # Cost 3: Cek log error disk/sistem
    "test_disk_system_error_logs",
    # Cost 3: Cek riwayat kode error
    "test_error_code_history",
    # Cost 5: Tes memori - paling mahal (restart)
    "test_memory_diagnostic",
]


@dataclass
class ChecklistResult:
    """Hasil eksekusi checklist untuk satu kasus."""
    case_id: str
    performed_tests: list[dict[str, Any]] = field(default_factory=list)
    total_cost: float = 0.0
    test_count: int = 0
    diagnosis: str | None = None
    status: str = "inconclusive"
    evidence_sufficiency: str = "partial"
    final_state: DiagnosisState | None = None


def run_checklist_for_case(
    case: dict[str, Any],
    verbose: bool = False,
) -> ChecklistResult:
    """Jalankan checklist tetap untuk satu kasus evaluasi.

    Args:
        case: Dictionary kasus evaluasi dari evaluation_dataset.json.
        verbose: Jika True, cetak log detail.

    Returns:
        ChecklistResult berisi hasil lengkap.
    """
    initial_symptoms = case["initial_symptoms"]
    simulated_results = case["simulated_results"]

    state = initialize_diagnosis(initial_symptoms)
    performed = []
    total_cost = 0.0

    # Tentukan urutan test yang relevan dengan kategori yang mungkin
    # Checklist tetap memeriksa semua test dalam urutan, tapi hanya
    # menjalankan test yang relevan dengan kategori yang masih mungkin
    # DAN yang hasilnya tersedia di simulated_results.

    for test_id in CHECKLIST_ORDER:
        test = get_test_by_id(test_id)
        if test is None:
            continue

        # Hanya lakukan test jika:
        # 1. Test relevan dengan kategori yang masih mungkin
        # 2. Hasil simulasi tersedia untuk test ini
        if test["category"] not in state.possible_categories:
            continue

        if test_id not in simulated_results:
            continue

        outcome = simulated_results[test_id]

        try:
            state = apply_test_result(state, test_id, outcome)
        except Exception:
            # Jika test tidak bisa diterapkan (mis. sudah dilakukan), skip
            continue

        total_cost += test["cost"]
        performed.append({
            "test_id": test_id,
            "test_name": test["name"],
            "outcome": outcome,
            "cost": test["cost"],
            "cumulative_cost": state.cumulative_cost,
            "step": len(performed) + 1,
        })

        if verbose:
            print(f"  Step {len(performed)}: {test['name']} = {outcome} (cost {test['cost']}, cumulative {state.cumulative_cost})")

        # Cek apakah diagnosis sudah konklusif
        eval_result = evaluate_diagnosis(state)
        if eval_result["status"] == "conclusive":
            if verbose:
                print(f"  -> Diagnosis konklusif: {eval_result['category_name']}")
            break
        elif eval_result["status"] == "inconclusive":
            if verbose:
                print(f"  -> Inconclusive, tidak ada test relevan tersisa")
            break
        # Jika in_progress, lanjut ke test berikutnya

    # Evaluasi akhir. Checklist bersifat fixed-order: jika seluruh urutan
    # selesai tanpa konfirmasi, hasilnya inkonklusif, bukan in_progress.
    final_eval = evaluate_diagnosis(state)
    final_status = final_eval["status"]
    if final_status == "in_progress":
        final_status = "inconclusive"
    result = ChecklistResult(
        case_id=case["case_id"],
        performed_tests=performed,
        total_cost=total_cost,
        test_count=len(performed),
        diagnosis=final_eval.get("diagnosed_category"),
        status=final_status,
        evidence_sufficiency=final_eval.get("evidence_sufficiency", "partial"),
        final_state=state,
    )

    return result


def run_checklist_all_cases(
    cases: list[dict[str, Any]],
    verbose: bool = False,
) -> list[ChecklistResult]:
    """Jalankan checklist untuk semua kasus evaluasi."""
    results = []
    for case in cases:
        if verbose:
            print(f"\n=== Kasus: {case['case_id']} ({case['name']}) ===")
        result = run_checklist_for_case(case, verbose=verbose)
        results.append(result)
    return results


def compare_with_expected(
    result: ChecklistResult,
    case: dict[str, Any],
) -> dict[str, Any]:
    """Bandingkan hasil checklist dengan expected diagnosis kasus."""
    expected_diagnosis = case["expected_diagnosis"]
    expected_status = case["expected_status"]

    # Cek diagnosis benar
    diagnosis_correct = (result.diagnosis == expected_diagnosis)

    # Cek status sesuai (conclusive/inconclusive)
    status_correct = (result.status == expected_status)

    # Tentukan kategori hasil
    if expected_status == "conclusive":
        if diagnosis_correct and status_correct:
            outcome = "correct"
        elif result.status == "inconclusive":
            outcome = "false_negative"  # Seharusnya konklusif tapi inconclusive
        else:
            outcome = "wrong_diagnosis"  # Diagnosis salah
    else:  # expected inconclusive
        if result.status == "inconclusive":
            outcome = "correct_inconclusive"
        else:
            outcome = "false_positive"  # Seharusnya inconclusive tapi konklusif

    return {
        "case_id": case["case_id"],
        "expected_diagnosis": expected_diagnosis,
        "expected_status": expected_status,
        "actual_diagnosis": result.diagnosis,
        "actual_status": result.status,
        "outcome": outcome,
        "test_count": result.test_count,
        "total_cost": result.total_cost,
    }


if __name__ == "__main__":
    # Quick test
    import json
    from pathlib import Path

    dataset_path = Path(__file__).resolve().parent.parent / "evaluation" / "evaluation_dataset.json"
    with dataset_path.open(encoding="utf-8") as f:
        dataset = json.load(f)

    cases = dataset["test_cases"]
    results = run_checklist_all_cases(cases, verbose=True)

    for result, case in zip(results, cases):
        comparison = compare_with_expected(result, case)
        print(f"\n{case['case_id']}: {comparison['outcome']} | "
              f"expected={comparison['expected_diagnosis']}/{comparison['expected_status']} "
              f"actual={comparison['actual_diagnosis']}/{comparison['actual_status']} | "
              f"tests={comparison['test_count']} cost={comparison['total_cost']}")