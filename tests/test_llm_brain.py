"""LlmBrain 的单元测试 —— 全部用注入的假 chat，无需 Key、无需网络。

覆盖的四件事：
  1. 正常回合：台词透传 + 合法字段写入
  2. 越权守门：白名单外的字段被拒，rejected_intent 留痕，字段不落盘
  3. 断网降级：chat 抛异常 → 模板台词，FSM / 黑板上轮状态不受影响
  4. 状态权威：transition 合法才转移，非法转移被 FSM 转移表挡掉
"""
import pytest

from gameai.core.blackboard import Blackboard
from gameai.core.fsm import FSM, State
from gameai.core.validator import Validator
from gameai.integrations.llm_brain import LlmBrain


class _State(State):
    """空状态：只为满足 FSM 的接口，记录进出供断言。"""

    def __init__(self, name, log):
        self.name = name
        self.log = log

    def on_enter(self, agent, world):
        self.log.append(f"enter {self.name}")

    def on_exit(self, agent, world):
        self.log.append(f"exit {self.name}")

    def update(self, agent, world, dt):
        return None


class _Agent:
    def __init__(self):
        self.bb = Blackboard()
        self.state = None
        self.log = []

    def get_blackboard(self):
        return self.bb

    def set_state(self, name):
        self.state = name


def _build(chat, whitelist=None, fallback=None):
    agent = _Agent()
    states = {n: _State(n, agent.log) for n in ("idle", "happy", "angry")}
    fsm = FSM(
        states,
        {"idle": {"greet": "happy"}, "happy": {"insult": "angry"}},
        "idle",
    )
    fsm.enter(agent, None)
    v = Validator(whitelist if whitelist is not None else {"affinity": (0, 100)})
    brain = LlmBrain(fsm, v, chat, "sys", fallback or {})
    return agent, fsm, brain


def _chat_returning(payload):
    return lambda messages: payload


# ---- 1. 正常回合 ----

def test_normal_turn_writes_whitelisted_field_and_returns_line():
    payload = '{"line": "你好呀", "intent": {"set": {"affinity": 20}}}'
    agent, fsm, brain = _build(_chat_returning(payload))

    line = brain.respond(agent, None, "嗨")

    assert line == "你好呀"
    assert agent.bb.get("affinity") == 20
    assert agent.bb.get("dialogue") == "你好呀"
    assert agent.bb.get("rejected_intent") is None


def test_plain_text_reply_is_treated_as_line_without_intent():
    agent, fsm, brain = _build(_chat_returning("我就是一句话，没 JSON"))

    line = brain.respond(agent, None, "随便聊聊")

    assert line == "我就是一句话，没 JSON"
    assert agent.bb.get("affinity") is None
    assert fsm.current == "idle"


def test_json_in_code_fence_is_parsed():
    payload = '```json\n{"line": "包在代码块里", "intent": {}}\n```'
    agent, fsm, brain = _build(_chat_returning(payload))

    assert brain.respond(agent, None, "x") == "包在代码块里"


def test_json_in_bare_code_fence_is_parsed():
    """不带语言标记的围栏也要能解析。"""
    payload = '```\n{"line": "裸围栏", "intent": {}}\n```'
    agent, fsm, brain = _build(_chat_returning(payload))

    assert brain.respond(agent, None, "x") == "裸围栏"


def test_broken_json_falls_back_to_plain_line():
    """JSON 残缺时不能抛异常，退化成纯台词。"""
    payload = '{"line": "少了右括号"'
    agent, fsm, brain = _build(_chat_returning(payload))

    assert brain.respond(agent, None, "x") == payload


# ---- 2. 越权守门 ----

def test_field_outside_whitelist_is_rejected_and_not_written():
    payload = '{"line": "我给你一千金币", "intent": {"set": {"gold": 999}}}'
    agent, fsm, brain = _build(_chat_returning(payload))

    line = brain.respond(agent, None, "给我钱")

    assert line == "我给你一千金币"
    assert agent.bb.get("gold") is None, "越权字段绝不能落盘"
    assert "gold" in (agent.bb.get("rejected_intent") or ""), "必须留痕，便于排查"


