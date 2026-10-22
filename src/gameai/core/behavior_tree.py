from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, List

from .abc import IAgent, IBlackboard, IWorld


class Status(Enum):
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3


class Node(ABC):
    """Base node of a behavior tree (GoF Composite pattern)."""

    @abstractmethod
    def tick(self, agent: IAgent, world: IWorld, bb: IBlackboard) -> Status:
        ...


class Leaf(Node):
    """Base for terminal nodes (actions / conditions)."""


class Action(Leaf):
    def __init__(self, fn: Callable[[IAgent, IWorld, IBlackboard], Status]) -> None:
        self._fn = fn

    def tick(self, agent: IAgent, world: IWorld, bb: IBlackboard) -> Status:
        return self._fn(agent, world, bb)


class Condition(Leaf):
    def __init__(self, fn: Callable[[IAgent, IWorld, IBlackboard], bool]) -> None:
        self._fn = fn

    def tick(self, agent: IAgent, world: IWorld, bb: IBlackboard) -> Status:
        return Status.SUCCESS if self._fn(agent, world, bb) else Status.FAILURE


class Composite(Node):
    def __init__(self, children: List[Node]) -> None:
        self._children = children


class Sequence(Composite):
    """Run children in order; fail fast on first non-success."""

    def tick(self, agent: IAgent, world: IWorld, bb: IBlackboard) -> Status:
        for child in self._children:
            status = child.tick(agent, world, bb)
            if status != Status.SUCCESS:
                return status
        return Status.SUCCESS


class Selector(Composite):
    """Try children in order; succeed on first non-failure."""

    def tick(self, agent: IAgent, world: IWorld, bb: IBlackboard) -> Status:
        for child in self._children:
            status = child.tick(agent, world, bb)
            if status != Status.FAILURE:
                return status
        return Status.FAILURE


class Decorator(Node):
    def __init__(self, child: Node) -> None:
        self._child = child


class Inverter(Decorator):
    def tick(self, agent: IAgent, world: IWorld, bb: IBlackboard) -> Status:
        status = self._child.tick(agent, world, bb)
        if status == Status.SUCCESS:
            return Status.FAILURE
        if status == Status.FAILURE:
            return Status.SUCCESS
        return status
