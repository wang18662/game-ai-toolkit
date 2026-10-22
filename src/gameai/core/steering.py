from __future__ import annotations

import math
import random

from .vector import Vector2

_EPS = 1e-6


def seek(pos: Vector2, target: Vector2, max_speed: float) -> Vector2:
    """Desired velocity straight at the target, capped at max_speed."""
    to = target - pos
    if to.length_sq() < _EPS:
        return Vector2(0.0, 0.0)
    return to.normalized() * max_speed


def arrive(pos: Vector2, target: Vector2, max_speed: float, slow_radius: float) -> Vector2:
    """Seek that decelerates inside slow_radius (smooth stop at target)."""
    to = target - pos
    dist = to.length()
    if dist < _EPS:
        return Vector2(0.0, 0.0)
    speed = max_speed * (dist / slow_radius) if dist <= slow_radius else max_speed
    return to.normalized() * speed


def flee(pos: Vector2, threat: Vector2, max_speed: float, flee_radius: float) -> Vector2:
    """Velocity away from threat, active only while inside flee_radius."""
    away = pos - threat
    dist = away.length()
    if dist < _EPS or dist >= flee_radius:
        return Vector2(0.0, 0.0)
    return away.normalized() * max_speed


def obstacle_avoidance(
    pos: Vector2,
    desired: Vector2,
    is_walkable,
    lookahead: float = 1.5,
    max_speed: float = 3.0,
) -> Vector2:
    """个体避障（身体本能层）：沿 desired 方向探测，前方被挡则产生侧向绕行力。

    职责边界：这里不决定「往哪走」（那是 brain 的决策层职责），
    只负责「怎么走不撞墙」——这是每个 agent 都有的身体本能。
    前方畅通时返回零向量，完全不干预正常移动；返回的绕行力由调用方
    叠加到 desired 上，再 cap 到 max_speed。
    """
    if desired.length_sq() < _EPS:
        return Vector2(0.0, 0.0)
    forward = desired.normalized()
    # 前方多档采样（近→远）：任一档被挡就触发。单点探测会漏掉「紧邻
    # 障碍的凸角」——agent 贴墙时远点擦过障碍，前进一小步就 round 进障碍格
    # 被硬停，所以要从近处就提前感知并绕行。
    blocked = False
    for d in (0.5, 0.9, 1.3):
        p = pos + forward * d
        if not is_walkable(p.x, p.y):
            blocked = True
            break
    if not blocked:
        return Vector2(0.0, 0.0)
    # 前方被挡：优先侧向绕行（左/右 90°），两边都堵（死胡同）则掉头
    left = Vector2(-forward.y, forward.x)
    right = Vector2(forward.y, -forward.x)
    for side in (left, right):
        p = pos + side * lookahead
        if is_walkable(p.x, p.y):
            return side * max_speed
    return -forward * max_speed


def pursue(
    pos: Vector2,
    vel: Vector2,
    target_pos: Vector2,
    target_vel: Vector2,
    max_speed: float,
    max_prediction: float,
) -> Vector2:
    """追击（预判式 seek）：假设目标保持当前速度，预测它在「预测时间」后的
    位置，再朝预测点 seek。直接朝当前位置追，等追到目标早跑了。
    """
    to_target = target_pos - pos
    distance = to_target.length()
    speed = vel.length()
    if max_prediction <= _EPS:
        return seek(pos, target_pos, max_speed)
    if speed <= distance / max_prediction:
        prediction = max_prediction
    else:
        prediction = distance / speed
    predicted = target_pos + target_vel * prediction
    return seek(pos, predicted, max_speed)


def evade(
    pos: Vector2,
    vel: Vector2,
    threat_pos: Vector2,
    threat_vel: Vector2,
    max_speed: float,
    max_prediction: float,
) -> Vector2:
    """逃避（预判式 flee）：与 pursue 对称，预测威胁未来位置，朝它的反方向逃。
    不做 flee_radius 判定——预判点本身已含威胁运动，逃离方向连续。
    """
    to_threat = threat_pos - pos
    distance = to_threat.length()
    speed = vel.length()
    if max_prediction <= _EPS:
        prediction = 0.0
    elif speed <= distance / max_prediction:
        prediction = max_prediction
    else:
        prediction = distance / speed
    predicted = threat_pos + threat_vel * prediction
    away = pos - predicted
    if away.length_sq() < _EPS:
        return Vector2(0.0, 0.0)
    return away.normalized() * max_speed


