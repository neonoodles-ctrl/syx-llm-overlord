# JSONL log format

Path: `/home/hermesprime/GAMES/Neonoodles-ctrl/syx/logs/overlord-memory.jsonl`

One JSON object per line.

## Example entries

```json
{"ts":"2026-06-29T11:22:16+00:00","kind":"tick","tick":18,"day":0,"text":"Tick 18 day=0 pop=0 throne=(384,128). Plan: Build home near throne. Results: OK build home @(386,128): Built _HOME..."}
{"ts":"2026-06-29T11:22:16+00:00","kind":"failure","tick":18,"day":0,"text":"FAILED build well at (5,5): WELL_NORMAL not placeable..."}
{"ts":"2026-06-29T11:30:00+00:00","kind":"order","text":"Player order: Stop wells. Focus on homes."}
{"ts":"2026-06-29T11:31:00+00:00","kind":"note","text":"Throne confirmed 384,128 on this save."}
```

## Fields

| Field | Description |
|-------|-------------|
| `ts` | ISO timestamp UTC |
| `kind` | `tick` \| `failure` \| `order` \| `note` |
| `tick` | Bridge tick number (optional) |
| `day` | In-game day (optional) |
| `text` | Human-readable line for LLM prompt |

## Limits

- Max 500 entries on disk (trimmed automatically)
- Last 30 entries in LLM prompt
