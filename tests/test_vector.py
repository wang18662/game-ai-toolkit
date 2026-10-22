from gameai.core.vector import Vector2


def test_add_sub():
    assert Vector2(1, 2) + Vector2(3, 4) == Vector2(4, 6)
    assert Vector2(3, 4) - Vector2(1, 1) == Vector2(2, 3)


def test_scalar_mul_div():
    assert Vector2(2, 3) * 2 == Vector2(4, 6)
    assert Vector2(4, 6) / 2 == Vector2(2, 3)


def test_length_and_normalize():
    assert Vector2(3, 4).length() == 5.0
    assert Vector2(0, 10).normalized().length() == 1.0


def test_distance():
    assert Vector2(0, 0).distance(Vector2(3, 4)) == 5.0


def test_dot():
    assert Vector2(1, 2).dot(Vector2(3, 4)) == 11
