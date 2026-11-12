"""Pengujian reset sesi diagnosis terpusat.

Mencakup skenario wajib:
1. Reset setelah diagnosis konklusif.
2. Reset setelah diagnosis inkonklusif.
3. Reset ketika terdapat custom symptom.
4. Reset ketika terdapat hasil pemeriksaan.
5. Reset ketika terdapat input BSOD.
6. Evidence lama tidak terbawa.
7. Sesi baru dapat dimulai langsung.
"""

import pytest

import app as app_module
from app import (
    CUSTOM_CATEGORY_KEY_PREFIX,
    DIAGNOSIS_STATE_DEFAULTS,
    DIAGNOSIS_WIDGET_KEYS,
    NEW_DIAGNOSIS_FEEDBACK_KEY,
    clear_diagnosis_state,
    consume_new_diagnosis_feedback,
    reset_diagnosis_session,
    start_new_diagnosis,
)
from core.diagnosis import (
    apply_test_result,
    evaluate_diagnosis,
    initialize_diagnosis,
)


def _build_active_session(overrides: dict | None = None) -> dict:
    """Bangun mapping session_state berisi state diagnosis aktif."""
    session = dict(DIAGNOSIS_STATE_DEFAULTS)
    session["diag_state"] = "state-placeholder"
    session["diag_symptoms"] = ("sym_bsod_driver",)
    session["diag_log"] = [{"test_id": "test_driver_status"}]
    session["skipped_tests"] = ["test_smart_disk"]
    session["text_analysis"] = {"matches": ["sym_bsod_driver"]}
    session["bsod_validation"] = {"status": "valid", "code": "0x00000023"}
    session["pending_custom_symptom"] = {"success": True, "symptom": {}}
    session["analysis_signature"] = "sig-current"
    session["confirmed_analysis_signature"] = "sig-current"
    session["custom_symptoms"] = {"sym_user_deadbeef": {"id": "sym_user_deadbeef"}}
    session["confirm_reset"] = True
    # Widget keys
    session["symptom_selector"] = ["sym_bsod_driver"]
    session["free_text_input"] = "layar biru saat boot"
    session["bsod_input"] = "0x00000023"
    session[CUSTOM_CATEGORY_KEY_PREFIX + "sym_user_deadbeef"] = ["driver_software"]
    # Data non-diagnosis yang harus dipertahankan
    session["app_theme"] = "dark"
    session["nav_page"] = "diagnosis"
    if overrides:
        session.update(overrides)
    return session


def _assert_fully_reset(session: dict) -> None:
    """Pastikan semua key state diagnosis kembali ke nilai awal."""
    for key, default in DIAGNOSIS_STATE_DEFAULTS.items():
        if isinstance(default, list):
            assert session[key] == []
        elif isinstance(default, dict):
            assert session[key] == {}
        else:
            assert session[key] is default or session[key] == default

    for key in DIAGNOSIS_WIDGET_KEYS:
        assert key not in session

    assert not any(
        str(k).startswith(CUSTOM_CATEGORY_KEY_PREFIX) for k in session
    )


def test_clear_diagnosis_state_logic():
    session = _build_active_session()
    clear_diagnosis_state(session)
    _assert_fully_reset(session)
    # Konfigurasi aplikasi dipertahankan
    assert session["app_theme"] == "dark"
    assert session["nav_page"] == "diagnosis"


def test_reset_after_conclusive_diagnosis():
    """Skenario 1: reset setelah diagnosis konklusif."""
    # Overheating konklusif dengan satu tes
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "elevated")
    evaluation = evaluate_diagnosis(state)
    assert evaluation["status"] == "conclusive"

    session = _build_active_session()
    session["diag_state"] = state
    clear_diagnosis_state(session)

    _assert_fully_reset(session)
    assert session["diag_state"] is None


def test_reset_after_inconclusive_diagnosis():
    """Skenario 2: reset setelah diagnosis inkonklusif."""
    state = initialize_diagnosis(["sym_disk_slow_freeze"])
    state = apply_test_result(state, "test_smart_disk", "healthy")
    evaluation = evaluate_diagnosis(state)
    assert evaluation["status"] == "inconclusive"

    session = _build_active_session()
    session["diag_state"] = state
    clear_diagnosis_state(session)

    _assert_fully_reset(session)
    assert session["diag_state"] is None


def test_reset_when_custom_symptom_present():
    """Skenario 3: reset ketika ada custom symptom session-scoped."""
    session = _build_active_session()
    session["custom_symptoms"] = {
        "sym_user_aaaa1111": {
            "id": "sym_user_aaaa1111",
            "name": "Gejala khusus saya",
            "related_categories": ["ram_memory"],
        }
    }
    session["pending_custom_symptom"] = {
        "success": True,
        "symptom": {"id": "sym_user_bbbb2222"},
    }
    session[CUSTOM_CATEGORY_KEY_PREFIX + "sym_user_aaaa1111"] = ["ram_memory"]

    clear_diagnosis_state(session)

    _assert_fully_reset(session)
    assert session["custom_symptoms"] == {}
    assert session["pending_custom_symptom"] is None


