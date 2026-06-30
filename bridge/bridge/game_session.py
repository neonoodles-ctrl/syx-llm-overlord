"""Detect new Songs of Syx saves so memory/knowledge reset per settlement."""
from __future__ import annotations

from .models import GameState


class GameSessionTracker:
    """Track throne/day signature; fire when the player starts a new game."""

    def __init__(self) -> None:
        self._last_throne: tuple[int | None, int | None] | None = None
        self._last_day: int | None = None
        self._initialized = False

    @staticmethod
    def _throne_xy(state: GameState) -> tuple[int | None, int | None]:
        if not state.throne:
            return None, None
        try:
            return int(state.throne.get("x")), int(state.throne.get("y"))
        except (TypeError, ValueError):
            return None, None

    @staticmethod
    def _day(state: GameState) -> int | None:
        if not state.gameTime:
            return None
        try:
            return int(state.gameTime.get("day", 0))
        except (TypeError, ValueError):
            return None

    def check_new_game(self, state: GameState) -> bool:
        """Return True once when we detect a new settlement / rolled-back save."""
        throne = self._throne_xy(state)
        day = self._day(state)

        if not self._initialized:
            self._initialized = True
            self._last_throne = throne
            self._last_day = day
            return False

        if throne[0] is not None and self._last_throne != throne:
            self._last_throne = throne
            self._last_day = day
            return True

        if day is not None and self._last_day is not None and day <= 1 and self._last_day >= 3:
            self._last_throne = throne
            self._last_day = day
            return True

        self._last_throne = throne
        self._last_day = day
        return False
