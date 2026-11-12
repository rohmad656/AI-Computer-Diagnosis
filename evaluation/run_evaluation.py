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

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from core.diagnosis import (
    apply_test_result,
    evaluate_diagnosis,
    get_available_tests,
    get_conflicting_categories,
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
    """Jalankan UCS untuk satu kasus menggunakan mesin diagnosis yang ada.

    Integritas evaluasi: fungsi ini hanya menerima gejala awal dan hasil tes
    yang benar-benar dipilih oleh UCS. ``expected_diagnosis`` dan
    ``expected_status`` tidak dibaca di sini. Mapping ``simulated_results``
    hanya diakses setelah UCS mengembalikan test berikutnya, sehingga hasil
    tes yang belum dieksekusi tidak pernah masuk ke ``DiagnosisState``.
    """
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
    if evaluation["status"] == "in_progress":
        raise ValueError(
            f"{case['case_id']}: UCS berhenti dalam status in_progress tanpa hasil final"
        )

    total_cost = sum(step["cost"] for step in route)
    if abs(total_cost - state.cumulative_cost) > 1e-9:
        raise ValueError(f"{case['case_id']}: perhitungan cost UCS tidak konsisten")

    contradicting = sorted(evaluation.get("contradicting_evidence", []))
    return {
        "route": route,
        "total_cost": total_cost,
        "test_count": len(route),
        "diagnosis": evaluation.get("diagnosed_category"),
        "status": evaluation["status"],
        "evidence_sufficiency": evaluation.get("evidence_sufficiency", "partial"),
        "supporting_evidence": sorted(evaluation.get("supporting_evidence", [])),
        "contradicting_evidence": contradicting,
        "trusted_support": sorted(evaluation.get("trusted_support", [])),
        "misleading_support": sorted(evaluation.get("misleading_support", [])),
        "neutral_evidence": sorted(evaluation.get("neutral_evidence", [])),
        "conflicting_categories": sorted(evaluation.get("conflicting_categories", [])),
        "possible_categories": sorted(evaluation.get("possible_categories", [])),
        "observed_contradiction": bool(contradicting),
    }


def checklist_result_to_dict(result: ChecklistResult) -> dict[str, Any]:
    """Konversi ChecklistResult ke struktur yang sama dengan hasil UCS."""
    total_cost = sum(step["cost"] for step in result.performed_tests)
    if abs(total_cost - result.total_cost) > 1e-9:
        raise ValueError(f"{result.case_id}: perhitungan cost checklist tidak konsisten")

    final_state = result.final_state
    contradicting = sorted(final_state.contradicting_evidence) if final_state else []
    return {
        "route": result.performed_tests,
        "total_cost": total_cost,
        "test_count": result.test_count,
        "diagnosis": result.diagnosis,
        "status": result.status,
        "evidence_sufficiency": result.evidence_sufficiency,
        "supporting_evidence": sorted(final_state.supporting_evidence) if final_state else [],
        "contradicting_evidence": contradicting,
        "trusted_support": sorted(final_state.trusted_support) if final_state else [],
        "misleading_support": sorted(final_state.misleading_support) if final_state else [],
        "neutral_evidence": sorted(final_state.neutral_evidence) if final_state else [],
        "conflicting_categories": (
            sorted(get_conflicting_categories(final_state)) if final_state else []
        ),
        "possible_categories": sorted(final_state.possible_categories) if final_state else [],
        "observed_contradiction": bool(contradicting),
    }


CORRECT_CONCLUSIVE = "correct_conclusive"
INCORRECT_CONCLUSIVE = "incorrect_conclusive"
CORRECT_INCONCLUSIVE = "correct_inconclusive"
MISSED_CONCLUSIVE = "missed_conclusive"
FALSE_POSITIVE = "false_positive"
OBSERVATION_LIMITED_CONCLUSIVE = "observation_limited_conclusive"

FINAL_OUTCOME_KEYS: tuple[str, ...] = (
    CORRECT_CONCLUSIVE,
    INCORRECT_CONCLUSIVE,
    CORRECT_INCONCLUSIVE,
    MISSED_CONCLUSIVE,
    FALSE_POSITIVE,
    OBSERVATION_LIMITED_CONCLUSIVE,
)

# Alias lama dipertahankan untuk kompatibilitas pembaca laporan sebelumnya.
LEGACY_OUTCOME_ALIASES: dict[str, str] = {
    CORRECT_CONCLUSIVE: "correct",
    INCORRECT_CONCLUSIVE: "wrong_diagnosis",
    MISSED_CONCLUSIVE: "false_negative",
}


def classify_outcome(
    actual_diagnosis: str | None,
    actual_status: str,
    expected_diagnosis: str | None,
    expected_status: str,
    observed_contradicting_evidence: list[str] | tuple[str, ...] = (),
    expected_contradicting_evidence: list[str] | tuple[str, ...] = (),
) -> str:
    """Klasifikasikan hasil akhir ke tepat satu bucket yang saling eksklusif.

    Bucket final:
    - ``correct_conclusive``: label konklusif, hasil konklusif, diagnosis sama.
    - ``incorrect_conclusive``: label konklusif, hasil konklusif, diagnosis beda.
    - ``correct_inconclusive``: label inkonklusif, hasil inkonklusif.
    - ``missed_conclusive``: label konklusif, hasil inkonklusif. Ini adalah
      kategori inkonklusif tersendiri, bukan "salah diagnosis". Metrik
      ``false_negative`` diturunkan dari bucket ini secara eksplisit.
    - ``false_positive``: label inkonklusif, hasil konklusif, dan sistem
      benar-benar mengamati bukti kontradiktif (atau label tidak menyimpan
      kontradiksi sama sekali sehingga konklusi tidak didukung label).
    - ``observation_limited_conclusive``: label inkonklusif, hasil konklusif,
      tetapi satu-satunya bukti kontradiktif berada pada tes yang tidak pernah
      dieksekusi UCS. Kasus ini tidak boleh dihitung sebagai false positive
      karena kontradiksi tersebut tidak pernah diamati sistem.
    """
    if expected_status == "conclusive":
        if actual_status != "conclusive":
            return MISSED_CONCLUSIVE
        if actual_diagnosis == expected_diagnosis:
            return CORRECT_CONCLUSIVE
        return INCORRECT_CONCLUSIVE

    # Label kasus inkonklusif.
    if actual_status != "conclusive":
        return CORRECT_INCONCLUSIVE

    if observed_contradicting_evidence:
        return FALSE_POSITIVE
    if expected_contradicting_evidence:
        return OBSERVATION_LIMITED_CONCLUSIVE
    # Label inkonklusif karena bukti tidak cukup, tetapi sistem menyimpulkan
    # tanpa kontradiksi yang tersimpan di label: tetap dianggap false positive.
    return FALSE_POSITIVE


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


def _ratio(numerator: float, denominator: float) -> float:
    """Bagi dengan aman; kembalikan 0.0 jika denominator nol."""
    return numerator / denominator if denominator else 0.0


def build_confusion_matrix(
    records: list[dict[str, Any]],
    method: str,
) -> dict[str, dict[str, int]]:
    """Confusion matrix multiclass: baris aktual, kolom label expected.

    Label ``inconclusive`` dipakai untuk expected_diagnosis=None dan untuk
    hasil aktual yang inkonklusif. Matriks ini membuat distribusi kesalahan
    empat kategori terlihat tanpa memaksakan definisi binary.
    """
    labels = [
        "driver_software",
        "overheating",
        "storage_disk",
        "ram_memory",
        "inconclusive",
    ]
    matrix = {row: {col: 0 for col in labels} for row in labels}
    for record in records:
        expected = record["expected_diagnosis"] or "inconclusive"
        actual = record[method]["diagnosis"] or "inconclusive"
        matrix[actual][expected] += 1
    return matrix


def summarize_method(
    records: list[dict[str, Any]],
    method: str,
) -> dict[str, Any]:
    """Hitung metrik ringkasan untuk satu metode.

    Setiap kasus masuk tepat satu bucket ``outcomes``. Metrik turunan
    (false_negative, false_positive, coverage, accuracy) dihitung dari bucket
    tersebut dengan denominator yang didokumentasikan pada laporan.
    """
    results = [record[method] for record in records]
    outcomes = {key: 0 for key in FINAL_OUTCOME_KEYS}
    for result in results:
        outcomes[result["outcome"]] += 1

    total_cases = len(results)
    if sum(outcomes.values()) != total_cases:
        raise ValueError(
            f"{method}: bucket hasil tidak saling eksklusif "
            f"({sum(outcomes.values())} != {total_cases})"
        )

    expected_conclusive = sum(
        1 for record in records if record["expected_status"] == "conclusive"
    )
    expected_inconclusive = total_cases - expected_conclusive
    actual_conclusive = sum(1 for result in results if result["status"] == "conclusive")
    actual_inconclusive = total_cases - actual_conclusive
    correct_total = outcomes[CORRECT_CONCLUSIVE] + outcomes[CORRECT_INCONCLUSIVE]

    expected_conclusive_costs = [
        result["total_cost"]
        for record, result in zip(records, results)
        if record["expected_status"] == "conclusive"
    ]
    actual_conclusive_costs = [
        result["total_cost"] for result in results if result["status"] == "conclusive"
    ]

    observed_conflict_records = [
        record for record in records if record[method]["contradicting_evidence"]
    ]
    observed_conflict_inconclusive = sum(
        1
        for record in observed_conflict_records
        if record[method]["status"] == "inconclusive"
    )
    expected_conflict_records = [
        record for record in records if record["expected_contradicting_evidence"]
    ]
    expected_conflict_inconclusive = sum(
        1
        for record in expected_conflict_records
        if record[method]["status"] == "inconclusive"
    )
    expected_conflict_unobserved = sum(
        1
        for record in expected_conflict_records
        if not record[method]["contradicting_evidence"]
    )
    evidence_consistent = sum(
        1 for record in records if record["evidence_consistent"][method]
    )

    evaluable_conclusive = (
        outcomes[CORRECT_CONCLUSIVE]
        + outcomes[INCORRECT_CONCLUSIVE]
        + outcomes[FALSE_POSITIVE]
    )
    evaluable_total = total_cases - outcomes[OBSERVATION_LIMITED_CONCLUSIVE]

    return {
        "cases_total": total_cases,
        "expected_conclusive_cases": expected_conclusive,
        "expected_inconclusive_cases": expected_inconclusive,
        "actual_conclusive_cases": actual_conclusive,
        "actual_inconclusive_cases": actual_inconclusive,
        "correct_conclusive": outcomes[CORRECT_CONCLUSIVE],
        "incorrect_conclusive": outcomes[INCORRECT_CONCLUSIVE],
        "correct_inconclusive": outcomes[CORRECT_INCONCLUSIVE],
        "missed_conclusive": outcomes[MISSED_CONCLUSIVE],
        "false_negative": outcomes[MISSED_CONCLUSIVE],
        "false_positive": outcomes[FALSE_POSITIVE],
        "observation_limited_conclusive": outcomes[OBSERVATION_LIMITED_CONCLUSIVE],
        "correct_total": correct_total,
        "coverage": _ratio(actual_conclusive, total_cases),
        "accuracy_among_conclusive_label": _ratio(
            outcomes[CORRECT_CONCLUSIVE], actual_conclusive
        ),
        "accuracy_among_evaluable_conclusive": _ratio(
            outcomes[CORRECT_CONCLUSIVE], evaluable_conclusive
        ),
        "overall_correct_rate": _ratio(correct_total, total_cases),
        "overall_correct_rate_evaluable": _ratio(correct_total, evaluable_total),
        "accuracy": _ratio(correct_total, total_cases),
        "false_negative_rate": _ratio(
            outcomes[MISSED_CONCLUSIVE], expected_conclusive
        ),
        "false_positive_rate": _ratio(
            outcomes[FALSE_POSITIVE], expected_inconclusive
        ),
        "average_cost": mean(result["total_cost"] for result in results)
        if results
        else 0.0,
        "average_conclusive_cost": mean(expected_conclusive_costs)
        if expected_conclusive_costs
        else 0.0,
        "average_expected_conclusive_cost": mean(expected_conclusive_costs)
        if expected_conclusive_costs
        else 0.0,
        "average_actual_conclusive_cost": mean(actual_conclusive_costs)
        if actual_conclusive_costs
        else 0.0,
        "average_test_count": mean(result["test_count"] for result in results)
        if results
        else 0.0,
        "observed_conflict_cases": len(observed_conflict_records),
        "observed_conflict_cases_inconclusive": observed_conflict_inconclusive,
        "expected_conflict_cases": len(expected_conflict_records),
        "expected_conflict_cases_inconclusive": expected_conflict_inconclusive,
        "expected_conflict_cases_unobserved": expected_conflict_unobserved,
        "evidence_consistent_cases": evidence_consistent,
        "outcomes": outcomes,
        "outcomes_legacy": {
            LEGACY_OUTCOME_ALIASES.get(key, key): value
            for key, value in outcomes.items()
        },
        "confusion_matrix": build_confusion_matrix(records, method),
    }


def write_per_case_csv(records: list[dict[str, Any]], path: Path) -> None:
    """Tulis tabel hasil per kasus ke CSV."""
    fieldnames = [
        "case_id",
        "category",
        "name",
        "expected_diagnosis",
        "expected_status",
        "expected_supporting_evidence",
        "expected_contradicting_evidence",
        "ucs_diagnosis",
        "ucs_status",
        "ucs_outcome",
        "ucs_test_count",
        "ucs_total_cost",
        "ucs_tests",
        "ucs_supporting_evidence",
        "ucs_contradicting_evidence",
        "ucs_trusted_support",
        "ucs_misleading_support",
        "ucs_observed_contradiction",
        "ucs_observation_limited",
        "checklist_diagnosis",
        "checklist_status",
        "checklist_outcome",
        "checklist_test_count",
        "checklist_total_cost",
        "checklist_tests",
        "checklist_supporting_evidence",
        "checklist_contradicting_evidence",
        "checklist_trusted_support",
        "checklist_misleading_support",
        "checklist_observed_contradiction",
        "checklist_observation_limited",
        "ucs_evidence_consistent",
        "checklist_evidence_consistent",
    ]

    def join(values: list[str] | tuple[str, ...]) -> str:
        return "|".join(values)

    def route_text(route: list[dict[str, Any]]) -> str:
        return "|".join(
            f"{step['test_id']}:{step['outcome']}" for step in route
        )

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
                    "expected_supporting_evidence": join(
                        record["expected_supporting_evidence"]
                    ),
                    "expected_contradicting_evidence": join(
                        record["expected_contradicting_evidence"]
                    ),
                    "ucs_diagnosis": record["ucs"]["diagnosis"] or "",
                    "ucs_status": record["ucs"]["status"],
                    "ucs_outcome": record["ucs"]["outcome"],
                    "ucs_test_count": record["ucs"]["test_count"],
                    "ucs_total_cost": record["ucs"]["total_cost"],
                    "ucs_tests": route_text(record["ucs"]["route"]),
                    "ucs_supporting_evidence": join(
                        record["ucs"]["supporting_evidence"]
                    ),
                    "ucs_contradicting_evidence": join(
                        record["ucs"]["contradicting_evidence"]
                    ),
                    "ucs_trusted_support": join(record["ucs"]["trusted_support"]),
                    "ucs_misleading_support": join(
                        record["ucs"]["misleading_support"]
                    ),
                    "ucs_observed_contradiction": record["ucs"][
                        "observed_contradiction"
                    ],
                    "ucs_observation_limited": (
                        record["ucs"]["outcome"]
                        == OBSERVATION_LIMITED_CONCLUSIVE
                    ),
                    "checklist_diagnosis": record["checklist"]["diagnosis"] or "",
                    "checklist_status": record["checklist"]["status"],
                    "checklist_outcome": record["checklist"]["outcome"],
                    "checklist_test_count": record["checklist"]["test_count"],
                    "checklist_total_cost": record["checklist"]["total_cost"],
                    "checklist_tests": route_text(record["checklist"]["route"]),
                    "checklist_supporting_evidence": join(
                        record["checklist"]["supporting_evidence"]
                    ),
                    "checklist_contradicting_evidence": join(
                        record["checklist"]["contradicting_evidence"]
                    ),
                    "checklist_trusted_support": join(
                        record["checklist"]["trusted_support"]
                    ),
                    "checklist_misleading_support": join(
                        record["checklist"]["misleading_support"]
                    ),
                    "checklist_observed_contradiction": record["checklist"][
                        "observed_contradiction"
                    ],
                    "checklist_observation_limited": (
                        record["checklist"]["outcome"]
                        == OBSERVATION_LIMITED_CONCLUSIVE
                    ),
                    "ucs_evidence_consistent": record["evidence_consistent"]["ucs"],
                    "checklist_evidence_consistent": record["evidence_consistent"][
                        "checklist"
                    ],
                }
            )