def test_reset_when_test_results_present():
    """Skenario 4: reset ketika sudah ada hasil pemeriksaan & evidence."""
    state = initialize_diagnosis(["sym_fan_loud_hot"])
    state = apply_test_result(state, "test_cpu_gpu_temp", "elevated")
    assert state.test_results
    assert state.supporting_evidence

    session = _build_active_session()
    session["diag_state"] = state
    session["diag_log"] = [{"test_id": "test_cpu_gpu_temp", "outcome": "elevated"}]
    clear_diagnosis_state(session)

    _assert_fully_reset(session)
    assert session["diag_state"] is None
    assert session["diag_log"] == []


def test_reset_when_bsod_input_present():
    """Skenario 5: reset ketika ada input kode BSOD."""
    session = _build_active_session()
    session["bsod_input"] = "FAT_FILE_SYSTEM (0x00000023)"
    session["bsod_validation"] = {
        "status": "valid",
        "code": "0x00000023",
        "name": "FAT_FILE_SYSTEM",
    }

    clear_diagnosis_state(session)

    _assert_fully_reset(session)
    assert "bsod_input" not in session
    assert session["bsod_validation"] is None


def test_old_evidence_not_carried_over():
    """Skenario 6: evidence lama tidak terbawa ke sesi baru."""
    state = initialize_diagnosis(["sym_bsod_memory_management"])
    state = apply_test_result(state, "test_memory_diagnostic", "errors_found")
    old_evidence = set(state.supporting_evidence)
    assert old_evidence

    session = _build_active_session()
    session["diag_state"] = state
    clear_diagnosis_state(session)

    new_state = initialize_diagnosis(["sym_disk_slow_freeze"])
    assert not new_state.supporting_evidence
    assert not (old_evidence & set(new_state.supporting_evidence))
    assert new_state.cumulative_cost == 0
    assert not new_state.performed_tests
    assert not new_state.test_results


def test_new_session_can_start_immediately():
    """Skenario 7: sesi baru dapat dimulai langsung setelah reset."""
    session = _build_active_session()
    clear_diagnosis_state(session)

    _assert_fully_reset(session)

    # Simulasikan user memilih gejala baru dan memulai diagnosis.
    new_state = initialize_diagnosis(["sym_device_manager_yellow"])
    assert new_state.initial_symptoms == frozenset({"sym_device_manager_yellow"})
    assert new_state.cumulative_cost == 0
    assert not new_state.performed_tests
    assert new_state.possible_categories


# --------------------------------------------------------------------------
# Pengujian flag feedback animasi sesi diagnosis baru.
# --------------------------------------------------------------------------

def test_feedback_flag_not_part_of_diagnosis_defaults():
    """Flag feedback UI harus terpisah dari state diagnosis/UCS."""
    assert NEW_DIAGNOSIS_FEEDBACK_KEY not in DIAGNOSIS_STATE_DEFAULTS


def test_start_new_diagnosis_sets_feedback_flag(monkeypatch):
    """start_new_diagnosis() mereset sesi sekaligus menandai feedback."""
    fake_state: dict = dict(DIAGNOSIS_STATE_DEFAULTS)
    fake_state["diag_state"] = "active"
    fake_state["custom_symptoms"] = {"sym_user_x": {"id": "sym_user_x"}}
    fake_state["bsod_validation"] = {"status": "valid"}
    monkeypatch.setattr(app_module.st, "session_state", fake_state, raising=False)

    start_new_diagnosis()

    assert fake_state["diag_state"] is None
    assert fake_state["custom_symptoms"] == {}
    assert fake_state["bsod_validation"] is None
    assert fake_state[NEW_DIAGNOSIS_FEEDBACK_KEY] == {"status": "ready"}


def test_clear_diagnosis_state_preserves_feedback_flag():
    """clear_diagnosis_state() tidak boleh menghapus flag feedback UI."""
    session = _build_active_session()
    session[NEW_DIAGNOSIS_FEEDBACK_KEY] = {"status": "ready"}

    clear_diagnosis_state(session)

    assert session[NEW_DIAGNOSIS_FEEDBACK_KEY] == {"status": "ready"}


def test_consume_feedback_only_once(monkeypatch):
    """Feedback dikonsumsi sekali; rerun berikutnya tidak menampilkannya lagi."""
    fake_state: dict = {NEW_DIAGNOSIS_FEEDBACK_KEY: {"status": "ready"}}
    monkeypatch.setattr(app_module.st, "session_state", fake_state, raising=False)

    assert consume_new_diagnosis_feedback() is True
    assert fake_state[NEW_DIAGNOSIS_FEEDBACK_KEY] is None
    assert consume_new_diagnosis_feedback() is False


def test_sidebar_reset_does_not_trigger_feedback(monkeypatch):
    """Reset sidebar tetap tanpa feedback otomatis (perilaku 2 tahap dipertahankan)."""
    fake_state: dict = dict(DIAGNOSIS_STATE_DEFAULTS)
    fake_state["diag_state"] = "active"
    monkeypatch.setattr(app_module.st, "session_state", fake_state, raising=False)

    reset_diagnosis_session()

    assert fake_state["diag_state"] is None
    assert not fake_state.get(NEW_DIAGNOSIS_FEEDBACK_KEY)

