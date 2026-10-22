from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional

from .abc import IAgent, IWorld


class State(ABC):
    """A single FSM state (GoF State pattern)."""

    @abstractmethod
    def on_enter(self, agent: IAgent, world: IWorld) -> None:
        ...

    @abstractmethod
    def on_exit(self, agent: IAgent, world: IWorld) -> None:
        ...

    @abstractmethod
    def update(self, agent: IAgent, world: IWorld, dt: float) -> Optional[str]:
        """Return a transition event name to trigger, or None to stay."""
        ...


class FSM:
    """Finite state machine driving an agent through States via events."""

    def __init__(
        self,
        states: Dict[str, State],
        transitions: Dict[str, Dict[str, str]],
        initial: str,
    ) -> None:
        if initial not in states:
            raise ValueError(f"initial state {initial!r} not in states")
        self._states = states
        self._transitions = transitions
        self._current_name = initial
        self._current = states[initial]

    @property
    def current(self) -> str:
        return self._current_name

    def enter(self, agent: IAgent, world: IWorld) -> None:
        self._current.on_enter(agent, world)

    def update(self, agent: IAgent, world: IWorld, dt: float) -> None:
        event = self._current.update(agent, world, dt)
        if event is not None:
            self.trigger(agent, world, event)

    def trigger(self, agent: IAgent, world: IWorld, event: str) -> None:
        targets = self._transitions.get(self._current_name, {})
        if event in targets:
            nxt = targets[event]
            self._current.on_exit(agent, world)
            self._current = self._states[nxt]
            self._current_name = nxt
            self._current.on_enter(agent, world)
