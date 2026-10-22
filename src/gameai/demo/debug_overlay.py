from __future__ import annotations

try:
    import pygame
except ImportError:
    pygame = None

from ..core.abc import Team
from ..sim.world import World


class HudOverlay:
    """Separate debug/diagnostic layer: team counts, step, FPS legend.

    Kept apart from the world renderer so the AI logic and the diagnostics
    can evolve independently (single-responsibility).
    """

    def __init__(self, world: World) -> None:
        if pygame is None:
            raise RuntimeError("pygame is not installed; cannot render")
        self._world = world
        # Use the bundled default font (no system scan) to avoid the Windows
        # initsysfonts_win32() crash with "expected str, bytes or os.PathLike object, not int".
        try:
            self._font = pygame.font.Font(None, 14)
        except Exception:
            self._font = None

    def draw(self, surface) -> None:
        if self._font is None:
            return
        a_alive = self._world.alive_count(Team.A)
        b_alive = self._world.alive_count(Team.B)
        line = f"step {self._world.step():>4}   A:{a_alive}  B:{b_alive}"
        text = self._font.render(line, True, (235, 235, 235))
        surface.blit(text, (6, 6))