def write_summary_csv(summary: dict[str, Any], path: Path) -> None:
    """Tulis tabel ringkasan metrik ke CSV."""
    metrics = [
        ("cases_total", "Total kasus"),
        ("expected_conclusive_cases", "Kasus label konklusif"),
        ("expected_inconclusive_cases", "Kasus label inkonklusif"),
        ("actual_conclusive_cases", "Hasil aktual konklusif"),
        ("actual_inconclusive_cases", "Hasil aktual inkonklusif"),
        ("correct_conclusive", "Correct conclusive"),
        ("incorrect_conclusive", "Incorrect conclusive"),
        ("correct_inconclusive", "Correct inconclusive"),
        ("missed_conclusive", "Missed conclusive (inconclusive)"),
        ("false_negative", "False negative (diturunkan)"),
        ("false_positive", "False positive (bukti teramati)"),
        ("observation_limited_conclusive", "Observation-limited conclusive"),
        ("correct_total", "Total hasil sesuai label"),
        ("coverage", "Coverage / diagnosis completion rate"),
        ("accuracy_among_conclusive_label", "Accuracy among conclusive (label)"),
        (
            "accuracy_among_evaluable_conclusive",
            "Accuracy among evaluable conclusive",
        ),
        ("overall_correct_rate", "Overall correct rate"),
        ("overall_correct_rate_evaluable", "Overall correct rate (evaluable)"),
        ("accuracy", "Akurasi terhadap label (alias overall_correct_rate)"),
        ("false_negative_rate", "False negative rate"),
        ("false_positive_rate", "False positive rate"),
        ("average_cost", "Rata-rata total cost"),
        ("average_expected_conclusive_cost", "Rata-rata cost label konklusif"),
        ("average_actual_conclusive_cost", "Rata-rata cost hasil konklusif"),
        ("average_test_count", "Rata-rata jumlah pemeriksaan"),
        ("observed_conflict_cases", "Kasus dengan kontradiksi teramati"),
        (
            "observed_conflict_cases_inconclusive",
            "Kontradiksi teramati yang berakhir inkonklusif",
        ),
        ("expected_conflict_cases", "Kasus label dengan kontradiksi"),
        (
            "expected_conflict_cases_inconclusive",
            "Kasus label kontradiksi yang berakhir inkonklusif",
        ),
        (
            "expected_conflict_cases_unobserved",
            "Kasus label kontradiksi tanpa kontradiksi teramati",
        ),
        ("evidence_consistent_cases", "Kasus dengan bukti konsisten"),
    ]
    # Perbarui baris writer untuk mencocokkan field baru
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "label", "ucs", "checklist"])
        for key, label in metrics:
            ucs_val = summary["ucs"].get(key, 0)
            chk_val = summary["checklist"].get(key, 0)
            writer.writerow([key, label, ucs_val, chk_val])


