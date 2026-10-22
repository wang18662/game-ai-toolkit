from gameai.core.blackboard import Blackboard


def test_set_get_has():
    bb = Blackboard()
    assert bb.has("k") is False
    bb.set("k", 42)
    assert bb.has("k") is True
    assert bb.get("k") == 42
    assert bb.get("missing", "default") == "default"
