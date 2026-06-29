#!/bin/bash
# Syx LLM Overlord - Single Launcher
# Starts game, bridge, dashboard. One command, everything runs.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GAME_DIR="/home/hermesprime/GAMES/Steam/_steamapps/steamapps/common/Songs of Syx Demo"
MOD_DIR="$HOME/.config/songsofsyx/mods/syx-llm-overlord"
MOD_JAR="$MOD_DIR/V69/script/002_LLM_Overlord.jar"
BASE_SCRIPT_JAR="$GAME_DIR/base/script/002_LLM_Overlord.jar"
BRIDGE_DIR="$SCRIPT_DIR/bridge"
CONFIG_FILE="$BRIDGE_DIR/config.yaml"
MOD_API="http://localhost:47823"
DASHBOARD_URL="http://localhost:3847"
GAME_LOG="/tmp/syx-game.log"

# Load only the API key we need (bulk export breaks on paths with spaces in .env)
if [ -f "$HOME/.hermes/.env" ]; then
    _or_key=$(grep -E '^OPENROUTER_API_KEY=' "$HOME/.hermes/.env" | tail -1 | cut -d= -f2-)
    [ -n "$_or_key" ] && export OPENROUTER_API_KEY="$_or_key"
    unset _or_key
fi

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

install_mod() {
    if [ -f "$MOD_JAR" ] && [ -f "$MOD_DIR/_Info.txt" ] && [ -f "$BASE_SCRIPT_JAR" ]; then
        ok "Mod installed: $MOD_JAR"
        return 0
    fi
    warn "Mod not fully installed. Building now..."
    (cd "$SCRIPT_DIR/syx-llm-mod" && ./mvnw install -P linux -q)
    [ -f "$MOD_JAR" ] || { err "Mod build failed — missing $MOD_JAR"; exit 1; }
    [ -f "$MOD_DIR/_Info.txt" ] || { err "Mod build failed — missing $MOD_DIR/_Info.txt"; exit 1; }
    ok "Mod built and installed."
}

preflight() {
    local fail=0
    command -v python3 &>/dev/null || { err "python3 not found"; fail=1; }
    command -v curl &>/dev/null    || { err "curl not found"; fail=1; }
    [ -f "$GAME_DIR/SongsOfSyx.jar" ] || { err "Game not found: $GAME_DIR"; fail=1; }
    [ -x "$GAME_DIR/LinuxNvidiaFix.sh" ] || { err "Game launcher missing: $GAME_DIR/LinuxNvidiaFix.sh"; fail=1; }
    bash "$SCRIPT_DIR/scripts/fix-display.sh" >/dev/null 2>&1 || true
    install_mod
    [ -f "$CONFIG_FILE" ] || cp "$BRIDGE_DIR/config.example.yaml" "$CONFIG_FILE"
    [ -n "$OPENROUTER_API_KEY" ] || { err "OPENROUTER_API_KEY not set in $HOME/.hermes/.env"; fail=1; }
    [ $fail -eq 0 ] || exit 1
}

install_deps() {
    if ! python3 -c "import fastapi" 2>/dev/null; then
        log "Installing Python dependencies..."
        pip3 install --break-system-packages -q -r "$BRIDGE_DIR/requirements.txt"
        ok "Python deps installed."
    fi
}

# ── Launch ──────────────────────────────────────────────

launch_game() {
    log "Launching Songs of Syx (fullscreen, direct start)..."
    cd "$GAME_DIR"
    local CP="$GAME_DIR/base/script/000_Tutorial.jar:$GAME_DIR/base/script/001_Tutorial.jar:$GAME_DIR/base/script/002_LLM_Overlord.jar:$GAME_DIR/SongsOfSyx.jar"
    __GL_THREADED_OPTIMIZATIONS=0 ./jre/bin/java \
        -Xms512m -Xmx4096m -XX:+UseCompressedOops -Dfile.encoding=UTF-8 -server \
        -cp "$CP" init.Main >>"$GAME_LOG" 2>&1 &
    PIDS+=($!)
    ok "Game PID ${PIDS[-1]} (log: $GAME_LOG)"
    echo ""
    echo -e "  ${YELLOW}Required: New Game → Scripts → check \"LLM Overlord\" → Start${NC}"
    echo ""
}

wait_for_mod() {
    log "Waiting for mod API (:47823) — start a new game with LLM Overlord enabled..."
    local dots=""
    for i in $(seq 1 120); do
        if curl -s --max-time 2 "$MOD_API/api/health" 2>/dev/null | grep -q "ok"; then
            echo ""
            ok "Mod API live!"
            return 0
        fi
        sleep 5
        dots="${dots}."
        [ ${#dots} -gt 3 ] && dots="."
        printf "\r${CYAN}[overlord]${NC} Waiting for you to start a game%s " "$dots"
    done
    echo ""
    err "Mod API not responding after 10 minutes."
    err "Enable LLM Overlord in Mods + Scripts, then start a new game."
    exit 1
}

launch_bridge() {
    log "Starting LLM bridge (Owl Alpha via OpenRouter)..."
    cd "$BRIDGE_DIR"
    python3 -m bridge &>/tmp/syx-bridge.log &
    PIDS+=($!)
    ok "Bridge PID ${PIDS[-1]}"

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