def print_summary(summary: dict[str, Any], records: list[dict[str, Any]]) -> None:
    """Cetak ringkasan ke stdout."""
    print("\n=== RINGKASAN ===")
    for method_name in ("ucs", "checklist"):
        method = summary[method_name]
        print(f"\n{method_name.upper()}")
        print(f"  Total kasus                        : {method['cases_total']}")
        print(f"  Kasus label konklusif              : {method['expected_conclusive_cases']}")
        print(f"  Kasus label inkonklusif            : {method['expected_inconclusive_cases']}")
        print(f"  Hasil aktual konklusif             : {method['actual_conclusive_cases']}")
        print(f"  Hasil aktual inkonklusif           : {method['actual_inconclusive_cases']}")
        print(f"  Correct conclusive                 : {method['correct_conclusive']}")
        print(f"  Incorrect conclusive               : {method['incorrect_conclusive']}")
        print(f"  Correct inconclusive               : {method['correct_inconclusive']}")
        print(f"  Missed conclusive (inconclusive)   : {method['missed_conclusive']}")
        print(f"  False negative (diturunkan)        : {method['false_negative']}")
        print(f"  False positive (bukti teramati)    : {method['false_positive']}")
        print(
            f"  Observation-limited conclusive     : "
            f"{method['observation_limited_conclusive']}"
        )
        print(f"  Coverage                           : {method['coverage']:.2%}")
        print(
            f"  Accuracy among conclusive (label)  : "
            f"{method['accuracy_among_conclusive_label']:.2%}"
        )
        print(
            f"  Accuracy among evaluable conclusive: "
            f"{method['accuracy_among_evaluable_conclusive']:.2%}"
        )
        print(f"  Overall correct rate               : {method['overall_correct_rate']:.2%}")
        print(
            f"  Overall correct rate (evaluable)   : "
            f"{method['overall_correct_rate_evaluable']:.2%}"
        )
        print(f"  Rata-rata total cost               : {method['average_cost']:.2f}")
        print(f"  Rata-rata jumlah tes               : {method['average_test_count']:.2f}")
        print(
            f"  Kontradiksi teramati               : "
            f"{method['observed_conflict_cases_inconclusive']}/"
            f"{method['observed_conflict_cases']} berakhir inkonklusif"
        )
        print(
            f"  Label kontradiksi                  : "
            f"{method['expected_conflict_cases_inconclusive']}/"
            f"{method['expected_conflict_cases']} berakhir inkonklusif "
            f"({method['expected_conflict_cases_unobserved']} kontradiksi tidak teramati)"
        )
        print(
            f"  Bukti konsisten                    : "
            f"{method['evidence_consistent_cases']}/{method['cases_total']}"
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


def run_evaluation(
    cases: list[dict[str, Any]],
    dataset_name: str,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Jalankan evaluasi untuk sekumpulan kasus dan simpan laporan.

    Args:
        cases: Daftar kasus dengan schema baseline.
        dataset_name: Nama dataset untuk metadata laporan.
        output_dir: Direktori keluaran JSON/CSV.

    Returns:
        Report dictionary yang juga ditulis ke disk.
    """
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
            ucs["contradicting_evidence"],
            case["expected_contradicting_evidence"],
        )
        checklist["outcome"] = classify_outcome(
            checklist["diagnosis"],
            checklist["status"],
            case["expected_diagnosis"],
            case["expected_status"],
            checklist["contradicting_evidence"],
            case["expected_contradicting_evidence"],
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
            "dataset": dataset_name,
            "note": (
                "Hasil hanya berlaku untuk skenario simulasi yang disiapkan. "
                "Tidak mengklaim akurasi terhadap kerusakan komputer nyata."
            ),
        },
        "summary": summary,
        "cases": records,
    }

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "evaluation_report.json"
    per_case_path = output_path / "results_per_case.csv"
    summary_path = output_path / "summary_metrics.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
    write_per_case_csv(records, per_case_path)
    write_summary_csv(summary, summary_path)

    print_summary(summary, records)
    print(f"\nHasil JSON : {json_path}")
    print(f"Hasil CSV  : {per_case_path}")
    print(f"Ringkasan  : {summary_path}")
    return report


def main() -> None:
    """Jalankan seluruh eksperimen dengan argparse standar."""
    parser = argparse.ArgumentParser(
        description=(
            "Evaluasi komparatif UCS vs Fixed-Order Checklist pada dataset "
            "simulasi diagnosis komputer."
        )
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATASET_PATH,
        help=f"Path dataset evaluasi (default: {DATASET_PATH})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RESULTS_DIR,
        help=f"Direktori keluaran JSON/CSV (default: {RESULTS_DIR})",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    dataset = load_evaluation_dataset(dataset_path)
    cases = dataset["test_cases"]
    run_evaluation(cases, dataset_path.name, args.output_dir)


if __name__ == "__main__":
    main()