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
        """把 LLM 文本解析成 {"line": ..., "intent": {...}}；解析失败当作纯台词。

        兼容三种常见输出形态：
          1. 纯 JSON            {"line": "...", "intent": {...}}
          2. 围栏代码块         ```json\\n{...}\\n```      ← 带语言标记，最常见
          3. 裸代码块           ```\\n{...}\\n```
        解析不了就当纯台词——绝不让格式问题把整轮对话搞崩。
        """
        raw = raw.strip()

        # 去掉围栏标记，含 ```json / ```JSON / ``` 三种写法
        if raw.startswith("```"):
            body = raw[3:]
            # 首行可能是语言标记（json / JSON / json5 等），整行丢掉
            if "\n" in body:
                first, rest = body.split("\n", 1)
                if first.strip().lower() in ("json", "json5", ""):
                    body = rest
                # 首行不是语言标记 → 可能本身就是 JSON，保留
            raw = body.strip()
            if raw.endswith("```"):
                raw = raw[:-3].strip()

        if raw.startswith("{"):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                # JSON 残缺时不抛，退化成纯台词
                return {"line": raw}
        return {"line": raw}
