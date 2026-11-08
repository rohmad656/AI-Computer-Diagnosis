"""Pengujian mesin diagnosis dan knowledge base."""

from __future__ import annotations

import pytest

from core.diagnosis import (
    DiagnosisState,
    apply_test_result,
    evaluate_diagnosis,
    get_evidence_sufficiency,
    get_next_recommended_test,
    get_pending_tests,
    initialize_diagnosis,
    is_category_confirmed,
    is_category_ruled_out,
    is_goal_state,
)
from core.exceptions import InvalidStateError
from core.knowledge_base import (
    get_categories,
    load_diagnostic_tests,
    load_symptoms,
    load_test_cases,
    validate_knowledge_base,
)


# ------------------------------------------------------------------
# Pengujian Knowledge Base
# ------------------------------------------------------------------


def test_symptoms_contains_four_categories() -> None:
    """Data gejala harus memiliki tepat empat kategori."""
    categories = load_symptoms()["categories"]
    assert len(categories) == 4


def test_category_ids_are_unique() -> None:
    """Setiap kategori harus memiliki id yang unik."""
    categories = load_symptoms()["categories"]
    ids = [c["id"] for c in categories]
    assert len(ids) == len(set(ids))


def test_expected_category_ids_exist() -> None:
    """Keempat kategori yang ditetapkan harus ada dalam data."""
    ids = {c["id"] for c in get_categories()}
    expected = {"driver_software", "overheating", "storage_disk", "ram_memory"}
    assert expected == ids


def test_all_symptoms_have_valid_categories() -> None:
    """Setiap gejala harus merujuk kategori yang ada."""
    data = load_symptoms()
    valid_cats = {c["id"] for c in data["categories"]}
    for sym in data["symptoms"]:
        for cat_id in sym["related_categories"]:
            assert cat_id in valid_cats, (
                f"Symptom '{sym['id']}' merujuk kategori tidak dikenal: '{cat_id}'"
            )


def test_diagnostic_tests_data_valid() -> None:
    """File diagnostic_tests.json harus valid dan memiliki data test."""
    data = load_diagnostic_tests()
    assert "tests" in data
    assert len(data["tests"]) > 0


def test_all_tests_have_evidence_mapping_for_all_outcomes() -> None:
    """Setiap test harus memiliki evidence_mapping untuk setiap possible_outcome."""
    for test in load_diagnostic_tests()["tests"]:
        for outcome in test["possible_outcomes"]:
            assert outcome in test["evidence_mapping"], (
                f"Test '{test['id']}' tidak memiliki evidence_mapping untuk outcome '{outcome}'"
            )


def test_test_cases_data_valid() -> None:
    """File test_cases.json harus valid dan memiliki kasus uji."""
    data = load_test_cases()
    assert "test_cases" in data
    assert len(data["test_cases"]) > 0


def test_validate_knowledge_base_passes() -> None:
    """Validasi seluruh knowledge base harus berhasil."""
    result = validate_knowledge_base()
    assert result["valid"] is True
    assert result["categories_count"] == 4
    assert result["symptoms_count"] > 0
    assert result["tests_count"] > 0


# ------------------------------------------------------------------
# Pengujian State Diagnosis
# ------------------------------------------------------------------


def test_initialize_diagnosis_builds_valid_state() -> None:
    """initialize_diagnosis harus membentuk state awal yang valid."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    assert isinstance(state, DiagnosisState)
    assert "sym_shutdown_thermal" in state.initial_symptoms
    assert len(state.performed_tests) == 0
    assert len(state.test_results) == 0
    assert "overheating" in state.possible_categories


def test_initialize_diagnosis_with_multiple_symptoms() -> None:
    """State awal dengan beberapa gejala harus menyertakan semua kategori relevan."""
    state = initialize_diagnosis(["sym_bsod_driver", "sym_app_crash_random"])
    # sym_bsod_driver => driver_software; sym_app_crash_random => ram_memory
    assert "driver_software" in state.possible_categories
    assert "ram_memory" in state.possible_categories


def test_initialize_diagnosis_rejects_invalid_symptom() -> None:
    """initialize_diagnosis harus menolak ID gejala yang tidak dikenal."""
    with pytest.raises(InvalidStateError):
        initialize_diagnosis(["symptom_yang_tidak_ada"])


def test_apply_test_result_adds_supporting_evidence() -> None:
    """Hasil test positif harus menambahkan bukti pendukung ke state baru."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    new_state = apply_test_result(state, "test_cpu_gpu_temp", "critical")
    assert "high_temperature_confirmed" in new_state.supporting_evidence


def test_apply_test_result_adds_contradicting_evidence() -> None:
    """Hasil test normal harus menambahkan bukti bertentangan ke state baru."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    new_state = apply_test_result(state, "test_cpu_gpu_temp", "normal")
    assert "high_temperature_confirmed" in new_state.contradicting_evidence


def test_apply_test_result_records_test_in_performed() -> None:
    """Test yang dilakukan harus tercatat di state baru."""
    state = initialize_diagnosis(["sym_disk_slow_freeze"])
    new_state = apply_test_result(state, "test_smart_disk", "warning")
    assert "test_smart_disk" in new_state.performed_tests


def test_apply_test_result_accumulates_cost() -> None:
    """Biaya kumulatif harus bertambah setiap test diterapkan."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    assert state.cumulative_cost == 0.0
    new_state = apply_test_result(state, "test_cpu_gpu_temp", "critical")
    assert new_state.cumulative_cost == 1  # cost test_cpu_gpu_temp = 1


