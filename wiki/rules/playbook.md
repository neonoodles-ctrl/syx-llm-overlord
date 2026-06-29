# Songs of Syx — Starter Playbook

> Injected into the overlord system prompt every tick. Edit here in Obsidian; bridge loads from this file.

Follow until **population > 20**.

## Core facts

- You control the settlement via JSON commands only. You cannot click the UI.
- Throne coordinates are in game state — **always** anchor builds within ~20 tiles of throne (x,y).
- **Never** build at (0,0) unless throne is at (0,0). Wrong coords cause repeated failures.
- Only `build` and `set_speed` actually work. `set_policy`, `recruit`, `set_tax`, `set_ration`, `demolish` are **not** implemented — do not use them.
- After placing buildings, always `set_speed` to **2** (normal) so construction proceeds.

## Day 0 priorities (population = 0)

1. Read throne position from state. All x/y in build commands must be near throne.
2. Build **home** (alias: house, housing) — indoor room, attracts settlers. Try `throne.x+2`, `throne.y` or spiral offsets.
3. Build **farm** or **pasture** — outdoor food (farm = area, default 4×4).
4. Build **well** — outdoor single tile; only one well until population grows. Needs clear outdoor tile.
5. **Stockpile** is tricky — indoor area room; "insufficient Crates" means bad location or blocked tiles. Build home/farm first; retry stockpile elsewhere.
6. Do **not** spam the same failed build 3+ times. Change room type or coordinates.

## Room types (target names)

| Category | Targets |
|----------|---------|
| Indoor area | stockpile, home |
| Outdoor area | farm, pasture, orchard, woodcutter |
| Outdoor single | well, fishery, hunter |
| Logistics (later) | export, import, hauler, transport |

## Build command format

```json
{"action":"build","target":"home","x":386,"y":128,"params":{"width":4,"height":4}}
```

- `x`, `y` required.
- Area rooms: `params.width` / `params.height` (4–6 early game).

## Reading failures

See [[failures]] — failures are also logged to [[../memory/overview|session memory]].

## Mid-game (population > 0)

- Happiness: food (farm/pasture/fishery), water (well), housing (more homes).
- Industry: woodcutter + mine when pop > 10.
- **builder** room speeds construction.
- tavern/market for happiness later.

## Strategy

- One focused goal per tick. Max 2 build attempts + `set_speed`.
- If last 3 ticks failed the same action, switch strategy entirely.
- Prefer proven coordinates from **SESSION MEMORY** over guessing.
