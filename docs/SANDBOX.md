# Sandbox instance — debug GitHub without touching your play setup

Run a **second copy** of the stack for public-repo work while your personal play instance keeps running.

## Two instances

| | **Play** (keep using) | **Sandbox** (GitHub / debug) |
|--|----------------------|------------------------------|
| Code | `/home/hermesprime/CODE/Boiler Room/_current/syx-llm-overlord` | `/home/hermesprime/CODE/Boiler Room/_current/syx-llm-overlord-github` |
| Git branch | `main` (local WIP) | `sandbox` (tracks `origin/main`) |
| Launcher | `/home/hermesprime/GAMES/Neonoodles-ctrl/syx/syx` | `/home/hermesprime/GAMES/Neonoodles-ctrl/syx-sandbox/syx-sandbox` |
| Dashboard | http://localhost:3847 | http://localhost:3848 |
| Logs / memory | `…/syx/logs/` | `…/syx-sandbox/logs/` |
| Mod API | `:47823` (shared — one game) | same |

The **game and mod JAR are shared** (one Songs of Syx process, one `:47823`). You can run **both bridges in parallel** for UI/API debugging. Full mod swaps require a game restart — use sandbox only when you intend to test a GitHub build.

## Quick start

```bash
# One-time bootstrap (worktree + venv + config)
bash "/home/hermesprime/CODE/Boiler Room/_current/syx-llm-overlord/scripts/sandbox-bootstrap.sh"

# Start sandbox bridge (safe while playing on :3847)
/home/hermesprime/GAMES/Neonoodles-ctrl/syx-sandbox/syx-sandbox bridge

# Run Python tests against GitHub tree
/home/hermesprime/GAMES/Neonoodles-ctrl/syx-sandbox/syx-sandbox test

# Status of both instances
/home/hermesprime/GAMES/Neonoodles-ctrl/syx-sandbox/syx-sandbox status
```

## Workflow: play vs ship

1. **Play daily** — personal `syx` + `_current/syx-llm-overlord` (your WIP).
2. **Harden for GitHub** — commit/cherry-pick into `sandbox` branch in the github worktree.
3. **Test sandbox** — `syx-sandbox bridge` + dashboard `:3848`; run `test`, `verify_settlement.py`.
4. **Mod changes** — build in github worktree (`syx-sandbox build-mod`); restarts game with sandbox JAR (brief downtime — don't run during a live play session).
5. **Publish** — push `sandbox` → PR → `main` on GitHub → go public when ready.

## Sync play → sandbox

```bash
cd "/home/hermesprime/CODE/Boiler Room/_current/syx-llm-overlord-github"
git fetch origin
git cherry-pick <commit>   # or merge main from play repo
```

Keep machine-specific paths out of commits (see `docs/PERSONAL-LAUNCHER.md`).

## Environment variables (sandbox)

Set in `/home/hermesprime/GAMES/Neonoodles-ctrl/syx-sandbox/instance.env`:

| Variable | Sandbox default |
|----------|-----------------|
| `SYX_OVERLORD_ROOT` | github worktree path |
| `SYX_OVERLORD_LOGS` | `syx-sandbox/logs` |
| `SYX_BRIDGE_PORT` | `3848` |
| `SYX_MEMORY_PATH` | separate JSONL |
| `SYX_KNOWLEDGE_PATH` | separate knowledge file |

## Limits

- Mod HTTP port `47823` is fixed in Java — only one mod binds per game session.
- Sandbox and play **cannot** use different mod versions simultaneously without stopping the game and swapping `002_LLM_Overlord.jar`.
- Bridge-only sandbox testing works anytime (mock/disconnected game is OK).
