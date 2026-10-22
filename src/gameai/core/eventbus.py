from __future__ import annotations

from typing import Any, Callable, Dict, List


class EventBus:
    """Observer-pattern event dispatcher.

    Decouples AI subsystems from the demo/engine layer: producers publish
    events, subscribers react without either side knowing about the other.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[type, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        handlers = self._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: Any) -> None:
        for handler in list(self._subscribers.get(type(event), [])):
            handler(event)
