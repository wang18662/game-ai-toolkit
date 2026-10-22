from gameai.core.fsm import FSM, State


class _Agent:
    def __init__(self):
        self.t = 0.0
        self.log: list = []


class Patrol(State):
    def on_enter(self, a, w):
        a.log.append("enter patrol")

    def on_exit(self, a, w):
        a.log.append("exit patrol")

    def update(self, a, w, dt):
        a.t += dt
        return "see_enemy" if a.t >= 1.0 else None


class Chase(State):
    def on_enter(self, a, w):
        a.log.append("enter chase")

    def on_exit(self, a, w):
        a.log.append("exit chase")

    def update(self, a, w, dt):
        a.t += dt
        return "lost_enemy" if a.t >= 2.0 else None


def _build():
    a = _Agent()
    fsm = FSM(
        {"patrol": Patrol(), "chase": Chase()},
        {"patrol": {"see_enemy": "chase"}, "chase": {"lost_enemy": "patrol"}},
        "patrol",
    )
    fsm.enter(a, None)
    return a, fsm


def test_no_transition_before_threshold():
    a, fsm = _build()
    fsm.update(a, None, 0.6)
    assert fsm.current == "patrol"
    assert a.log == ["enter patrol"]


def test_transitions_both_ways():
    a, fsm = _build()
    fsm.update(a, None, 0.6)  # t=0.6
    fsm.update(a, None, 0.6)  # t=1.2 -> see_enemy
    assert fsm.current == "chase"
    fsm.update(a, None, 1.0)  # t=2.2 -> lost_enemy
    assert fsm.current == "patrol"
    assert "enter chase" in a.log and "exit patrol" in a.log


def test_unknown_event_is_ignored():
    a, fsm = _build()
    fsm.trigger(a, None, "no_such_event")
    assert fsm.current == "patrol"
