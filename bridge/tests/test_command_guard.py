"""Tests for command_guard pre-flight validation."""
from __future__ import annotations

import unittest

from bridge.command_guard import (
    validate_command,
    apply_timeout_backoff,
    filter_commands,
    is_timeout_result,
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


if __name__ == "__main__":
    unittest.main()
