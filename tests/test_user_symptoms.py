"""Unit test untuk fitur Gejala Tambahan (User-Defined Symptom).

Menguji bahwa laporan pengguna dapat dirumuskan menjadi gejala terstruktur,
dikonfirmasi, dimasukkan ke sesi diagnosis, dan diproses oleh UCS tanpa
memalsukan bukti diagnosis.

Seluruh pengujian bersifat deterministik dan tidak bergantung pada ML/API.
"""

from __future__ import annotations

from core.symptom_matcher import (
    create_user_defined_symptom,
    match_bsod_code,
    suggest_symptoms_from_text,
)
from core.diagnosis import (
    apply_test_result,
    evaluate_diagnosis,
    get_available_tests,
    get_next_recommended_test,
    initialize_diagnosis,
)

import app as app_module


# 1. Gejala tambahan berhasil dibuat
def test_user_symptom_created_successfully() -> None:
    res = create_user_defined_symptom(
        "Laptop sering bluescreen DPC_WATCHDOG_VIOLATION tiba-tiba restart",
        "DPC_WATCHDOG_VIOLATION",
    )
    assert res["success"] is True
    sym = res["symptom"]
    assert sym is not None
    assert sym["source"] == "user_report"
    assert sym["error_code"] == "DPC_WATCHDOG_VIOLATION"
    assert sym["confirmed"] is False
    assert sym["related_categories"]
    assert sym["candidate_tests"]
    assert sym["uncertainty_notes"]


# 2. Gejala tambahan memiliki ID sesi yang stabil
def test_user_symptom_stable_id() -> None:
    a = create_user_defined_symptom("layar biru saat main game", "DPC_WATCHDOG_VIOLATION", "s1")
    b = create_user_defined_symptom("layar biru saat main game", "DPC_WATCHDOG_VIOLATION", "s1")
    assert a["symptom"]["id"] == b["symptom"]["id"]
    # ID berbeda untuk laporan berbeda
    c = create_user_defined_symptom("hard disk lambat", "DPC_WATCHDOG_VIOLATION", "s1")
    assert a["symptom"]["id"] != c["symptom"]["id"]


# 3. Gejala tambahan dapat dikonfirmasi
def test_user_symptom_can_be_confirmed() -> None:
    res = create_user_defined_symptom("komputer panas dan mati mendadak", "")
    sym = res["symptom"]
    assert sym["confirmed"] is False
    sym["confirmed"] = True
    assert sym["confirmed"] is True


# 4. Gejala tambahan masuk ke diagnosis state
def test_user_symptom_enters_diagnosis_state() -> None:
    res = create_user_defined_symptom("layar biru BSOD driver crash", "SYSTEM_SERVICE_EXCEPTION")
    sym = res["symptom"]
    state = initialize_diagnosis([sym["id"]], custom_symptoms={sym["id"]: sym})
    assert sym["id"] in state.initial_symptoms
    assert "driver_software" in state.possible_categories


# 5. Gejala tambahan dapat menghasilkan rekomendasi UCS
def test_user_symptom_generates_ucs_recommendation() -> None:
    res = create_user_defined_symptom("driver error di device manager", "")
    sym = res["symptom"]
    state = initialize_diagnosis([sym["id"]], custom_symptoms={sym["id"]: sym})
    nxt = get_next_recommended_test(state)
    assert nxt is not None
    assert nxt["category"] in state.possible_categories


# 6. DPC_WATCHDOG_VIOLATION -> kandidat driver dan storage
def test_dpc_watchdog_candidates_driver_and_storage() -> None:
    res = match_bsod_code("DPC_WATCHDOG_VIOLATION")
    assert res["found"] is True
    assert "driver_software" in res["candidate_categories"]
    assert "storage_disk" in res["candidate_categories"]

    # Gejala tambahan mewarisi kedua kategori tersebut
    usr = create_user_defined_symptom("laptop bluescreen tiba-tiba restart", "DPC_WATCHDOG_VIOLATION")
    assert "driver_software" in usr["symptom"]["related_categories"]
    assert "storage_disk" in usr["symptom"]["related_categories"]


# 7. Kode BSOD tidak otomatis menjadi evidence
def test_bsod_does_not_produce_evidence() -> None:
    res = create_user_defined_symptom("layar biru", "DPC_WATCHDOG_VIOLATION")
    sym = res["symptom"]
    state = initialize_diagnosis([sym["id"]], custom_symptoms={sym["id"]: sym})
    assert len(state.supporting_evidence) == 0
    assert len(state.contradicting_evidence) == 0
    # Output matcher tidak mengandung field evidence
    bsod = match_bsod_code("DPC_WATCHDOG_VIOLATION")
    assert "supporting_evidence" not in bsod
    assert "contradicting_evidence" not in bsod


