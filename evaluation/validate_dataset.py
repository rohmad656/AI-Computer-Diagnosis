"""Validasi dataset evaluasi dan extended dataset.

Skrip ini memvalidasi:
1. JSON dapat dibaca.
2. ID kasus unik.
3. Schema kasus lengkap.
4. Kategori utama valid.
5. Gejala yang digunakan terdaftar.
6. Tes dan outcome yang digunakan terdaftar.
7. Evidence mapping valid.
8. Status conclusive/inconclusive konsisten dengan expected diagnosis.
9. Metadata source_type valid.
10. documentation_based mempunyai source_reference.
11. development bernilai true pada seluruh kasus extended.
12. Tidak ada referensi ID yang rusak.
13. Jumlah kasus sesuai target.
14. Komposisi tipe kasus sesuai rancangan.

Jalankan:
    python -m evaluation.validate_dataset
    python -m evaluation.validate_dataset --baseline
    python -m evaluation.validate_dataset --extended
    python -m evaluation.validate_dataset --combined
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = PROJECT_ROOT / "evaluation" / "evaluation_dataset.json"
EXTENDED_PATH = PROJECT_ROOT / "data" / "extended_dataset.json"
DATA_DIR = PROJECT_ROOT / "data"

VALID_CATEGORIES = {"driver_software", "overheating", "storage_disk", "ram_memory"}
VALID_SOURCE_TYPES = {"documentation_based", "expert_curated", "real_world_incident"}
VALID_CASE_TYPES = {"simple", "cross_category", "uncertain", "contradictory", "misleading"}
VALID_STATUSES = {"conclusive", "inconclusive"}

# Ambil data knowledge base langsung dari JSON (tidak melalui loader agar portable)
def _load_kb_json(filename: str) -> dict[str, Any]:
    path = DATA_DIR / filename
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _build_kb_index() -> dict[str, Any]:
    symptoms_data = _load_kb_json("symptoms.json")
    tests_data = _load_kb_json("diagnostic_tests.json")

    symptom_ids = {s["id"] for s in symptoms_data["symptoms"]}
    # Gejala map: id → related_categories
    symptom_cats: dict[str, list[str]] = {
        s["id"]: s["related_categories"] for s in symptoms_data["symptoms"]
    }
    # Test map: id → {possible_outcomes, evidence_mapping}
    test_map: dict[str, dict[str, Any]] = {
        t["id"]: t for t in tests_data["tests"]
    }
    return {
        "symptom_ids": symptom_ids,
        "symptom_cats": symptom_cats,
        "test_map": test_map,
    }


def _resolve_possible_categories(symptom_ids_list: list[str], symptom_cats: dict[str, list[str]]) -> set[str]:
    cats: set[str] = set()
    for sid in symptom_ids_list:
        cats.update(symptom_cats.get(sid, []))
    if not cats:
        cats = set(VALID_CATEGORIES)
    return cats


def _get_required_tests(possible_cats: set[str], test_map: dict[str, dict[str, Any]]) -> set[str]:
    return {t_id for t_id, t in test_map.items() if t["category"] in possible_cats}


def _get_evidence_from_simulated(simulated: dict[str, str], test_map: dict[str, dict[str, Any]]) -> tuple[set[str], set[str]]:
    supports: set[str] = set()
    contradicts: set[str] = set()
    for t_id, outcome in simulated.items():
        t = test_map.get(t_id)
        if t is None:
            continue
        mapping = t["evidence_mapping"].get(outcome, {})
        # uncertain outcome: check outcome_types
        otype = t.get("outcome_types", {}).get(outcome, "abnormal")
        if otype == "uncertain":
            continue  # neutral, no evidence
        supports.update(mapping.get("supports", []))
        contradicts.update(mapping.get("contradicts", []))
    return supports, contradicts


CATEGORY_REQUIRED_EVIDENCE = {
    "driver_software": "driver_issue_confirmed",
    "overheating": "high_temperature_confirmed",
    "storage_disk": "disk_issue_confirmed",
    "ram_memory": "memory_issue_confirmed",
}


class ValidationReport:
    def __init__(self, dataset_name: str) -> None:
        self.dataset_name = dataset_name
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.case_count = 0
        self.category_counts: dict[str, int] = {}
        self.case_type_counts: dict[str, int] = {}

    def error(self, case_id: str, msg: str) -> None:
        self.errors.append(f"[ERROR] {case_id}: {msg}")

    def warn(self, case_id: str, msg: str) -> None:
        self.warnings.append(f"[WARN]  {case_id}: {msg}")

    def print_report(self) -> None:
        print(f"\n{'='*60}")
        print(f"Validasi Dataset: {self.dataset_name}")
        print(f"{'='*60}")
        print(f"Jumlah kasus: {self.case_count}")
        print(f"\nDistribusi kategori:")
        for cat, cnt in sorted(self.category_counts.items()):
            print(f"  {cat}: {cnt}")
        if self.case_type_counts:
            print(f"\nDistribusi tipe kasus:")
            for ctype, cnt in sorted(self.case_type_counts.items()):
                print(f"  {ctype}: {cnt}")

        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  {w}")
        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(f"  {e}")
        else:
            print(f"\nOK: Tidak ada error. Dataset valid.")

    def is_valid(self) -> bool:
        return len(self.errors) == 0


def _validate_baseline_case(
    case: dict[str, Any],
    idx: int,
    seen_ids: set[str],
    kb: dict[str, Any],
    report: ValidationReport,
) -> None:
    """Validasi satu kasus dari baseline dataset (schema berbeda)."""
    required_keys = {
        "case_id", "category", "name", "initial_symptoms",
        "simulated_results", "expected_supporting_evidence",
        "expected_contradicting_evidence", "expected_diagnosis", "expected_status",
    }
    case_id = case.get("case_id", f"baseline[{idx}]")
    missing = required_keys - set(case.keys())
    if missing:
        report.error(case_id, f"kunci wajib hilang: {sorted(missing)}")
        return

    if case_id in seen_ids:
        report.error(case_id, "ID duplikat")
    seen_ids.add(case_id)

    # expected_status
    if case["expected_status"] not in VALID_STATUSES:
        report.error(case_id, f"expected_status tidak valid: '{case['expected_status']}'")

    # expected_diagnosis
    if case["expected_status"] == "conclusive":
        if case["expected_diagnosis"] is None:
            report.error(case_id, "expected_status=conclusive tetapi expected_diagnosis=null")
        elif case["expected_diagnosis"] not in VALID_CATEGORIES:
            report.error(case_id, f"expected_diagnosis '{case['expected_diagnosis']}' tidak valid")
    else:
        if case["expected_diagnosis"] is not None:
            report.error(case_id, "expected_status=inconclusive tetapi expected_diagnosis tidak null")

    # Gejala awal
    for sid in case["initial_symptoms"]:
        if sid not in kb["symptom_ids"]:
            report.error(case_id, f"gejala tidak dikenal: '{sid}'")

    # simulated_results: test id dan outcome
    for t_id, outcome in case["simulated_results"].items():
        t = kb["test_map"].get(t_id)
        if t is None:
            report.error(case_id, f"test tidak dikenal: '{t_id}'")
        elif outcome not in t["possible_outcomes"]:
            report.error(case_id, f"outcome '{outcome}' tidak valid untuk test '{t_id}'")

    # Kelengkapan simulated_results
    possible_cats = _resolve_possible_categories(case["initial_symptoms"], kb["symptom_cats"])
    required_tests = _get_required_tests(possible_cats, kb["test_map"])
    missing_tests = required_tests - set(case["simulated_results"].keys())
    if missing_tests:
        report.error(case_id, f"simulated_results belum lengkap untuk: {sorted(missing_tests)}")

    # Tes RAM snapshot hanya relevan jika kategori RAM masih mungkin.
    if (
        "test_ram_usage_snapshot" in case["simulated_results"]
        and "ram_memory" not in possible_cats
    ):
        report.warn(
            case_id,
            "test_ram_usage_snapshot dipakai padahal kategori ram_memory "
            "tidak relevan dengan gejala awal",
        )

    # kategori (baseline boleh memakai 'mixed' sebagai label skenario lintas kategori)
    cat = case["category"]
    if cat not in VALID_CATEGORIES and cat != "mixed":
        report.error(case_id, f"category tidak valid: '{cat}'")
    report.category_counts[cat] = report.category_counts.get(cat, 0) + 1


def _validate_extended_case(
    case: dict[str, Any],
    idx: int,
    seen_ids: set[str],
    kb: dict[str, Any],
    report: ValidationReport,
) -> None:
    """Validasi satu kasus dari extended dataset."""
    required_keys = {
        "id", "primary_category", "initial_symptoms",
        "simulated_test_results", "expected_supporting_evidence",
        "expected_contradicting_evidence", "expected_diagnosis", "expected_status",
        "case_type", "development", "source_type", "rationale",
    }
    case_id = case.get("id", f"extended[{idx}]")
    missing = required_keys - set(case.keys())
    if missing:
        report.error(case_id, f"kunci wajib hilang: {sorted(missing)}")
        return

    if case_id in seen_ids:
        report.error(case_id, "ID duplikat")
    seen_ids.add(case_id)

    # development flag
    if case.get("development") is not True:
        report.error(case_id, "field 'development' harus bernilai true")

    # primary_category
    if case["primary_category"] not in VALID_CATEGORIES:
        report.error(case_id, f"primary_category tidak valid: '{case['primary_category']}'")

    # case_type
    if case["case_type"] not in VALID_CASE_TYPES:
        report.warn(case_id, f"case_type tidak dikenal: '{case['case_type']}'")

    # source_type
    if case["source_type"] not in VALID_SOURCE_TYPES:
        report.error(case_id, f"source_type tidak valid: '{case['source_type']}'")
    if case["source_type"] == "documentation_based":
        if not case.get("source_reference"):
            report.error(case_id, "source_type=documentation_based tapi source_reference kosong")
    if case["source_type"] == "real_world_incident":
        if not case.get("source_reference"):
            report.error(case_id, "source_type=real_world_incident tapi source_reference kosong")

    # expected_status
    if case["expected_status"] not in VALID_STATUSES:
        report.error(case_id, f"expected_status tidak valid: '{case['expected_status']}'")

    # expected_diagnosis konsistensi
    if case["expected_status"] == "conclusive":
        if case["expected_diagnosis"] is None:
            report.error(case_id, "expected_status=conclusive tetapi expected_diagnosis=null")
        elif case["expected_diagnosis"] not in VALID_CATEGORIES:
            report.error(case_id, f"expected_diagnosis '{case['expected_diagnosis']}' tidak valid")
    else:
        if case["expected_diagnosis"] is not None:
            report.error(case_id, "expected_status=inconclusive tetapi expected_diagnosis tidak null")

    # Gejala awal
    for sid in case["initial_symptoms"]:
        if sid not in kb["symptom_ids"]:
            report.error(case_id, f"gejala tidak dikenal: '{sid}'")

    # simulated_test_results: test id dan outcome
    sim = case.get("simulated_test_results", {})
    for t_id, outcome in sim.items():
        t = kb["test_map"].get(t_id)
        if t is None:
            report.error(case_id, f"test tidak dikenal: '{t_id}'")
        elif outcome not in t["possible_outcomes"]:
            report.error(case_id, f"outcome '{outcome}' tidak valid untuk test '{t_id}'")

    # Kelengkapan simulated_test_results
    possible_cats = _resolve_possible_categories(case["initial_symptoms"], kb["symptom_cats"])
    required_tests = _get_required_tests(possible_cats, kb["test_map"])
    missing_tests = required_tests - set(sim.keys())
    if missing_tests:
        report.error(case_id, f"simulated_test_results belum lengkap untuk: {sorted(missing_tests)}")

    # Tes RAM snapshot hanya relevan jika kategori RAM masih mungkin.
    if "test_ram_usage_snapshot" in sim and "ram_memory" not in possible_cats:
        report.warn(
            case_id,
            "test_ram_usage_snapshot dipakai padahal kategori ram_memory "
            "tidak relevan dengan gejala awal",
        )

    # Validasi evidence konsistensi
    actual_sup, actual_con = _get_evidence_from_simulated(sim, kb["test_map"])
    exp_sup = set(case.get("expected_supporting_evidence", []))
    exp_con = set(case.get("expected_contradicting_evidence", []))

    if actual_sup != exp_sup:
        report.warn(
            case_id,
            f"expected_supporting_evidence tidak match dengan simulated. "
            f"Expected: {sorted(exp_sup)}, Actual dari sim: {sorted(actual_sup)}"
        )
    if not exp_con.issubset(actual_con):
        report.warn(
            case_id,
            f"expected_contradicting_evidence tidak subset dari actual. "
            f"Expected: {sorted(exp_con)}, Actual dari sim: {sorted(actual_con)}"
        )

    # Validasi conclusive: required evidence harus ada di supporting
    if case["expected_status"] == "conclusive" and case["expected_diagnosis"]:
        required_ev = CATEGORY_REQUIRED_EVIDENCE.get(case["expected_diagnosis"])
        if required_ev and required_ev not in exp_sup:
            report.error(
                case_id,
                f"expected_status=conclusive untuk '{case['expected_diagnosis']}' "
                f"tapi required evidence '{required_ev}' tidak ada di expected_supporting_evidence"
            )

    # Distribusi
    cat = case["primary_category"]
    report.category_counts[cat] = report.category_counts.get(cat, 0) + 1
    ctype = case.get("case_type", "unknown")
    report.case_type_counts[ctype] = report.case_type_counts.get(ctype, 0) + 1


def validate_baseline(path: Path = BASELINE_PATH) -> ValidationReport:
    """Validasi dataset baseline."""
    report = ValidationReport(f"Baseline — {path.name}")
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        report.error("FILE", f"File tidak ditemukan: {path}")
        return report
    except json.JSONDecodeError as e:
        report.error("FILE", f"JSON tidak valid: {e}")
        return report

    cases = data.get("test_cases", [])
    report.case_count = len(cases)
    kb = _build_kb_index()
    seen_ids: set[str] = set()

    for idx, case in enumerate(cases):
        _validate_baseline_case(case, idx, seen_ids, kb, report)

    if report.case_count != 20:
        report.warn("DATASET", f"Target 20 kasus baseline, ditemukan {report.case_count}")

    return report


def validate_extended(path: Path = EXTENDED_PATH) -> ValidationReport:
    """Validasi extended dataset."""
    report = ValidationReport(f"Extended — {path.name}")
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        report.error("FILE", f"File tidak ditemukan: {path}")
        return report
    except json.JSONDecodeError as e:
        report.error("FILE", f"JSON tidak valid: {e}")
        return report

    cases = data.get("cases", [])
    report.case_count = len(cases)
    kb = _build_kb_index()
    seen_ids: set[str] = set()

    for idx, case in enumerate(cases):
        _validate_extended_case(case, idx, seen_ids, kb, report)

    # Periksa jumlah
    if report.case_count != 180:
        report.warn("DATASET", f"Target 180 kasus, ditemukan {report.case_count}")

    # Periksa distribusi kategori
    for cat in VALID_CATEGORIES:
        cnt = report.category_counts.get(cat, 0)
        if cnt != 45:
            report.warn("DISTRIBUSI", f"Kategori '{cat}' memiliki {cnt} kasus (target 45)")

    return report


def validate_combined(baseline_path: Path = BASELINE_PATH, extended_path: Path = EXTENDED_PATH) -> ValidationReport:
    """Validasi gabungan baseline + extended (cek duplikasi ID cross-dataset)."""
    base_report = validate_baseline(baseline_path)
    ext_report = validate_extended(extended_path)

    report = ValidationReport("Combined — baseline + extended")
    report.errors.extend(base_report.errors)
    report.errors.extend(ext_report.errors)
    report.warnings.extend(base_report.warnings)
    report.warnings.extend(ext_report.warnings)
    report.case_count = base_report.case_count + ext_report.case_count

    for cat, cnt in base_report.category_counts.items():
        report.category_counts[cat] = report.category_counts.get(cat, 0) + cnt
    for cat, cnt in ext_report.category_counts.items():
        report.category_counts[cat] = report.category_counts.get(cat, 0) + cnt

    # Cross-dataset ID check: collect baseline IDs
    try:
        with baseline_path.open(encoding="utf-8") as f:
            base_data = json.load(f)
        base_ids = {c.get("case_id") for c in base_data.get("test_cases", [])}
    except Exception:
        base_ids = set()

    try:
        with extended_path.open(encoding="utf-8") as f:
            ext_data = json.load(f)
        ext_ids = {c.get("id") for c in ext_data.get("cases", [])}
    except Exception:
        ext_ids = set()

    cross_dup = base_ids & ext_ids
    if cross_dup:
        for cid in sorted(cross_dup):
            report.error(cid, "ID duplikat antara baseline dan extended")

    print(f"\nBaseline: {base_report.case_count} kasus")
    print(f"Extended: {ext_report.case_count} kasus")
    print(f"Total gabungan: {report.case_count} kasus")

    if report.case_count != 200:
        report.warn("DATASET", f"Target gabungan 200 kasus, ditemukan {report.case_count}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validasi dataset evaluasi diagnosis komputer."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--baseline", action="store_true", help="Validasi hanya baseline")
    group.add_argument("--extended", action="store_true", help="Validasi hanya extended")
    group.add_argument("--combined", action="store_true", help="Validasi gabungan")
    args = parser.parse_args()

    if args.baseline:
        report = validate_baseline()
    elif args.extended:
        report = validate_extended()
    elif args.combined:
        report = validate_combined()
    else:
        # Default: jalankan semua
        print("Menjalankan validasi baseline...")
        base_report = validate_baseline()
        base_report.print_report()

        if EXTENDED_PATH.exists():
            print("\nMenjalankan validasi extended...")
            ext_report = validate_extended()
            ext_report.print_report()

            print("\nMenjalankan validasi combined...")
            combined_report = validate_combined()
            combined_report.print_report()

            if not (base_report.is_valid() and ext_report.is_valid() and combined_report.is_valid()):
                raise SystemExit(1)
        else:
            print(f"\n[INFO] Extended dataset tidak ditemukan di {EXTENDED_PATH}, skip.")
            if not base_report.is_valid():
                raise SystemExit(1)
        return

    report.print_report()
    if not report.is_valid():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
