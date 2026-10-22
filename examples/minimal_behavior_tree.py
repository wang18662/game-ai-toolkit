"""Minimal behavior tree: attack if enemy in range, else patrol."""
from gameai.core.behavior_tree import (
    Action,
    Condition,
    Selector,
    Sequence,
    Status,
)


def enemy_in_range(agent, world, bb):
    return agent.enemy_distance < 5.0


def do_attack(agent, world, bb):
    agent.action = "attack"
    return Status.SUCCESS


def do_patrol(agent, world, bb):
    agent.action = "patrol"
    return Status.SUCCESS


if __name__ == "__main__":
    bt = Selector(
        [
            Sequence([Condition(enemy_in_range), Action(do_attack)]),
            Action(do_patrol),
        ]
    )

    class Agent:
        enemy_distance = 2.0
        action = "?"

    a = Agent()
    bt.tick(a, None, None)
    print("enemy near ->", a.action)

    a.enemy_distance = 99.0
    bt.tick(a, None, None)
    print("enemy far  ->", a.action)
