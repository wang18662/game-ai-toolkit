from gameai.core.utility import Consideration, CurveType, Option, decide, normalize, response_curve


def test_normalize_clamps():
    assert normalize(5.0, 0.0, 10.0) == 0.5
    assert normalize(-3.0, 0.0, 10.0) == 0.0
    assert normalize(99.0, 0.0, 10.0) == 1.0
    assert normalize(5.0, 5.0, 5.0) == 0.0


def test_response_curves():
    assert response_curve(CurveType.LINEAR, 0.5) == 0.5
    assert abs(response_curve(CurveType.QUADRATIC, 0.5) - 0.25) < 1e-9
    assert abs(response_curve(CurveType.POWER, 0.25) - 0.5) < 1e-9


def test_decide_picks_highest_score():
    near = Consideration(lambda a, w: 10.0, CurveType.LINEAR, 0.0, 10.0, 1.0)
    far = Consideration(lambda a, w: 0.0, CurveType.LINEAR, 0.0, 10.0, 1.0)
    attack = Option("attack", [near])
    flee = Option("flee", [far])
    best, score = decide([attack, flee], None, None)
    assert best.name == "attack"
    assert abs(score - 1.0) < 1e-9


def test_weighted_score():
    c = Consideration(lambda a, w: 5.0, CurveType.QUADRATIC, 0.0, 10.0, 1.0)
    o = Option("x", [c])
    assert abs(o.score(None, None) - 0.25) < 1e-9
