from __future__ import annotations

from ..core.abc import Order, Team
from ..core.astar import find_path
from ..core.behavior_tree import Action, Condition, Node, Selector, Sequence, Status
from ..core.fsm import FSM, State
from ..core.steering import arrive, evade, pursue, wander
from ..core.utility import Consideration, CurveType, Option, decide
from ..core.vector import Vector2

_EPS = 1e-6


# --------------------------------------------------------------------------
# Shared action helpers (used by FSM states, the utility brain and the BT).
# Each sets the agent's velocity and/or performs an attack. None import pygame.
#
# Every helper consults ``world.get_order(team)`` -- this single injection
# point lets a player/scripted commander bias all three AI paradigms at once.
# --------------------------------------------------------------------------
def _order(agent, world) -> Order:
    return world.get_order(agent.get_team())


def _target(agent, world):
    """Enemy to act on: FOCUS picks the lowest-HP enemy, else nearest."""
    if _order(agent, world) is Order.FOCUS:
        return world.focus_target(agent.get_team())
    return world.nearest_enemy(agent)


def _hold(agent, world) -> None:
    """Rally on the team centroid (RETREAT regroup)."""
    cc = world.team_centroid(agent.get_team())
    if cc is None:
        _patrol(agent, world, 0.0)
    else:
        agent.set_velocity(arrive(agent.get_position(), cc, agent.max_speed(), 2.5))


def _patrol(agent, world, dt: float) -> None:
    # Skirmish default: push toward the enemy mass so the two sides actually meet.
    # Fall back to random wander only when no enemies remain.
    # RETREAT turtles back to the rally point; DEFEND still advances to make
    # contact (it only "holds the line" once enemies are close -- see _chase).
    order = _order(agent, world)
    if order is Order.RETREAT:
        _hold(agent, world)
        return
    cc = world.enemy_centroid(agent)
    if cc is None:
        # 无敌人：wander 游荡（前方圆随机点），替代「随机 waypoint + 直线 arrive」。
        # heading 用当前速度方向；静止时给一个初始朝向，否则无从游荡。
        heading = agent.get_velocity().normalized()
        if heading.length_sq() < _EPS:
            heading = Vector2(1.0, 0.0)
        agent.set_velocity(wander(
            agent.get_position(), heading, agent.max_speed(),
            wander_offset=2.0, wander_radius=1.5, wander_rate=0.8,
        ))
    else:
        agent.set_velocity(arrive(agent.get_position(), cc, agent.max_speed(), 3.0))


def _move_toward(agent, world, target_cell) -> None:
    start = world.cell_of(agent.get_position())
    path = find_path(start, target_cell, world.is_walkable)
    if path and len(path) > 1:
        agent.set_velocity(arrive(agent.get_position(), path[1], agent.max_speed(), 1.5))
    else:
        e = world.nearest_enemy(agent)
        if e:
            agent.set_velocity(pursue(
                agent.get_position(), agent.get_velocity(),
                e.get_position(), e.get_velocity(),
                agent.max_speed(), 1.0,
            ))


def _chase(agent, world) -> None:
    order = _order(agent, world)
    if order is Order.RETREAT:
        _flee(agent, world)
        return
    e = _target(agent, world)
    if e is None:
        _patrol(agent, world, 0.0)
        return
    d = agent.get_position().distance(e.get_position())
    if order is Order.DEFEND:
        # hold the line: engage (and close the last gap) once the enemy is
        # visible, otherwise keep advancing to re-establish contact instead of
        # freezing -- a frozen defender just stalls the match.
        if d <= agent.sight_range() * 0.9:
            _move_toward(agent, world, world.cell_of(e.get_position()))
        else:
            _patrol(agent, world, 0.0)
        return
    if d <= agent.attack_range():
        agent.set_velocity(Vector2(0.0, 0.0))
        return
    if order is Order.ATTACK:
        # aggressive: pursue 预判敌人走位（比 seek 直线追更准），全速压上
        agent.set_velocity(pursue(
            agent.get_position(), agent.get_velocity(),
            e.get_position(), e.get_velocity(),
            agent.max_speed(), 1.0,
        ))
        return
    _move_toward(agent, world, world.cell_of(e.get_position()))


def _attack(agent, world) -> None:
    order = _order(agent, world)
    if order is Order.RETREAT:
        # hit-and-run: shoot when the enemy is in range, otherwise kite away
        e = _target(agent, world)
        if e is None:
            return
        if agent.get_position().distance(e.get_position()) <= agent.attack_range():
            agent.set_velocity(Vector2(0.0, 0.0))
            agent.try_attack(world, e)
        else:
            _flee(agent, world)
        return
    e = _target(agent, world)
    if e is None:
        return
    d = agent.get_position().distance(e.get_position())
    if d <= agent.attack_range():
        # DEFEND: don't over-extend -- only fire when the enemy is genuinely close
        if order is Order.DEFEND and d > agent.sight_range() * 0.8:
            _hold(agent, world)
            return
        agent.set_velocity(Vector2(0.0, 0.0))
        agent.try_attack(world, e)
    else:
        _chase(agent, world)


