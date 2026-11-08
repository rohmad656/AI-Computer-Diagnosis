"""Implementasi Uniform Cost Search (UCS) untuk diagnosis komputer.

UCS adalah algoritma pencarian berbasis biaya yang selalu mengeksplorasi node
dengan biaya kumulatif terkecil terlebih dahulu. Menggunakan priority queue
(heapq) untuk efisiensi.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Hashable, Iterable, Optional, TypeVar

from core.exceptions import NoPathFoundError

State = TypeVar("State", bound=Hashable)


@dataclass(order=True)
class SearchNode(Generic[State]):
    """Node dalam pencarian UCS.

    Urutan ditentukan oleh total_cost (priority queue min-heap).
    """
    total_cost: float
    state: State = field(compare=False)
    parent: Optional["SearchNode[State]"] = field(default=None, compare=False)
    action: Optional[str] = field(default=None, compare=False)


def reconstruct_path(node: SearchNode[State]) -> list[tuple[str, State]]:
    """Merekonstruksi jalur dari node tujuan ke node awal.

    Returns:
        List of (action, state) dari awal ke tujuan.
    """
    path: list[tuple[str, State]] = []
    current = node
    while current.parent is not None:
        path.append((current.action or "", current.state))
        current = current.parent
    path.append(("", current.state))  # state awal tanpa action
    path.reverse()
    return path


def uniform_cost_search(
    start: State,
    is_goal: Callable[[State], bool],
    expand: Callable[[State], Iterable[tuple[State, float, str]]],
) -> tuple[list[tuple[str, State]], float]:
    """Uniform Cost Search menggunakan priority queue (heapq).

    Args:
        start: State awal pencarian.
        is_goal: Fungsi predicate yang mengembalikan True jika state adalah goal.
        expand: Fungsi yang mengembalikan iterable of (next_state, step_cost, action_name)
                untuk state yang diberikan.

    Returns:
        Tuple berisi (path, total_cost) di mana path adalah list of (action, state)
        dari start ke goal, dan total_cost adalah biaya kumulatif.

    Raises:
        NoPathFoundError: Jika tidak ada jalur ke goal state.
    """
    # Priority queue: (total_cost, tiebreaker, node)
    # tiebreaker digunakan untuk menghindari perbandingan state yang tidak support ordering
    frontier: list[tuple[float, int, SearchNode[State]]] = []
    tiebreaker = 0

    start_node = SearchNode(total_cost=0.0, state=start)
    heapq.heappush(frontier, (0.0, tiebreaker, start_node))
    tiebreaker += 1

    # explored: state -> best_known_cost
    explored: dict[State, float] = {start: 0.0}

    while frontier:
        current_cost, _, current_node = heapq.heappop(frontier)

        # Jika cost node ini lebih besar dari best known, skip (sudah ditemukan jalur lebih baik)
        if current_cost > explored.get(current_node.state, float("inf")):
            continue

        if is_goal(current_node.state):
            path = reconstruct_path(current_node)
            return path, current_node.total_cost

        for next_state, step_cost, action in expand(current_node.state):
            new_cost = current_cost + step_cost

            # Jika next_state belum dieksplor atau ditemukan jalur lebih murah
            if next_state not in explored or new_cost < explored[next_state]:
                explored[next_state] = new_cost
                next_node = SearchNode(
                    total_cost=new_cost,
                    state=next_state,
                    parent=current_node,
                    action=action,
                )
                heapq.heappush(frontier, (new_cost, tiebreaker, next_node))
                tiebreaker += 1

    raise NoPathFoundError("Tidak ditemukan jalur ke goal state.")


def uniform_cost_search_with_limit(
    start: State,
    is_goal: Callable[[State], bool],
    expand: Callable[[State], Iterable[tuple[State, float, str]]],
    max_cost: float = float("inf"),
) -> tuple[list[tuple[str, State]], float] | None:
    """UCS dengan batas biaya maksimum.

    Args:
        start: State awal.
        is_goal: Fungsi goal test.
        expand: Fungsi ekspansi state.
        max_cost: Biaya kumulatif maksimum yang diperbolehkan.

    Returns:
        (path, total_cost) jika ditemukan goal dalam batas biaya, None jika tidak.
    """
    frontier: list[tuple[float, int, SearchNode[State]]] = []
    tiebreaker = 0

    start_node = SearchNode(total_cost=0.0, state=start)
    heapq.heappush(frontier, (0.0, tiebreaker, start_node))
    tiebreaker += 1

    explored: dict[State, float] = {start: 0.0}

    while frontier:
        current_cost, _, current_node = heapq.heappop(frontier)

        if current_cost > explored.get(current_node.state, float("inf")):
            continue

        if current_cost > max_cost:
            continue

        if is_goal(current_node.state):
            path = reconstruct_path(current_node)
            return path, current_node.total_cost

        for next_state, step_cost, action in expand(current_node.state):
            new_cost = current_cost + step_cost

            if new_cost > max_cost:
                continue

            if next_state not in explored or new_cost < explored[next_state]:
                explored[next_state] = new_cost
                next_node = SearchNode(
                    total_cost=new_cost,
                    state=next_state,
                    parent=current_node,
                    action=action,
                )
                heapq.heappush(frontier, (new_cost, tiebreaker, next_node))
                tiebreaker += 1

    return None