"""Pre-flight command validation before hitting the game mod API."""
from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING

from .models import Command, GameState

if TYPE_CHECKING:
    from .knowledge import OverlordKnowledge

MAX_THRONE_DISTANCE = 20
EARLY_GAME_POP_THRESHOLD = 10
TMPAREA_FARMS_ONLY_AFTER = 8
TMPAREA_CLEAR_EVERY = 1

# Normalized room tokens blocked until population grows
EARLY_GAME_BLOCKED = frozenset({
    "hunter", "hunter_normal", "woodcutter", "_woodcutter",
    "stockpile", "_stockpile", "pasture", "pasture_aur",
    "fishery", "fishery_normal", "orchard", "orchard_fruit",
    "mine", "mine_clay", "mine_stone", "mine_ore",
    "graveyard", "graveyard_normal", "hauler", "_hauler",
    "import", "export", "transport",
})

# When TmpArea saturation detected — only outdoor area farms relocate successfully
FARMS_ONLY_ALLOWED = frozenset({
    "farm", "pasture", "orchard", "cotton", "farm_cotton",
    "farm_grain", "farm_veg", "farm_herb", "farm_mushroom",
})

# Obvious bad coordinates the LLM hallucinates
BAD_COORDS = frozenset({(0, 0), (100, 100), (300, 300)})

TIMEOUT_BACKOFF_THRESHOLD = 3

_tmparea_streak = 0
_farms_only = False


def reset_session_guard() -> None:
    """Clear TmpArea / farms-only state for a new game."""
    global _tmparea_streak, _farms_only
    _tmparea_streak = 0
    _farms_only = False


def farms_only_active() -> bool:
    return _farms_only


def should_clear_placement() -> bool:
    """Auto-send clear_placement every N TmpArea failures."""
    return _tmparea_streak > 0 and _tmparea_streak % TMPAREA_CLEAR_EVERY == 0


def record_build_outcome(success: bool, message: str, target: str | None) -> None:
    """Track TmpArea streak and enable farms-only mode."""
    global _tmparea_streak, _farms_only
    msg = (message or "").lower()
    if success:
        _tmparea_streak = max(0, _tmparea_streak - 2)
        return
    if "tmparea" in msg.replace(" ", "") or "_home error" in msg or "collision" in msg:
        _tmparea_streak += 1
        if _tmparea_streak >= TMPAREA_FARMS_ONLY_AFTER:
            _farms_only = True


def guard_status() -> dict:
    return {
        "tmparea_streak": _tmparea_streak,
        "farms_only": _farms_only,
        "max_throne_distance": MAX_THRONE_DISTANCE,
    }


def _normalize_target(target: str | None) -> str:
    if not target:
        return ""
    return re.sub(r"[^a-z0-9_]", "", target.lower())


def _population(state: GameState) -> int:
    try:
        return int(state.population.get("total", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _throne_xy(state: GameState) -> tuple[int | None, int | None]:
    if not state.throne:
        return None, None
    try:
        return int(state.throne.get("x")), int(state.throne.get("y"))
    except (TypeError, ValueError):
        return None, None


def _distance(x: int, y: int, tx: int, ty: int) -> float:
    return math.hypot(x - tx, y - ty)


def validate_command(
    cmd: Command,
    state: GameState,
    knowledge: OverlordKnowledge | None = None,
) -> tuple[bool, str | None]:
    """Return (allowed, rejection_reason). rejection_reason set when blocked."""
    if cmd.action != "build":
        return True, None

    target = _normalize_target(cmd.target)
    x, y = cmd.x, cmd.y

    if x is None or y is None:
        return False, "build requires x and y coordinates"

    if (x, y) in BAD_COORDS:
        tx, ty = _throne_xy(state)
        if tx is None or ty is None or _distance(x, y, tx, ty) > 5:
            return False, f"coordinates ({x},{y}) are invalid — build near throne"

    tx, ty = _throne_xy(state)
    if tx is not None and ty is not None:
        dist = _distance(x, y, tx, ty)
        if dist > MAX_THRONE_DISTANCE:
            return False, (
                f"({x},{y}) is {dist:.0f} tiles from throne ({tx},{ty}) "
                f"(max {MAX_THRONE_DISTANCE})"
            )

    if _farms_only:
        allowed = any(f in target for f in FARMS_ONLY_ALLOWED)
        if not allowed:
            return False, (
                "farms-only mode (TmpArea saturation) — only farm/pasture/orchard builds; "
                "use clear_placement or new game to reset"
            )

    if knowledge is not None:
        blocked, reason = knowledge.is_blocked(cmd.action, cmd.target, x, y)
        if blocked:
            return False, reason

    pop = _population(state)
    if pop < EARLY_GAME_POP_THRESHOLD and target in EARLY_GAME_BLOCKED:
        return False, (
            f"{cmd.target} blocked until population >= {EARLY_GAME_POP_THRESHOLD} "
            f"(current {pop}) — use home, farm, well"
        )

    return True, None


def filter_commands(
    commands: list[Command],
    state: GameState,
    knowledge: OverlordKnowledge | None = None,
) -> tuple[list[Command], list[tuple[Command, str]]]:
    """Split commands into allowed list and (cmd, reason) rejections."""
    allowed: list[Command] = []
    rejected: list[tuple[Command, str]] = []
    for cmd in commands:
        ok, reason = validate_command(cmd, state, knowledge)
        if ok:
            allowed.append(cmd)
        elif reason:
            rejected.append((cmd, reason))
    return allowed, rejected


def apply_timeout_backoff(
    commands: list[Command],
    consecutive_timeouts: int,
) -> tuple[list[Command], bool]:
    """When game thread is saturated, only allow set_speed this tick."""
    if consecutive_timeouts < TIMEOUT_BACKOFF_THRESHOLD:
        return commands, False
    speed = [c for c in commands if c.action == "set_speed"]
    if speed:
        return speed[:1], True
    return [Command(action="set_speed", params={"value": 2})], True


def is_timeout_result(message: str) -> bool:
    return "timed out" in (message or "").lower()


def is_tmparea_result(message: str) -> bool:
    msg = (message or "").lower()
    return "tmparea" in msg.replace(" ", "") or "_home error" in msg
