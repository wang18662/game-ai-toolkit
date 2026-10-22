"""字段写权限校验器 —— 混合架构里「数据层」的确定性守门人。

LLM 每轮都能提出「想改哪些字段」的意图，能不能写由这里判定。
状态转移**不归它管**——那由 FSM 的转移表判定（状态变化的权威）。
关键原则：绝不能用 LLM 去校验 LLM（运动员当裁判，越权判定就失效了）。
"""
from __future__ import annotations

from typing import Dict, Tuple


class IntentRejected(Exception):
    """意图被校验器拒绝，reason 说明原因，供上层降级或重试。"""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class Validator:
    """校验 LLM 意图里的字段写入是否越权 / 越界。

    规则（两条）：
      1. 字段在「可写白名单」里吗？
      2. 数值在合法范围内吗？

    意图形如：:

        {"set": {"affinity": 20.0}}
    """

    def __init__(self, whitelist: Dict[str, Tuple[float, float]]) -> None:
        # {字段: (最小值, 最大值)}；只有列出的字段可被 LLM 写入
        self._whitelist = whitelist or {}

    def validate(self, intent: Dict) -> None:
        """校验意图；通过则无副作用返回，不通过抛 IntentRejected。"""
        for field, value in intent.get("set", {}).items():
            if field not in self._whitelist:
                raise IntentRejected(f"字段 {field!r} 不在可写白名单里")
            lo, hi = self._whitelist[field]
            if not (lo <= value <= hi):
                raise IntentRejected(f"{field}={value} 超出合法范围 [{lo}, {hi}]")
