"""Minimal FSM demo: a guard that patrols, chases on sight, returns when lost."""
from gameai.core.fsm import FSM, State


class Guard:
    def __init__(self):
        self.t = 0.0
        self.sees_enemy = False
        self.state = "init"


class Patrol(State):
    def on_enter(self, a, w):
        a.state = "patrol"

    def on_exit(self, a, w):
        pass

    def update(self, a, w, dt):
        a.t += dt
        return "see_enemy" if a.sees_enemy else None


class Chase(State):
    def on_enter(self, a, w):
        a.state = "chase"

    def on_exit(self, a, w):
        pass

    def update(self, a, w, dt):
        a.t += dt
        return "lost_enemy" if not a.sees_enemy else None


if __name__ == "__main__":
    g = Guard()
    fsm = FSM(
        {"patrol": Patrol(), "chase": Chase()},
        {"patrol": {"see_enemy": "chase"}, "chase": {"lost_enemy": "patrol"}},
        "patrol",
    )
    fsm.enter(g, None)
    g.sees_enemy = True
    fsm.update(g, None, 0.1)
    print("after seeing enemy:", fsm.current)
    g.sees_enemy = False
    fsm.update(g, None, 0.1)
    print("after losing enemy:", fsm.current)
