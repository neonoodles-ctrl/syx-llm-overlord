"""Songs of Syx starter knowledge injected into the overlord system prompt."""
from __future__ import annotations

from .paths import playbook_path

VAULT_PLAYBOOK = playbook_path()

_DEFAULT_PLAYBOOK = """
SONGS OF SYX — STARTER PLAYBOOK (follow this until population > 20)

## Core facts
- You control the settlement via JSON commands only. You cannot click the UI.
- Throne coordinates are in game state — ALWAYS anchor builds within ~20 tiles of throne (x,y).
- NEVER build at (0,0) unless throne is at (0,0). Wrong coords cause repeated failures.
- Only `build` and `set_speed` actually work. `set_policy`, `recruit`, `set_tax`, `set_ration`, `demolish` are NOT implemented — do not use them.
- After placing buildings, always `set_speed` to 2 (normal) so construction proceeds.

## Day 0 priorities (population = 0)
1. Read throne position from state. All x/y in build commands must be near throne.
2. Build **home** (alias: house, housing) — indoor room, attracts settlers. Try throne.x+2, throne.y or spiral offsets.
3. Build **farm** or **pasture** — outdoor food (farm = area, default 4x4).
4. Build **well** — outdoor single tile, only ONE well until population grows. Needs clear outdoor tile.
5. **Stockpile** is tricky — indoor area room; failures like "insufficient Crates" mean bad location or blocked tiles. Try a different spot near throne, not on existing rooms.
6. Do NOT spam the same failed build 3+ times. Change room type or coordinates.

## Room types (target names)
- Indoor area: stockpile, home
- Outdoor area: farm, pasture, orchard, woodcutter (use params width/height, default 4)
- Outdoor single: well, woodcutter (item), fishery, hunter
- Logistics later: export, import, hauler, transport

## Build command format
{"action":"build","target":"home","x":386,"y":128,"params":{"width":4,"height":4}}
- x,y required. For area rooms add width/height (4-6 is fine early game).

## Reading failures (learn from memory log)
- "not placeable" / "blocked" / "Must not be placed on room" → try adjacent tile, different room, or outdoor vs indoor
- "insufficient: Crates" on stockpile → wrong spot; build home or farm first, retry stockpile elsewhere later
- "Out of bounds" → coordinates invalid
- "timed out" → game busy; next tick retry ONE command only
- "Unknown room type" → use aliases from playbook (home, well, farm, stockpile, woodcutter)

## Mid-game (population > 0)
- Keep happiness up: food (farm/pasture/fishery), water (well), housing capacity (more homes)
- woodcutter + mine for industry when pop > 10
- builder room speeds construction
- tavern/market for happiness later

## Strategy
- One focused goal per tick. Max 2 build attempts + set_speed.
- If last 3 ticks failed the same action, switch strategy entirely.
- Prefer proven coordinates from SESSION MEMORY over guessing.
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


# Loaded once at import; reload_llm_brain() re-imports via module reload if needed
SOS_PLAYBOOK = load_playbook()
