from __future__ import annotations

import argparse
import os
import sys
import traceback

# Make the `gameai` package importable WITHOUT needing PYTHONPATH set.
# - Dev / run_demo.bat: add ../src relative to this file.
# - Frozen (PyInstaller): gameai is bundled into sys._MEIPASS; nothing to add.
if getattr(sys, "frozen", False):
    _SRC = None
else:
    _SRC = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
    if _SRC not in sys.path:
        sys.path.insert(0, _SRC)

from gameai.core.abc import Team  # noqa: E402
from gameai.core.json_defs import MapDef  # noqa: E402
from gameai.sim.world import World  # noqa: E402

DT = 0.1


def _resolve_map(path: str) -> str:
    """Resolve the map path for both dev and frozen (PyInstaller) contexts.

    When frozen onefile, the script runs from a temp dir, so a relative
    default map only exists inside the bundle (sys._MEIPASS).
    """
    if os.path.isabs(path) or os.path.exists(path):
        return path
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = os.path.join(sys._MEIPASS, path)  # type: ignore[attr-defined]
        if os.path.exists(bundled):
            return bundled
    return path


def _run_headless(world: World, max_steps: int) -> None:
    for _ in range(max_steps):
        if world.alive_count(Team.A) == 0 or world.alive_count(Team.B) == 0:
            break
        world.tick(DT)
    a = world.alive_count(Team.A)
    b = world.alive_count(Team.B)
    winner = "A" if b == 0 and a > 0 else "B" if a == 0 and b > 0 else "draw/timeout"
    print(f"steps={world.step()}  A_alive={a}  B_alive={b}  winner={winner}")


def _run_pygame(world: World, map_def: MapDef, brain_a: str, brain_b: str, loop: bool, control: str = "B") -> None:
    from gameai.demo.pygame_adapter import PygameRenderer
    from gameai.core.abc import Team

    renderer = PygameRenderer(world, cell_px=28)
    renderer.set_player_team(Team.B if control == "B" else Team.A)
    print(f"[pygame window open] A={brain_a} vs B={brain_b}"
          f"  (you command team {control}){'  [loop on]' if loop else ''}")
    print("  >> CLICK the game window to give it keyboard focus, THEN press the keys below.")
    print("  keys: 1 Attack  2 Defend  3 Focus  4 Retreat  5 Auto  T switch team"
          "  (close window to exit)")
    seed = 7
    match_cap = 1500  # ~150s; restart stalled matches (e.g. turtle vs turtle) so the demo never freezes
    while True:
        if not renderer.tick_frame(DT):
            break  # user closed the window
        if world.alive_count(Team.A) == 0 or world.alive_count(Team.B) == 0 or world.step() > match_cap:
            won = "A" if world.alive_count(Team.B) == 0 else "B" if world.alive_count(Team.A) == 0 else "draw"
            print(f"match over: winner={won}" + ("" if world.step() <= match_cap else " (time cap)"))
            if not loop:
                while renderer.handle_events():
                    pass
                break
            # loop mode: restart with a new seed, never auto-close.
            # Re-apply the human's last directive + controlled team so a state
            # change does not get wiped every time a match restarts.
            seed = (seed + 1) % 100000
            world = World(map_def, seed=seed)
            world.populate(map_def, brain_a, brain_b)
            world.set_order(renderer.get_player_team(), renderer.get_last_order())
            renderer.set_world(world)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Playable-ish AI skirmish demo (engine-agnostic gameai toolkit). "
                    "Opens a pygame window; red vs blue AI teams fight automatically.")
    ap.add_argument("map", nargs="?", default="tests/fixtures/maps/arena.json",
                    help="path to a map JSON (default: tests/fixtures/maps/arena.json)")
    ap.add_argument("brain_a", nargs="?", default="bt",
                    help="red team brain: fsm | utility | bt (default: bt)")
    ap.add_argument("brain_b", nargs="?", default="utility",
                    help="blue team brain: fsm | utility | bt (default: utility)")
    ap.add_argument("--max-steps", type=int, default=2000,
                    help="headless safety cap (default 2000)")
    ap.add_argument("--loop", dest="loop", action="store_true", default=True,
                    help="restart matches automatically (default ON, good for demos)")
    ap.add_argument("--no-loop", dest="loop", action="store_false",
                    help="stop after one match and wait for window close")
    ap.add_argument("--control", choices=["A", "B"], default="B",
                    help="which team the human commands (default B / blue)")
    args = ap.parse_args()

    map_def = MapDef.from_file(_resolve_map(args.map))
    world = World(map_def, seed=7)
    world.populate(map_def, args.brain_a, args.brain_b)

    try:
        import pygame  # noqa: F401
    except ImportError:
        pygame = None  # type: ignore[assignment]

    if pygame is None:
        print("(pygame not installed -> headless text mode)")
        _run_headless(world, args.max_steps)
        return

    try:
        _run_pygame(world, map_def, args.brain_a, args.brain_b, args.loop, args.control)
    except Exception as exc:  # surface the real error instead of silently dying
        print("!! pygame window failed:", repr(exc))
        traceback.print_exc()
        print("-> falling back to headless text mode")
        _run_headless(world, args.max_steps)


if __name__ == "__main__":
    main()
