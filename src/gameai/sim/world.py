from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from ..core.abc import IWorld, Order, Team
from ..core.agent import Agent
from ..core.eventbus import EventBus
from ..core.json_defs import MapDef
from ..core.vector import Vector2
from .behaviors import make_brain


@dataclass
class AttackEvent:
    attacker_id: int
    target_id: int
    amount: float


@dataclass
class OrderEvent:
    """Published whenever a commander directive changes for a team."""

    team: Team
    order: Order


class World(IWorld):
    """Headless grid world. Engine-agnostic: no pygame, no rendering.

    Coordinates are in grid cells (float for agent positions). The demo/pygame
    layer only reads this world to draw it.
    """

    def __init__(self, map_def: MapDef, seed: int = 12345) -> None:
        self._w = map_def.width
        self._h = map_def.height
        self._obstacles = {(int(c[0]), int(c[1])) for c in map_def.obstacles}
        self._agents: List[Agent] = []
        self._bus = EventBus()
        self._rng = random.Random(seed)
        self._step = 0
        self._orders = {Team.A: Order.NONE, Team.B: Order.NONE}

    # --- IWorld ---
    def get_agents(self) -> List[Agent]:
        return self._agents

    def is_walkable(self, x: float, y: float) -> bool:
        xi, yi = int(round(x)), int(round(y))
        if xi < 0 or yi < 0 or xi >= self._w or yi >= self._h:
            return False
        return (xi, yi) not in self._obstacles

    def emit(self, event) -> None:
        self._bus.publish(event)

    # --- construction helpers ---
    def add_agent(self, agent: Agent) -> None:
        self._agents.append(agent)

    def populate(self, map_def: MapDef, brain_a: str, brain_b: str, jitter: float = 0.4) -> None:
        """Spawn agents from map_def spawns with a small seeded position jitter.

        The jitter makes different ``seed`` values yield different skirmishes,
        so the benchmark's win-rate is a meaningful statistical quantity.
        """
        aid = 0
        for team_name, team, kind in (("A", Team.A, brain_a), ("B", Team.B, brain_b)):
            for cell in map_def.spawns.get(team_name, []):
                jx = self._rng.uniform(-jitter, jitter)
                jy = self._rng.uniform(-jitter, jitter)
                pos = Vector2(float(cell[0]) + jx, float(cell[1]) + jy)
                self.add_agent(Agent(aid, team, pos, make_brain(kind)))
                aid += 1

    def subscribe(self, event_type: type, handler) -> None:
        self._bus.subscribe(event_type, handler)

    # --- commander directives (player / scripted input) ---
    def set_order(self, team: Team, order: Order) -> None:
        """Issue a high-level directive to ``team``.

        Stored on the world and broadcast via the event bus so the demo/UI can
        react (HUD, replays) without the AI knowing who gave the command.
        """
        self._orders[team] = order
        self.emit(OrderEvent(team, order))

    def get_order(self, team: Team) -> Order:
        return self._orders.get(team, Order.NONE)

    # --- queries used by brains ---
    def cell_of(self, pos: Vector2):
        return (int(round(pos.x)), int(round(pos.y)))

    def random_walkable_cell(self):
        for _ in range(200):
            x = self._rng.randint(0, self._w - 1)
            y = self._rng.randint(0, self._h - 1)
            if (x, y) not in self._obstacles:
                return (x, y)
        return (0, 0)

    def nearest_enemy(self, agent: Agent) -> Optional[Agent]:
        best: Optional[Agent] = None
        best_d = float("inf")
        for other in self._agents:
            if other is agent or other.get_team() == agent.get_team() or not other.is_alive():
                continue
            d = agent.get_position().distance(other.get_position())
            if d < best_d:
                best_d = d
                best = other
        return best

    def enemy_centroid(self, agent: Agent) -> Optional[Vector2]:
        """Average position of alive enemies; drives patrol toward the fight."""
        pts = [a.get_position() for a in self._agents
               if a.get_team() != agent.get_team() and a.is_alive()]
        if not pts:
            return None
        return Vector2(
            sum(p.x for p in pts) / len(pts),
            sum(p.y for p in pts) / len(pts),
        )

    def focus_target(self, team: Team) -> Optional[Agent]:
        """Lowest-HP alive enemy of ``team`` -- used by the FOCUS directive so
        the whole team concentrates fire on one victim."""
        best: Optional[Agent] = None
        for other in self._agents:
            if other.get_team() == team or not other.is_alive():
                continue
            if best is None or other.hp() < best.hp():
                best = other
        return best

    def team_centroid(self, team: Team) -> Optional[Vector2]:
        """Average position of alive allies of ``team`` -- the DEFEND/RETREAT
        rally point."""
        pts = [a.get_position() for a in self._agents
               if a.get_team() == team and a.is_alive()]
        if not pts:
            return None
        return Vector2(
            sum(p.x for p in pts) / len(pts),
            sum(p.y for p in pts) / len(pts),
        )

    def attack(self, attacker: Agent, target: Agent) -> None:
        target.take_damage(attacker.damage())
        self.emit(AttackEvent(attacker.get_id(), target.get_id(), attacker.damage()))

    # --- loop ---
    def tick(self, dt: float) -> None:
        for agent in self._agents:
            agent.tick(dt, self)
        self._step += 1

    def alive_count(self, team: Team) -> int:
        return sum(1 for a in self._agents if a.is_alive() and a.get_team() == team)

    def step(self) -> int:
        return self._step

    def width(self) -> int:
        return self._w

    def height(self) -> int:
        return self._h