def separation(
    pos: Vector2,
    neighbors: list[Vector2],
    max_speed: float,
    threshold: float,
    decay_coefficient: float,
) -> Vector2:
    """群体分离：推开过近的邻居，防止单位互相重叠。排斥强度按平方反比衰减
    （越近越强），多个邻居的排斥力累加后 cap 到 max_speed。

    neighbors: 邻居的位置列表（不含自己）。
    注意方向：away = pos - neighbor（远离邻居）。C++ 参考实现写成了
    target - character（指向邻居），会把单位「挤在一起」——那是 bug，这里取反。
    """
    total = Vector2(0.0, 0.0)
    for npos in neighbors:
        away = pos - npos
        distance = away.length()
        if distance < _EPS:
            continue  # 完全重叠：方向未定义，跳过避免 NaN
        if distance < threshold:
            strength = min(decay_coefficient / (distance * distance), max_speed)
            total += away.normalized() * strength
    if total.length() > max_speed:
        total = total.normalized() * max_speed
    return total


def collision_avoidance(
    pos: Vector2,
    vel: Vector2,
    targets: list[tuple[Vector2, Vector2]],
    max_speed: float,
    radius: float,
) -> Vector2:
    """碰撞规避（比 separation 聪明）：预测未来是否真会相撞，只对「最早会撞上」
    的那个目标做远离。不恐慌式乱躲。

    targets: 其他移动角色的 (位置, 速度) 列表。
    关键公式（式 3.1）：最接近点时间 t = -dot(rel_pos, rel_vel) / |rel_vel|²。
    注意负号——C++ 参考实现漏了负号，导致「正迎面撞来」被判成「正在远离」而跳过。
    """
    shortest_time = float("inf")
    avoid_dir = None
    for tpos, tvel in targets:
        rel_pos = tpos - pos
        rel_vel = tvel - vel
        rel_speed_sq = rel_vel.length_sq()
        if rel_speed_sq < _EPS:
            continue  # 相对静止，不会相撞
        time_to_collision = -rel_pos.dot(rel_vel) / rel_speed_sq
        if time_to_collision <= 0.0:
            continue  # 正在远离或已过最近点
        predicted = rel_pos + rel_vel * time_to_collision  # 最近时刻的相对位置
        if predicted.length() > 2.0 * radius:
            continue  # 最近点仍比 2r 远，安全
        if time_to_collision < shortest_time:
            shortest_time = time_to_collision
            avoid_dir = -predicted.normalized()  # 远离预测碰撞点
    if avoid_dir is None:
        return Vector2(0.0, 0.0)
    return avoid_dir * max_speed


def _rotate(v: Vector2, angle: float) -> Vector2:
    c, s = math.cos(angle), math.sin(angle)
    return Vector2(v.x * c - v.y * s, v.x * s + v.y * c)


def wander(
    pos: Vector2,
    heading: Vector2,
    max_speed: float,
    wander_offset: float,
    wander_radius: float,
    wander_rate: float,
    rng: random.Random | None = None,
) -> Vector2:
    """游荡：在角色前方 wander_offset 处放一个半径 wander_radius 的圆，圆上随机
    取一点朝它 seek。因为圆始终在前进方向前方、漂移角集中在小范围，轨迹平滑不抖。

    heading: 当前朝向（单位向量，通常用上一帧速度方向）。静止 agent 需调用方给一个
    非零初始朝向，否则无从游荡。
    rng: 可注入 Random(seed)，测试可复现。
    """
    rng = rng or random
    # 二项分布近似：两个均匀随机之差，集中在 0 附近，避免大角度跳变
    drift = (rng.random() - rng.random()) * wander_rate
    circle_center = pos + heading * wander_offset
    wander_target = circle_center + _rotate(heading, drift) * wander_radius
    return seek(pos, wander_target, max_speed)
