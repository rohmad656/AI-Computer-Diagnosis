"""Modul pemuatan dan validasi knowledge base diagnosis.

Menyediakan fungsi untuk memuat data gejala, pemeriksaan diagnostik,
dan kasus uji dari file JSON dengan validasi struktur.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.exceptions import (
    KnowledgeBaseError,
    KnowledgeBaseFileNotFoundError,
    KnowledgeBaseInvalidJSONError,
    KnowledgeBaseValidationError,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def _read_json_file(filename: str) -> dict[str, Any]:
    """Membaca dan mem-parsing file JSON dari direktori data."""
    path = DATA_DIR / filename
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise KnowledgeBaseFileNotFoundError(
            f"File knowledge base tidak ditemukan: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise KnowledgeBaseInvalidJSONError(
            f"File {filename} tidak valid JSON: {exc.msg} pada baris {exc.lineno}, kolom {exc.colno}"
        ) from exc


def _validate_required_keys(data: dict[str, Any], required_keys: list[str], context: str) -> None:
    """Memastikan kunci wajib ada dalam dictionary."""
    missing = [key for key in required_keys if key not in data]
    if missing:
        raise KnowledgeBaseValidationError(
            f"{context}: kunci wajib hilang: {', '.join(missing)}"
        )


def _validate_symptoms_structure(data: dict[str, Any]) -> None:
    """Memvalidasi struktur data gejala."""
    _validate_required_keys(data, ["schema_version", "categories", "symptoms"], "symptoms.json")

    if not isinstance(data["categories"], list) or not data["categories"]:
        raise KnowledgeBaseValidationError("symptoms.json: 'categories' harus list non-kosong")

    if not isinstance(data["symptoms"], list):
        raise KnowledgeBaseValidationError("symptoms.json: 'symptoms' harus list")

    # Validasi setiap kategori
    category_ids = set()
    for idx, cat in enumerate(data["categories"]):
        _validate_required_keys(cat, ["id", "name", "description"], f"categories[{idx}]")
        if cat["id"] in category_ids:
            raise KnowledgeBaseValidationError(f"categories[{idx}]: duplikasi id '{cat['id']}'")
        category_ids.add(cat["id"])

    # Validasi setiap gejala
    symptom_ids = set()
    for idx, sym in enumerate(data["symptoms"]):
        _validate_required_keys(sym, ["id", "name", "description", "related_categories"], f"symptoms[{idx}]")
        if sym["id"] in symptom_ids:
            raise KnowledgeBaseValidationError(f"symptoms[{idx}]: duplikasi id '{sym['id']}'")
        symptom_ids.add(sym["id"])

        for cat_id in sym["related_categories"]:
            if cat_id not in category_ids:
                raise KnowledgeBaseValidationError(
                    f"symptoms[{idx}]: related_categories merujuk kategori tidak dikenal '{cat_id}'"
                )


def _validate_diagnostic_tests_structure(data: dict[str, Any]) -> None:
    """Memvalidasi struktur data pemeriksaan diagnostik."""
    _validate_required_keys(data, ["schema_version", "tests"], "diagnostic_tests.json")

    if not isinstance(data["tests"], list):
        raise KnowledgeBaseValidationError("diagnostic_tests.json: 'tests' harus list")

    test_ids = set()
    valid_categories = {"driver_software", "overheating", "storage_disk", "ram_memory"}

    for idx, test in enumerate(data["tests"]):
        _validate_required_keys(
            test, ["id", "name", "category", "description", "cost", "possible_outcomes", "evidence_mapping"],
            f"tests[{idx}]"
        )
        if test["id"] in test_ids:
            raise KnowledgeBaseValidationError(f"tests[{idx}]: duplikasi id '{test['id']}'")
        test_ids.add(test["id"])

        if test["category"] not in valid_categories:
            raise KnowledgeBaseValidationError(
                f"tests[{idx}]: kategori '{test['category']}' tidak valid. Harus salah satu dari {sorted(valid_categories)}"
            )

        if not isinstance(test["cost"], int) or test["cost"] < 0:
            raise KnowledgeBaseValidationError(f"tests[{idx}]: 'cost' harus integer non-negatif")

        if not isinstance(test["possible_outcomes"], list) or not test["possible_outcomes"]:
            raise KnowledgeBaseValidationError(f"tests[{idx}]: 'possible_outcomes' harus list non-kosong")

        if not isinstance(test["evidence_mapping"], dict):
            raise KnowledgeBaseValidationError(f"tests[{idx}]: 'evidence_mapping' harus dictionary")

        # Validasi optional outcome_types
        allowed_outcome_types = {"normal", "abnormal", "uncertain", "misleading"}
        outcome_types = test.get("outcome_types")
        if outcome_types is not None:
            if not isinstance(outcome_types, dict):
                raise KnowledgeBaseValidationError(f"tests[{idx}]: 'outcome_types' harus dictionary")
            for outcome, otype in outcome_types.items():
                if outcome not in test["possible_outcomes"]:
                    raise KnowledgeBaseValidationError(
                        f"tests[{idx}]: outcome_types merujuk outcome tidak dikenal '{outcome}'"
                    )
                if otype not in allowed_outcome_types:
                    raise KnowledgeBaseValidationError(
                        f"tests[{idx}]: outcome_types['{outcome}'] tipe '{otype}' tidak valid. Harus salah satu dari {sorted(allowed_outcome_types)}"
                    )
            # Pastikan setiap possible_outcome memiliki outcome_type (opsional, tidak memaksa)
            # Hanya peringatan, tidak error

        for outcome in test["possible_outcomes"]:
            if outcome not in test["evidence_mapping"]:
                raise KnowledgeBaseValidationError(
                    f"tests[{idx}]: outcome '{outcome}' tidak memiliki evidence_mapping"
                )
            mapping = test["evidence_mapping"][outcome]
            _validate_required_keys(mapping, ["supports", "contradicts"], f"evidence_mapping['{outcome}']")
            if not isinstance(mapping["supports"], list) or not isinstance(mapping["contradicts"], list):
                raise KnowledgeBaseValidationError(
                    f"tests[{idx}]: evidence_mapping['{outcome}'] 'supports' dan 'contradicts' harus list"
                )


def _validate_test_cases_structure(data: dict[str, Any]) -> None:
    """Memvalidasi struktur data kasus uji."""
    _validate_required_keys(data, ["schema_version", "test_cases"], "test_cases.json")

    if not isinstance(data["test_cases"], list):
        raise KnowledgeBaseValidationError("test_cases.json: 'test_cases' harus list")

    for idx, case in enumerate(data["test_cases"]):
        _validate_required_keys(
            case, ["id", "name", "description", "initial_symptoms", "simulated_test_results", "expected_diagnosis", "expected_status"],
            f"test_cases[{idx}]"
        )
        if not isinstance(case["initial_symptoms"], list):
            raise KnowledgeBaseValidationError(f"test_cases[{idx}]: 'initial_symptoms' harus list")
        if not isinstance(case["simulated_test_results"], dict):
            raise KnowledgeBaseValidationError(f"test_cases[{idx}]: 'simulated_test_results' harus dictionary")
        if case["expected_status"] not in ("conclusive", "inconclusive"):
            raise KnowledgeBaseValidationError(
                f"test_cases[{idx}]: expected_status harus 'conclusive' atau 'inconclusive'"
            )


def load_symptoms() -> dict[str, Any]:
    """Memuat data gejala dan kategori diagnosis dari symptoms.json."""
    data = _read_json_file("symptoms.json")
    _validate_symptoms_structure(data)
    return data


def load_diagnostic_tests() -> dict[str, Any]:
    """Memuat data pemeriksaan diagnostik dari diagnostic_tests.json."""
    data = _read_json_file("diagnostic_tests.json")
    _validate_diagnostic_tests_structure(data)
    return data


def load_test_cases() -> dict[str, Any]:
    """Memuat data kasus uji simulasi dari test_cases.json."""
    data = _read_json_file("test_cases.json")
    _validate_test_cases_structure(data)
    return data


def validate_knowledge_base() -> dict[str, Any]:
    """Memvalidasi seluruh knowledge base secara keseluruhan.

    Returns:
        Dictionary berisi status validasi dan ringkasan data.
    """
    symptoms = load_symptoms()
    tests = load_diagnostic_tests()
    test_cases = load_test_cases()

    # Cross-reference validasi
    category_ids = {cat["id"] for cat in symptoms["categories"]}
    symptom_ids = {sym["id"] for sym in symptoms["symptoms"]}
    test_ids = {test["id"] for test in tests["tests"]}

    for test in tests["tests"]:
        if test["category"] not in category_ids:
            raise KnowledgeBaseValidationError(
                f"Test '{test['id']}' merujuk kategori tidak dikenal: {test['category']}"
            )

    for sym in symptoms["symptoms"]:
        for cat_id in sym["related_categories"]:
            if cat_id not in category_ids:
                raise KnowledgeBaseValidationError(
                    f"Symptom '{sym['id']}' merujuk kategori tidak dikenal: {cat_id}"
                )

    for case in test_cases["test_cases"]:
        for sym_id in case["initial_symptoms"]:
            if sym_id not in symptom_ids:
                raise KnowledgeBaseValidationError(
                    f"Test case '{case['id']}' merujuk symptom tidak dikenal: {sym_id}"
                )
        for test_id in case["simulated_test_results"]:
            if test_id not in test_ids:
                raise KnowledgeBaseValidationError(
                    f"Test case '{case['id']}' merujuk test tidak dikenal: {test_id}"
                )
        if case["expected_diagnosis"] is not None and case["expected_diagnosis"] not in category_ids:
            raise KnowledgeBaseValidationError(
                f"Test case '{case['id']}' expected_diagnosis tidak dikenal: {case['expected_diagnosis']}"
            )

    return {
        "valid": True,
        "categories_count": len(category_ids),
        "symptoms_count": len(symptom_ids),
        "tests_count": len(test_ids),
        "test_cases_count": len(test_cases["test_cases"]),
    }


def get_categories() -> list[dict[str, Any]]:
    """Mengembalikan daftar kategori diagnosis dari data gejala."""
    return list(load_symptoms()["categories"])


def get_symptoms_by_category(category_id: str) -> list[dict[str, Any]]:
    """Mengembalikan gejala yang terkait dengan kategori tertentu."""
    data = load_symptoms()
    return [sym for sym in data["symptoms"] if category_id in sym["related_categories"]]


def get_test_by_id(test_id: str) -> dict[str, Any] | None:
    """Mencari pemeriksaan diagnostik berdasarkan ID."""
    data = load_diagnostic_tests()
    for test in data["tests"]:
        if test["id"] == test_id:
            return test
    return None


def get_category_by_id(category_id: str) -> dict[str, Any] | None:
    """Mencari kategori berdasarkan ID."""
    for cat in get_categories():
        if cat["id"] == category_id:
            return cat
    return None