import pytest
from core.symptom_matcher import (
    normalize_text,
    match_bsod_code,
    match_free_text,
    suggest_symptoms_from_text,
)

def test_normalize_text_lowercase():
    assert normalize_text("HELLO WORLD") == "hello world"

def test_normalize_text_strips_punctuation():
    assert normalize_text("Halo, dunia! Komputer... rusak?") == "halo dunia komputer rusak"

def test_match_bsod_known_code():
    res = match_bsod_code("MEMORY_MANAGEMENT")
    assert res["found"] is True
    assert "sym_bsod_memory_management" in res["candidate_symptoms"]

def test_match_bsod_unknown_code():
    res = match_bsod_code("TOTALLY_FAKE_CODE")
    assert res["found"] is False
    assert res["candidate_symptoms"] == []

def test_match_bsod_case_insensitive():
    res1 = match_bsod_code("memory_management")
    res2 = match_bsod_code("Memory_Management")
    assert res1["code"] == "MEMORY_MANAGEMENT"
    assert res2["code"] == "MEMORY_MANAGEMENT"

def test_match_free_text_bsod_alias():
    available = ["sym_bsod_driver"]
    res = match_free_text("layar biru driver", available)
    assert "sym_bsod_driver" in res["matched_symptoms"]

def test_match_free_text_no_match():
    available = ["sym_bsod_driver"]
    res = match_free_text("mesin kopi tidak menyala", available)
    assert res["matched_symptoms"] == []
    assert res["confidence"] == "none"

def test_match_free_text_multiple_candidates():
    # "layar biru" matches bsod_driver and bsod_mem
    available = ["sym_bsod_driver", "sym_bsod_memory_management"]
    res = match_free_text("layar biru", available)
    assert len(res["matched_symptoms"]) >= 2
    assert res["confidence"] == "medium"

def test_match_free_text_empty_input():
    res = match_free_text("", ["sym_bsod_driver"])
    assert res["matched_symptoms"] == []
    assert res["confidence"] == "none"

def test_free_text_does_not_produce_evidence():
    # Ensure no evidence key produced and suggestion only
    res = match_free_text("layar biru", ["sym_bsod_driver"])
    assert "evidence" not in res
    assert "supporting_evidence" not in res
    assert "contradicting_evidence" not in res

def test_suggest_symptoms_combined():
    all_symptoms = {
        "sym_bsod_driver": {"name": "Layar Biru Driver"},
        "sym_bsod_memory_management": {"name": "Memory Management BSOD"}
    }
    res = suggest_symptoms_from_text("layar biru", "MEMORY_MANAGEMENT", all_symptoms)
    assert "sym_bsod_memory_management" in res["suggested_symptom_ids"]
    assert "sym_bsod_driver" in res["suggested_symptom_ids"]
    assert res["bsod_result"]["found"] is True

def test_suggest_symptoms_unrecognized():
    all_symptoms = {"sym_bsod_driver": {"name": "Layar Biru"}}
    res = suggest_symptoms_from_text("mesin kopi rusak", "", all_symptoms)
    assert res["suggested_symptom_ids"] == []
    assert "belum" in res["summary"].lower()

def test_skip_test_does_not_produce_evidence():
    from core.diagnosis import initialize_diagnosis
    from app import get_next_recommended_test_filtered
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    t1 = get_next_recommended_test_filtered(state, [])
    assert t1 is not None
    t2 = get_next_recommended_test_filtered(state, [t1["id"]])
    if t2 is not None:
        assert t2["id"] != t1["id"]
    # Bukti state tidak terisi apapun saat di-skip
    assert len(state.supporting_evidence) == 0
    assert len(state.contradicting_evidence) == 0
    assert len(state.performed_tests) == 0

