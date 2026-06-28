#!/bin/bash
# Syx LLM Overlord - Single Launcher
# Starts the game, bridge service, and dashboard in one go.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GAME_DIR="/home/hermesprime/GAMES/Steam/_steamapps/steamapps/common/Songs of Syx Demo"
BRIDGE_DIR="$SCRIPT_DIR/bridge"
CONFIG_FILE="$BRIDGE_DIR/config.yaml"
MOD_API="http://localhost:47823"
DASHBOARD_URL="http://localhost:3847"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[overlord]${NC} $1"; }
ok()   { echo -e "${GREEN}[  ok  ]${NC} $1"; }
warn() { echo -e "${YELLOW}[ warn ]${NC} $1"; }
err()  { echo -e "${RED}[error ]${NC} $1"; }

# Track PIDs for cleanup
PIDS=()
cleanup() {
    log "Shutting down..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    log "All processes stopped."
}
trap cleanup EXIT INT TERM

# ── Checks ──────────────────────────────────────────────

check_deps() {
    local missing=()
    command -v java &>/dev/null    || missing+=("java")
    command -v python3 &>/dev/null || missing+=("python3")
    command -v pip3 &>/dev/null    && ! pip3 show fastapi &>/dev/null && {
        warn "Python dependencies not installed. Installing..."
        pip3 install -q -r "$BRIDGE_DIR/requirements.txt"
    }
    if [ ${#missing[@]} -gt 0 ]; then
        err "Missing: ${missing[*]}"
        exit 1
    fi
}

check_game() {
    if [ ! -f "$GAME_DIR/SongsOfSyx.jar" ]; then
        err "Game not found at $GAME_DIR"
        exit 1
    fi
    if [ ! -f "$HOME/.config/songsofsyx/mods/syx-llm-overlord/V69/script/syx-llm-overlord-1.0.0.jar" ]; then
        err "Mod not installed. Run: cd syx-llm-mod && ./mvnw install -P linux"
        exit 1
    fi
}

check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        warn "No config.yaml found. Copying from example..."
        cp "$BRIDGE_DIR/config.example.yaml" "$CONFIG_FILE"
        warn "Edit $CONFIG_FILE to set your LLM provider and API key."
    fi
}

# ── Launchers ───────────────────────────────────────────

launch_game() {
    log "Launching Songs of Syx..."
    cd "$GAME_DIR"
    java -Xmx1G -jar SongsOfSyx.jar &>/dev/null &
    PIDS+=($!)
    ok "Game launched (PID: ${PIDS[-1]})"
    log "  -> Enable 'LLM Overlord' in Scripts, then start a New Game"
}

wait_for_mod() {
    log "Waiting for mod HTTP API on :47823..."
    local attempts=0
    local max=120  # 10 minutes
    while [ $attempts -lt $max ]; do
        if curl -s "$MOD_API/api/health" &>/dev/null; then
            ok "Mod API is live!"
            return 0
        fi
        sleep 5
        attempts=$((attempts + 1))
        if [ $((attempts % 12)) -eq 0 ]; then
            log "  Still waiting... (enable the mod in-game and start a new game)"
        fi
    done
    err "Mod API not responding after 10 minutes. Is the game running with the mod enabled?"
    return 1
}

launch_bridge() {
    log "Starting LLM bridge service..."
    cd "$BRIDGE_DIR"
    python3 -m bridge &>/dev/null &
    PIDS+=($!)
    ok "Bridge started (PID: ${PIDS[-1]})"
}

open_dashboard() {
    sleep 2
    log "Opening dashboard at $DASHBOARD_URL"
    if command -v xdg-open &>/dev/null; then
        xdg-open "$DASHBOARD_URL" 2>/dev/null &
    elif command -v firefox &>/dev/null; then
        firefox "$DASHBOARD_URL" 2>/dev/null &
    elif command -v chromium &>/dev/null; then
        chromium "$DASHBOARD_URL" 2>/dev/null &
    else
        warn "Open $DASHBOARD_URL in your browser manually."
    fi
}

# ── Main ────────────────────────────────────────────────

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        SYX LLM OVERLORD LAUNCHER        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

check_deps
check_game
check_config

# Install Python deps if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    log "Installing Python dependencies..."
    pip3 install -q -r "$BRIDGE_DIR/requirements.txt"
    ok "Python deps installed."
fi

launch_game
launch_bridge
open_dashboard

echo ""
ok "All systems launched!"
echo ""
echo -e "  ${CYAN}Game:${NC}      Enable 'LLM Overlord' in Scripts -> New Game"
echo -e "  ${CYAN}Dashboard:${NC} $DASHBOARD_URL"
echo -e "  ${CYAN}Mod API:${NC}   $MOD_API/api/health"
echo ""
log "Waiting for you to start a game with the mod enabled..."
log "Press Ctrl+C to stop everything."
echo ""

# Wait for mod to come online, then just wait forever
wait_for_mod

echo ""
ok "LLM Overlord is ACTIVE. The AI is watching."
log "Dashboard: $DASHBOARD_URL"
echo ""

# Keep running until user kills
wait
