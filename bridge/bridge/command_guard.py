"""Pre-flight command validation before hitting the game mod API."""
from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING

from .map_constants import MAX_THRONE_DISTANCE
from .models import Command, GameState

if TYPE_CHECKING:
    from .knowledge import OverlordKnowledge
EARLY_GAME_POP_THRESHOLD = 10
INDUSTRY_POP_THRESHOLD = 15
TMPAREA_FARMS_ONLY_AFTER = 8
TMPAREA_CLEAR_EVERY = 1
FOREST_TILE_CHARS = frozenset({"^"})

# Normalized room tokens blocked until population grows (wood/stockpile handled separately)
EARLY_GAME_BLOCKED = frozenset({
    "hunter", "hunter_normal",
    "pasture", "pasture_aur",
    "fishery", "fishery_normal", "orchard", "orchard_fruit",
    "mine", "mine_clay", "mine_stone", "mine_ore",
    "graveyard", "graveyard_normal", "hauler", "_hauler",
    "import", "export", "transport",
})

WOODCUTTER_TARGETS = frozenset({"woodcutter", "_woodcutter"})
STOCKPILE_TARGETS = frozenset({"stockpile", "_stockpile"})
WELL_TARGETS = frozenset({"well", "wellnormal", "well_normal"})
COTTON_FARM_MARKERS = frozenset({"cotton", "farmcotton"})

WELL_FAIL_BACKOFF_AFTER = 3
WELL_FAIL_BACKOFF_TICKS = 10

# When TmpArea saturation detected — only outdoor area farms relocate successfully
FARMS_ONLY_ALLOWED = frozenset({
    "farm", "pasture", "orchard", "cotton", "farm_cotton",
    "farm_grain", "farm_veg", "farm_herb", "farm_mushroom",
})

# Obvious bad coordinates the LLM hallucinates
BAD_COORDS = frozenset({(0, 0), (100, 100), (300, 300)})

TIMEOUT_BACKOFF_THRESHOLD = 3

HOME_TARGETS = frozenset({"home", "_home", "house", "housing"})
HOME_HEADROOM = 2
BUILD_WAIT_BRIDGE_TICKS = 6

_tmparea_streak = 0
_farms_only = False
_well_fail_streak = 0
_well_blocked_ticks = 0
_build_wait_ticks = 0
_session_build_counts: dict[str, int] = {"home": 0, "farm": 0, "well": 0}


def reset_session_guard() -> None:
    """Clear TmpArea / farms-only state for a new game."""
    global _tmparea_streak, _farms_only, _well_fail_streak, _well_blocked_ticks, _session_build_counts, _build_wait_ticks
    _tmparea_streak = 0
    _farms_only = False
    _well_fail_streak = 0
    _well_blocked_ticks = 0
    _build_wait_ticks = 0
    _session_build_counts = {"home": 0, "farm": 0, "well": 0}


def tick_guard_cooldowns(state: GameState | None = None) -> None:
    """Call once per bridge decision tick."""
    global _well_blocked_ticks, _build_wait_ticks
    if _well_blocked_ticks > 0:
        _well_blocked_ticks -= 1
    if state is not None and not _construction_pending(state):
        _build_wait_ticks = 0
    elif _build_wait_ticks > 0:
        _build_wait_ticks -= 1


def farms_only_active() -> bool:
    return _farms_only


def should_clear_placement() -> bool:
    """Auto-send clear_placement every N TmpArea failures."""
    return _tmparea_streak > 0 and _tmparea_streak % TMPAREA_CLEAR_EVERY == 0


def record_clear_placement_outcome(success: bool) -> None:
    """Exit farms-only mode once TmpArea ghosts are cleared in-game."""
    global _tmparea_streak, _farms_only
    if success:
        _tmparea_streak = 0
        _farms_only = False


def record_build_outcome(success: bool, message: str, target: str | None) -> None:
    """Track TmpArea streak and enable farms-only mode."""
    global _tmparea_streak, _farms_only, _well_fail_streak, _well_blocked_ticks, _session_build_counts, _build_wait_ticks
    msg = (message or "").lower()
    norm = _normalize_target(target)
    if success:
        _tmparea_streak = max(0, _tmparea_streak - 2)
        if _is_well_target(norm):
            _well_fail_streak = 0
        _count_successful_build(message or "")
        _build_wait_ticks = BUILD_WAIT_BRIDGE_TICKS
        return
    if _is_well_target(norm) and (
        "tmparea" in msg.replace(" ", "") or "well" in msg and "error" in msg
    ):
        _well_fail_streak += 1
        if _well_fail_streak >= WELL_FAIL_BACKOFF_AFTER:
            _well_blocked_ticks = WELL_FAIL_BACKOFF_TICKS
    if "tmparea" in msg.replace(" ", "") or "_home error" in msg or "collision" in msg:
        _tmparea_streak += 1
        if _tmparea_streak >= TMPAREA_FARMS_ONLY_AFTER:
            _farms_only = True


