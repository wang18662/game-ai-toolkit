"""最小「LLM 驱动的 NPC」演示 —— 每轮说话 + 每轮校验 + FSM 只在状态变化时定行为。

跑法（在项目根目录）：
  python examples/llm_npc_demo.py

演示两部分：
  1. 假 LLM（无需 key）展示完整三段式：说话 / 校验拦越权 / FSM 状态转移
  2. 真实 chat（无 key）展示「断网降级」——LLM 挂了 FSM 照跑
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gameai.core.blackboard import Blackboard
from gameai.core.fsm import FSM, State
from gameai.core.validator import Validator
from gameai.integrations.llm import chat
from gameai.integrations.llm_brain import LlmBrain


class NPC:
    """极简对话 agent（鸭子类型，满足 LlmBrain 所需的最小接口）。"""

    def __init__(self, name: str) -> None:
        self.name = name
        self._state = "neutral"
        self._bb = Blackboard()

    def get_state(self) -> str:
        return self._state

    def set_state(self, s: str) -> None:
        self._state = s

    def get_blackboard(self):
        return self._bb


# ---- 确定性层：关系状态机（状态转移的权威）----
class _Neutral(State):
    def on_enter(self, a, w): a.set_state("neutral")
    def on_exit(self, a, w): pass
    def update(self, a, w, dt): return None


class _Friendly(State):
    def on_enter(self, a, w): a.set_state("friendly")
    def on_exit(self, a, w): pass
    def update(self, a, w, dt): return None


class _Hostile(State):
    def on_enter(self, a, w): a.set_state("hostile")
    def on_exit(self, a, w): pass
    def update(self, a, w, dt): return None


def build_relationship_fsm() -> FSM:
    states = {"neutral": _Neutral(), "friendly": _Friendly(), "hostile": _Hostile()}
    transitions = {
        "neutral": {"befriend": "friendly", "offend": "hostile"},
        "friendly": {"offend": "hostile"},
        "hostile": {"apologize": "neutral"},
    }
    return FSM(states, transitions, "neutral")


SYSTEM_PROMPT = (
    "你是一名文字互动剧的 NPC。根据当前关系状态，说一句符合人设的台词。"
    "若对话引发了关系变化，输出 JSON："
    '{"line": "台词", "intent": {"transition": "事件", "set": {"affinity": 数值}}}，'
    "affinity 必须在 0~100 之间。"
)

FALLBACK = {
    "neutral": "（冷淡地）嗯，你好。",
    "friendly": "（微笑）你来了呀。",
    "hostile": "（皱眉）你来干什么。",
}


def main() -> None:
    validator = Validator(whitelist={"affinity": (0.0, 100.0)})

    # --- 假 LLM：可控、无需 key，展示完整三段式 ---
    def fake_chat(messages):
        user = messages[-1]["content"]
        if "你好" in user or "帮" in user:
            return json.dumps({"line": "（微笑）谢谢你，你人真好。",
                               "intent": {"transition": "befriend", "set": {"affinity": 60.0}}})
        if "没礼貌" in user or "讨厌" in user:
            return json.dumps({"line": "（皱眉）你什么意思。",
                               "intent": {"transition": "offend", "set": {"gold": 999}}})
        if "对不起" in user:
            return json.dumps({"line": "（缓和）算了，不跟你计较。",
                               "intent": {"transition": "apologize"}})
        return json.dumps({"line": "嗯。"})

    npc = NPC("房东")
    brain = LlmBrain(build_relationship_fsm(), validator, fake_chat, SYSTEM_PROMPT, FALLBACK)

    print("=== 完整三段式（假 LLM 模拟）===")
    for user_says in ["你好，我帮你把快递搬上来了", "你这个人真没礼貌", "对不起，我刚才太冲了"]:
        reply = brain.respond(npc, None, user_says)
        bb = npc.get_blackboard()
        print(f"玩家：{user_says}")
        print(f"  状态={npc.get_state():<8} 台词={reply}  好感度={bb.get('affinity', '?')}")
        if bb.get("rejected_intent"):
            print(f"  ↳ 校验器拒绝：{bb.get('rejected_intent')}")
        print()

    # --- 真实 chat：无 key → 断网降级，FSM 照跑 ---
    print("=== 断网降级（真实 chat，未设 DEEPSEEK_API_KEY）===")
    npc2 = NPC("房东2")
    brain2 = LlmBrain(build_relationship_fsm(), validator, chat, SYSTEM_PROMPT, FALLBACK)
    reply2 = brain2.respond(npc2, None, "你好")
    print(f"状态={npc2.get_state()} 台词={reply2}（LLM 不可用，降级成模板）")


if __name__ == "__main__":
    main()
