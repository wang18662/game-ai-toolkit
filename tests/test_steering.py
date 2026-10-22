import random

from gameai.core.steering import (
    arrive,
    collision_avoidance,
    evade,
    flee,
    obstacle_avoidance,
    pursue,
    seek,
    separation,
    wander,
)
from gameai.core.vector import Vector2


def test_seek_points_at_target():
    v = seek(Vector2(0, 0), Vector2(3, 0), 5.0)
    assert v.x > 0 and abs(v.y) < 1e-9
    assert abs(v.length() - 5.0) < 1e-6


def test_arrive_decelerates_near_target():
    far = arrive(Vector2(0, 0), Vector2(10, 0), 5.0, slow_radius=3.0)
    near = arrive(Vector2(8, 0), Vector2(10, 0), 5.0, slow_radius=3.0)
    assert far.length() > near.length()
    assert abs(far.length() - 5.0) < 1e-6


def test_arrive_zero_at_target():
    assert arrive(Vector2(1, 1), Vector2(1, 1), 5.0, 3.0).length() == 0.0


def test_flee_points_away_and_zero_beyond_radius():
    v = flee(Vector2(0, 0), Vector2(2, 0), 5.0, flee_radius=4.0)
    assert v.x < 0  # away from threat on +x
    assert abs(v.length() - 5.0) < 1e-6
    # beyond radius -> stand still
    assert flee(Vector2(0, 0), Vector2(10, 0), 5.0, flee_radius=4.0).length() == 0.0


def test_obstacle_avoidance_zero_when_path_clear():
    v = obstacle_avoidance(Vector2(0, 0), Vector2(1, 0), lambda x, y: True)
    assert v.length() == 0.0


def test_obstacle_avoidance_zero_when_desired_zero():
    v = obstacle_avoidance(Vector2(0, 0), Vector2(0, 0), lambda x, y: False)
    assert v.length() == 0.0


def test_obstacle_avoidance_steers_perpendicular_when_blocked():
    # wall at x >= 0.9 blocks the forward probes; sides stay open
    def walkable(x, y):
        return x < 0.9

    v = obstacle_avoidance(Vector2(0, 0), Vector2(1, 0), walkable, lookahead=1.5, max_speed=3.0)
    assert v.length() > 0
    # steering must be perpendicular to desired (pure sideways, no cut-corner)
    assert abs(v.x) < 1e-6
    assert abs(v.y) > 0


def test_obstacle_avoidance_u_turn_when_cornered():
    # only the space behind (x < -0.9) is walkable -> forced U-turn
    def walkable(x, y):
        return x < -0.9

    v = obstacle_avoidance(Vector2(0, 0), Vector2(1, 0), walkable, lookahead=1.5, max_speed=3.0)
    assert v.x < 0  # reversed


def test_pursue_equals_seek_when_target_static():
    # 目标静止 → 预测点就是当前位置，pursue 退化为 seek
    v = pursue(Vector2(0, 0), Vector2(0, 0), Vector2(4, 0), Vector2(0, 0), 5.0, 2.0)
    s = seek(Vector2(0, 0), Vector2(4, 0), 5.0)
    assert abs(v.x - s.x) < 1e-6 and abs(v.y - s.y) < 1e-6


def test_pursue_leads_moving_target():
    # 目标在 (4,0) 向上跑，追击应朝「预测点」(上方) 而非当前位置(纯右)
    v = pursue(Vector2(0, 0), Vector2(0, 0), Vector2(4, 0), Vector2(0, 4), 5.0, 2.0)
    assert v.y > 0  # 朝目标前方预判
    assert v.x > 0


def test_evade_flees_predicted_threat():
    # 威胁在 (4,0) 向上跑，逃避应朝远离预测点(4,8)的方向，即左下方
    v = evade(Vector2(0, 0), Vector2(0, 0), Vector2(4, 0), Vector2(0, 4), 5.0, 2.0)
    assert v.x < 0 and v.y < 0


def test_separation_pushes_away_from_close_neighbor():
    # 邻居在 +x 方向 0.5 处（threshold=2 内），应朝 -x 推开，且无 y 分量
    v = separation(Vector2(0, 0), [Vector2(0.5, 0)], 5.0, threshold=2.0, decay_coefficient=2.0)
    assert v.x < 0
    assert abs(v.y) < 1e-6


def test_separation_ignores_far_neighbor():
    v = separation(Vector2(0, 0), [Vector2(10, 0)], 5.0, threshold=2.0, decay_coefficient=2.0)
    assert v.length() == 0.0


def test_collision_avoidance_steers_aside_head_on():
    # 对方从 +x 方向斜着撞来（相对位置(2,0.5)、相对速度(-4,0)），最接近点在自己
    # (0,0.5) 附近；应产生侧向让开（-y）的力，而不是朝对方或朝后
    v = collision_avoidance(
        Vector2(0, 0), Vector2(0, 0), [(Vector2(2, 0.5), Vector2(-4, 0))], 5.0, radius=0.5
    )
    assert v.y < 0
    assert abs(v.x) < 1e-6


def test_collision_avoidance_zero_when_moving_apart():
    # 对方朝远离方向移动，不会撞 → 无力
    v = collision_avoidance(
        Vector2(0, 0), Vector2(0, 0), [(Vector2(3, 0), Vector2(3, 0))], 5.0, radius=0.5
    )
    assert v.length() == 0.0


def test_wander_moves_in_heading_direction():
    v = wander(
        Vector2(0, 0), Vector2(1, 0), 5.0,
        wander_offset=2.0, wander_radius=1.0, wander_rate=0.5, rng=random.Random(42),
    )
    assert v.length() > 0
    assert v.x > 0  # 大致朝前方（heading +x）


def test_wander_is_seeded_reproducible():
    a = wander(Vector2(0, 0), Vector2(1, 0), 5.0, 2.0, 1.0, 0.5, rng=random.Random(7))
    b = wander(Vector2(0, 0), Vector2(1, 0), 5.0, 2.0, 1.0, 0.5, rng=random.Random(7))
    assert abs(a.x - b.x) < 1e-9 and abs(a.y - b.y) < 1e-9
