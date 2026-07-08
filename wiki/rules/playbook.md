# Songs of Syx — Starter Playbook

> Injected into the overlord system prompt every tick. Edit here in Obsidian; bridge loads from this file.

Follow until **population > 20**.

## Core facts

- You control the settlement via JSON commands only. You cannot click the UI.
- Throne coordinates are in game state — **always** anchor builds within ~40 tiles of throne (x,y).
- **Never** build at (0,0) unless throne is at (0,0). Wrong coords cause repeated failures.
- Only `build` and `set_speed` actually work. `set_policy`, `recruit`, `set_tax`, `set_ration`, `demolish` are **not** implemented — do not use them.
- After placing buildings, always `set_speed` to **2** (normal) so construction proceeds.

## Day 0 priorities (population = 0)

1. Read throne position from state. All x/y in build commands must be near throne.
2. Build **home** — indoor room, attracts settlers. Try `throne.x+2`, `throne.y` or spiral offsets.
3. Build **farm** or **pasture** — outdoor food (farm = area, default 4×4).
4. Build **well** — outdoor single tile; only one well until population grows.
5. **Stockpile / woodcutter** — bridge blocks until pop ≥ 15 (stockpile always; woodcutter unless ^ on mapRows at target).
6. Do **not** spam stockpile/woodcutter — they waste ticks on missing crates or sparse trees.

## Pop 10–14

- Focus: **home**, **farm**, **well**, `set_speed` 2.
- No stockpile. No woodcutter unless mapRows shows `^` at your coordinates.

## Pop 15+

- Stockpile on indoor `.` without overlapping rooms.
- Woodcutter on `^` tiles only.

## Learning (not static rules)

- **SESSION MEMORY** — failures and orders from *this* game.
- **PERSISTENT KNOWLEDGE** — blacklisted coords and patterns learned across *all* games (auto-updated by the bridge). **Always read both before building.**
- Never retry a blacklisted coordinate. If unsure, pick a new spot 10+ tiles from throne.

## Room types (target names)

| Category | Targets |
|----------|---------|
| Indoor area | stockpile, home |
| Outdoor area | farm, pasture, orchard, woodcutter |
| Outdoor single | well, fishery, hunter |

## Build command format

```json
{"action":"build","target":"home","x":386,"y":128,"params":{"width":4,"height":4}}
```

## Strategy

- One focused goal per tick. Max 2 build attempts + `set_speed`.
- If last 3 ticks failed the same action, switch strategy entirely.