def guard_status() -> dict:
    return {
        "tmparea_streak": _tmparea_streak,
        "farms_only": _farms_only,
        "max_throne_distance": MAX_THRONE_DISTANCE,
        "industry_pop_threshold": INDUSTRY_POP_THRESHOLD,
        "well_blocked_ticks": _well_blocked_ticks,
        "well_fail_streak": _well_fail_streak,
        "build_wait_ticks": _build_wait_ticks,
        "session_builds": dict(_session_build_counts),
    }


def _construction_pending(state: GameState) -> bool:
    con = state.construction or {}
    try:
        instances = int(con.get("instances") or 0)
        area = int(con.get("area") or 0)
    except (TypeError, ValueError):
        return False
    return instances > 0 or area > 0


def _construction_summary(state: GameState) -> str:
    con = state.construction or {}
    instances = con.get("instances", 0)
    area = con.get("area", 0)
    return f"{instances} site(s), {area} tile(s)"


def _count_successful_build(message: str) -> None:
    msg = message.upper()
    if "_HOME" in msg or " BUILT HOME" in msg:
        _session_build_counts["home"] = _session_build_counts.get("home", 0) + 1
    elif "WELL" in msg:
        _session_build_counts["well"] = _session_build_counts.get("well", 0) + 1
    elif "FARM" in msg:
        _session_build_counts["farm"] = _session_build_counts.get("farm", 0) + 1


def _is_home_target(target: str) -> bool:
    return any(t in target for t in HOME_TARGETS) or target.startswith("home")


def _home_count(state: GameState) -> int:
    rc = state.roomCounts or {}
    for key in ("home", "_home", "HOME"):
        if key in rc:
            try:
                return int(rc[key])
            except (TypeError, ValueError):
                pass
    return _session_build_counts.get("home", 0)


def _farm_count(state: GameState) -> int:
    rc = state.roomCounts or {}
    for key in ("farm", "farm_grain", "FARM"):
        if key in rc:
            try:
                return int(rc[key])
            except (TypeError, ValueError):
                pass
    return _session_build_counts.get("farm", 0)


def _well_count(state: GameState) -> int:
    rc = state.roomCounts or {}
    for key in ("well", "well_normal", "WELL"):
        if key in rc:
            try:
                return int(rc[key])
            except (TypeError, ValueError):
                pass
    return _session_build_counts.get("well", 0)


def _game_needs_speed(state: GameState) -> bool:
    speed = state.gameSpeed or {}
    try:
        paused = float(speed.get("paused") or 0) > 0
        target = float(speed.get("target") if speed.get("target") is not None else 2)
        actual = float(speed.get("actual") if speed.get("actual") is not None else target)
    except (TypeError, ValueError):
        return False
    return paused or target < 1 or actual < 0.25


def apply_gameplay_adjustments(
    commands: list[Command],
    state: GameState,
) -> tuple[list[Command], str | None]:
    """When paused/slow or construction pending, prioritize set_speed over builds."""
    builds = [c for c in commands if c.action == "build"]
    non_builds = [c for c in commands if c.action != "build"]

    if _construction_pending(state) and builds:
        speeds = [c for c in non_builds if c.action == "set_speed"]
        note = (
            f"construction in progress ({_construction_summary(state)}) — "
            "set_speed only until finished"
        )
        if speeds:
            return speeds[:1], note
        return [Command(action="set_speed", params={"value": 2})], note

    if not _game_needs_speed(state):
        if len(builds) > 1:
            first_build = builds[0]
            return [first_build, *non_builds], "one build per tick — dropped extra builds"
        return commands, None
    if builds:
        return [Command(action="set_speed", params={"value": 2})], "game paused/slow — set_speed 2 instead of build"
    speeds = [c for c in commands if c.action == "set_speed"]
    if speeds:
        return speeds[:1], None
    return [Command(action="set_speed", params={"value": 2})], "game paused — injecting set_speed 2"


def _map_origin(state: GameState) -> tuple[int, int]:
    """World tile at mapRows[0][0]."""
    if state.mapFull and state.mapX2 >= state.mapX1:
        return state.mapX1, state.mapY1
    if state.mapRadius:
        return state.mapCenterX - state.mapRadius, state.mapCenterY - state.mapRadius
    return 0, 0