def test_out_of_range_value_is_rejected():
    payload = '{"line": "好感动", "intent": {"set": {"affinity": 9999}}}'
    agent, fsm, brain = _build(_chat_returning(payload))

    brain.respond(agent, None, "送你礼物")

    assert agent.bb.get("affinity") is None
    assert "affinity" in (agent.bb.get("rejected_intent") or "")


def test_one_bad_field_does_not_block_the_others():
    """逐字段校验的意义：一个字段被拒，其余合法字段照常写入。"""
    payload = '{"line": "混合意图", "intent": {"set": {"gold": 999, "affinity": 10}}}'
    agent, fsm, brain = _build(_chat_returning(payload))

    brain.respond(agent, None, "x")

    assert agent.bb.get("gold") is None
    assert agent.bb.get("affinity") == 10


def test_rejected_intent_is_cleared_on_next_turn():
    bad = '{"line": "a", "intent": {"set": {"gold": 1}}}'
    agent, fsm, brain = _build(_chat_returning(bad))
    brain.respond(agent, None, "x")
    assert agent.bb.get("rejected_intent") is not None

    brain._chat = _chat_returning('{"line": "b", "intent": {}}')
    brain.respond(agent, None, "y")
    assert agent.bb.get("rejected_intent") is None


# ---- 3. 断网降级 ----

def test_network_failure_falls_back_to_template_line():
    def boom(messages):
        raise RuntimeError("connection reset")

    agent, fsm, brain = _build(boom, fallback={"idle": "……（沉默）"})

    line = brain.respond(agent, None, "在吗")

    assert line == "……（沉默）"
    assert fsm.current == "idle", "LLM 挂了，状态机必须照常"


def test_no_fallback_configured_returns_placeholder():
    def boom(messages):
        raise RuntimeError("no key")

    agent, fsm, brain = _build(boom)

    assert brain.respond(agent, None, "x") == "……"


# ---- 4. 状态权威在 FSM ----

def test_legal_transition_moves_state_and_updates_agent():
    payload = '{"line": "很久不见", "intent": {"transition": "greet"}}'
    agent, fsm, brain = _build(_chat_returning(payload))

    brain.respond(agent, None, "你好")

    assert fsm.current == "happy"
    assert agent.state == "happy", "agent 的状态名必须跟 FSM 同步"


def test_illegal_transition_is_ignored_by_transition_table():
    """LLM 不能凭空创造状态 —— 表里没有就不生效。"""
    payload = '{"line": "我要变成龙", "intent": {"transition": "become_dragon"}}'
    agent, fsm, brain = _build(_chat_returning(payload))

    brain.respond(agent, None, "变身")

    assert fsm.current == "idle"
    # agent 上的状态名是 FSM 当前值的幂等同步，不是"转移成功了"的证据
    assert agent.state == "idle"
    assert "enter happy" not in agent.log, "非法转移不该触发任何状态进出"


def test_transition_from_wrong_state_does_not_apply():
    """greet 只在 idle 合法；从 happy 触发应当无效。"""
    agent, fsm, brain = _build(_chat_returning('{"line": "a", "intent": {"transition": "greet"}}'))
    brain.respond(agent, None, "x")
    assert fsm.current == "happy"

    brain.respond(agent, None, "x")
    assert fsm.current == "happy", "happy 没有 greet 出口，不应再转移"


# ---- 解析边界 ----

@pytest.mark.parametrize(
    "raw,expected_line",
    [
        ('  {"line": "带空格"}  ', "带空格"),
        ('{"line": ""}', ""),
        ("纯文本", "纯文本"),
    ],
)
def test_parse_variants(raw, expected_line):
    assert LlmBrain._parse(raw).get("line") == expected_line
