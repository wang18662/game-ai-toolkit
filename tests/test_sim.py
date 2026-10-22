from gameai.core.abc import Team
from gameai.core.agent import Agent
from gameai.core.json_defs import MapDef
from gameai.core.vector import Vector2
from gameai.sim.behaviors import make_brain
from gameai.sim.world import World


def _tiny_world(brain_a="fsm", brain_b="fsm", seed=1):
    mp = MapDef(width=12, height=12, obstacles=[], spawns={})
    world = World(mp, seed=seed)
    world.add_agent(Agent(0, Team.A, Vector2(2, 6), make_brain(brain_a)))
    world.add_agent(Agent(1, Team.B, Vector2(9, 6), make_brain(brain_b)))
    return world


def test_agents_engage_and_damage():
    world = _tiny_world()
    a, b = world.get_agents()
    assert a.is_alive() and b.is_alive()
    for _ in range(400):  # 40s sim
        world.tick(0.1)
        if not (a.is_alive() and b.is_alive()):
            break
    # at least one took damage (someone engaged)
    assert a.hp() < a.max_hp() or b.hp() < b.max_hp()


def test_full_skirmish_engages_and_stays_in_bounds():
    mp = MapDef.from_file("tests/fixtures/maps/skirmish.json")
    world = World(mp, seed=3)
    world.populate(mp, "fsm", "utility")
    start_a, start_b = world.alive_count(Team.A), world.alive_count(Team.B)
    steps = 0
    for _ in range(3000):
        if world.alive_count(Team.A) == 0 or world.alive_count(Team.B) == 0:
            break
        world.tick(0.1)
        steps += 1
    # combat happened: at least one side took losses
    assert world.alive_count(Team.A) < start_a or world.alive_count(Team.B) < start_b
    # any survivor is on a walkable cell
    for ag in world.get_agents():
        if ag.is_alive():
            assert world.is_walkable(ag.get_position().x, ag.get_position().y)


def test_determinism_supports_parity():
    def run_once():
        mp = MapDef.from_file("tests/fixtures/maps/skirmish.json")
        world = World(mp, seed=42)
        world.populate(mp, "fsm", "bt")
        for _ in range(3000):
            if world.alive_count(Team.A) == 0 or world.alive_count(Team.B) == 0:
                break
            world.tick(0.1)
        return (world.alive_count(Team.A), world.alive_count(Team.B))

    r1 = run_once()
    r2 = run_once()
    assert r1 == r2  # same seed -> identical outcome (basis for C++ parity)
