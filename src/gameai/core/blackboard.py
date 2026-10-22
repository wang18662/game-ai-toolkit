from __future__ import annotations

from typing import Any, Dict, Optional

from .abc import IBlackboard


class Blackboard(IBlackboard):
    """Default in-memory blackboard implementation."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def has(self, key: str) -> bool:
        return key in self._data