def _flee(agent, world) -> None:
    e = world.nearest_enemy(agent)
    if e is None:
        _patrol(agent, world, 0.0)
        return
    d = agent.get_position().distance(e.get_position())
    if d > agent.sight_range():
        # 敌人已远（safe）：RETREAT 转为「归队」，否则原地待命（上层 FSM/BT 会转 patrol）。
        # 归队是「选择」而非「逃跑 + 归队两矢量相加」——两个行为二选一，不叠加。
        if _order(agent, world) is Order.RETREAT:
            cc = world.team_centroid(agent.get_team())
            if cc is not None:
                agent.set_velocity(arrive(agent.get_position(), cc, agent.max_speed() * 0.5, 3.0))
                return
        agent.set_velocity(Vector2(0.0, 0.0))
        return
    # 敌人在视线内：evade 预判威胁未来位置，朝反方向逃（比 flee 直线逃更聪明）。
    # 逃得比追击者稍慢（0.85 倍），追击者能追上。
    away = evade(
        agent.get_position(), agent.get_velocity(),
        e.get_position(), e.get_velocity(),
        agent.max_speed() * 0.85, 1.0,
    )
    agent.set_velocity(away)


# --------------------------------------------------------------------------
# FSM states: patrol -> chase -> attack -> flee
# --------------------------------------------------------------------------
class PatrolState(State):
    def on_enter(self, a, w): a.set_state("patrol")
    def on_exit(self, a, w): pass
    def update(self, a, w, dt: float):
        e = w.nearest_enemy(a)
        if e and a.get_position().distance(e.get_position()) <= a.sight_range():
            a.get_blackboard().set("enemy_id", e.get_id())
            return "enemy_spotted"
        _patrol(a, w, dt)
        return None


class ChaseState(State):
    def on_enter(self, a, w): a.set_state("chase")
    def on_exit(self, a, w): pass
    def update(self, a, w, dt: float):
        e = w.nearest_enemy(a)
        if e is None:
            return "enemy_lost"
        if a.get_position().distance(e.get_position()) <= a.attack_range():
            return "in_range"
        _chase(a, w)
        return None


class AttackState(State):
    def on_enter(self, a, w): a.set_state("attack")
    def on_exit(self, a, w): pass
    def update(self, a, w, dt: float):
        e = w.nearest_enemy(a)
        if e is None:
            return "enemy_lost"
        if a.get_position().distance(e.get_position()) > a.attack_range():
            return "out_of_range"
        if a.hp() < 0.3 * a.max_hp():
            return "low_hp"
        _attack(a, w)
        return None


class FleeState(State):
    def on_enter(self, a, w): a.set_state("flee")
    def on_exit(self, a, w): pass
    def update(self, a, w, dt: float):
        e = w.nearest_enemy(a)
        if e is None:
            return "safe"
        if a.get_position().distance(e.get_position()) > a.sight_range():
            return "safe"
        _flee(a, w)
        return None


class FSMBrain:
    def __init__(self, fsm: FSM) -> None:
        self._fsm = fsm

    def tick(self, agent, world, dt: float) -> None:
        self._fsm.update(agent, world, dt)
        agent.set_state(self._fsm.current)

    def current(self) -> str:
        return self._fsm.current


def build_fsm_brain() -> FSMBrain:
    states = {
        "patrol": PatrolState(),
        "chase": ChaseState(),
        "attack": AttackState(),
        "flee": FleeState(),
    }
    transitions = {
        "patrol": {"enemy_spotted": "chase"},
        "chase": {"in_range": "attack", "enemy_lost": "patrol"},
        "attack": {"out_of_range": "chase", "low_hp": "flee", "enemy_lost": "patrol"},
        "flee": {"safe": "patrol"},
    }
    return FSMBrain(FSM(states, transitions, "patrol"))


# --------------------------------------------------------------------------
# Utility brain: score Advance / Attack / Retreat, execute the winner
# --------------------------------------------------------------------------
def _enemy_closeness(agent, world) -> float:
    e = world.nearest_enemy(agent)
    if e is None:
        return 0.0
    return max(0.0, agent.sight_range() - agent.get_position().distance(e.get_position()))


def _in_attack_range(agent, world) -> float:
    e = world.nearest_enemy(agent)
    if e is None:
        return 0.0
    return 1.0 if agent.get_position().distance(e.get_position()) <= agent.attack_range() else 0.0


