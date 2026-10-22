from gameai.core.behavior_tree import (
    Action,
    Condition,
    Inverter,
    Selector,
    Sequence,
    Status,
)


def test_sequence_succeeds_when_all_succeed():
    s = Sequence([Action(lambda a, w, bb: Status.SUCCESS), Action(lambda a, w, bb: Status.SUCCESS)])
    assert s.tick(None, None, None) == Status.SUCCESS


def test_sequence_fails_fast():
    s = Sequence([Action(lambda a, w, bb: Status.FAILURE), Action(lambda a, w, bb: Status.SUCCESS)])
    assert s.tick(None, None, None) == Status.FAILURE


def test_selector_picks_first_non_failure():
    sel = Selector([Action(lambda a, w, bb: Status.FAILURE), Action(lambda a, w, bb: Status.SUCCESS)])
    assert sel.tick(None, None, None) == Status.SUCCESS


def test_selector_fails_when_all_fail():
    sel = Selector([Action(lambda a, w, bb: Status.FAILURE), Action(lambda a, w, bb: Status.FAILURE)])
    assert sel.tick(None, None, None) == Status.FAILURE


def test_inverter_flips_status():
    assert Inverter(Action(lambda a, w, bb: Status.SUCCESS)).tick(None, None, None) == Status.FAILURE
    assert Inverter(Action(lambda a, w, bb: Status.FAILURE)).tick(None, None, None) == Status.SUCCESS


def test_condition_maps_bool_to_status():
    assert Condition(lambda a, w, bb: True).tick(None, None, None) == Status.SUCCESS
    assert Condition(lambda a, w, bb: False).tick(None, None, None) == Status.FAILURE