def test_apply_test_result_rejects_invalid_outcome() -> None:
    """Outcome yang tidak valid untuk test harus ditolak."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    with pytest.raises(InvalidStateError):
        apply_test_result(state, "test_cpu_gpu_temp", "outcome_tidak_valid")


def test_apply_test_result_rejects_invalid_test_id() -> None:
    """Test ID yang tidak dikenal harus ditolak."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    with pytest.raises(InvalidStateError):
        apply_test_result(state, "test_yang_tidak_ada", "normal")


# ------------------------------------------------------------------
# Pengujian Goal State dan Evaluasi
# ------------------------------------------------------------------


def test_is_goal_state_false_before_any_test() -> None:
    """State awal tanpa test belum boleh menjadi goal state."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    assert is_goal_state(state) is False


def test_is_goal_state_true_after_confirming_evidence() -> None:
    """Goal state harus tercapai setelah bukti pendukung yang cukup ditemukan."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "critical")
    assert is_goal_state(state) is True


def test_is_category_confirmed_true_when_evidence_present() -> None:
    """is_category_confirmed harus True jika bukti pendukung ada."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "elevated")
    assert is_category_confirmed(state, "overheating") is True


def test_is_category_ruled_out_when_contradicting_evidence() -> None:
    """is_category_ruled_out harus True jika bukti bertentangan ada."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "normal")
    assert is_category_ruled_out(state, "overheating") is True


def test_evaluate_diagnosis_conclusive() -> None:
    """evaluate_diagnosis harus mengembalikan 'conclusive' ketika satu kategori terkonfirmasi."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "critical")
    result = evaluate_diagnosis(state)
    assert result["status"] == "conclusive"
    assert result["diagnosed_category"] == "overheating"
    assert len(result["recommendations"]) > 0


def test_evaluate_diagnosis_inconclusive_when_all_tests_done_no_support() -> None:
    """Jika semua test relevan menghasilkan normal, status harus 'inconclusive'."""
    # Gunakan kategori overheating — satu-satunya test: test_cpu_gpu_temp
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    # Lakukan test dengan hasil normal (contradicts overheating)
    state = apply_test_result(state, "test_cpu_gpu_temp", "normal")
    result = evaluate_diagnosis(state)
    # Semua test untuk overheating sudah dilakukan, tidak ada bukti pendukung
    assert result["status"] in ("inconclusive", "in_progress")


def test_evaluate_diagnosis_has_no_false_diagnosis() -> None:
    """Diagnosis tidak boleh diklaim tanpa bukti pendukung."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    # State awal tanpa test apapun
    result = evaluate_diagnosis(state)
    assert result["diagnosed_category"] is None


def test_get_next_recommended_test_returns_test_for_active_category() -> None:
    """get_next_recommended_test harus merekomendasikan test yang relevan."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    test = get_next_recommended_test(state)
    assert test is not None
    # Test yang direkomendasikan harus untuk kategori yang relevan
    assert test["category"] in state.possible_categories


def test_get_next_recommended_test_returns_none_at_goal() -> None:
    """get_next_recommended_test harus None jika sudah goal state."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "critical")
    assert is_goal_state(state) is True
    test = get_next_recommended_test(state)
    assert test is None


def test_full_diagnosis_flow_overheating() -> None:
    """Alur diagnosis lengkap untuk kasus overheating harus menghasilkan diagnosis yang benar."""
    # 1. Inisialisasi dengan gejala overheating
    state = initialize_diagnosis(["sym_shutdown_thermal", "sym_fan_loud_hot"])
    assert not is_goal_state(state)

    # 2. Dapatkan rekomendasi test
    next_test = get_next_recommended_test(state)
    assert next_test is not None

    # 3. Simulasikan hasil test: suhu critical
    state = apply_test_result(state, "test_cpu_gpu_temp", "critical")

    # 4. Evaluasi
    assert is_goal_state(state)
    result = evaluate_diagnosis(state)
    assert result["status"] == "conclusive"
    assert result["diagnosed_category"] == "overheating"
    assert state.cumulative_cost == 1  # cost test_cpu_gpu_temp


def test_same_test_cannot_be_applied_twice() -> None:
    """Pemeriksaan yang sudah dilakukan tidak boleh diterapkan ulang."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "normal")

    with pytest.raises(InvalidStateError):
        apply_test_result(state, "test_cpu_gpu_temp", "critical")


def test_ruled_out_category_is_not_silently_reset() -> None:
    """Kategori yang tereliminasi tidak boleh dikembalikan diam-diam."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "normal")

    assert state.possible_categories == frozenset()
    result = evaluate_diagnosis(state)
    assert result["status"] == "inconclusive"
    assert result["diagnosed_category"] is None


def test_evidence_sufficiency_transitions() -> None:
    """Status kecukupan bukti harus mengikuti perkembangan pemeriksaan."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    assert get_evidence_sufficiency(state) == "partial"

    confirmed_state = apply_test_result(state, "test_cpu_gpu_temp", "critical")
    assert get_evidence_sufficiency(confirmed_state) == "sufficient"

    ruled_out_state = apply_test_result(state, "test_cpu_gpu_temp", "normal")
    assert get_evidence_sufficiency(ruled_out_state) == "insufficient"


def test_pending_tests_shrink_after_test_is_performed() -> None:
    """Pemeriksaan yang sudah dilakukan harus hilang dari daftar pending."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    initial_ids = {test["id"] for test in get_pending_tests(state)}
    assert "test_cpu_gpu_temp" in initial_ids

    state = apply_test_result(state, "test_cpu_gpu_temp", "normal")
    assert get_pending_tests(state) == []


def test_evaluation_includes_pending_tests_and_sufficiency() -> None:
    """Hasil evaluasi harus menyertakan pemeriksaan tersisa dan status bukti."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    result = evaluate_diagnosis(state)

    assert result["evidence_sufficiency"] == "partial"
    assert "test_cpu_gpu_temp" in {test["id"] for test in result["pending_tests"]}