#!/usr/bin/env bash
# Create / refresh the GitHub sandbox worktree + personal sandbox launcher.
set -euo pipefail

PLAY_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GITHUB_ROOT="/home/hermesprime/CODE/Boiler Room/_current/syx-llm-overlord-github"
SANDBOX_HOME="/home/hermesprime/GAMES/Neonoodles-ctrl/syx-sandbox"
GAME="/home/hermesprime/GAMES/Steam/_steamapps/steamapps/common/Songs of Syx Demo"

echo "== Syx LLM Overlord — sandbox bootstrap =="

# Worktree
if [[ -d "${GITHUB_ROOT}/.git" ]]; then
  echo "Worktree OK: ${GITHUB_ROOT}"
elif git -C "${PLAY_ROOT}" worktree list | grep -qF "${GITHUB_ROOT}"; then
  echo "Worktree registered: ${GITHUB_ROOT}"
else
  cd "${PLAY_ROOT}"
  git fetch origin
  if git show-ref --verify --quiet refs/heads/sandbox; then
    git worktree add "${GITHUB_ROOT}" sandbox
  else
    git worktree add "${GITHUB_ROOT}" -b sandbox origin/main
  fi
fi

mkdir -p "${SANDBOX_HOME}/logs" "${SANDBOX_HOME}/scripts"

# Instance env (never commit — lives outside repo)
cat >"${SANDBOX_HOME}/instance.env" <<EOF
# Syx sandbox instance — separate from play (syx/)
SYX_INSTANCE=sandbox
SYX_OVERLORD_ROOT="${GITHUB_ROOT}"
SYX_OVERLORD_LOGS="${SANDBOX_HOME}/logs"
SYX_BRIDGE_PORT=3848
SYX_MOD_URL=http://localhost:47823
SYX_MEMORY_PATH="${SANDBOX_HOME}/logs/overlord-memory.jsonl"
SYX_KNOWLEDGE_PATH="${SANDBOX_HOME}/logs/overlord-knowledge.json"
SYX_SCREENSHOTS_DIR="${SANDBOX_HOME}/logs/screenshots"
SYX_RESTART_SCRIPT="${SANDBOX_HOME}/scripts/restart-game-only.sh"
SONGSOFSYX_DIR="${GAME}"
SONGSOFSYX_JAR="${GAME}/SongsOfSyx.jar"
DISPLAY=:0
EOF

# Sandbox bridge starter
cat >"${SANDBOX_HOME}/scripts/start-bridge.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT}/instance.env"
PID_FILE="${SYX_OVERLORD_LOGS}/bridge.pid"
PORT="${SYX_BRIDGE_PORT:-3848}"

if curl -sf --max-time 2 "http://127.0.0.1:${PORT}/api/health" 2>/dev/null | grep -q '"status":"ok"'; then
  echo "Sandbox bridge already on http://localhost:${PORT}"
  exit 0
fi

if [[ -f "${PID_FILE}" ]]; then
  old=$(cat "${PID_FILE}" 2>/dev/null || true)
  [[ -n "${old}" ]] && kill "${old}" 2>/dev/null || true
fi
pkill -f "SYX_OVERLORD_ROOT=${SYX_OVERLORD_ROOT}.*python3 -m bridge" 2>/dev/null || true
sleep 1

mkdir -p "${SYX_OVERLORD_LOGS}"
export SYX_OVERLORD_ROOT SYX_OVERLORD_LOGS SYX_BRIDGE_PORT SYX_MOD_URL
export SYX_MEMORY_PATH SYX_KNOWLEDGE_PATH SYX_SCREENSHOTS_DIR DISPLAY

# API keys: read OPENROUTER key only (avoid sourcing full .hermes/.env — paths with spaces break)
if [[ -f /home/hermesprime/.hermes/.env ]]; then
  _or_key=$(grep -E '^OPENROUTER_API_KEY=' /home/hermesprime/.hermes/.env | tail -1 | cut -d= -f2- || true)
  _or_key="${_or_key%\"}"; _or_key="${_or_key#\"}"
  [[ -n "${_or_key}" ]] && export OPENROUTER_API_KEY="${_or_key}"
  unset _or_key
fi
[[ -f "${SYX_OVERLORD_ROOT}/.env" ]] && set -a && source "${SYX_OVERLORD_ROOT}/.env" && set +a

cd "${SYX_OVERLORD_ROOT}/bridge"
if [[ ! -d "${SYX_OVERLORD_ROOT}/.venv" ]]; then
  echo "Run: ${ROOT}/../syx-sandbox install" >&2
  exit 1
