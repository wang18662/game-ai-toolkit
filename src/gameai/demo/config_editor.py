from __future__ import annotations

import json
from typing import Dict, List

from ..core.json_defs import BehaviorDef, MapDef


def load_map(path: str) -> MapDef:
    return MapDef.from_file(path)


def save_map(map_def: MapDef, path: str) -> None:
    data = {
        "width": map_def.width,
        "height": map_def.height,
        "cell_size": map_def.cell_size,
        "obstacles": [list(c) for c in map_def.obstacles],
        "spawns": {k: [list(c) for c in v] for k, v in map_def.spawns.items()},
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def load_behavior(path: str) -> BehaviorDef:
    return BehaviorDef.from_file(path)


def save_behavior(behavior: BehaviorDef, path: str) -> None:
    data = {
        "name": behavior.name,
        "fsm": behavior.fsm,
        "bt": behavior.bt,
        "utility": behavior.utility,
        "astar": behavior.astar,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def set_spawn_count(map_def: MapDef, team: str, cells: List[List[int]]) -> MapDef:
    """Return a new MapDef with the given team's spawn cells replaced."""
    spawns: Dict[str, List[List[int]]] = {k: [list(c) for c in v] for k, v in map_def.spawns.items()}
    spawns[team] = [list(c) for c in cells]
    return MapDef(
        width=map_def.width,
        height=map_def.height,
        cell_size=map_def.cell_size,
        obstacles=[list(c) for c in map_def.obstacles],
        spawns=spawns,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python -m gameai.demo.config_editor <map.json>")
        raise SystemExit(1)
    mp = sys.argv[1]
    m = load_map(mp)
    print(f"map {m.width}x{m.height}, obstacles={len(m.obstacles)}, teams={list(m.spawns.keys())}")
