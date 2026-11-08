"""Pengujian implementasi Uniform Cost Search (UCS).

Semua pengujian menggunakan graph kecil yang dapat diverifikasi secara manual.
Format path dari UCS: list of (action, state) dimulai dari ("", start_state).
Contoh: [("", "start"), ("step1", "mid"), ("step2", "goal")]
"""

from __future__ import annotations

import pytest

from core.exceptions import NoPathFoundError
from core.ucs import SearchNode, uniform_cost_search, uniform_cost_search_with_limit


def test_ucs_finds_minimum_cost_path() -> None:
    """UCS harus menemukan jalur dengan biaya kumulatif paling rendah.

    Graph:
        start -> mid  (cost 5)
        start -> mid2 (cost 2)
        mid   -> goal (cost 1) => total 6
        mid2  -> goal (cost 1) => total 3  <-- OPTIMAL
    """

    def is_goal(state: str) -> bool:
        return state == "goal"

    def expand(state: str) -> list[tuple[str, float, str]]:
        if state == "start":
            return [("mid", 5, "a"), ("mid2", 2, "b")]
        elif state == "mid":
            return [("goal", 1, "c")]
        elif state == "mid2":
            return [("goal", 1, "d")]
        return []

    path, total_cost = uniform_cost_search("start", is_goal, expand)
    assert total_cost == 3
    # Path berisi 3 node: ("", "start"), ("b", "mid2"), ("d", "goal")
    assert len(path) == 3
    assert path[0] == ("", "start")
    assert path[1][1] == "mid2"   # node tengah dalam jalur optimal
    assert path[2][1] == "goal"


def test_ucs_avoids_higher_cost_revisit() -> None:
    """UCS harus menghindari revisit state dengan biaya lebih tinggi.

    Graph:
        start -> intermediate (cost 1)
        start -> intermediate (cost 10)   # jalur mahal ke state sama
        intermediate -> goal  (cost 1)
    Total optimal: 1 + 1 = 2
    """

    def is_goal(state: str) -> bool:
        return state == "goal"

    def expand(state: str) -> list[tuple[str, float, str]]:
        if state == "start":
            return [("intermediate", 1, "low_cost"), ("intermediate", 10, "high_cost")]
        return [("goal", 1, "to_goal")]

    path, total_cost = uniform_cost_search("start", is_goal, expand)
    assert total_cost == 2


def test_ucs_returns_path_structure() -> None:
    """UCS harus merekonstruksi jalur dengan benar.

    Graph:
        start -> mid  (cost 3)
        mid   -> goal (cost 2)
    Total: 5. Path harus berisi 3 node.
    """

    def is_goal(state: str) -> bool:
        return state == "goal"

    def expand(state: str) -> list[tuple[str, float, str]]:
        if state == "start":
            return [("mid", 3, "step1")]
        elif state == "mid":
            return [("goal", 2, "step2")]
        return []

    path, total_cost = uniform_cost_search("start", is_goal, expand)
    assert total_cost == 5
    # Path berisi 3 node: start, mid, goal
    assert len(path) == 3
    assert path[0] == ("", "start")
    assert path[1] == ("step1", "mid")
    assert path[2] == ("step2", "goal")


def test_ucs_handles_unreachable_goal() -> None:
    """UCS harus mengangkat NoPathFoundError ketika goal tidak ditemukan."""

    def is_goal(state: str) -> bool:
        return state == "goal"

    def expand(state: str) -> list[tuple[str, float, str]]:
        # Graph tidak terhubung ke goal — terjebak ke "other" selamanya
        if state == "start":
            return [("other", 1, "away")]
        return []

    with pytest.raises(NoPathFoundError):
        uniform_cost_search("start", is_goal, expand)


def test_ucs_with_limit_excludes_expensive_goal() -> None:
    """UCS dengan batas biaya tidak boleh mengembalikan jalur di atas batas.

    Graph:
        start -> mid  (cost 5)
        mid   -> goal (cost 5) => total 10
    Dengan max_cost=8, goal tidak ditemukan.
    """

    def is_goal(state: str) -> bool:
        return state == "goal"

    def expand(state: str) -> list[tuple[str, float, str]]:
        if state == "start":
            return [("mid", 5, "step1")]
        elif state == "mid":
            return [("goal", 5, "step2")]  # total 10
        return []

    result = uniform_cost_search_with_limit("start", is_goal, expand, max_cost=8)
    assert result is None


def test_ucs_with_limit_finds_goal_within_limit() -> None:
    """UCS dengan batas biaya harus menemukan goal jika total_cost <= max_cost."""

    def is_goal(state: str) -> bool:
        return state == "goal"

    def expand(state: str) -> list[tuple[str, float, str]]:
        if state == "start":
            return [("mid", 2, "step1")]
        elif state == "mid":
            return [("goal", 3, "step2")]  # total 5
        return []

    result = uniform_cost_search_with_limit("start", is_goal, expand, max_cost=10)
    assert result is not None
    path, total_cost = result
    assert total_cost == 5


def test_searchnode_comparison() -> None:
    """SearchNode harus berkomparasi berdasarkan total_cost."""
    n1 = SearchNode(total_cost=5, state="a")
    n2 = SearchNode(total_cost=3, state="b")
    n3 = SearchNode(total_cost=5, state="c")

    assert n2 < n1
    assert n2 < n3
    assert n1.total_cost == n3.total_cost == 5


def test_ucs_explores_lower_cost_first() -> None:
    """UCS harus memilih jalur berbiaya total terendah.

    Graph:
        start -> A (cost 1)  -> goal (cost 100) => total 101
        start -> B (cost 10) -> goal (cost 1)   => total 11  <-- OPTIMAL
    """

    def is_goal(state: str) -> bool:
        return state == "goal"

    def expand(state: str) -> list[tuple[str, float, str]]:
        if state == "start":
            return [("A", 1, "to_A"), ("B", 10, "to_B")]
        elif state == "A":
            return [("goal", 100, "to_goal_A")]
        elif state == "B":
            return [("goal", 1, "to_goal_B")]
        return []

    path, total_cost = uniform_cost_search("start", is_goal, expand)
    assert total_cost == 11
    # path[0] = ("", "start"), path[1] = ("to_B", "B"), path[2] = ("to_goal_B", "goal")
    assert path[1][1] == "B"


def test_ucs_with_duplicate_states_different_cost() -> None:
    """UCS harus memilih jalur termurah saat state yang sama bisa dicapai dengan biaya berbeda.

    Graph:
        start -> mid (cost 2) => mid -> goal (cost 1) => total 3  <-- OPTIMAL
        start -> mid (cost 5) => mid -> goal (cost 1) => total 6
    """

    def is_goal(state: str) -> bool:
        return state == "goal2"

    def expand(state: str) -> list[tuple[str, float, str]]:
        if state == "start":
            return [("mid", 2, "cheap"), ("mid", 5, "expensive")]
        elif state == "mid":
            return [("goal2", 1, "to_goal")]
        return []

    path, total_cost = uniform_cost_search("start", is_goal, expand)
    assert total_cost == 3
    # Path berisi 3 node: start, mid, goal2
    assert len(path) == 3
    assert path[0][1] == "start"
    assert path[1][1] == "mid"
    assert path[2][1] == "goal2"