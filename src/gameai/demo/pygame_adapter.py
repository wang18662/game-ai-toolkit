from __future__ import annotations

try:
    import pygame
except ImportError:  # headless environments: importable, but cannot render
    pygame = None

from ..core.abc import Order, Team
from ..sim.world import World

TEAM_COLORS = {
    Team.A: (214, 75, 74),   # red
    Team.B: (55, 138, 221),  # blue
}
GRID_COLOR = (60, 60, 60)
OBSTACLE_COLOR = (120, 120, 120)
BG_COLOR = (25, 25, 28)

# key -> commander directive (issued to the player-controlled team)
_ORDER_KEYS = {
    "1": Order.ATTACK,
    "2": Order.DEFEND,
    "3": Order.FOCUS,
    "4": Order.RETREAT,
    "5": Order.NONE,
    "0": Order.NONE,
}


class PygameRenderer:
    """Thin pygame adapter that draws a headless World. No AI logic here."""

    def __init__(self, world: World, cell_px: int = 24) -> None:
        if pygame is None:
            raise RuntimeError("pygame is not installed; cannot render")
        pygame.init()  # required before using display / font modules
        self._world = world
        self._cell = cell_px
        self._player_team = Team.B  # which team the human commands (toggle with T)
        self._last_order = Order.NONE  # last directive the human issued (kept across loop restarts)
        w = world.width() * cell_px
        h = world.height() * cell_px
        self._screen = pygame.display.set_mode((w, h))
        # Make it obvious the window must be clicked before key input works.
        pygame.display.set_caption("game-ai-toolkit  --  CLICK HERE, then press 1-5 / T")
        self._clock = pygame.time.Clock()
        # NOTE: do NOT use pygame.font.SysFont — on some Windows installs a
        # corrupted font registry entry makes initsysfonts_win32() crash with
        # "expected str, bytes or os.PathLike object, not int". Use the bundled
        # default font (no system scan) instead.
        try:
            self._font = pygame.font.Font(None, 13)
        except Exception:
            self._font = None  # HUD text degrades gracefully if fonts are broken

    def draw(self, show_debug: bool = True) -> None:
        self._screen.fill(BG_COLOR)
        # grid + obstacles
        for y in range(self._world.height()):
            for x in range(self._world.width()):
                rect = pygame.Rect(x * self._cell, y * self._cell, self._cell, self._cell)
                if (x, y) in self._world._obstacles:
                    pygame.draw.rect(self._screen, OBSTACLE_COLOR, rect)
                else:
                    pygame.draw.rect(self._screen, GRID_COLOR, rect, 1)
        # agents
        for a in self._world.get_agents():
            if not a.is_alive():
                continue
            cx = int(a.get_position().x * self._cell + self._cell / 2)
            cy = int(a.get_position().y * self._cell + self._cell / 2)
            r = max(5, int(self._cell / 2.5))
            color = TEAM_COLORS.get(a.get_team(), (200, 200, 200))
            pygame.draw.circle(self._screen, color, (cx, cy), r)
            pygame.draw.circle(self._screen, (255, 255, 255), (cx, cy), r, 1)
            hp_ratio = a.hp() / a.max_hp()
            bar_w = self._cell
            pygame.draw.rect(self._screen, (40, 40, 40), pygame.Rect(cx - bar_w // 2, cy - r - 6, bar_w, 3))
            pygame.draw.rect(self._screen, (90, 200, 90), pygame.Rect(cx - bar_w // 2, cy - r - 6, int(bar_w * hp_ratio), 3))
            if show_debug:
                self._draw_debug(a, cx, cy)
        # HUD: top status bar (counts + current directive + which team you command)
        bar_h = 22
        pygame.draw.rect(self._screen, (15, 15, 18), pygame.Rect(0, 0, self._screen.get_width(), bar_h))
        a_alive = self._world.alive_count(Team.A)
        b_alive = self._world.alive_count(Team.B)
        oa = self._world.get_order(Team.A).name
        ob = self._world.get_order(Team.B).name
        if self._font is not None:
            you_a = " (YOU)" if self._player_team is Team.A else ""
            you_b = " (YOU)" if self._player_team is Team.B else ""
            self._screen.blit(
                self._font.render(f"RED {a_alive} [{oa}]{you_a}", True, TEAM_COLORS[Team.A]), (8, 5))
            self._screen.blit(
                self._font.render(f"BLUE {b_alive} [{ob}]{you_b}", True, TEAM_COLORS[Team.B]),
                (self._screen.get_width() - 160, 5))
            self._screen.blit(
                self._font.render(f"step {self._world.step()}  ({self._world.step() * 0.1:.1f}s)",
                                  True, (220, 220, 220)), (self._screen.get_width() // 2 - 70, 5))
        # bottom control hint
        hint_h = 16
        pygame.draw.rect(self._screen, (15, 15, 18),
                         pygame.Rect(0, self._screen.get_height() - hint_h, self._screen.get_width(), hint_h))
        if self._font is not None:
            hint = "1 Attack   2 Defend   3 Focus   4 Retreat   5 Auto   T switch team"
            self._screen.blit(self._font.render(hint, True, (180, 180, 180)),
                              (8, self._screen.get_height() - hint_h + 1))
        pygame.display.flip()

    def _draw_debug(self, agent, cx, cy) -> None:
        if self._font is None:
            return
        text = self._font.render(f"{agent.get_state()} {int(agent.hp())}", True, (230, 230, 230))
        self._screen.blit(text, (cx + 6, cy - 6))

    def set_player_team(self, team: Team) -> None:
        self._player_team = team

    def get_player_team(self) -> Team:
        return self._player_team

    def get_last_order(self) -> Order:
        return self._last_order

    def _apply_key(self, key) -> None:
        name = pygame.key.name(key)
        if name in _ORDER_KEYS:
            order = _ORDER_KEYS[name]
            self._world.set_order(self._player_team, order)
            self._last_order = order
        elif name in ("t", "tab"):
            self._player_team = Team.A if self._player_team is Team.B else Team.B

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                self._apply_key(event.key)
        return True

    def tick_frame(self, dt: float, show_debug: bool = True) -> bool:
        if not self.handle_events():
            return False
        self._world.tick(dt)
        self.draw(show_debug)
        self._clock.tick(30)
        return True

    def set_world(self, world: World) -> None:
        """Swap the simulated world (used by loop mode to restart a match)."""
        self._world = world
