from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Tuple

from .abc import IAgent, IWorld

_E = 2.718281828459045


class CurveType(Enum):
    LINEAR = "linear"
    QUADRATIC = "quadratic"
    POWER = "power"
    SIGMOID = "sigmoid"


def normalize(value: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 0.0
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def response_curve(curve: CurveType, x: float) -> float:
    x = max(0.0, min(1.0, x))
    if curve == CurveType.LINEAR:
        return x
    if curve == CurveType.QUADRATIC:
        return x * x
    if curve == CurveType.POWER:
        return x ** 0.5
    if curve == CurveType.SIGMOID:
        return 1.0 / (1.0 + _E ** (-(x - 0.5) * 10.0))
    return x


@dataclass
class Consideration:
    """One input -> response-curve -> weighted score (GoF Strategy on the curve)."""

    input_fn: Callable[[IAgent, IWorld], float]
    curve: CurveType
    min_val: float = 0.0
    max_val: float = 1.0
    weight: float = 1.0


@dataclass
class Option:
    name: str
    considerations: List[Consideration] = field(default_factory=list)

    def score(self, agent: IAgent, world: IWorld) -> float:
        if not self.considerations:
            return 0.0
        total = 0.0
        weight_sum = 0.0
        for c in self.considerations:
            raw = c.input_fn(agent, world)
            n = normalize(raw, c.min_val, c.max_val)
            total += c.weight * response_curve(c.curve, n)
            weight_sum += c.weight
        return total / weight_sum if weight_sum else 0.0


def decide(options: List[Option], agent: IAgent, world: IWorld) -> Tuple[Option, float]:
    """Return the highest-scoring option and its score."""
    best: Option = options[0] if options else Option("none")
    best_score = -1.0
    for o in options:
        s = o.score(agent, world)
        if s > best_score:
            best_score = s
            best = o
    return best, best_score