# 8. Kode tidak dikenal ditangani dengan aman
def test_unknown_bsod_handled_safely() -> None:
    res = match_bsod_code("SUPER_FAKE_CODE_XYZ")
    assert res["found"] is False
    assert res["candidate_symptoms"] == []
    assert res["candidate_categories"] == []


# 9. Gejala tanpa pemeriksaan relevan tidak menghasilkan diagnosis palsu
def test_symptom_without_relevant_tests_no_fake_diagnosis() -> None:
    # Deskripsi di luar domain 4 kategori teknis
    res = create_user_defined_symptom("mesin kopi tidak mau menyala", "")
    assert res["success"] is False
    assert res["symptom"] is None
    assert "aturan pemeriksaan" in res["message"]

    # Bahkan bila dipaksa menjadi custom symptom tanpa kategori,
    # state harus inkonklusif dan tanpa bukti.
    fake_sym = {
        "id": "sym_user_test_nocat",
        "name": "Tanpa kategori",
        "description": "test",
        "source": "user_report",
        "related_categories": [],
        "candidate_tests": [],
    }
    state = initialize_diagnosis([fake_sym["id"]], custom_symptoms={fake_sym["id"]: fake_sym})
    # Tanpa kategori spesifik -> semua kategori mungkin, tetapi tidak ada bukti
    assert len(state.supporting_evidence) == 0
    evaluation = evaluate_diagnosis(state)
    assert evaluation["status"] != "conclusive"
    assert evaluation["diagnosed_category"] is None


# 10. Gejala tambahan tidak bocor antar sesi
def test_user_symptoms_do_not_leak_between_sessions() -> None:
    session_a: dict[str, dict] = {}
    session_b: dict[str, dict] = {}

    res_a = create_user_defined_symptom("driver error laptop", "", "sessA")
    res_b = create_user_defined_symptom("hard disk lambat", "", "sessB")

    session_a[res_a["symptom"]["id"]] = res_a["symptom"]
    session_b[res_b["symptom"]["id"]] = res_b["symptom"]

    assert res_a["symptom"]["id"] not in session_b
    assert res_b["symptom"]["id"] not in session_a


# 11. Reset menghapus gejala tambahan
def test_reset_removes_user_symptoms(monkeypatch) -> None:
    class FakeState:
        def __init__(self) -> None:
            object.__setattr__(self, "_data", {})

        def __getattr__(self, name):
            data = object.__getattribute__(self, "_data")
            if name in data:
                return data[name]
            raise AttributeError(name)

        def __setattr__(self, name, value):
            object.__getattribute__(self, "_data")[name] = value

        def get(self, name, default=None):
            return object.__getattribute__(self, "_data").get(name, default)

        def __contains__(self, name):
            return name in object.__getattribute__(self, "_data")

        def __getitem__(self, name):
            return object.__getattribute__(self, "_data")[name]

        def __setitem__(self, name, value):
            object.__getattribute__(self, "_data")[name] = value

        def __delitem__(self, name):
            del object.__getattribute__(self, "_data")[name]

        def keys(self):
            return object.__getattribute__(self, "_data").keys()

    fake = FakeState()
    fake.diag_state = "dummy"
    fake.diag_symptoms = ("a",)
    fake.diag_log = [{"x": 1}]
    fake.confirm_reset = True
    fake.skipped_tests = ["t"]
    fake.text_analysis = {"x": 1}
    fake.custom_symptoms = {"sym_user_x": {"id": "sym_user_x"}}
    fake.pending_custom_symptom = {"success": True}

    monkeypatch.setattr(app_module.st, "session_state", fake, raising=False)
    app_module.reset_diagnosis_session()

    assert fake.diag_state is None
    assert fake.custom_symptoms == {}
    assert fake.pending_custom_symptom is None
    assert fake.skipped_tests == []
    assert fake.text_analysis is None


# 12. Kontradiksi tetap mengeliminasi kategori secara benar
def test_contradiction_still_eliminates_category() -> None:
    res = create_user_defined_symptom("hard disk lambat dan sering freeze", "")
    sym = res["symptom"]
    assert "storage_disk" in sym["related_categories"]
    state = initialize_diagnosis([sym["id"]], custom_symptoms={sym["id"]: sym})
    assert "storage_disk" in state.possible_categories

    # SMART disk sehat -> kontradiksi disk_issue_confirmed -> kategori storage tereliminasi
    new_state = apply_test_result(state, "test_smart_disk", "healthy")
    assert "storage_disk" not in new_state.possible_categories
    assert "disk_issue_confirmed" in new_state.contradicting_evidence


# 13. Gejala bawaan yang sudah ada tetap berfungsi
def test_builtin_symptoms_still_work() -> None:
    state = initialize_diagnosis(["sym_shutdown_thermal"])
    assert state.possible_categories == frozenset({"overheating"})
    nxt = get_next_recommended_test(state)
    assert nxt is not None
    assert nxt["category"] == "overheating"
    assert get_available_tests(state)
