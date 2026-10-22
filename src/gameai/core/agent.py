from __future__ import annotations

from typing import Optional

from .abc import IAgent, Team
from .blackboard import Blackboard
from .steering import obstacle_avoidance, separation
from .vector import Vector2

_EPS = 1e-6


class Agent(IAgent):
    """Concrete, engine-agnostic agent.

    Holds position/velocity/health and delegates decision-making to a pluggable
    ``brain`` (FSM / behavior tree / utility). The brain sets ``velocity`` and
    may call ``world.attack(...)``; the agent integrates motion and clamps to
    walkable cells. No pygame, no rendering -- safe to run headless.
    """

    def __init__(
        self,
        aid: int,
        team: Team,
        pos: Vector2,
        brain,
        max_speed: float = 3.0,
        max_hp: float = 100.0,
        sight_range: float = 6.0,
        attack_range: float = 1.6,
        damage: float = 20.0,
        attack_cooldown: float = 0.5,
        lookahead: float = 1.5,
    ) -> None:
        self._id = aid
        self._team = team
        self._pos = pos
        self._vel = Vector2(0.0, 0.0)
        self._bb = Blackboard()
        self._brain = brain
        self._max_speed = max_speed
        self._hp = max_hp
        self._max_hp = max_hp
        self._sight = sight_range
        self._attack_range = attack_range
        self._damage = damage
        self._cooldown = attack_cooldown
        self._lookahead = lookahead
        self._alive = True
        self._atk_timer = 0.0
        self._state_name = "init"

    # --- IAgent ---
    def get_id(self) -> int:
        return self._id

    def get_team(self) -> Team:
        return self._team

    def get_position(self) -> Vector2:
        return self._pos

    def set_velocity(self, velocity: Vector2) -> None:
        self._vel = velocity

    def get_velocity(self) -> Vector2:
        return self._vel

    def get_blackboard(self):
        return self._bb

    def tick(self, dt: float, world) -> None:
        if not self._alive:
            self._vel = Vector2(0.0, 0.0)
            return
        if self._atk_timer > 0:
            self._atk_timer -= dt
        self._brain.tick(self, world, dt)
        # 个体避障（身体本能层·替代）：brain 只产「意图方向」，前方被挡时用
        # 绕行方向「替代」意图方向，而不是叠加——叠加会合成出对角方向，
        # 恰好切过障碍角被 is_walkable 硬停。绕行是纯轴方向，不会切角。
        avoid = obstacle_avoidance(
            self._pos, self._vel, world.is_walkable, self._lookahead, self._max_speed
        )
        if avoid.length_sq() > _EPS:
            self._vel = avoid
        # 群体分离（身体本能层·叠加）：推开过近的队友，防止单位挤成一团。
        # 与避障不同——避障是「替代」，分离是「叠加」(blended)：分离和意图方向
        # 语义互补，相加后再 cap，而不是「替代」；否则单位一靠近就停下不执行意图。
        # 这里对「禁止矢量叠加」原则做精确化：禁的是语义冲突的叠加（如逃跑+归队），
        # 语义互补的叠加（前进+分离）正是书里 BlendedSteering 的标准做法。
        allies = [
            a.get_position() for a in world.get_agents()
            if a is not self and a.get_team() == self._team and a.is_alive()
        ]
        if allies:
            self._vel = self._vel + separation(
                self._pos, allies, self._max_speed, threshold=1.2, decay_coefficient=2.0
            )
        if self._vel.length() > self._max_speed:
            self._vel = self._vel.normalized() * self._max_speed
        # integrate + clamp to walkable cells
        new_pos = self._pos + self._vel * dt
        if world.is_walkable(new_pos.x, new_pos.y):
            self._pos = new_pos
        else:
            self._vel = Vector2(0.0, 0.0)

    # --- combat / bookkeeping ---
    def take_damage(self, amount: float) -> None:
        if not self._alive:
            return
        self._hp -= amount
        if self._hp <= 0.0:
            self._hp = 0.0
            self._alive = False

    def try_attack(self, world, target) -> bool:
        if self._atk_timer > 0 or not target.is_alive():
            return False
        self._atk_timer = self._cooldown
        world.attack(self, target)
        return True

    def is_alive(self) -> bool:
        return self._alive

    def hp(self) -> float:
        return self._hp

    def max_hp(self) -> float:
        return self._max_hp

    def damage(self) -> float:
        return self._damage

    def max_speed(self) -> float:
        return self._max_speed

    def sight_range(self) -> float:
        return self._sight

    def attack_range(self) -> float:
        return self._attack_range

    def set_state(self, name: str) -> None:
        self._state_name = name

    def get_state(self) -> str:
        return self._state_name
