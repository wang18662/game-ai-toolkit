"""Minimal utility AI: pick the action with the highest weighted score."""
from gameai.core.utility import Consideration, CurveType, Option, decide


class Agent:
    enemy_distance = 3.0
    health = 40.0


def distance_input(a, w):
    return a.enemy_distance


def health_input(a, w):
    return a.health


if __name__ == "__main__":
    attack = Option(
        "attack",
        [Consideration(distance_input, CurveType.LINEAR, 0.0, 10.0, 1.0)],
    )
    retreat = Option(
        "retreat",
        [Consideration(health_input, CurveType.QUADRATIC, 0.0, 100.0, 1.0)],
    )
    a = Agent()
    best, score = decide([attack, retreat], a, None)
    print(f"chosen: {best.name} (score={score:.3f})")
