"""Cross-language parity: prove the Python core and the C++17 thin port
produce byte-identical results on the *same* inputs / shared JSON.

The C++ side exposes a small ``parity_runner`` executable (cpp/src/parity_runner.cpp)
that consumes the same map/behavior JSON the Python core uses and prints a
normalized result. This test locates that executable (built by the CI ``cpp``
job) and asserts Python and C++ agree.

If the executable has not been built, every test is skipped — so the Python
CI job stays green, while the C++ CI job (which builds first) actually runs
the comparison. This is the single source of truth for cross-language parity.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import pytest

from gameai.core.astar import find_path, Octile, UniformCost
from gameai.core.utility import (
    Consideration,
    CurveType,
    Option,
    decide,
)
from gameai.core.fsm import FSM, State


# ---------------------------------------------------------------------------
# Locate the C++ parity_runner executable (built by the cpp CI job).
# ---------------------------------------------------------------------------
def _find_exe() -> str | None:
    env = os.environ.get("PARITY_EXE")
    if env and os.path.exists(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    candidates = [
        os.path.join(repo, "cpp", "build", "parity_runner"),
        os.path.join(repo, "cpp", "build", "parity_runner.exe"),
        os.path.join(repo, "cpp", "build", "Release", "parity_runner.exe"),
        os.path.join(repo, "cpp", "build", "Debug", "parity_runner.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


EXE = _find_exe()
pytestmark = pytest.mark.skipif(EXE is None, reason="parity_runner not built (run the cpp CI job)")


def _run(args: list[str]) -> str:
    out = subprocess.run([EXE, *args], capture_output=True, text=True, check=True)
    return out.stdout.strip()


# ---------------------------------------------------------------------------
# A* parity — same shared JSON map, same path formatting.
# ---------------------------------------------------------------------------
def _write_map(path: str, width: int, height: int, obstacles: list[list[int]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"width": width, "height": height, "obstacles": obstacles}, f)


def _py_path_string(start, goal, walkable, diag) -> str:
    path = find_path(start, goal, walkable, Octile(), UniformCost(), diag)
    if not path:
        return "NONE"
    return ";".join(f"{round(v.x):d},{round(v.y):d}" for v in path)


def _map_walkable(width, height, obstacles):
    obs = set((o[0], o[1]) for o in obstacles)
    def fn(x, y):
        if x < 0 or y < 0 or x >= width or y >= height:
            return False
        return (x, y) not in obs
    return fn


def test_astar_open_diagonal_parity():
    with tempfile.TemporaryDirectory() as d:
        mp = os.path.join(d, "m.json")
        _write_map(mp, 8, 8, [])
        walkable = _map_walkable(8, 8, [])
        expected = _py_path_string((0, 0), (5, 5), walkable, True)
        got = _run(["astar", mp, "0", "0", "5", "5", "1"])
        assert got == expected
        assert expected == "0,0;1,1;2,2;3,3;4,4;5,5"


def test_astar_detour_parity():
    # vertical wall at x=3 for rows 0..6, gap at row 7 — forces a unique detour.
    obstacles = [[3, y] for y in range(7)]
    with tempfile.TemporaryDirectory() as d:
        mp = os.path.join(d, "m.json")
        _write_map(mp, 8, 8, obstacles)
        walkable = _map_walkable(8, 8, obstacles)
        expected = _py_path_string((0, 0), (7, 0), walkable, True)
        got = _run(["astar", mp, "0", "0", "7", "0", "1"])
        assert got == expected
        assert got != "NONE"


def test_astar_unreachable_parity():
    obstacles = [[3, y] for y in range(8)]  # full wall, no gap
    with tempfile.TemporaryDirectory() as d:
        mp = os.path.join(d, "m.json")
        _write_map(mp, 8, 8, obstacles)
        walkable = _map_walkable(8, 8, obstacles)
        expected = _py_path_string((0, 0), (7, 0), walkable, True)
        got = _run(["astar", mp, "0", "0", "7", "0", "1"])
        assert got == expected == "NONE"


# ---------------------------------------------------------------------------
# Utility parity — mirror the exact 3-option skirmish brain used by the C++ runner.
# ---------------------------------------------------------------------------
def _py_enemy_closeness(a, w):
    if not w.enemy_exists:
        return 0.0
    return max(0.0, a.sight_range - w.enemy_distance)


def _py_in_attack_range(a, w):
    if not w.enemy_exists:
        return 0.0
    return 1.0 if w.enemy_distance <= a.attack_range else 0.0


def _py_retreat_score(a, w):
    low = 1.0 - a.hp / a.max_hp
    threat = 0.6 if (w.enemy_exists and w.enemy_distance <= a.sight_range) else 0.0
    return max(low, threat)


class _V:
    def __init__(self, hp, max_hp, sight, attack):
        self.hp = hp
        self.max_hp = max_hp
        self.sight_range = sight
        self.attack_range = attack
        self.enemy_exists = False
        self.enemy_distance = 0.0


def _py_decide_name(hp, max_hp, sight, attack, exists, dist) -> str:
    a = _V(hp, max_hp, sight, attack)
    a.enemy_exists = exists
    a.enemy_distance = dist
    options = [
        Option("Advance", [Consideration(_py_enemy_closeness, CurveType.LINEAR, 0.0, 8.0, 1.0)]),
        Option("Attack", [Consideration(_py_in_attack_range, CurveType.LINEAR, 0.0, 1.0, 1.5)]),
        Option("Retreat", [Consideration(_py_retreat_score, CurveType.LINEAR, 0.0, 1.0, 1.2)]),
    ]
    chosen, _ = decide(options, a, a)
    return chosen.name


def test_utility_in_range_picks_attack():
    expected = _py_decide_name(100, 100, 6, 1.6, True, 1.0)
    got = _run(["utility", "100", "100", "6", "1.6", "1", "1.0"])
    assert got == expected == "Attack"


def test_utility_low_hp_picks_retreat():
    expected = _py_decide_name(10, 100, 6, 1.6, True, 5.0)
    got = _run(["utility", "10", "100", "6", "1.6", "1", "5.0"])
    assert got == expected == "Retreat"


def test_utility_no_enemy_picks_advance():
    expected = _py_decide_name(100, 100, 6, 1.6, False, 0.0)
    got = _run(["utility", "100", "100", "6", "1.6", "0", "0.0"])
    assert got == expected == "Advance"


# ---------------------------------------------------------------------------
# FSM parity — same 4 skirmish states, same transition table, start in patrol.
# ---------------------------------------------------------------------------
class _VAgent:
    def __init__(self, hp, max_hp, sight, attack):
        self._hp = hp
        self._max_hp = max_hp
        self._sight = sight
        self._attack = attack

    def hp(self):
        return self._hp

    def max_hp(self):
        return self._max_hp

    def sight_range(self):
        return self._sight

    def attack_range(self):
        return self._attack


class _VWorld:
    def __init__(self, exists, dist):
        self.enemy_exists = exists
        self.enemy_distance = dist


class _Patrol(State):
    def on_enter(self, a, w):
        pass
    def on_exit(self, a, w):
        pass
    def update(self, a, w, dt):
        if w.enemy_exists and w.enemy_distance <= a.sight_range():
            return "enemy_spotted"
        return None


class _Chase(State):
    def on_enter(self, a, w):
        pass
    def on_exit(self, a, w):
        pass
    def update(self, a, w, dt):
        if not w.enemy_exists:
            return "enemy_lost"
        if w.enemy_distance <= a.attack_range():
            return "in_range"
        return None


class _Attack(State):
    def on_enter(self, a, w):
        pass
    def on_exit(self, a, w):
        pass
    def update(self, a, w, dt):
        if not w.enemy_exists:
            return "enemy_lost"
        if w.enemy_distance > a.attack_range():
            return "out_of_range"
        if a.hp() < 0.3 * a.max_hp():
            return "low_hp"
        return None


class _Flee(State):
    def on_enter(self, a, w):
        pass
    def on_exit(self, a, w):
        pass
    def update(self, a, w, dt):
        if not w.enemy_exists:
            return "safe"
        if w.enemy_distance > a.sight_range():
            return "safe"
        return None


def _py_fsm_current(hp, max_hp, sight, attack, exists, dist) -> str:
    states = {
        "patrol": _Patrol(),
        "chase": _Chase(),
        "attack": _Attack(),
        "flee": _Flee(),
    }
    transitions = {
        "patrol": {"enemy_spotted": "chase"},
        "chase": {"in_range": "attack", "enemy_lost": "patrol"},
        "attack": {"out_of_range": "chase", "low_hp": "flee", "enemy_lost": "patrol"},
        "flee": {"safe": "patrol"},
    }
    fsm = FSM(states, transitions, "patrol")
    fsm.update(_VAgent(hp, max_hp, sight, attack), _VWorld(exists, dist), 0.0)
    return fsm.current


def test_fsm_enemy_in_sight_patrol_to_chase():
    expected = _py_fsm_current(100, 100, 6, 1.6, True, 2.0)
    got = _run(["fsm", "100", "100", "6", "1.6", "1", "2.0"])
    assert got == expected == "chase"


def test_fsm_no_enemy_stays_patrol():
    expected = _py_fsm_current(100, 100, 6, 1.6, False, 0.0)
    got = _run(["fsm", "100", "100", "6", "1.6", "0", "0.0"])
    assert got == expected == "patrol"


def test_fsm_enemy_beyond_sight_stays_patrol():
    expected = _py_fsm_current(100, 100, 6, 1.6, True, 20.0)
    got = _run(["fsm", "100", "100", "6", "1.6", "1", "20.0"])
    assert got == expected == "patrol"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
