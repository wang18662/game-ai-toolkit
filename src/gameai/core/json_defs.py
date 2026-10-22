from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MapDef:
    """Neutral grid-map definition shared by the Python core and the C++ port."""

    width: int
    height: int
    cell_size: float = 1.0
    obstacles: List[List[int]] = field(default_factory=list)
    spawns: Dict[str, List[List[int]]] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str) -> "MapDef":
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(
            width=int(data["width"]),
            height=int(data["height"]),
            cell_size=float(data.get("cell_size", 1.0)),
            obstacles=[list(c) for c in data.get("obstacles", [])],
            spawns={k: [list(c) for c in v] for k, v in data.get("spawns", {}).items()},
        )


@dataclass
class BehaviorDef:
    """Neutral behavior definition; same schema is consumed by both languages.

    Only the `name` is required in M1; fsm/bt/utility/astar blocks are filled
    in M2 and mirrored by the C++ port in M4.
    """

    name: str = "untitled"
    fsm: Dict = field(default_factory=dict)
    bt: Dict = field(default_factory=dict)
    utility: Dict = field(default_factory=dict)
    astar: Dict = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str) -> "BehaviorDef":
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(
            name=data.get("name", "untitled"),
            fsm=data.get("fsm", {}),
            bt=data.get("bt", {}),
            utility=data.get("utility", {}),
            astar=data.get("astar", {}),
        )
