"""LlmBrain —— 每轮「LLM 说话 + 校验器守门 + FSM 定状态」的对话 NPC 大脑。

控制流（药定的三件事）：
  1. 每轮：LLM 生成「台词 + 意图」（NPC 每轮都说话）
  2. 每轮：Validator 校验字段写权限，越权拒绝（每轮都过守门人）
  3. 只在状态变化时：FSM 判定并执行状态转移（转移表是状态的权威）

断网 / 没 key：LLM 降级模板台词，FSM / validator 照常工作，游戏绝不崩。
"""
from __future__ import annotations

import json
from typing import Callable, Dict, Optional, Tuple

from ..core.fsm import FSM
from ..core.validator import IntentRejected, Validator


class LlmBrain:
    def __init__(
        self,
        fsm: FSM,
        validator: Validator,
        chat: Callable[[list], str],
        system_prompt: str,
        fallback_lines: Optional[Dict[str, str]] = None,
    ) -> None:
        self._fsm = fsm
        self._validator = validator
        self._chat = chat
        self._system = system_prompt
        self._fallback = fallback_lines or {}

    def respond(self, agent, world, user_input: str) -> str:
        """玩家说一句 → NPC 回一句，返回台词。"""
        bb = agent.get_blackboard()
        bb.set("rejected_intent", None)  # 清上一轮的拒绝记录
        state = self._fsm.current

        line, intent = self._generate(agent, state, user_input)

        # 每轮：校验字段写权限（数据越权由 validator 拦）
        for field, value in intent.get("set", {}).items():
            try:
                self._validator.validate({"set": {field: value}})
            except IntentRejected as e:
                bb.set("rejected_intent", e.reason)
                continue
            bb.set(field, value)

        # 只在状态变化时：FSM 判定 + 执行转移（状态权威）
        transition = intent.get("transition")
        if transition:
            self._fsm.trigger(agent, world, transition)
            agent.set_state(self._fsm.current)

        bb.set("dialogue", line)
        return line

    # ---- 生成 ----
    def _generate(self, agent, state: str, user_input: str) -> Tuple[str, dict]:
        try:
            raw = self._chat([
                {"role": "system", "content": self._system},
                {"role": "user", "content": f"当前状态：{state}。玩家说：{user_input}"},
            ])
            parsed = self._parse(raw)
            return parsed.get("line", ""), parsed.get("intent") or {}
        except Exception:
            return self._fallback.get(state, "……"), {}

    @staticmethod
    def _parse(raw: str) -> dict:
        """把 LLM 文本解析成 {"line": ..., "intent": {...}}；解析失败当作纯台词。"""
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").strip()
        if raw.startswith("{"):
            return json.loads(raw)
        return {"line": raw}
