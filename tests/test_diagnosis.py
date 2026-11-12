"""Pengujian mesin diagnosis dan knowledge base."""

from __future__ import annotations

import pytest

from core.diagnosis import (
    DiagnosisState,
    apply_test_result,
    evaluate_diagnosis,
    get_conflicting_categories,
    get_evidence_sufficiency,
    get_next_recommended_test,
    get_outcome_type,
    get_pending_tests,
    initialize_diagnosis,
    is_category_confirmed,
    is_category_conflicting,
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


def test_misleading_false_positive_adds_supporting_evidence_only() -> None:
    """False-positive: test salah melaporkan masalah sehingga menambah supporting evidence."""
    state = initialize_diagnosis(["sym_device_manager_yellow"])
    # test_driver_status=false_positive adalah outcome misleading yang tetap
    # memetakan ke driver_issue_confirmed (sesuai evidence_mapping eksplisit).
    state = apply_test_result(state, "test_driver_status", "false_positive")

    assert "driver_issue_confirmed" in state.supporting_evidence
    assert "driver_issue_confirmed" not in state.contradicting_evidence
    assert state.neutral_evidence == frozenset()


def test_misleading_false_negative_adds_contradicting_evidence_only() -> None:
    """False-negative: test salah melaporkan normal sehingga menambah contradicting evidence."""
    state = initialize_diagnosis(["sym_app_crash_random"])
    state = apply_test_result(state, "test_memory_diagnostic", "false_negative")

    assert "memory_issue_confirmed" in state.contradicting_evidence
    assert "memory_issue_confirmed" not in state.supporting_evidence


def test_misleading_outcome_can_produce_contradicting_evidence() -> None:
    """Outcome misleading dapat menghasilkan evidence yang bertentangan."""
    state = initialize_diagnosis(["sym_bsod_driver"])

    # false_negative pada riwayat error driver menolak driver_issue_confirmed
    state = apply_test_result(state, "test_error_code_history", "false_negative")

    assert "driver_issue_confirmed" in state.contradicting_evidence
    assert is_category_ruled_out(state, "driver_software") is True


def test_misleading_outcome_can_create_conflicting_state() -> None:
    """Dua outcome misleading pada kategori yang sama dapat membentuk state konflik."""
    state = initialize_diagnosis(["sym_bsod_driver"])

    # false_positive mendukung driver_issue_confirmed
    state = apply_test_result(state, "test_driver_status", "false_positive")
    # false_negative menolak driver_issue_confirmed yang sama
    state = apply_test_result(state, "test_error_code_history", "false_negative")

    assert is_category_conflicting(state, "driver_software") is True
    assert is_goal_state(state) is False


def test_outcome_types_are_explicit_for_every_test() -> None:
    """Setiap outcome pada setiap test harus punya tipe eksplisit di outcome_types."""
    for test in load_diagnostic_tests()["tests"]:
        outcome_types = test.get("outcome_types", {})
        for outcome in test["possible_outcomes"]:
            assert outcome in outcome_types, (
                f"{test['id']}: outcome '{outcome}' tidak punya outcome_type"
            )
            assert outcome_types[outcome] in {
                "normal",
                "abnormal",
                "uncertain",
                "misleading",
            }


def test_evidence_sufficiency_transitions() -> None:
    """Status kecukupan bukti harus mengikuti perkembangan pemeriksaan."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    assert get_evidence_sufficiency(state) == "partial"

    confirmed_state = apply_test_result(state, "test_cpu_gpu_temp", "critical")
    assert get_evidence_sufficiency(confirmed_state) == "sufficient"

    ruled_out_state = apply_test_result(state, "test_cpu_gpu_temp", "normal")
    assert get_evidence_sufficiency(ruled_out_state) == "insufficient"


# ------------------------------------------------------------------
# Pengujian Outcome Uncertain (netral)
# ------------------------------------------------------------------


def test_uncertain_outcome_adds_no_supporting_evidence() -> None:
    """Outcome uncertain tidak menambah supporting evidence."""
    before = initialize_diagnosis(["sym_shutdown_thermal"])
    after = apply_test_result(before, "test_cpu_gpu_temp", "inconclusive")

    assert after.supporting_evidence == before.supporting_evidence
    assert "high_temperature_confirmed" not in after.supporting_evidence


def test_uncertain_outcome_adds_no_contradicting_evidence() -> None:
    """Outcome uncertain tidak menambah contradicting evidence."""
    before = initialize_diagnosis(["sym_shutdown_thermal"])
    after = apply_test_result(before, "test_cpu_gpu_temp", "inconclusive")

    assert after.contradicting_evidence == before.contradicting_evidence
    assert "high_temperature_confirmed" not in after.contradicting_evidence


def test_uncertain_outcome_recorded_as_neutral_evidence() -> None:
    """Outcome uncertain harus tercatat sebagai neutral evidence."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "inconclusive")

    assert state.neutral_evidence == frozenset(
        {("test_cpu_gpu_temp", "inconclusive")}
    )


def test_uncertain_outcome_is_not_treated_as_normal() -> None:
    """Outcome uncertain tidak boleh diperlakukan seperti outcome normal."""
    uncertain = apply_test_result(
        initialize_diagnosis(["sym_shutdown_thermal"]),
        "test_cpu_gpu_temp",
        "inconclusive",
    )
    normal = apply_test_result(
        initialize_diagnosis(["sym_shutdown_thermal"]),
        "test_cpu_gpu_temp",
        "normal",
    )

    # normal menolak overheating; uncertain tidak menolak apapun
    assert is_category_ruled_out(normal, "overheating") is True
    assert is_category_ruled_out(uncertain, "overheating") is False
    assert uncertain.contradicting_evidence != normal.contradicting_evidence


def test_uncertain_outcome_allows_further_tests() -> None:
    """Setelah outcome uncertain, sistem masih dapat melanjutkan pemeriksaan lain."""
    state = initialize_diagnosis(["sym_system_crash"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "inconclusive")

    pending_ids = {test["id"] for test in get_pending_tests(state)}
    assert "test_cpu_gpu_temp" not in pending_ids
    assert "test_driver_status" in pending_ids

    # Pemeriksaan berikutnya tetap bisa diterapkan.
    state = apply_test_result(state, "test_driver_status", "yellow_bang")
    assert is_category_confirmed(state, "driver_software") is True


def test_uncertain_outcome_leaves_result_inconclusive() -> None:
    """Tanpa evidence yang cukup, hasil akhir tetap inconclusive."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "inconclusive")

    result = evaluate_diagnosis(state)
    assert result["status"] == "inconclusive"
    assert result["diagnosed_category"] is None
    assert result["neutral_evidence"] == [("test_cpu_gpu_temp", "inconclusive")]


# ------------------------------------------------------------------
# Pengujian State Konflik
# ------------------------------------------------------------------


def test_conflict_single_category_supporting_only() -> None:
    """Satu kategori hanya dengan supporting evidence."""
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "critical")

    assert is_category_confirmed(state, "overheating") is True
    assert is_category_conflicting(state, "overheating") is False


def test_valid_abnormal_outcome_allows_conclusive() -> None:
    """Valid abnormal outcome (non-misleading) enables conclusive diagnosis."""
    # Overheating hanya memiliki satu tes yang bisa dikonfirmasi
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "elevated")
    assert is_category_confirmed(state, "overheating") is True
    result = evaluate_diagnosis(state)
    assert result["status"] == "conclusive"
    assert result["diagnosed_category"] == "overheating"


def test_misleading_cannot_be_sole_basis() -> None:
    """Misleading outcome alone cannot confirm category."""
    state = initialize_diagnosis(["sym_device_manager_yellow"])
    state = apply_test_result(state, "test_driver_status", "false_positive")
    assert is_category_confirmed(state, "driver_software") is False
    assert is_category_conflicting(state, "driver_software") is False
    assert is_goal_state(state) is False
    assert "driver_issue_confirmed" in state.misleading_support
    assert "driver_issue_confirmed" not in state.trusted_support
    result = evaluate_diagnosis(state)
    assert result["status"] != "conclusive"
    assert result["diagnosed_category"] is None


def test_misleading_then_valid_evidence() -> None:
    """Misleading evidence followed by valid evidence enables conclusive diagnosis."""
    state = initialize_diagnosis(["sym_device_manager_yellow"])
    state = apply_test_result(state, "test_driver_status", "false_positive")
    state = apply_test_result(state, "test_error_code_history", "driver_errors_found")
    assert is_category_confirmed(state, "driver_software") is True
    result = evaluate_diagnosis(state)
    assert result["status"] == "conclusive"
    assert result["diagnosed_category"] == "driver_software"


def test_misleading_with_contradicting_evidence() -> None:
    """Misleading evidence with contradicting evidence results in inconclusive."""
    state = initialize_diagnosis(["sym_device_manager_yellow"])
    state = apply_test_result(state, "test_driver_status", "false_positive")
    state = apply_test_result(state, "test_error_code_history", "false_negative")
    assert is_category_conflicting(state, "driver_software") is True
    assert is_goal_state(state) is False
    result = evaluate_diagnosis(state)
    assert result["status"] == "inconclusive"
    assert result["diagnosed_category"] is None


def test_uncertain_outcome_not_confirmation() -> None:
    """Outcome uncertain does not count as confirmation."""
    state = initialize_diagnosis(["sym_device_manager_yellow"])
    state = apply_test_result(state, "test_driver_status", "inconclusive")
    assert is_category_confirmed(state, "driver_software") is False
    assert "driver_issue_confirmed" not in state.trusted_support
    result = evaluate_diagnosis(state)
    assert result["status"] != "conclusive"
    assert result["diagnosed_category"] is None


def test_continues_if_tests_available() -> None:
    """System continues diagnosis if relevant tests remain."""
    state = initialize_diagnosis(["sym_device_manager_yellow"])
    state = apply_test_result(state, "test_driver_status", "false_positive")
    assert len(get_pending_tests(state)) > 0
    next_test = get_next_recommended_test(state)
    assert next_test is not None
    assert next_test["id"] == "test_error_code_history"


def test_no_test_repetition() -> None:
    """System prevents reapplying the same test."""
    state = initialize_diagnosis(["sym_device_manager_yellow"])
    state = apply_test_result(state, "test_driver_status", "yellow_bang")
    with pytest.raises(InvalidStateError):
        apply_test_result(state, "test_driver_status", "yellow_bang")


def test_stops_inconclusive_no_tests_left() -> None:
    """System stops inconclusive when no relevant tests remain."""
    state = initialize_diagnosis(["sym_device_manager_yellow"])
    state = apply_test_result(state, "test_driver_status", "inconclusive")
    state = apply_test_result(state, "test_error_code_history", "inconclusive")
    assert get_pending_tests(state) == []
    result = evaluate_diagnosis(state)
    assert result["status"] == "inconclusive"
    assert result["diagnosed_category"] is None


def test_ext_drv_045_no_early_stop() -> None:
    """EXT_DRV_045 no longer stops prematurely with misleading evidence."""
    state = initialize_diagnosis(["sym_device_manager_yellow"])
    state = apply_test_result(state, "test_driver_status", "false_positive")
    state = apply_test_result(state, "test_error_code_history", "inconclusive")
    assert len(state.performed_tests) == 2
    result = evaluate_diagnosis(state)
    assert result["status"] == "inconclusive"
    assert result["diagnosed_category"] is None
    assert result["pending_tests"] == []
    assert "driver_issue_confirmed" in result["misleading_support"]


def test_conflict_single_category_support_and_contradict() -> None:
    """Satu kategori dengan supporting dan contradicting evidence sekaligus."""
    state = initialize_diagnosis(["sym_bsod_driver"])
    state = apply_test_result(state, "test_driver_status", "yellow_bang")
    state = apply_test_result(state, "test_error_code_history", "no_driver_errors")

    assert "driver_issue_confirmed" in state.supporting_evidence
    assert "driver_issue_confirmed" in state.contradicting_evidence
    assert is_category_conflicting(state, "driver_software") is True
    assert is_category_confirmed(state, "driver_software") is False


def test_conflict_two_categories_supported_together() -> None:
    """Dua kategori yang didukung secara bersamaan → conflicting."""
    state = initialize_diagnosis(["sym_bsod_driver", "sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "critical")
    state = apply_test_result(state, "test_driver_status", "yellow_bang")

    assert is_category_confirmed(state, "overheating") is True
    assert is_category_confirmed(state, "driver_software") is True
    # Kedua kategori memiliki trusted evidence → conflicting
    assert get_evidence_sufficiency(state) == "conflicting"


def test_conflict_ambiguous_symptoms_not_yet_resolvable() -> None:
    """Gejala ambigu menyisakan beberapa kategori sebelum pemeriksaan dilakukan."""
    state = initialize_diagnosis(["sym_system_crash"])

    assert {"driver_software", "overheating", "storage_disk"} <= set(
        state.possible_categories
    )
    result = evaluate_diagnosis(state)
    assert result["status"] == "in_progress"
    assert result["diagnosed_category"] is None


def test_conflict_unsolvable_stays_inconclusive() -> None:
    """Konflik yang tidak dapat diselesaikan harus inconclusive."""
    state = initialize_diagnosis(["sym_bsod_driver"])
    state = apply_test_result(state, "test_driver_status", "yellow_bang")
    state = apply_test_result(state, "test_error_code_history", "no_driver_errors")

    assert get_conflicting_categories(state) == ["driver_software"]
    result = evaluate_diagnosis(state)
    assert result["status"] == "inconclusive"
    assert result["diagnosed_category"] is None


def test_conflict_with_additional_evidence_still_detected() -> None:
    """Konflik tetap terdeteksi walaupun ada tambahan evidence dari kategori lain."""
    state = initialize_diagnosis(["sym_bsod_driver", "sym_shutdown_thermal"])
    state = apply_test_result(state, "test_driver_status", "yellow_bang")
    state = apply_test_result(state, "test_error_code_history", "no_driver_errors")
    state = apply_test_result(state, "test_cpu_gpu_temp", "critical")

    assert is_category_confirmed(state, "overheating") is True
    assert is_category_conflicting(state, "driver_software") is True
    assert "driver_software" in get_conflicting_categories(state)


def test_is_goal_state_rejects_conflicting_state() -> None:
    """is_goal_state harus menolak state yang mengandung konflik evidence."""
    state = initialize_diagnosis(["sym_bsod_driver"])
    state = apply_test_result(state, "test_driver_status", "yellow_bang")
    state = apply_test_result(state, "test_error_code_history", "no_driver_errors")

    assert is_goal_state(state) is False


def test_evaluate_diagnosis_returns_inconclusive_when_conflict_unresolved() -> None:
    """evaluate_diagnosis harus inconclusive selama konflik belum terselesaikan."""
    state = initialize_diagnosis(["sym_bsod_driver"])
    state = apply_test_result(state, "test_driver_status", "yellow_bang")
    state = apply_test_result(state, "test_error_code_history", "no_driver_errors")

    result = evaluate_diagnosis(state)
    assert result["status"] == "inconclusive"
    assert result["diagnosed_category"] is None
    assert result["conflicting_categories"] == ["driver_software"]


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