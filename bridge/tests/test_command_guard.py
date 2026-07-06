"""Tests for command_guard pre-flight validation."""
from __future__ import annotations

import unittest

from bridge.command_guard import (
    validate_command,
    apply_timeout_backoff,
    apply_gameplay_adjustments,
    filter_commands,
    is_timeout_result,
    record_build_outcome,
    reset_session_guard,
    _has_forest_near_throne,
)
from bridge.knowledge import OverlordKnowledge
from bridge.models import Command, GameState
from pathlib import Path
import tempfile


def _state(pop: int = 5, tx: int = 400, ty: int = 160) -> GameState:
    return GameState(
        population={"total": pop},
        throne={"x": tx, "y": ty},
    )


class CommandGuardTests(unittest.TestCase):
    def test_blocks_far_from_throne(self):
        cmd = Command(action="build", target="home", x=100, y=100)
        ok, reason = validate_command(cmd, _state())
        self.assertFalse(ok)
        self.assertIn("100", reason or "")

    def test_blocks_early_game_hunter(self):
        cmd = Command(action="build", target="hunter", x=402, y=160)
        ok, reason = validate_command(cmd, _state(pop=3))
        self.assertFalse(ok)
        self.assertIn("population", reason or "")

    def test_allows_farm_early(self):
        cmd = Command(action="build", target="farm", x=402, y=160)
        ok, _ = validate_command(cmd, _state(pop=3))
        self.assertTrue(ok)

    def test_blacklist_coord(self):
        with tempfile.TemporaryDirectory() as tmp:
            k = OverlordKnowledge(path=Path(tmp) / "k.json")
            k.record_failure(
                action="build", target="home", x=405, y=160,
                message="_HOME error TmpArea",
            )
            k.record_failure(
                action="build", target="home", x=405, y=160,
                message="_HOME error TmpArea",
            )
            cmd = Command(action="build", target="farm", x=405, y=160)
            ok, reason = validate_command(cmd, _state(), k)
            self.assertFalse(ok)
            self.assertIn("blacklisted", reason or "")

    def test_timeout_backoff(self):
        cmds = [
            Command(action="build", target="home", x=410, y=160),
            Command(action="set_speed", params={"value": 2}),
        ]
        out, backoff = apply_timeout_backoff(cmds, 3)
        self.assertTrue(backoff)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].action, "set_speed")

    def test_is_timeout_result(self):
        self.assertTrue(is_timeout_result("Command timed out waiting for game thread"))

    def test_blocks_home_when_headroom_met(self):
        reset_session_guard()
        state = _state(pop=5)
        state.roomCounts = {"home": 8}
        cmd = Command(action="build", target="home", x=402, y=160)
        ok, reason = validate_command(cmd, state)
        self.assertFalse(ok)
        self.assertIn("headroom", reason or "")

    def test_apply_gameplay_adjustments_when_paused(self):
        state = _state()
        state.gameSpeed = {"paused": 1.0, "target": 0.0, "actual": 0.0}
        cmds = [Command(action="build", target="farm_grain", x=402, y=160)]
        out, note = apply_gameplay_adjustments(cmds, state)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].action, "set_speed")
        self.assertIn("set_speed", note or "")

    def test_blocks_build_when_construction_pending(self):
        state = _state()
        state.construction = {"instances": 1, "area": 4}
        cmd = Command(action="build", target="home", x=402, y=160)
        ok, reason = validate_command(cmd, state)
        self.assertFalse(ok)
        self.assertIn("construction in progress", reason or "")

    def test_apply_gameplay_strips_builds_when_construction_pending(self):
        state = _state()
        state.construction = {"instances": 2, "area": 8}
        cmds = [
            Command(action="build", target="farm_grain", x=402, y=160),
            Command(action="set_speed", params={"value": 2}),
        ]
        out, note = apply_gameplay_adjustments(cmds, state)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].action, "set_speed")
        self.assertIn("construction", note or "")

    def test_forest_near_throne_uses_map_full_origin(self):
        """mapFull exports index rows from mapX1/mapY1, not mapCenter - radius."""
        rows = ["." * 60 for _ in range(120)]
        row = list(rows[115])
        row[50] = "^"
        rows[115] = "".join(row)
        state = GameState(
            throne={"x": 120, "y": 180},
            mapRows=rows,
            mapRadius=40,
            mapCenterX=120,
            mapCenterY=180,
            mapFull=True,
            mapX1=50,
            mapY1=50,
            mapX2=109,
            mapY2=169,
        )
        self.assertTrue(_has_forest_near_throne(state))

    def test_forest_near_throne_false_without_forest_tiles(self):
        state = GameState(
            throne={"x": 120, "y": 180},
            mapRows=["." * 10 for _ in range(10)],
            mapRadius=40,
            mapCenterX=120,
            mapCenterY=180,
            mapFull=True,
            mapX1=50,
            mapY1=50,
            mapX2=59,
            mapY2=59,
        )
        self.assertFalse(_has_forest_near_throne(state))


if __name__ == "__main__":
    unittest.main()
