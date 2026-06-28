#!/bin/bash
# Syx LLM Overlord - Single Launcher
# Starts game, bridge, dashboard. One command, everything runs.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GAME_DIR="/home/hermesprime/GAMES/Steam/_steamapps/steamapps/common/Songs of Syx Demo"
BRIDGE_DIR="$SCRIPT_DIR/bridge"
CONFIG_FILE="$BRIDGE_DIR/config.yaml"
MOD_API="http://localhost:47823"
DASHBOARD_URL="http://localhost:3847"

# Load API keys from hermes env
[ -f "$HOME/.hermes/.env" ] && export $(grep -v '^#' "$HOME/.hermes/.env" | grep -v '^\s*$' | xargs)

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${CYAN}[overlord]${NC} $1"; }
ok()   { echo -e "${GREEN}[  ok  ]${NC} $1"; }
warn() { echo -e "${YELLOW}[ warn ]${NC} $1"; }
err()  { echo -e "${RED}[ fail ]${NC} $1"; }

PIDS=()
cleanup() {
    log "Shutting down..."
    for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done
    wait 2>/dev/null
    log "All stopped."
}
trap cleanup EXIT INT TERM

# ── Pre-flight ──────────────────────────────────────────

preflight() {
    local fail=0
    command -v java &>/dev/null    || { err "java not found"; fail=1; }
    command -v python3 &>/dev/null || { err "python3 not found"; fail=1; }
    command -v curl &>/dev/null    || { err "curl not found"; fail=1; }
    [ -f "$GAME_DIR/SongsOfSyx.jar" ] || { err "Game not found: $GAME_DIR"; fail=1; }
    [ -f "$HOME/.config/songsofsyx/mods/syx-llm-overlord/V69/script/syx-llm-overlord-1.0.0.jar" ] || {
        warn "Mod not installed. Building now..."
        (cd "$SCRIPT_DIR/syx-llm-mod" && ./mvnw install -P linux -q 2>&1 | tail -3)
        ok "Mod built and installed."
    }
    [ -f "$CONFIG_FILE" ] || cp "$BRIDGE_DIR/config.example.yaml" "$CONFIG_FILE"
    [ -n "$OPENROUTER_API_KEY" ] || { err "OPENROUTER_API_KEY not set in ~/.hermes/.env"; fail=1; }
    [ $fail -eq 0 ] || exit 1
}

install_deps() {
    if ! python3 -c "import fastapi" 2>/dev/null; then
        log "Installing Python dependencies..."
        pip3 install -q -r "$BRIDGE_DIR/requirements.txt"
        ok "Python deps installed."
    fi
}

# ── Launch ──────────────────────────────────────────────

launch_game() {
    log "Launching Songs of Syx..."
    cd "$GAME_DIR"
    java -Xmx1G -jar SongsOfSyx.jar &>/dev/null &
    PIDS+=($!)
    ok "Game PID ${PIDS[-1]}"
    echo ""
    echo -e "  ${YELLOW}>>> In the game launcher: enable 'LLM Overlord' in Scripts, then New Game <<<${NC}"
    echo ""
}

wait_for_mod() {
    log "Waiting for mod API (:47823)..."
    local dots=""
    for i in $(seq 1 120); do
        if curl -s --max-time 2 "$MOD_API/api/health" 2>/dev/null | grep -q "ok"; then
            echo ""
            ok "Mod API live!"
            return 0
        fi
        sleep 5
        dots="${dots}."
        printf "\r${CYAN}[overlord]${NC} Waiting%s " "$dots"
    done
    echo ""
    err "Mod API not responding. Did you enable the mod and start a game?"
    exit 1
}

launch_bridge() {
    log "Starting LLM bridge (Owl Alpha via OpenRouter)..."
    cd "$BRIDGE_DIR"
    python3 -m bridge &>/tmp/syx-bridge.log &
    PIDS+=($!)
    ok "Bridge PID ${PIDS[-1]}"

    # Wait for bridge HTTP
    for i in $(seq 1 10); do
        if curl -s --max-time 2 "http://localhost:3847/api/health" 2>/dev/null | grep -q "ok"; then
            ok "Bridge API live on :3847"
            return 0
        fi
        sleep 1
    done
    warn "Bridge may still be starting (check /tmp/syx-bridge.log)"
}

open_dashboard() {
    sleep 1
    log "Opening dashboard..."
    xdg-open "$DASHBOARD_URL" 2>/dev/null &
    ok "Dashboard: $DASHBOARD_URL"
}

# ── Main ────────────────────────────────────────────────

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        SYX LLM OVERLORD LAUNCHER        ║${NC}"
echo -e "${CYAN}║    Owl Alpha  ·  OpenRouter  ·  Free     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

preflight
install_deps
launch_game
wait_for_mod
launch_bridge
open_dashboard

echo ""
ok "ALL SYSTEMS GO"
echo ""
echo -e "  ${CYAN}Game:${NC}      Running with LLM Overlord mod"
echo -e "  ${CYAN}LLM:${NC}       Owl Alpha (openrouter/owl-alpha) -- free"
echo -e "  ${CYAN}Dashboard:${NC} $DASHBOARD_URL"
echo ""
log "The AI overlord is now observing your kingdom."
log "Press Ctrl+C to shut everything down."
echo ""

wait
