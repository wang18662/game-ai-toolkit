"""DeepSeek 客户端 —— LLM 生成层（可选集成，不属于 core）。

只从环境变量读 key，绝不硬编码；首次调用才校验，避免离线测试被 key 缺失阻断。
"""
from __future__ import annotations

import os
from typing import List

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash"


class LLMError(RuntimeError):
    """LLM 生成层不可用（没 key / 网络失败）。上层据此降级到模板台词。"""


def _api_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise LLMError("未设置 DEEPSEEK_API_KEY，LLM 生成层不可用")
    return key


def chat(messages: List[dict], temperature: float = 0.8, model: str = MODEL) -> str:
    """发送一轮对话，返回模型的文本回复。任何异常统一包装成 LLMError。"""
    try:
        import requests  # 懒加载：只有真正调 LLM 时才需要（可选依赖）
    except ImportError as e:
        raise LLMError(f"未安装 requests（pip install gameai[llm]）：{e}") from e
    try:
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {_api_key()}"},
            json={"model": model, "messages": messages, "temperature": temperature},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except LLMError:
        raise
    except Exception as e:  # 网络 / HTTP / 解析错误统一归为「生成层不可用」
        raise LLMError(f"LLM 调用失败：{e}") from e
