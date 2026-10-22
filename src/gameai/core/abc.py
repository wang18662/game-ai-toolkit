from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List, Optional

from .vector import Vector2


class Team(Enum):
    A = "A"
    B = "B"


class Order(Enum):
    """High-level commander directive issued to a whole team.

    A directive biases the team's AI (whatever brain it runs) at the *action*
    level -- the AI still does micro (pathfinding, targeting, firing), the
    player only sets the macro posture. This is the injection point that makes
    the AI "commandable" rather than just autonomous.
    """

    NONE = "none"        # brain default posture (no player override)
    ATTACK = "attack"    # aggressive: full-speed push, engage at max range
    DEFEND = "defend"    # hold near team centroid, fire only when enemy is close
    FOCUS = "focus"      # every agent targets the enemy with the lowest HP
    RETREAT = "retreat"  # fall back toward team centroid, avoid combat


class IBlackboard(ABC):
    """Shared memory readable/writable by FSM, behavior trees and utility AI."""

    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        ...

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        ...

    @abstractmethod
    def has(self, key: str) -> bool:
        ...


class IAgent(ABC):
    """Engine-agnostic agent. Concrete engines (e.g. pygame) implement this."""

    @abstractmethod
    def get_id(self) -> int:
        ...

    @abstractmethod
    def get_team(self) -> Team:
        ...

    @abstractmethod
    def get_position(self) -> Vector2:
        ...

    @abstractmethod
    def set_velocity(self, velocity: Vector2) -> None:
        ...

    @abstractmethod
    def get_blackboard(self) -> IBlackboard:
        ...

    @abstractmethod
    def tick(self, dt: float, world: "IWorld") -> None:
        ...


class IWorld(ABC):
    """The environment agents perceive and act within. Implemented by the engine."""

    @abstractmethod
    def get_agents(self) -> List[IAgent]:
        ...

    @abstractmethod
    def is_walkable(self, x: int, y: int) -> bool:
        ...

    @abstractmethod
    def get_order(self, team: "Team") -> "Order":
        """Current commander directive for ``team`` (default Order.NONE)."""
        ...

    @abstractmethod
    def emit(self, event: Any) -> None:
        ...


class IEventSink(ABC):
    """Any object that can react to a published event."""

    @abstractmethod
    def handle(self, event: Any) -> None:
        ...