def _retreat_score(agent, world) -> float:
    low = 1.0 - agent.hp() / agent.max_hp()
    e = world.nearest_enemy(agent)
    threat = 0.0
    if e is not None:
        d = agent.get_position().distance(e.get_position())
        # 「贴脸才有压迫感」：2 格内越近威胁越强，2 格外威胁为 0。
        # 原来的「看见敌人(6格)就 threat=0.6」会让满血 agent 隔老远就全撤。
        threat = max(0.0, 1.0 - d / 2.0)
    return max(low, threat)


def _exec_utility(name: str, agent, world, dt: float) -> None:
    if name == "Attack":
        e = _target(agent, world)
        if e and agent.get_position().distance(e.get_position()) <= agent.attack_range():
            agent.set_velocity(Vector2(0.0, 0.0))
            agent.try_attack(world, e)
        else:
            _patrol(agent, world, dt)
    elif name == "Retreat":
        _flee(agent, world)
    elif name == "Advance":
        e = world.nearest_enemy(agent)
        if e:
            _chase(agent, world)
        else:
            _patrol(agent, world, dt)
    else:
        _patrol(agent, world, dt)


class UtilityBrain:
    def __init__(self) -> None:
        self._options = [
            Option("Advance", [Consideration(_enemy_closeness, CurveType.LINEAR, 0.0, 8.0, 1.0)]),
            Option("Attack", [Consideration(_in_attack_range, CurveType.LINEAR, 0.0, 1.0, 1.5)]),
            Option("Retreat", [Consideration(_retreat_score, CurveType.LINEAR, 0.0, 1.0, 1.2)]),
        ]

    def _allowed_options(self, order: Order):
        # 指挥官指令 = 硬约束（选项门控），不是评分软输入：
        # 进攻/集火 → 禁撤退（必须进攻）；撤退 → 只撤退；防守/自动 → 全自主。
        if order is Order.ATTACK or order is Order.FOCUS:
            return [o for o in self._options if o.name != "Retreat"]
        if order is Order.RETREAT:
            return [o for o in self._options if o.name == "Retreat"]
        return self._options

    def tick(self, agent, world, dt: float) -> None:
        options = self._allowed_options(world.get_order(agent.get_team()))
        chosen, _ = decide(options, agent, world)
        agent.set_state(chosen.name)
        _exec_utility(chosen.name, agent, world, dt)

    def current(self) -> str:
        return "utility"


# --------------------------------------------------------------------------
# Behavior-tree brain: orchestrate the same actions via a Selector
# --------------------------------------------------------------------------
def _bt_in_range(a, w, bb) -> bool:
    e = w.nearest_enemy(a)
    return e is not None and a.get_position().distance(e.get_position()) <= a.attack_range()


def _bt_enemy_spotted(a, w, bb) -> bool:
    e = w.nearest_enemy(a)
    return e is not None and a.get_position().distance(e.get_position()) <= a.sight_range()


def _bt_low_hp(a, w, bb) -> bool:
    # 低血且敌人近才逃：敌人已远则退回 patrol/chase（与 FSM FleeState 的
    # "safe" 退出对齐）——否则低血 agent 会「想逃但 flee 返回零」原地卡死。
    if a.hp() >= 0.3 * a.max_hp():
        return False
    e = w.nearest_enemy(a)
    return e is not None and a.get_position().distance(e.get_position()) <= a.sight_range()


def _bt_attack(a, w, bb) -> Status:
    _attack(a, w)
    return Status.SUCCESS


def _bt_chase(a, w, bb) -> Status:
    _chase(a, w)
    return Status.SUCCESS


def _bt_flee(a, w, bb) -> Status:
    _flee(a, w)
    return Status.SUCCESS


def _bt_patrol(a, w, bb) -> Status:
    _patrol(a, w, 0.0)
    return Status.SUCCESS


class BehaviorTreeBrain:
    def __init__(self, root: Node) -> None:
        self._root = root

    def tick(self, agent, world, dt: float) -> None:
        self._root.tick(agent, world, agent.get_blackboard())

    def current(self) -> str:
        return "bt"


def build_bt_brain() -> BehaviorTreeBrain:
    root = Selector([
        Sequence([Condition(_bt_in_range), Action(_bt_attack)]),
        Sequence([Condition(_bt_enemy_spotted), Action(_bt_chase)]),
        Sequence([Condition(_bt_low_hp), Action(_bt_flee)]),
        Action(_bt_patrol),
    ])
    return BehaviorTreeBrain(root)


# --------------------------------------------------------------------------
# Factory
# --------------------------------------------------------------------------
def make_brain(kind: str):
    if kind == "fsm":
        return build_fsm_brain()
    if kind == "utility":
        return UtilityBrain()
    if kind == "bt":
        return build_bt_brain()
    raise ValueError(f"unknown brain kind: {kind!r}")
