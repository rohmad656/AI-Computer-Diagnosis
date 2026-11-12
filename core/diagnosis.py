"""Mesin diagnosis berbasis Uniform Cost Search.

Mengelola state diagnosis, integrasi dengan knowledge base, dan eksekusi UCS
untuk menentukan urutan pemeriksaan diagnostik optimal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.exceptions import InvalidStateError, NoPathFoundError
from core.knowledge_base import (
    get_category_by_id,
    get_test_by_id,
    load_diagnostic_tests,
    load_symptoms,
)
from core.ucs import uniform_cost_search


@dataclass(frozen=True)
class DiagnosisState:
    """State dalam pencarian diagnosis.

    Immutable untuk memastikan konsistensi saat digunakan dalam UCS.
    """
    initial_symptoms: frozenset[str]              # ID gejala awal pengguna
    performed_tests: frozenset[str]               # ID test yang sudah dilakukan
    test_results: frozenset[tuple[str, str]]      # (test_id, outcome)
    supporting_evidence: frozenset[str]           # Bukti pendukung (termasuk dari outcome misleading)
    contradicting_evidence: frozenset[str]        # Bukti yang bertentangan
    possible_categories: frozenset[str]           # Kategori yang masih mungkin
    cumulative_cost: float                        # Total biaya kumulatif
    neutral_evidence: frozenset[tuple[str, str]] = frozenset()  # (test_id, outcome) yang tidak meyakinkan
    trusted_support: frozenset[str] = frozenset()     # Bukti yang didukung outcome non-misleading
    misleading_support: frozenset[str] = frozenset()  # Bukti yang hanya didukung outcome misleading

    def with_test_result(self, test_id: str, outcome: str) -> "DiagnosisState":
        """Membuat state baru dengan hasil test ditambahkan.

        Args:
            test_id: ID pemeriksaan yang dilakukan.
            outcome: Hasil pemeriksaan (harus valid untuk test tersebut).

        Returns:
            DiagnosisState baru dengan bukti diperbarui.
        """
        test = get_test_by_id(test_id)
        if test is None:
            raise InvalidStateError(f"Test tidak dikenal: {test_id}")

        if test_id in self.performed_tests:
            raise InvalidStateError(
                f"Test '{test_id}' sudah pernah dilakukan pada sesi diagnosis ini."
            )

        if outcome not in test["possible_outcomes"]:
            raise InvalidStateError(
                f"Outcome '{outcome}' tidak valid untuk test '{test_id}'. "
                f"Valid: {test['possible_outcomes']}"
            )

        outcome_type = get_outcome_type(test, outcome)

        if outcome_type == "uncertain":
            # Outcome tidak meyakinkan: tidak menambah dukungan maupun kontradiksi.
            mapping = {"supports": [], "contradicts": []}
        else:
            mapping = test["evidence_mapping"][outcome]

        new_supporting = set(self.supporting_evidence) | set(mapping["supports"])
        new_contradicting = set(self.contradicting_evidence) | set(mapping["contradicts"])

        # Pisahkan bukti yang boleh dipakai untuk konfirmasi final.
        # Outcome misleading hanya menghasilkan "indikasi awal" sehingga tidak
        # boleh menjadi satu-satunya dasar diagnosis konklusif.
        new_trusted = set(self.trusted_support)
        new_misleading = set(self.misleading_support)
        if outcome_type == "misleading":
            new_misleading |= set(mapping["supports"])
        elif outcome_type != "uncertain":
            new_trusted |= set(mapping["supports"])

        # Kategori tetap mungkin selama belum ada bukti yang bertentangan.
        # Jika seluruh kategori tereliminasi, hasil akhirnya harus tidak konklusif;
        # jangan mengembalikan semua kategori secara diam-diam.
        new_possible = {
            category_id
            for category_id in self.possible_categories
            if not any(
                evidence in new_contradicting
                for evidence in get_category_evidence_keys(category_id)
            )
        }

        new_neutral = set(self.neutral_evidence)
        if outcome_type == "uncertain":
            new_neutral.add((test_id, outcome))

        return DiagnosisState(
            initial_symptoms=self.initial_symptoms,
            performed_tests=self.performed_tests | {test_id},
            test_results=self.test_results | {(test_id, outcome)},
            supporting_evidence=frozenset(new_supporting),
            contradicting_evidence=frozenset(new_contradicting),
            possible_categories=frozenset(new_possible),
            cumulative_cost=self.cumulative_cost + test["cost"],
            neutral_evidence=frozenset(new_neutral),
            trusted_support=frozenset(new_trusted),
            misleading_support=frozenset(new_misleading),
        )

    def get_test_result(self, test_id: str) -> str | None:
        """Mengembalikan outcome test jika sudah dilakukan."""
        for tid, outcome in self.test_results:
            if tid == test_id:
                return outcome
        return None


def get_outcome_type(test: dict[str, Any], outcome: str) -> str:
    """Mengembalikan tipe outcome: normal, abnormal, uncertain, atau misleading.

    Default ke ``abnormal`` untuk kompatibilitas data lama yang belum
    memiliki metadata ``outcome_types``.
    """
    return test.get("outcome_types", {}).get(outcome, "abnormal")


def get_category_evidence_keys(category_id: str) -> list[str]:
    """Mengembalikan kunci bukti yang relevan untuk kategori.

    Kunci bukti adalah string seperti 'driver_issue_confirmed', 'high_temperature_confirmed',
    'disk_issue_confirmed', 'memory_issue_confirmed'.
    """
    mapping = {
        "driver_software": ["driver_issue_confirmed"],
        "overheating": ["high_temperature_confirmed"],
        "storage_disk": ["disk_issue_confirmed"],
        "ram_memory": ["memory_issue_confirmed"],
    }
    return mapping.get(category_id, [])


def is_category_confirmed(state: DiagnosisState, category_id: str) -> bool:
    """Memeriksa apakah kategori memiliki bukti konfirmasi yang cukup.

    Hanya ``trusted_support`` (outcome non-misleading) yang boleh dipakai.
    Bukti dari outcome misleading adalah indikasi awal, bukan konfirmasi.
    Kategori juga tidak dianggap terkonfirmasi jika bukti yang sama tercatat
    sebagai bukti bertentangan.
    """
    required = get_category_evidence_keys(category_id)
    return all(ev in state.trusted_support for ev in required) and not any(
        ev in state.contradicting_evidence for ev in required
    )


def is_category_ruled_out(state: DiagnosisState, category_id: str) -> bool:
    """Memeriksa apakah kategori telah dibuang karena bukti bertentangan."""
    keys = get_category_evidence_keys(category_id)
    return any(ev in state.contradicting_evidence for ev in keys)


ALL_CATEGORY_IDS: tuple[str, ...] = (
    "driver_software",
    "overheating",
    "storage_disk",
    "ram_memory",
)


def is_category_conflicting(state: DiagnosisState, category_id: str) -> bool:
    """True jika evidence kategori yang sama mendukung sekaligus menolak.

    Kondisi ini menandakan data pemeriksaan saling bertentangan (misalnya
    outcome misleading), sehingga kategori tidak boleh langsung dianggap
    terkonfirmasi.
    """
    keys = get_category_evidence_keys(category_id)
    return any(
        ev in state.supporting_evidence and ev in state.contradicting_evidence
        for ev in keys
    )


def get_conflicting_categories(state: DiagnosisState) -> list[str]:
    """Mengembalikan daftar kategori dengan evidence internal yang bertentangan."""
    return [
        category_id
        for category_id in ALL_CATEGORY_IDS
        if is_category_conflicting(state, category_id)
    ]


def is_goal_state(state: DiagnosisState) -> bool:
    """Goal test: ada kategori terkonfirmasi (trusted evidence) tanpa konflik evidence.

    Hanya trusted_support (outcome non-misleading) yang memenuhi syarat konfirmasi.
    Misleading evidence adalah indikasi awal, bukan dasar diagnosis konklusif.
    """
    if get_conflicting_categories(state):
        return False
    return any(is_category_confirmed(state, cat) for cat in state.possible_categories)


def get_available_tests(state: DiagnosisState) -> list[dict[str, Any]]:
    """Mengembalikan daftar test yang belum dilakukan dan relevan dengan kategori yang mungkin."""
    all_tests = load_diagnostic_tests()["tests"]
    available = []
    for test in all_tests:
        if test["id"] not in state.performed_tests:
            # Hanya test untuk kategori yang masih mungkin
            if test["category"] in state.possible_categories:
                available.append(test)
    return available


def expand_state(state: DiagnosisState) -> list[tuple[DiagnosisState, float, str]]:
    """Fungsi ekspansi untuk UCS: generate next states dari state saat ini.

    Returns:
        List of (next_state, step_cost, action_name)
    """
    if is_goal_state(state):
        return []

    available_tests = get_available_tests(state)
    if not available_tests:
        return []

    next_states = []
    for test in available_tests:
        for outcome in test["possible_outcomes"]:
            next_state = state.with_test_result(test["id"], outcome)
            next_states.append((next_state, test["cost"], f"{test['id']}:{outcome}"))

    return next_states


def initialize_diagnosis(
    initial_symptom_ids: list[str],
    custom_symptoms: dict[str, dict[str, Any]] | None = None,
) -> DiagnosisState:
    """Membuat state diagnosis awal dari gejala pengguna.

    Args:
        initial_symptom_ids: List ID gejala yang dilaporkan pengguna.
        custom_symptoms: Dictionary gejala tambahan berbasis sesi pengguna
            (ID -> dict dengan field 'related_categories', 'name', dll).

    Returns:
        DiagnosisState awal dengan kategori yang relevan.
    """
    symptoms_data = load_symptoms()
    valid_symptoms_map = {sym["id"]: sym for sym in symptoms_data["symptoms"]}
    if custom_symptoms:
        valid_symptoms_map.update(custom_symptoms)

    valid_symptom_ids = set(valid_symptoms_map.keys())

    invalid = [sid for sid in initial_symptom_ids if sid not in valid_symptom_ids]
    if invalid:
        raise InvalidStateError(f"Symptom ID tidak valid: {invalid}")

    # Tentukan kategori yang relevan berdasarkan gejala
    relevant_categories = set()
    for sym_id in initial_symptom_ids:
        symptom = valid_symptoms_map[sym_id]
        relevant_categories.update(symptom.get("related_categories", []))

    # Jika tidak ada gejala atau related_categories kosong, semua kategori mungkin
    if not relevant_categories:
        relevant_categories = {"driver_software", "overheating", "storage_disk", "ram_memory"}

    return DiagnosisState(
        initial_symptoms=frozenset(initial_symptom_ids),
        performed_tests=frozenset(),
        test_results=frozenset(),
        supporting_evidence=frozenset(),
        contradicting_evidence=frozenset(),
        possible_categories=frozenset(relevant_categories),
        cumulative_cost=0.0,
    )


def get_next_recommended_test(state: DiagnosisState) -> dict[str, Any] | None:
    """Menjalankan UCS untuk menemukan test berikutnya yang optimal.

    UCS mencari jalur termurah ke goal state. Test pertama dalam jalur
    optimal adalah rekomendasi test berikutnya.

    Args:
        state: State diagnosis saat ini.

    Returns:
        Dictionary test yang direkomendasikan, atau None jika sudah goal
        atau tidak ada test tersedia.
    """
    if is_goal_state(state):
        return None

    available_tests = get_available_tests(state)
    if not available_tests:
        return None

    try:
        path, total_cost = uniform_cost_search(
            start=state,
            is_goal=is_goal_state,
            expand=expand_state,
        )
    except NoPathFoundError:
        # Tidak ada jalur ke goal - kembalikan test termurah sebagai fallback
        if available_tests:
            return min(available_tests, key=lambda t: t["cost"])
        return None

    # Path format: [("", start_state), (action, next_state), ...]
    # Action format: "test_id:outcome"
    if len(path) < 2:
        return None

    first_action = path[1][0]  # action dari start ke state berikutnya
    test_id = first_action.split(":")[0]

    return get_test_by_id(test_id)


def apply_test_result(state: DiagnosisState, test_id: str, outcome: str) -> DiagnosisState:
    """Menerapkan hasil test dan mengembalikan state baru.

    Args:
        state: State diagnosis saat ini.
        test_id: ID test yang dilakukan.
        outcome: Hasil test.

    Returns:
        DiagnosisState baru dengan bukti diperbarui.

    Raises:
        InvalidStateError: Jika test tidak dikenal, outcome tidak valid, atau
            test tersebut sudah pernah dilakukan.
    """
    return state.with_test_result(test_id, outcome)


def get_pending_tests(state: DiagnosisState) -> list[dict[str, Any]]:
    """Mengembalikan pemeriksaan yang belum dilakukan dan masih relevan."""
    return get_available_tests(state)


def get_evidence_sufficiency(state: DiagnosisState) -> str:
    """Menilai kecukupan bukti untuk diagnosis.

    Returns:
        Salah satu dari:
        - ``"sufficient"``: tepat satu kategori terkonfirmasi.
        - ``"conflicting"``: lebih dari satu kategori terkonfirmasi.
        - ``"insufficient"``: tidak ada pemeriksaan relevan yang tersisa.
        - ``"partial"``: bukti belum cukup, tetapi pemeriksaan masih tersedia.
    """
    if get_conflicting_categories(state):
        return "conflicting"

    confirmed = [
        category_id
        for category_id in state.possible_categories
        if is_category_confirmed(state, category_id)
    ]

    if len(confirmed) == 1:
        return "sufficient"
    if len(confirmed) > 1:
        return "conflicting"
    if not get_available_tests(state):
        return "insufficient"
    return "partial"


def evaluate_diagnosis(state: DiagnosisState) -> dict[str, Any]:
    """Evaluasi diagnosis berdasarkan state saat ini.

    Returns:
        Dictionary berisi:
        - status: 'conclusive' | 'inconclusive' | 'in_progress'
        - diagnosed_category: category_id atau None
        - supporting_evidence: list
        - contradicting_evidence: list
        - possible_categories: list
        - recommendations: list (jika conclusive)
        - cumulative_cost: float
    """
    conflicts = get_conflicting_categories(state)
    confirmed_categories = [
        cat for cat in state.possible_categories
        if is_category_confirmed(state, cat)
    ]
    pending_tests = get_pending_tests(state)
    sufficiency = get_evidence_sufficiency(state)

    if not conflicts and len(confirmed_categories) == 1:
        cat_id = confirmed_categories[0]
        category = get_category_by_id(cat_id)
        return {
            "status": "conclusive",
            "diagnosed_category": cat_id,
            "category_name": category["name"] if category else cat_id,
            "supporting_evidence": list(state.supporting_evidence),
            "contradicting_evidence": list(state.contradicting_evidence),
            "neutral_evidence": list(state.neutral_evidence),
            "trusted_support": list(state.trusted_support),
            "misleading_support": list(state.misleading_support),
            "conflicting_categories": conflicts,
            "possible_categories": list(state.possible_categories),
            "pending_tests": pending_tests,
            "evidence_sufficiency": sufficiency,
            "recommendations": category.get("recommendations", []) if category else [],
            "cumulative_cost": state.cumulative_cost,
        }

    # Konflik evidence atau tidak ada pemeriksaan relevan tersisa: inconclusive.
    if conflicts or not pending_tests:
        return {
            "status": "inconclusive",
            "diagnosed_category": None,
            "supporting_evidence": list(state.supporting_evidence),
            "contradicting_evidence": list(state.contradicting_evidence),
            "neutral_evidence": list(state.neutral_evidence),
            "trusted_support": list(state.trusted_support),
            "misleading_support": list(state.misleading_support),
            "conflicting_categories": conflicts,
            "possible_categories": list(state.possible_categories),
            "pending_tests": pending_tests,
            "evidence_sufficiency": sufficiency,
            "recommendations": [
                "Bukti pemeriksaan saling bertentangan atau tidak cukup untuk diagnosis pasti.",
                "Konsultasikan dengan teknisi profesional untuk analisis lebih lanjut."
            ],
            "cumulative_cost": state.cumulative_cost,
        }

    return {
        "status": "in_progress",
        "diagnosed_category": None,
        "supporting_evidence": list(state.supporting_evidence),
        "contradicting_evidence": list(state.contradicting_evidence),
        "neutral_evidence": list(state.neutral_evidence),
        "trusted_support": list(state.trusted_support),
        "misleading_support": list(state.misleading_support),
        "conflicting_categories": conflicts,
        "possible_categories": list(state.possible_categories),
        "pending_tests": pending_tests,
        "evidence_sufficiency": sufficiency,
        "recommendations": [],
        "cumulative_cost": state.cumulative_cost,
    }


def get_diagnosis_summary(state: DiagnosisState) -> dict[str, Any]:
    """Mengembalikan ringkasan lengkap state diagnosis untuk ditampilkan ke UI."""
    evaluation = evaluate_diagnosis(state)
    next_test = get_next_recommended_test(state)

    performed_tests_detail = []
    for test_id, outcome in state.test_results:
        test = get_test_by_id(test_id)
        if test:
            performed_tests_detail.append({
                "test_id": test_id,
                "test_name": test["name"],
                "outcome": outcome,
                "cost": test["cost"],
            })

    return {
        "initial_symptoms": list(state.initial_symptoms),
        "performed_tests": performed_tests_detail,
        "next_recommended_test": next_test,
        "evaluation": evaluation,
    }


class DiagnosisEngine:
    """Wrapper class untuk kompatibilitas dengan kode lama."""

    def __init__(self) -> None:
        self._state: DiagnosisState | None = None

    def initialize(self, symptom_ids: list[str]) -> None:
        self._state = initialize_diagnosis(symptom_ids)

    def get_next_test(self) -> dict[str, Any] | None:
        if self._state is None:
            raise InvalidStateError("Diagnosis belum diinisialisasi. Panggil initialize() dulu.")
        return get_next_recommended_test(self._state)

    def apply_result(self, test_id: str, outcome: str) -> None:
        if self._state is None:
            raise InvalidStateError("Diagnosis belum diinisialisasi.")
        self._state = apply_test_result(self._state, test_id, outcome)

    def evaluate(self) -> dict[str, Any]:
        if self._state is None:
            raise InvalidStateError("Diagnosis belum diinisialisasi.")
        return evaluate_diagnosis(self._state)

    def get_summary(self) -> dict[str, Any]:
        if self._state is None:
            raise InvalidStateError("Diagnosis belum diinisialisasi.")
        return get_diagnosis_summary(self._state)

    @property
    def state(self) -> DiagnosisState | None:
        return self._state