fi
# shellcheck source=/dev/null
source "${SYX_OVERLORD_ROOT}/.venv/bin/activate"
setsid python3 -m bridge >>"${SYX_OVERLORD_LOGS}/bridge.log" 2>&1 < /dev/null &
echo $! >"${PID_FILE}"
echo "Sandbox bridge starting → http://localhost:${PORT} (PID $(cat "${PID_FILE}"))"
SCRIPT
chmod +x "${SANDBOX_HOME}/scripts/start-bridge.sh"

# Minimal game restart for sandbox (same game install, sandbox mod build path)
cat >"${SANDBOX_HOME}/scripts/restart-game-only.sh" <<SCRIPT
#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=/dev/null
source "/home/hermesprime/GAMES/Neonoodles-ctrl/syx-sandbox/instance.env"
export SYX_USE_PORTABLE_RESTART=1
exec "/home/hermesprime/GAMES/Neonoodles-ctrl/syx/scripts/restart-game-only.sh"
SCRIPT
chmod +x "${SANDBOX_HOME}/scripts/restart-game-only.sh"

# Main sandbox CLI
cat >"${SANDBOX_HOME}/syx-sandbox" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "${ROOT}/instance.env"
export SYX_OVERLORD_ROOT SYX_OVERLORD_LOGS SYX_BRIDGE_PORT SYX_MOD_URL
export SYX_MEMORY_PATH SYX_KNOWLEDGE_PATH SYX_SCREENSHOTS_DIR SYX_RESTART_SCRIPT
export SONGSOFSYX_DIR SONGSOFSYX_JAR DISPLAY

cmd="${1:-status}"
shift || true

case "${cmd}" in
  install)
    cd "${SYX_OVERLORD_ROOT}"
    ./install.sh
    ;;
  bridge|start-bridge)
    bash "${ROOT}/scripts/start-bridge.sh"
    ;;
  stop-bridge)
    PID_FILE="${SYX_OVERLORD_LOGS}/bridge.pid"
    [[ -f "${PID_FILE}" ]] && kill "$(cat "${PID_FILE}")" 2>/dev/null || true
    echo "Sandbox bridge stopped"
    ;;
  test)
    cd "${SYX_OVERLORD_ROOT}"
    # shellcheck source=/dev/null
    source .venv/bin/activate
    python -m pytest bridge/tests/ -v "$@"
    ;;
  verify)
    cd "${SYX_OVERLORD_ROOT}"
    # shellcheck source=/dev/null
    source .venv/bin/activate
    SYX_BRIDGE_URL="http://127.0.0.1:${SYX_BRIDGE_PORT}" \
    python bridge/scripts/verify_settlement.py --health "$@"
    ;;
  build-mod)
    cd "${SYX_OVERLORD_ROOT}"
    ./run.sh build
    echo "Mod built. Restart game to load sandbox JAR (stops play mod until swap back)."
    ;;
  status)
    echo "=== Play instance ==="
    curl -sf --max-time 2 http://127.0.0.1:3847/api/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  bridge :3847 — down"
    echo ""
    echo "=== Sandbox (GitHub) ==="
    echo "  root: ${SYX_OVERLORD_ROOT}"
    echo "  branch: $(git -C "${SYX_OVERLORD_ROOT}" branch --show-current 2>/dev/null || echo '?')"
    curl -sf --max-time 2 "http://127.0.0.1:${SYX_BRIDGE_PORT}/api/health" 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  bridge :${SYX_BRIDGE_PORT} — down"
    curl -sf --max-time 2 http://127.0.0.1:47823/api/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  mod :47823 — down (game not running?)"
    ;;
  dashboard)
    xdg-open "http://localhost:${SYX_BRIDGE_PORT}" 2>/dev/null || true
    ;;
  help|-h|--help)
    cat <<EOF
Usage: ${ROOT}/syx-sandbox <command>

  install      First-time venv + mod build in github worktree
  bridge       Start sandbox dashboard on :3848 (parallel with play)
  stop-bridge  Stop sandbox bridge only
  test         pytest in github worktree
  verify       verify_settlement.py --health against sandbox bridge
  build-mod    Build mod from github worktree (game restart needed)
  status       Show play + sandbox health
  dashboard    Open http://localhost:3848

Play instance unchanged: /home/hermesprime/GAMES/Neonoodles-ctrl/syx/syx
EOF
    ;;
  *)
    echo "Unknown: ${cmd} (try help)" >&2
    exit 1
    ;;
esac
SCRIPT
chmod +x "${SANDBOX_HOME}/syx-sandbox"

echo ""
echo "Bootstrap complete."
echo "  GitHub worktree: ${GITHUB_ROOT} (branch sandbox)"
echo "  Sandbox launcher: ${SANDBOX_HOME}/syx-sandbox"
echo ""
echo "Next:"
echo "  ${SANDBOX_HOME}/syx-sandbox install"
echo "  ${SANDBOX_HOME}/syx-sandbox bridge"
echo "  ${SANDBOX_HOME}/syx-sandbox status"
