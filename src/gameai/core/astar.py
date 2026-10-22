from __future__ import annotations

import heapq
from abc import ABC, abstractmethod
from typing import Callable, List, Tuple

from .vector import Vector2

GridCoord = Tuple[int, int]


class Heuristic(ABC):
    """Cost-to-goal estimate (GoF Strategy pattern)."""

    @abstractmethod
    def __call__(self, a: GridCoord, b: GridCoord) -> float:
        ...


class Manhattan(Heuristic):
    def __call__(self, a: GridCoord, b: GridCoord) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Octile(Heuristic):
    def __call__(self, a: GridCoord, b: GridCoord) -> float:
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return (dx + dy) + (1.41421356 - 2.0) * min(dx, dy)


class Cost(ABC):
    """Per-step traversal cost (GoF Strategy pattern)."""

    @abstractmethod
    def __call__(self, node: GridCoord) -> float:
        ...


class UniformCost(Cost):
    def __call__(self, node: GridCoord) -> float:
        return 1.0


def _reconstruct(came_from: dict, current: GridCoord) -> List[Vector2]:
    path = [Vector2(float(current[0]), float(current[1]))]
    while came_from[current] is not None:
        current = came_from[current]
        path.append(Vector2(float(current[0]), float(current[1])))
    path.reverse()
    return path


def find_path(
    start: GridCoord,
    goal: GridCoord,
    is_walkable: Callable[[int, int], bool],
    heuristic: Heuristic = Octile(),
    cost: Cost = UniformCost(),
    allow_diagonal: bool = True,
) -> List[Vector2]:
    """Grid A* returning a list of Vector2 waypoints (start -> goal).

    Uses deterministic tie-breaking via insertion order; corners are not cut.
    Returns an empty list when no path exists.
    """
    start = (int(round(start[0])), int(round(start[1])))
    goal = (int(round(goal[0])), int(round(goal[1])))
    if not is_walkable(*goal):
        return []

    open_heap: List[Tuple[float, GridCoord]] = [(0.0, start)]
    came_from: dict = {start: None}
    g_score: dict = {start: 0.0}

    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if allow_diagonal:
        dirs = dirs + [(1, 1), (1, -1), (-1, 1), (-1, -1)]

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == goal:
            return _reconstruct(came_from, current)

        for dx, dy in dirs:
            nx, ny = current[0] + dx, current[1] + dy
            if not is_walkable(nx, ny):
                continue
            if dx and dy:
                if not (is_walkable(current[0] + dx, current[1]) and is_walkable(current[0], current[1] + dy)):
                    continue
            step = cost((nx, ny))
            if dx and dy:
                step *= 1.41421356
            tentative = g_score[current] + step
            if (nx, ny) not in g_score or tentative < g_score[(nx, ny)]:
                g_score[(nx, ny)] = tentative
                came_from[(nx, ny)] = current
                f = tentative + heuristic((nx, ny), goal)
                heapq.heappush(open_heap, (f, (nx, ny)))

    return []
