# Personal launcher setup

The repo includes a minimal `./run.sh` that starts the bridge and tells you to launch the game from Steam. This is enough for most users and for GitHub clones.

If you want **one command** that also launches the game, applies HiDPI fixes, pins the window to a monitor, and loads your API keys — create a personal launcher outside the repo.

---

## Why keep it separate?

Personal launchers often contain:

- Hardcoded Steam library paths
- Monitor names (`DP-2`, `MSI`, KDE/xrandr scripts)
- Private `.env` locations
- Machine-specific display hacks

Those do not belong in the public/private repo. The repo stays portable; your launcher wraps it.

---

## Minimal wrapper

Create a folder anywhere (example):

```
~/GAMES/Neonoodles-ctrl/syx/
  syx                    # your orchestrator
  syx.launch.conf        # optional display defaults
  scripts/               # optional monitor helpers
  logs/                  # runtime logs
```

Example `syx` script:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Point at your clone
export SYX_OVERLORD_ROOT="/home/YOU/CODE/Boiler Room/_current/syx-llm-overlord"
export SYX_RESTART_SCRIPT="${SYX_OVERLORD_ROOT}/scripts/restart-game-only.sh"

# Game paths (or rely on find-game-jar.sh)
export SONGSOFSYX_DIR="/path/to/Steam/steamapps/common/Songs of Syx Demo"
export SONGSOFSYX_JAR="${SONGSOFSYX_DIR}/SongsOfSyx.jar"

# API keys
[[ -f ~/.config/syx-overlord/.env ]] && source ~/.config/syx-overlord/.env

# Bridge + mod
"${SYX_OVERLORD_ROOT}/run.sh" bridge

# Launch game (your platform)
cd "${SONGSOFSYX_DIR}"
./LinuxNvidiaFix.sh &   # or: java -jar SongsOfSyx.jar

# Optional: open dashboard
xdg-open http://localhost:3847
```

```bash
chmod +x ~/GAMES/Neonoodles-ctrl/syx/syx
```

---

## Symlink the repo wiki into Obsidian

If you use the neonoodles-ctrl vault:

```bash
ln -sf "/path/to/syx-llm-overlord/wiki" \
  "/path/to/Obsidian Vaults/neonoodles-ctrl/1. IDEAS/syx-llm-overlord/wiki"
```

Edit `wiki/rules/playbook.md` in Obsidian — the bridge reads the repo copy when `SYX_OVERLORD_ROOT` points at the clone.

---

## Extend with monitor pinning

Reference implementation (Ivan's setup):

- `/home/hermesprime/GAMES/Neonoodles-ctrl/syx/syx`
- `/home/hermesprime/GAMES/Neonoodles-ctrl/syx/scripts/monitor-config.sh`
- `/home/hermesprime/GAMES/Neonoodles-ctrl/syx/scripts/pin-game-to-monitor.sh`

Copy patterns from there into your personal `scripts/` — do not commit machine-specific paths back to the repo.

---

## Environment variables reference

| Variable | Purpose |
|----------|---------|
| `SYX_OVERLORD_ROOT` | Path to git clone |
| `SONGSOFSYX_JAR` | Path to `SongsOfSyx.jar` |
| `SONGSOFSYX_DIR` | Game install directory |
| `SYX_GAME_VERSION` | e.g. `V69` (auto-detected if unset) |
| `SYX_RESTART_SCRIPT` | Game restart script for dashboard button |
| `OPENROUTER_API_KEY` | Cloud LLM key |
| `SYX_WIKI_DIR` | Override wiki location |
| `SYX_MEMORY_PATH` | Override JSONL memory log |

---

## Desktop entry (optional)

```ini
[Desktop Entry]
Name=Songs of Syx + LLM Overlord
Exec=/home/YOU/GAMES/Neonoodles-ctrl/syx/syx
Icon=songsofsyx
Terminal=true
Type=Application
Categories=Game;
```

Save to `~/.local/share/applications/syx-overlord.desktop` and adjust paths.
