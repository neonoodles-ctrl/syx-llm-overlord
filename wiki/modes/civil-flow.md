# Civil Flow State

Expert autopilot mode. Full wiki in system prompt. Minimize wasted ticks; maximize stable growth.

## Phase 0 — Day 0, pop 0

1. Parse throne `(x,y)` and mapRows center `T`.
2. Build **home** on nearest indoor-capable `.` within 20 tiles.
3. Build **farm** (4×4) on outdoor `.` — not on `+`, `~`, `^`, `X`.
4. Build **well** once on outdoor `.`.
5. `set_speed` **2** every tick until construction visibly progresses.

## Phase 1 — pop 1–10

- Maintain food + water + housing headroom (more homes than pop).
- Do not woodcutter until pop ≥ 10 unless `^` tiles adjacent to placement.
- Avoid stockpile until crates viable; if stockpile fails twice, skip until pop 10.
- TmpArea: farm-only recovery; never retry blacklisted coords.

## Phase 2 — pop 10–20

- **Stockpile** when indoor `.` available.
- **Woodcutter** on `^` tiles only.
- Expand homes in a line along open `.` tiles (not stacked on same column).
- Builder room optional if construction slow.

## Phase 3 — pop 20+

- Diversify: fishery/hunter/pasture per terrain.
- Keep happiness services in mind (see game state).
- One strategic goal per tick; max 2 commands.

## Expert rules

- Read **PERSISTENT KNOWLEDGE** every tick — hard blacklist.
- Read **SESSION MEMORY** for this run's failures.
- Honor **PLAYER MAP PINS** as priority coordinates.
- Reasoning: 2 sentences max. Mood: confident or cautious.