def _map_char_at(state: GameState, x: int, y: int) -> str | None:
    if not state.mapRows:
        return None
    ox, oy = _map_origin(state)
    col = x - ox
    row = y - oy
    if row < 0 or row >= len(state.mapRows):
        return None
    line = state.mapRows[row]
    if col < 0 or col >= len(line):
        return None
    return line[col]


def _has_forest_near_throne(state: GameState) -> bool:
    """True if mapRows shows ^ forest within build radius of throne."""
    tx, ty = _throne_xy(state)
    if tx is None or ty is None or not state.mapRows:
        return False
    ox, oy = _map_origin(state)
    for row_i, line in enumerate(state.mapRows):
        for col_i, ch in enumerate(line):
            if ch not in FOREST_TILE_CHARS:
                continue
            wx = ox + col_i
            wy = oy + row_i
            if _distance(wx, wy, tx, ty) <= MAX_THRONE_DISTANCE:
                return True
    return False


def _is_forest_build_site(state: GameState, x: int, y: int, reach: int = 2) -> bool:
    """Woodcutter needs trees at or near the requested coordinates."""
    for dx in range(-reach, reach + 1):
        for dy in range(-reach, reach + 1):
            ch = _map_char_at(state, x + dx, y + dy)
            if ch in FOREST_TILE_CHARS:
                return True
    return False


def _is_woodcutter_target(target: str) -> bool:
    return any(t in target for t in WOODCUTTER_TARGETS)


def _is_stockpile_target(target: str) -> bool:
    return any(t in target for t in STOCKPILE_TARGETS)


def _is_well_target(target: str) -> bool:
    return any(t in target for t in WELL_TARGETS) or target.startswith("well")


def _rewrite_build(cmd: Command) -> Command:
    """Route generic/cotton farms to food grain."""
    if cmd.action != "build":
        return cmd
    norm = _normalize_target(cmd.target)
    if norm == "farm" or norm in COTTON_FARM_MARKERS or ("farm" in norm and "cotton" in norm):
        return cmd.model_copy(update={"target": "farm_grain"})
    return cmd


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

    if _construction_pending(state):
        return False, (
            f"construction in progress ({_construction_summary(state)}) — "
            "wait for settlers to finish; use set_speed 2 only"
        )

    if _build_wait_ticks > 0:
        return False, (
            f"build wait ({_build_wait_ticks} bridge ticks left) — "
            "confirm current build finished before placing another"
        )

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

    if _is_well_target(target) and _well_blocked_ticks > 0:
        return False, (
            f"well backoff ({_well_blocked_ticks} ticks left) after repeated TmpArea failures — "
            "build farm_grain or home instead"
        )

    if _is_home_target(target):
        homes = _home_count(state)
        if homes >= pop + HOME_HEADROOM:
            return False, (
                f"home headroom met ({homes} homes for pop {pop}, max pop+{HOME_HEADROOM}) — "
                "build farm_grain, wait for immigration, or set_speed 2"
            )

    if _is_stockpile_target(target) and pop < INDUSTRY_POP_THRESHOLD:
        return False, (
            f"stockpile blocked until population >= {INDUSTRY_POP_THRESHOLD} "
            f"(current {pop}) — early stockpiles fail on missing crates; "
            "use home, farm, well"
        )

    if _is_woodcutter_target(target) and pop < INDUSTRY_POP_THRESHOLD:
        if not _has_forest_near_throne(state):
            return False, (
                f"woodcutter blocked until pop >= {INDUSTRY_POP_THRESHOLD} "
                f"(current {pop}) — no ^ forest tiles within {MAX_THRONE_DISTANCE} "
                "tiles of throne on mapRows; expand farms/homes"
            )
        if not _is_forest_build_site(state, x, y):
            return False, (
                f"woodcutter at ({x},{y}) has no ^ forest on mapRows nearby — "
                "pick coordinates on a ^ tile within "
                f"{MAX_THRONE_DISTANCE} of throne"
            )

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
    build_allowed = False
    for cmd in commands:
        cmd = _rewrite_build(cmd)
        if cmd.action == "build" and build_allowed:
            rejected.append((cmd, "one build per decision cycle — wait for current build to finish"))
            continue
        ok, reason = validate_command(cmd, state, knowledge)
        if ok:
            allowed.append(cmd)
            if cmd.action == "build":
                build_allowed = True
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
