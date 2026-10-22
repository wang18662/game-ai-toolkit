import os

from gameai.core.json_defs import BehaviorDef, MapDef

_FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_mapdef_loads():
    m = MapDef.from_file(os.path.join(_FIXTURES, "maps", "sample.json"))
    assert m.width == 32
    assert m.height == 32
    assert m.cell_size == 1.0
    assert [2, 2] in m.obstacles
    assert m.spawns["teamA"]


def test_behaviordef_loads():
    b = BehaviorDef.from_file(os.path.join(_FIXTURES, "behaviors", "sample.json"))
    assert b.name == "skirmish"
    assert b.astar.get("heuristic") == "octile"
