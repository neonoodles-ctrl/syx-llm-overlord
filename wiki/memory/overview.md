# Memory system overview

The overlord has **two kinds of memory**:

## 1. Playbook (static rules)

- Wiki: [[../rules/playbook]]
- Read **every tick** from `wiki/rules/playbook.md` (in the repo)
- Edit in Obsidian or any editor — no bridge restart needed

## 2. Session memory (dynamic log)

- File: `logs/overlord-memory.jsonl` (repo root, or `SYX_MEMORY_PATH`)
- Append-only JSONL — survives bridge restarts; clear manually or start fresh
- Last ~30 entries injected into each tick as **SESSION MEMORY**
- Dashboard panel: **Session Memory** on http://localhost:3847

### Live wiki mirror

Each tick the bridge writes [[live-log]] — a human-readable tail of the JSONL. Open in Obsidian for a running diary of failures and plans.

Manual sync: `python3 scripts/sync-memory-to-wiki.py`

### What gets logged automatically

| Kind | When |
|------|------|
| `tick` | Every decision cycle — plan + all command results |
| `failure` | Each failed command (extra line for learning) |
| `order` | Player direct order from dashboard |
| `note` | Manual note via API |

### Why it exists

The LLM only sees the last 3 ticks in `recent_history`. Memory keeps **failures and successes** across many ticks so it stops repeating "build well at (0,0)" forever.

### Promote to wiki

When you learn something durable (e.g. "throne on this map is always 384,128"), add it to [[../rules/playbook]] — don't rely on JSONL alone.

### Chat with the overlord

Dashboard **Talk to the Overlord** sends `POST /api/instruct` and returns an immediate `reply` field. Chat is logged as `chat_user` / `chat_reply` kinds in the JSONL.
