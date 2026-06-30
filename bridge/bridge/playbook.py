"""Songs of Syx starter knowledge injected into the overlord system prompt."""
from __future__ import annotations

from .paths import playbook_path, wiki_dir

VAULT_PLAYBOOK = playbook_path()

_DEFAULT_PLAYBOOK = """
SONGS OF SYX — STARTER PLAYBOOK (follow this until population > 20)

## Core facts
- You control the settlement via JSON commands only. You cannot click the UI.
- Throne coordinates are in game state — ALWAYS anchor builds within ~20 tiles of throne (x,y).
- NEVER build at (0,0) unless throne is at (0,0). Wrong coords cause repeated failures.
- Only `build`, `clear_placement`, and `set_speed` work. set_policy, recruit, set_tax, set_ration, demolish are NOT implemented.
- After placing buildings, always set_speed to 2 (normal) so construction proceeds.
- Hard limit: builds within 20 tiles of throne (bridge guard enforces this).

## TmpArea recovery
- TmpArea/_HOME error: clear_placement once, then farm only (farms relocate to open tiles).
- After 8 TmpArea failures bridge enters farms-only mode until recovery.
- Never retry same coordinates. Use mapRows: . = open, + = room, T = throne.
- New game clears session memory and coord blacklist automatically.

## Day 0 priorities (population = 0)
1. Read throne position from state. All x/y in build commands must be near throne.
2. Build home — indoor room, attracts settlers. Try throne.x+2, throne.y or spiral offsets.
3. Build farm or pasture — outdoor food (farm = area, default 4x4).
4. Build well — outdoor single tile, only ONE well until population grows.
5. Stockpile is tricky early — build home/farm first; retry elsewhere if crates fail.
6. Do NOT spam the same failed build twice — use clear_placement then farm after TmpArea errors.

## Learning (not static rules)
- SESSION MEMORY = failures and orders from THIS game.
- PERSISTENT KNOWLEDGE = blacklisted coords and patterns learned across ALL games (auto-updated). Read both before every build.
- Never retry a blacklisted coordinate. If unsure, pick a new spot 10+ tiles from throne.

## Room types (target names)
- Indoor area: stockpile, home
- Outdoor area: farm, pasture, orchard, woodcutter
- Outdoor single: well, fishery, hunter

## Build command format
{"action":"build","target":"home","x":386,"y":128,"params":{"width":4,"height":4}}

## Strategy
- One focused goal per tick. Max 1 build + set_speed.
- If last 3 ticks failed, switch to farm or clear_placement.
- Prefer mapRows open tiles within 20 tiles of throne.
"""


def load_playbook() -> str:
    """Load playbook from Obsidian wiki; fall back to embedded default."""
    if VAULT_PLAYBOOK.is_file():
        raw = VAULT_PLAYBOOK.read_text(encoding="utf-8")
        # Strip YAML frontmatter if present
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                raw = parts[2].lstrip("\n")
        return raw.strip()
    return _DEFAULT_PLAYBOOK.strip()


def _strip_frontmatter(raw: str) -> str:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip("\n").strip()
    return raw.strip()


def _read_wiki(relative: str) -> str:
    path = wiki_dir() / relative
    if path.is_file():
        return _strip_frontmatter(path.read_text(encoding="utf-8"))
    return ""


def load_mode_context(personality_id: str) -> str:
    """Extra wiki-backed prompt block for game modes."""
    pid = (personality_id or "").strip().lower()
    if pid == "teacher":
        body = _read_wiki("modes/teacher.md")
        return f"\n\n--- TEACHER MODE GUIDE ---\n{body}\n" if body else ""
    if pid == "civil_flow":
        chunks = [
            ("CIVIL FLOW STATE — expert doctrine", _read_wiki("modes/civil-flow.md")),
            ("ROOM TYPES (wiki)", _read_wiki("rules/rooms.md")),
            ("FAILURES (wiki)", _read_wiki("rules/failures.md")),
            ("COMMANDS (wiki)", _read_wiki("rules/commands.md")),
        ]
        parts = []
        for title, text in chunks:
            if text:
                parts.append(f"--- {title} ---\n{text}")
        return ("\n\n" + "\n\n".join(parts) + "\n") if parts else ""
    return ""


# Loaded once at import; reload via load_playbook() each tick in llm_brain
SOS_PLAYBOOK = load_playbook()
