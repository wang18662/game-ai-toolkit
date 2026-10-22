from __future__ import annotations

import math

from gameai.core.abc import Order, Team
from gameai.core.json_defs import MapDef
from gameai.core.vector import Vector2
from gameai.sim import behaviors
from gameai.sim.world import World


def _mini_world() -> World:
    """Tiny 20x20 arena, one agent per side, no obstacles."""
    m = MapDef(width=20, height=20, spawns={"A": [[18, 18]], "B": [[1, 1]]})
    w = World(m, seed=1)
    w.populate(m, "fsm", "fsm")
    return w


def test_set_get_order():
    w = _mini_world()
    assert w.get_order(Team.A) is Order.NONE
    assert w.get_order(Team.B) is Order.NONE
    w.set_order(Team.B, Order.ATTACK)
    assert w.get_order(Team.B) is Order.ATTACK
    assert w.get_order(Team.A) is Order.NONE  # the other team is unaffected


def test_focus_target_lowest_hp():
    w = _mini_world()
    a_agents = [a for a in w.get_agents() if a.get_team() == Team.A and a.is_alive()]
    victim = a_agents[0]
    victim.take_damage(60)  # make it the weakest enemy of team B
    assert w.focus_target(Team.B) is victim
    assert victim.hp() < 100


def test_team_centroid():
    w = _mini_world()
    cc = w.team_centroid(Team.A)
    pts = [a.get_position() for a in w.get_agents()
           if a.get_team() == Team.A and a.is_alive()]
    ex = sum(p.x for p in pts) / len(pts)
    ey = sum(p.y for p in pts) / len(pts)
    assert math.isclose(cc.x, ex, abs_tol=1e-6)
    assert math.isclose(cc.y, ey, abs_tol=1e-6)


def test_focus_directive_targets_weakest():
    w = _mini_world()
    w.set_order(Team.B, Order.FOCUS)
    a_agents = [a for a in w.get_agents() if a.get_team() == Team.A and a.is_alive()]
    victim = a_agents[0]
    victim.take_damage(70)
    b = [a for a in w.get_agents() if a.get_team() == Team.B][0]
    assert behaviors._target(b, w) is victim


def test_defend_engages_when_visible():
    # DEFEND: once an enemy is within sight, the agent closes the last gap and
    # trades fire (it does not freeze in place -- that would stall the match).
    w = _mini_world()
    w.set_order(Team.B, Order.DEFEND)
    b = [a for a in w.get_agents() if a.get_team() == Team.B][0]
    e = w.nearest_enemy(b)
    # pull the enemy to ~4 cells away (inside 0.9*sight, outside attack range)
    e._pos = b.get_position() + Vector2(4.0, 0.0)
    behaviors._chase(b, w)
    v = b.get_velocity()
    to_enemy = (e.get_position() - b.get_position()).normalized()
    assert v.length() > 0.5                       # it is moving, not frozen
    assert v.dot(to_enemy) > 0                     # moving toward the enemy (engaging)


def test_none_chases_enemy():
    # Default posture (NONE) actively moves toward the enemy.
    w = _mini_world()
    b = [a for a in w.get_agents() if a.get_team() == Team.B][0]
    behaviors._chase(b, w)
    assert b.get_velocity().length() > 1.0


def test_retreat_regroups_when_enemy_beyond_flee_radius():
    # RETREAT 且敌人超出 flee_radius(sight_range=6) 时 flee 返回零，应转为
    # 「归队」朝队伍质心靠拢（二选一，不叠加）。回归：此路径曾因 _EPS 未定义
    # 抛 NameError，须有单测覆盖到这一分支。
    m = MapDef(width=20, height=20, spawns={"A": [[18, 18]], "B": [[1, 1], [1, 3]]})
    w = World(m, seed=1)
    w.populate(m, "fsm", "fsm")
    w.set_order(Team.B, Order.RETREAT)
    b = [a for a in w.get_agents() if a.get_team() == Team.B][0]
    e = w.nearest_enemy(b)
    e._pos = b.get_position() + Vector2(12.0, 0.0)  # 敌人远在 flee_radius 之外
    behaviors._flee(b, w)
    v = b.get_velocity()
    cc = w.team_centroid(Team.B)
    assert v.length() > 0
    # 归队：朝队伍质心方向移动，而不是原地不动或抛异常
    assert v.dot((cc - b.get_position()).normalized()) > 0


def test_utility_order_gates_retreat_option():
    # 指挥官指令 = 硬约束（选项门控）：1/3 进攻禁撤退，4 撤退只撤退，5 自动全自主。
    m = MapDef(width=20, height=20, spawns={"A": [[10, 10]], "B": [[10, 13]]})
    w = World(m, seed=1)
    w.populate(m, "fsm", "utility")
    ub = behaviors.UtilityBrain()

    names = lambda opts: [o.name for o in opts]  # noqa: E731

    assert "Retreat" not in names(ub._allowed_options(Order.ATTACK))
    assert "Retreat" not in names(ub._allowed_options(Order.FOCUS))
    assert names(ub._allowed_options(Order.RETREAT)) == ["Retreat"]
    assert set(names(ub._allowed_options(Order.NONE))) == {"Advance", "Attack", "Retreat"}


def test_utility_attack_order_never_retreats():
    # 敌距 3（原 Retreat 得分 0.6 必赢的场景）下按 1(Attack)，蓝队必须进攻，
    # 不能因为 threat 高就自己撤退——否则玩家指令形同虚设。
    m = MapDef(width=20, height=20, spawns={"A": [[10, 10]], "B": [[10, 13]]})
    w = World(m, seed=1)
    w.populate(m, "fsm", "utility")
    b = [a for a in w.get_agents() if a.get_team() == Team.B][0]
    e = w.nearest_enemy(b)
    e._pos = b.get_position() + Vector2(0.0, -3.0)
    ub = behaviors.UtilityBrain()

    w.set_order(Team.B, Order.ATTACK)
    ub.tick(b, w, 0.1)
    assert b.get_state() != "Retreat"


def test_bt_low_hp_requires_enemy_near():
    # 低血但敌人远 → 不 flee（与 FSM FleeState 的 "safe" 退出对齐），
    # 防止低血 agent「想逃但 flee 返回零」原地卡死。
    m = MapDef(width=20, height=20, spawns={"A": [[10, 10]], "B": [[10, 17]]})
    w = World(m, seed=1)
    w.populate(m, "bt", "fsm")
    a = [x for x in w.get_agents() if x.get_team() == Team.A][0]
    a.take_damage(80)  # hp=20 < 30，低血
    bb = a.get_blackboard()
    # 敌人 7 格远（> sight_range 6）→ 不 flee
    assert not behaviors._bt_low_hp(a, w, bb)
    # 敌人拉到 3 格近 → flee
    e = w.nearest_enemy(a)
    e._pos = a.get_position() + Vector2(0.0, -3.0)
    assert behaviors._bt_low_hp(a, w, bb)
