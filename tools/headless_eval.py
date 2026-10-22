from __future__ import annotations

import csv
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from gameai.core.abc import Team
from gameai.core.json_defs import MapDef
from gameai.sim.world import World

DEFAULT_MAP = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "maps" / "skirmish.json"


def build_world(map_def: MapDef, brain_a: str, brain_b: str, seed: int) -> World:
    world = World(map_def, seed)
    world.populate(map_def, brain_a, brain_b)
    return world


@dataclass
class MatchResult:
    winner: Optional[str]
    steps: int
    ms_per_tick: float


def run_match(map_def: MapDef, brain_a: str, brain_b: str, seed: int, max_steps: int = 2000, dt: float = 0.1) -> MatchResult:
    world = build_world(map_def, brain_a, brain_b, seed)
    t0 = time.perf_counter()
    steps = 0
    for _ in range(max_steps):
        if world.alive_count(Team.A) == 0 or world.alive_count(Team.B) == 0:
            break
        world.tick(dt)
        steps += 1
    elapsed = time.perf_counter() - t0
    ms_per_tick = (elapsed / steps * 1000.0) if steps else 0.0
    if world.alive_count(Team.A) == 0 and world.alive_count(Team.B) == 0:
        winner = None
    elif world.alive_count(Team.B) == 0:
        winner = "A"
    elif world.alive_count(Team.A) == 0:
        winner = "B"
    else:
        winner = None  # timeout
    return MatchResult(winner, steps, ms_per_tick)


def evaluate(map_path: str, brains: List[str], matches: int = 20, seed_base: int = 1000) -> Dict[str, dict]:
    map_def = MapDef.from_file(map_path)
    summary: Dict[str, dict] = {}
    for challenger in brains:
        wins_a = 0
        wins_b = 0
        draws = 0
        latencies: List[float] = []
        step_counts: List[int] = []
        for i in range(matches):
            # challenger on Team A, FSM baseline on Team B
            res = run_match(map_def, challenger, "fsm", seed_base + i)
            if res.winner == "A":
                wins_a += 1
            elif res.winner == "B":
                wins_b += 1
            else:
                draws += 1
            latencies.append(res.ms_per_tick)
            step_counts.append(res.steps)
        summary[challenger] = {
            "vs_fsm_win_rate": wins_a / matches,
            "wins": wins_a,
            "losses": wins_b,
            "draws": draws,
            "avg_ms_per_tick": statistics.mean(latencies),
            "avg_steps": statistics.mean(step_counts),
        }
    return summary


def _write_csv(summary: Dict[str, dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["brain", "vs_fsm_win_rate", "wins", "losses", "draws", "avg_ms_per_tick", "avg_steps"])
        for brain, s in summary.items():
            w.writerow([brain, f"{s['vs_fsm_win_rate']:.2f}", s["wins"], s["losses"], s["draws"],
                        f"{s['avg_ms_per_tick']:.3f}", f"{s['avg_steps']:.1f}"])


def main() -> None:
    map_path = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_MAP)
    brains = sys.argv[2].split(",") if len(sys.argv) > 2 else ["fsm", "utility", "bt"]
    matches = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    print(f"map: {map_path}")
    print(f"brains: {brains}  matches/brain: {matches}")
    summary = evaluate(map_path, brains, matches)
    print(f"{'brain':<8} {'win%':>6} {'wins':>5} {'loss':>5} {'draw':>5} {'ms/tick':>9} {'steps':>7}")
    for brain, s in summary.items():
        print(f"{brain:<8} {s['vs_fsm_win_rate']*100:5.1f}% {s['wins']:>5} {s['losses']:>5} {s['draws']:>5} "
              f"{s['avg_ms_per_tick']:>8.3f} {s['avg_steps']:>7.1f}")

    _write_csv(summary, Path(__file__).resolve().parent.parent / "benchmarks" / "report_data" / "metrics.csv")
    print("wrote benchmarks/report_data/metrics.csv")

    # optional chart
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        labels = list(summary.keys())
        rates = [summary[b]["vs_fsm_win_rate"] * 100 for b in labels]
        plt.bar(labels, rates, color=["#5384dd", "#d84b4a", "#639922"][: len(labels)])
        plt.ylim(0, 100)
        plt.ylabel("win rate vs FSM baseline (%)")
        plt.title("AI brain benchmark")
        chart = Path(__file__).resolve().parent.parent / "benchmarks" / "report_data" / "win_rate.png"
        chart.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(chart)
        print(f"wrote {chart}")
    except Exception as exc:  # matplotlib optional
        print(f"(skipped chart: {exc})")


if __name__ == "__main__":
    main()
