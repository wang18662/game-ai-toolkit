"""校验器单测 —— 证明「LLM 字段写入必须过确定性守门人」这个不变量。"""
from gameai.core.validator import IntentRejected, Validator


def _make_validator() -> Validator:
    return Validator(whitelist={"affinity": (0.0, 100.0), "trust": (0.0, 10.0)})


def test_accepts_legal_set():
    _make_validator().validate({"set": {"affinity": 20.0}})


def test_rejects_unknown_field():
    v = _make_validator()
    try:
        v.validate({"set": {"gold": 999}})
    except IntentRejected as e:
        assert "gold" in e.reason
    else:
        raise AssertionError("应拒绝白名单之外的字段")


def test_rejects_out_of_range():
    v = _make_validator()
    try:
        v.validate({"set": {"affinity": 9999}})
    except IntentRejected:
        pass
    else:
        raise AssertionError("应拒绝超范围的数值")


def test_rejects_below_range():
    v = _make_validator()
    try:
        v.validate({"set": {"affinity": -5}})
    except IntentRejected:
        pass
    else:
        raise AssertionError("应拒绝低于下限的数值")


def test_rejects_multiple_fields_if_any_invalid():
    v = _make_validator()
    try:
        v.validate({"set": {"affinity": 10.0, "gold": 1}})
    except IntentRejected as e:
        assert "gold" in e.reason
    else:
        raise AssertionError("任一个字段越权就整体拒绝")
