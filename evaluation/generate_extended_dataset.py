"""Deterministic generator for the 180-case extended evaluation dataset.

All cases are **expert_curated** simulations built from the project knowledge base.
They are NOT real-world incidents and do not claim to be.

Run:
    .\\.venv\\Scripts\\python.exe -m evaluation.generate_extended_dataset

Output:
    data/extended_dataset.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "extended_dataset.json"

# ---------------------------------------------------------------------------
# Knowledge-base derived constants (kept in sync with data/*.json)
# ---------------------------------------------------------------------------

CATEGORY_ORDER = ("driver_software", "overheating", "storage_disk", "ram_memory")

REQUIRED_EVIDENCE = {
    "driver_software": "driver_issue_confirmed",
    "overheating": "high_temperature_confirmed",
    "storage_disk": "disk_issue_confirmed",
    "ram_memory": "memory_issue_confirmed",
}

# Cheapest supporting test per category.
SUPPORT_TEST = {
    "driver_software": ("test_driver_status", "yellow_bang"),
    "overheating": ("test_cpu_gpu_temp", "elevated"),
    "storage_disk": ("test_smart_disk", "warning"),
    "ram_memory": ("test_memory_diagnostic", "errors_found"),
}

# Second test that can contradict the same category (where available).
CONTRA_TEST = {
    "driver_software": ("test_error_code_history", "no_driver_errors"),
    "storage_disk": ("test_disk_system_error_logs", "no_errors"),
    "ram_memory": ("test_ram_usage_snapshot", "false_negative"),
}

# Symptom pools per category. Ambiguous symptoms appear in more than one pool
# on purpose, matching data/symptoms.json.
SYMPTOMS = {
    "driver_software": [
        ["sym_bsod_driver"],
        ["sym_device_manager_yellow"],
        ["sym_bsod_generic"],
        ["sym_disk_error"],
        ["sym_system_crash"],
    ],
    "overheating": [
        ["sym_shutdown_thermal"],
        ["sym_fan_loud_hot"],
        ["sym_system_crash"],
        ["sym_performance_degradation"],
    ],
    "storage_disk": [
        ["sym_disk_slow_freeze"],
        ["sym_chkdsk_auto"],
        ["sym_disk_error"],
        ["sym_bsod_generic"],
        ["sym_performance_degradation"],
    ],
    "ram_memory": [
        ["sym_app_crash_random"],
        ["sym_bsod_memory_management"],
        ["sym_bsod_generic"],
        ["sym_performance_degradation"],
    ],
}

# Pairings used for cross-category cases.
SECONDARY_SYMPTOM = {
    "driver_software": "sym_disk_slow_freeze",
    "overheating": "sym_bsod_driver",
    "storage_disk": "sym_bsod_driver",
    "ram_memory": "sym_bsod_driver",
}

ID_CODES = {
    "driver_software": "DRV",
    "overheating": "OH",
    "storage_disk": "STG",
    "ram_memory": "RAM",
}

CASE_TYPE_QUOTA = {
    "simple": 9,
    "cross_category": 14,
    "uncertain": 14,
    "contradictory": 8,
}


def _load_kb() -> tuple[dict[str, list[str]], dict[str, dict[str, Any]]]:
    symptoms_data = json.loads((DATA_DIR / "symptoms.json").read_text(encoding="utf-8"))
    tests_data = json.loads((DATA_DIR / "diagnostic_tests.json").read_text(encoding="utf-8"))

    symptom_categories = {
        s["id"]: list(s["related_categories"]) for s in symptoms_data["symptoms"]
    }
    test_map = {t["id"]: t for t in tests_data["tests"]}
    return symptom_categories, test_map


SYMPTOM_CATEGORIES, TEST_MAP = _load_kb()


def _possible_categories(symptoms: list[str]) -> set[str]:
    cats: set[str] = set()
    for sid in symptoms:
        cats.update(SYMPTOM_CATEGORIES.get(sid, []))
    return cats or set(CATEGORY_ORDER)


def _build_simulation(symptoms: list[str], overrides: dict[str, str]) -> dict[str, str]:
    """Fill every relevant test with an explicit outcome.

    Tests not listed in ``overrides`` receive the neutral ``inconclusive``
    outcome, which is part of every test definition.
    """
    possible = _possible_categories(symptoms)
    simulation: dict[str, str] = {}
    for test_id, test in TEST_MAP.items():
        if test["category"] not in possible:
            continue
        outcome = overrides.get(test_id, "inconclusive")
        if outcome not in test["possible_outcomes"]:
            raise ValueError(f"Outcome '{outcome}' invalid for {test_id}")
        simulation[test_id] = outcome
    return simulation


def _make_case(
    *,
    case_id: str,
    primary_category: str,
    symptoms: list[str],
    overrides: dict[str, str],
    expected_supporting: list[str],
    expected_contradicting: list[str],
    expected_diagnosis: str | None,
    expected_status: str,
    case_type: str,
    rationale: str,
) -> dict[str, Any]:
    return {
        "id": case_id,
        "primary_category": primary_category,
        "name": f"Extended {primary_category} — {case_type}",
        "initial_symptoms": symptoms,
        "simulated_test_results": _build_simulation(symptoms, overrides),
        "expected_supporting_evidence": expected_supporting,
        "expected_contradicting_evidence": expected_contradicting,
        "expected_diagnosis": expected_diagnosis,
        "expected_status": expected_status,
        "case_type": case_type,
        "development": True,
        "source_type": "expert_curated",
        "rationale": rationale,
    }


def _simple_case(primary: str, index: int) -> dict[str, Any]:
    symptom_pool = SYMPTOMS[primary]
    symptoms = symptom_pool[index % len(symptom_pool)]
    support_test, support_outcome = SUPPORT_TEST[primary]
    overrides = {support_test: support_outcome}
    required = REQUIRED_EVIDENCE[primary]
    return _make_case(
        case_id=f"EXT_{ID_CODES[primary]}_{index + 1:03d}",
        primary_category=primary,
        symptoms=symptoms,
        overrides=overrides,
        expected_supporting=[required],
        expected_contradicting=[],
        expected_diagnosis=primary,
        expected_status="conclusive",
        case_type="simple",
        rationale=(
            f"Kasus sederhana: gejala {symptoms} relevan dengan {primary}; "
            f"hasil {support_test}={support_outcome} mendukung {required}. "
            "Tes lain dibuat inconclusive agar tidak menambah evidence."
        ),
    )


def _cross_category_case(primary: str, index: int) -> dict[str, Any]:
    primary_sym = SYMPTOMS[primary][index % len(SYMPTOMS[primary])]
    secondary = SECONDARY_SYMPTOM[primary]
    # Avoid duplicate symptom IDs.
    symptoms = list(dict.fromkeys(primary_sym + [secondary]))
    support_test, support_outcome = SUPPORT_TEST[primary]
    overrides = {support_test: support_outcome}
    required = REQUIRED_EVIDENCE[primary]
    return _make_case(
        case_id=f"EXT_{ID_CODES[primary]}_{10 + index:03d}",
        primary_category=primary,
        symptoms=symptoms,
        overrides=overrides,
        expected_supporting=[required],
        expected_contradicting=[],
        expected_diagnosis=primary,
        expected_status="conclusive",
        case_type="cross_category",
        rationale=(
            f"Kasus lintas kategori: gejala mencakup {primary} dan kategori lain; "
            f"hasil {support_test}={support_outcome} hanya mengonfirmasi {primary}. "
            "Tes kategori lain tetap inconclusive sehingga tidak menambah evidence."
        ),
    )


def _uncertain_case(primary: str, index: int) -> dict[str, Any]:
    primary_sym = SYMPTOMS[primary][index % len(SYMPTOMS[primary])]
    secondary = SECONDARY_SYMPTOM[primary]
    symptoms = list(dict.fromkeys(primary_sym + [secondary]))
    return _make_case(
        case_id=f"EXT_{ID_CODES[primary]}_{24 + index:03d}",
        primary_category=primary,
        symptoms=symptoms,
        overrides={},  # all relevant tests -> inconclusive
        expected_supporting=[],
        expected_contradicting=[],
        expected_diagnosis=None,
        expected_status="inconclusive",
        case_type="uncertain",
        rationale=(
            "Kasus uncertain: seluruh pemeriksaan relevan menghasilkan outcome "
            "inconclusive (netral), sehingga tidak ada evidence yang cukup untuk "
            "diagnosis konklusif."
        ),
    )


def _contradictory_case(primary: str, index: int) -> dict[str, Any]:
    if primary == "overheating":
        # Overheating only has one test, so create a cross-category conflict.
        symptoms = ["sym_system_crash", "sym_shutdown_thermal"]
        overrides = {
            "test_cpu_gpu_temp": "elevated",
            "test_driver_status": "yellow_bang",
            "test_error_code_history": "no_driver_errors",
        }
        return _make_case(
            case_id=f"EXT_{ID_CODES[primary]}_{38 + index:03d}",
            primary_category=primary,
            symptoms=symptoms,
            overrides=overrides,
            expected_supporting=["high_temperature_confirmed", "driver_issue_confirmed"],
            expected_contradicting=["driver_issue_confirmed"],
            expected_diagnosis=None,
            expected_status="inconclusive",
            case_type="contradictory",
            rationale=(
                "Kasus kontradiktif lintas kategori: suhu mendukung overheating, "
                "tetapi status driver dan riwayat error saling bertentangan "
                "(driver_issue_confirmed didukung sekaligus ditolak)."
            ),
        )

    support_test, support_outcome = SUPPORT_TEST[primary]
    contra_test, contra_outcome = CONTRA_TEST[primary]
    symptoms = SYMPTOMS[primary][index % len(SYMPTOMS[primary])]
    # Add an ambiguous symptom so tests remain available after category elimination.
    if primary == "ram_memory":
        symptoms = ["sym_bsod_generic", "sym_app_crash_random"]
    else:
        symptoms = list(dict.fromkeys(symptoms + ["sym_bsod_generic"]))
    overrides = {
        support_test: support_outcome,
        contra_test: contra_outcome,
    }
    required = REQUIRED_EVIDENCE[primary]
    return _make_case(
        case_id=f"EXT_{ID_CODES[primary]}_{38 + index:03d}",
        primary_category=primary,
        symptoms=symptoms,
        overrides=overrides,
        expected_supporting=[required],
        expected_contradicting=[required],
        expected_diagnosis=None,
        expected_status="inconclusive",
        case_type="contradictory",
        rationale=(
            f"Kasus kontradiktif: {support_test}={support_outcome} mendukung "
            f"{required}, sedangkan {contra_test}={contra_outcome} menolak evidence "
            "yang sama. State harus dikenali sebagai conflicting."
        ),
    )


def _misleading_cases() -> list[dict[str, Any]]:
    """Two explicit misleading cases required by the robustness phase.

    Outcome ``misleading`` tetap mengikuti evidence_mapping eksplisit pada
    knowledge base (tidak membalik seluruh evidence secara otomatis).
    """
    false_positive = _make_case(
        case_id="EXT_DRV_045",
        primary_category="driver_software",
        symptoms=["sym_device_manager_yellow"],
        overrides={
            "test_driver_status": "false_positive",
            "test_error_code_history": "inconclusive",
        },
        expected_supporting=["driver_issue_confirmed"],
        expected_contradicting=[],
        expected_diagnosis="driver_software",
        expected_status="conclusive",
        case_type="misleading",
        rationale=(
            "Kasus misleading false-positive: test_driver_status salah "
            "melaporkan masalah driver. Mapping eksplisit memperlakukan "
            "false_positive sebagai pendukung driver_issue_confirmed, sehingga "
            "UCS menyimpulkan driver_software. Sistem tidak dapat mendeteksi "
            "kebohongan tes; ini keterbatasan yang harus dilaporkan, bukan "
            "diubah labelnya agar akurasi naik."
        ),
    )
    false_negative = _make_case(
        case_id="EXT_RAM_045",
        primary_category="ram_memory",
        symptoms=["sym_app_crash_random"],
        overrides={
            "test_memory_diagnostic": "false_negative",
            "test_ram_usage_snapshot": "inconclusive",
        },
        expected_supporting=[],
        expected_contradicting=["memory_issue_confirmed"],
        expected_diagnosis=None,
        expected_status="inconclusive",
        case_type="misleading",
        rationale=(
            "Kasus misleading false-negative: test_memory_diagnostic salah "
            "melaporkan normal sehingga menolak memory_issue_confirmed. "
            "Sistem mengeliminasi ram_memory dan berhenti inconclusive; "
            "kerusakan RAM tidak terdeteksi (risiko false-negative nyata)."
        ),
    )
    return [false_positive, false_negative]


def generate() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    for primary in CATEGORY_ORDER:
        for i in range(CASE_TYPE_QUOTA["simple"]):
            cases.append(_simple_case(primary, i))
        for i in range(CASE_TYPE_QUOTA["cross_category"]):
            cases.append(_cross_category_case(primary, i))
        for i in range(CASE_TYPE_QUOTA["uncertain"]):
            cases.append(_uncertain_case(primary, i))
        for i in range(CASE_TYPE_QUOTA["contradictory"]):
            cases.append(_contradictory_case(primary, i))

    # Replace the last contradictory case of driver and RAM with the two
    # required misleading cases, keeping the total at 180.
    misleading = _misleading_cases()
    cases = [c for c in cases if c["id"] not in {m["id"] for m in misleading}]
    cases.extend(misleading)

    # Sanity checks before writing.
    assert len(cases) == 180, len(cases)
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), "Duplicate case IDs"

    category_counts = {cat: 0 for cat in CATEGORY_ORDER}
    case_type_counts: dict[str, int] = {}
    for c in cases:
        category_counts[c["primary_category"]] += 1
        case_type_counts[c["case_type"]] = case_type_counts.get(c["case_type"], 0) + 1

    return {
        "schema_version": 1,
        "description": (
            "Dataset pengembangan 180 kasus simulasi. Seluruh kasus berlabel "
            "development:true dan source_type:expert_curated. Tidak ada klaim "
            "bahwa kasus ini merupakan insiden nyata."
        ),
        "methodology_note": (
            "Kasus disusun secara deterministik dari aturan knowledge base "
            "(expert_curated). Distribusi outcome tidak diklaim sebagai "
            "distribusi statistik kejadian nyata."
        ),
        "category_distribution": category_counts,
        "case_type_distribution": case_type_counts,
        "cases": cases,
    }


def main() -> None:
    dataset = generate()
    OUTPUT_PATH.write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Cases: {len(dataset['cases'])}")
    print(f"Category distribution: {dataset['category_distribution']}")
    print(f"Case type distribution: {dataset['case_type_distribution']}")


if __name__ == "__main__":
    main()
