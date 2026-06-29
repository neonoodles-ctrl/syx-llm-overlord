#!/usr/bin/env bash
# Restart game — delegates to personal launcher when present (monitor pin + HiDPI).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PERSONAL_ROOT="${SYX_PERSONAL_LAUNCHER:-${HOME}/GAMES/Neonoodles-ctrl/syx}"
PERSONAL_RESTART="${PERSONAL_ROOT}/scripts/restart-game-only.sh"

if [[ -z "${SYX_USE_PORTABLE_RESTART:-}" && -x "${PERSONAL_RESTART}" ]]; then
  exec bash "${PERSONAL_RESTART}"
fi

LOG="${ROOT}/logs/restart-game.log"
mkdir -p "${ROOT}/logs"

# shellcheck source=/dev/null
[[ -f "${ROOT}/.env" ]] && source "${ROOT}/.env"
# shellcheck source=/dev/null
[[ -f "${PERSONAL_ROOT}/syx.launch.conf" ]] && source "${PERSONAL_ROOT}/syx.launch.conf"
# shellcheck disable=SC1091
[[ -f "${PERSONAL_ROOT}/scripts/syx-hidpi-env.sh" ]] && source "${PERSONAL_ROOT}/scripts/syx-hidpi-env.sh"

JAR="$("${ROOT}/scripts/find-game-jar.sh")"
GAME="$(dirname "${JAR}")"
GAME_LAUNCHER="${GAME}/LinuxNvidiaFix.sh"

log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "${LOG}"; }

log "=== restart-game-only (portable) ==="
log "Game dir: ${GAME}"
log "DISPLAY=${DISPLAY:-unset}"

pkill -f 'SongsOfSyx.jar|songsofsyx' 2>/dev/null || true
pkill -f 'LinuxNvidiaFix' 2>/dev/null || true
sleep 2

if [[ -x "${GAME_LAUNCHER}" ]]; then
  cd "${GAME}"
  setsid env DISPLAY="${DISPLAY:-:0}" __GL_THREADED_OPTIMIZATIONS=0 \
    "${GAME_LAUNCHER}" >>"${ROOT}/logs/launch.log" 2>&1 &
  log "game PID $! (LinuxNvidiaFix.sh, setsid)"
elif [[ -f "${JAR}" ]]; then
  cd "${GAME}"
  setsid env DISPLAY="${DISPLAY:-:0}" java -jar "${JAR}" >>"${ROOT}/logs/launch.log" 2>&1 &
  log "game PID $! (java -jar, setsid)"
else
  log "ERROR: cannot launch — missing ${GAME_LAUNCHER} and ${JAR}"
  exit 1
fi

# Optional pin if personal scripts exist
if [[ -x "${PERSONAL_ROOT}/scripts/pin-game-to-monitor.sh" ]]; then
  # shellcheck source=/dev/null
  [[ -f "${PERSONAL_ROOT}/scripts/monitor-config.sh" ]] && source "${PERSONAL_ROOT}/scripts/monitor-config.sh"
  if declare -f syx_resolve_pin_target >/dev/null 2>&1; then
    syx_resolve_pin_target || true
    setsid bash "${PERSONAL_ROOT}/scripts/pin-game-to-monitor.sh" >>"${ROOT}/logs/pin-monitor.log" 2>&1 &
    log "pin watchdog PID $!"
  fi
fi

log "done — bridge stays up"
