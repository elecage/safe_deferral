#!/usr/bin/env bash
# local_e2e_launcher.sh — bring up the full safe_deferral stack on one M1 MacBook
#
# Starts (idempotently):
#   - mosquitto MQTT broker (via brew services)
#   - Ollama check (does NOT start it — assumes user has ollama running)
#   - Mac mini Python stack (mqtt subscribers + LLM/policy/validator/dispatcher)
#   - RPi Python stack (dashboard :8888, governance :8889, virtual node mgr,
#     paper-eval sweep runner)
#
# Usage:
#   ./scripts/local_e2e_launcher.sh                # start everything
#   ./scripts/local_e2e_launcher.sh --stop         # SIGTERM the started stacks
#   ./scripts/local_e2e_launcher.sh --no-mosquitto-start  # assume broker already up
#
# Exit codes:
#   0  everything healthy
#   1  precondition failed (brew/mosquitto/ollama/python deps)
#   2  stack failed to come up within timeout
#
# Environment:
#   - .env at ~/smarthome_workspace/.env auto-created with sensible defaults
#     if missing. Existing .env is never overwritten.
#   - Logs at /tmp/safe_deferral_e2e/{macmini,rpi}.log
#   - PIDs at /tmp/safe_deferral_e2e/{macmini,rpi}.pid

set -euo pipefail

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

WORKDIR="${SAFE_DEFERRAL_E2E_WORKDIR:-/tmp/safe_deferral_e2e}"
ENV_FILE="${HOME}/smarthome_workspace/.env"

DASHBOARD_PORT="${DASHBOARD_PORT:-8888}"
GOVERNANCE_PORT="${GOVERNANCE_PORT:-8889}"
MQTT_PORT="${MQTT_PORT:-1883}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"

# Health-gate timeout: rpi dashboard must respond within this many seconds.
# Mac mini stack has no listening port, so we trust process aliveness only.
RPI_HEALTH_TIMEOUT_S="${RPI_HEALTH_TIMEOUT_S:-30}"

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

log() { echo "[launcher] $*"; }
die() { echo "[launcher] ERROR: $*" >&2; exit 1; }

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "$1 not found. $2"
}

is_port_listening() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

http_ok() {
  curl -sf -o /dev/null --max-time 2 "$1"
}

# ----------------------------------------------------------------------
# --stop handler
# ----------------------------------------------------------------------

if [[ "${1:-}" == "--stop" ]]; then
  log "stopping safe_deferral E2E stacks"
  for name in macmini rpi; do
    pidfile="${WORKDIR}/${name}.pid"
    if [[ -f "$pidfile" ]]; then
      pid="$(cat "$pidfile")"
      if kill -0 "$pid" 2>/dev/null; then
        log "  SIGTERM $name (pid $pid)"
        kill -TERM "$pid" 2>/dev/null || true
        # Give it 3s to exit cleanly, then SIGKILL
        for _ in 1 2 3; do
          sleep 1
          kill -0 "$pid" 2>/dev/null || break
        done
        if kill -0 "$pid" 2>/dev/null; then
          log "  SIGKILL $name (did not exit on TERM)"
          kill -KILL "$pid" 2>/dev/null || true
        fi
      else
        log "  $name (pid $pid) already gone"
      fi
      rm -f "$pidfile"
    fi
  done
  log "done. mosquitto is left running — stop with 'brew services stop mosquitto' if desired."
  exit 0
fi

# ----------------------------------------------------------------------
# Preconditions
# ----------------------------------------------------------------------

NO_MOSQUITTO_START=0
if [[ "${1:-}" == "--no-mosquitto-start" ]]; then
  NO_MOSQUITTO_START=1
fi

log "checking preconditions"
require_command python "macOS bundles python; ensure 'python --version' works."
require_command curl "install via 'brew install curl' (usually pre-installed)."
require_command lsof "macOS bundles lsof."

python -c "import paho.mqtt" 2>/dev/null \
  || die "Python paho-mqtt missing. Install: pip install paho-mqtt"
python -c "import fastapi" 2>/dev/null \
  || die "Python fastapi missing. Install: pip install fastapi uvicorn"
python -c "import jsonschema" 2>/dev/null \
  || die "Python jsonschema missing. Install: pip install jsonschema"
python -c "import requests" 2>/dev/null \
  || die "Python requests missing. Install: pip install requests"

# ----------------------------------------------------------------------
# Mosquitto
# ----------------------------------------------------------------------

if [[ "$NO_MOSQUITTO_START" == "0" ]]; then
  if ! command -v mosquitto >/dev/null 2>&1; then
    die "mosquitto not installed. Install: brew install mosquitto"
  fi
  if is_port_listening "$MQTT_PORT"; then
    log "mosquitto already listening on :$MQTT_PORT"
  else
    log "starting mosquitto via brew services"
    brew services start mosquitto >/dev/null \
      || die "brew services failed to start mosquitto. Check 'brew services list'."
    # Wait up to 10s for it to bind.
    for _ in $(seq 1 20); do
      is_port_listening "$MQTT_PORT" && break
      sleep 0.5
    done
    is_port_listening "$MQTT_PORT" \
      || die "mosquitto did not start listening on :$MQTT_PORT within 10s"
  fi
else
  log "skipping mosquitto start (--no-mosquitto-start)"
  is_port_listening "$MQTT_PORT" \
    || die "MQTT port $MQTT_PORT not listening. Start your broker first."
fi

# ----------------------------------------------------------------------
# Ollama
# ----------------------------------------------------------------------

if ! is_port_listening "$OLLAMA_PORT"; then
  die "Ollama not listening on :$OLLAMA_PORT. Run 'ollama serve' or open the Ollama app."
fi
log "ollama up at :$OLLAMA_PORT"

# Check model is available; soft warning if not.
if ! curl -sf "http://localhost:${OLLAMA_PORT}/api/tags" 2>/dev/null \
     | grep -q '"name":"llama3.2'; then
  log "WARN: llama3.2 model not found in 'ollama list'. Run: ollama pull llama3.2"
fi

# ----------------------------------------------------------------------
# .env
# ----------------------------------------------------------------------

mkdir -p "$(dirname "$ENV_FILE")"
if [[ -f "$ENV_FILE" ]]; then
  log ".env exists at $ENV_FILE (left untouched)"
else
  log "writing default .env to $ENV_FILE"
  cat > "$ENV_FILE" <<'EOF'
# safe_deferral local M1 MacBook E2E defaults
# Generated by scripts/local_e2e_launcher.sh — edit freely.
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USER=
MQTT_PASS=

OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2

# false → keep the launcher quiet. Set true to hear macOS `say` output.
TTS_ENABLED=false
TTS_VOICE=Yuna

# Telegram is optional — empty token → caregiver escalation runs in mock mode.
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

DASHBOARD_PORT=8888
GOVERNANCE_PORT=8889
EOF
fi

# ----------------------------------------------------------------------
# Workdir + idempotent process check
# ----------------------------------------------------------------------

mkdir -p "$WORKDIR"

start_stack() {
  local name="$1" cwd="$2" cmd="$3"
  local pidfile="${WORKDIR}/${name}.pid"
  local logfile="${WORKDIR}/${name}.log"

  if [[ -f "$pidfile" ]]; then
    local existing_pid
    existing_pid="$(cat "$pidfile")"
    if kill -0 "$existing_pid" 2>/dev/null; then
      log "${name} already running (pid ${existing_pid}). use --stop to terminate."
      return 0
    else
      rm -f "$pidfile"
    fi
  fi

  log "starting ${name} (log: ${logfile})"
  (
    cd "$cwd"
    # nohup so the stack survives the launcher exiting.
    nohup python -u "$cmd" >>"$logfile" 2>&1 &
    echo "$!" > "$pidfile"
  )
}

# Mac mini stack
start_stack macmini "${REPO_ROOT}/mac_mini/code" main.py
# RPi stack
start_stack rpi "${REPO_ROOT}/rpi/code" main.py

# ----------------------------------------------------------------------
# Health gate — RPi dashboard must respond on /health
# ----------------------------------------------------------------------

log "waiting up to ${RPI_HEALTH_TIMEOUT_S}s for dashboard /health"
deadline=$(($(date +%s) + RPI_HEALTH_TIMEOUT_S))
healthy=0
while [[ $(date +%s) -lt $deadline ]]; do
  if http_ok "http://localhost:${DASHBOARD_PORT}/health"; then
    healthy=1
    break
  fi
  sleep 1
done

if [[ "$healthy" == "0" ]]; then
  log "ERROR: dashboard did not become healthy in ${RPI_HEALTH_TIMEOUT_S}s"
  log "  Check ${WORKDIR}/rpi.log for traceback."
  log "  Likely causes: port :${DASHBOARD_PORT} already in use, missing python deps,"
  log "                 or broker connection refused."
  exit 2
fi

# Quick liveness check on macmini PID
mac_pid="$(cat "${WORKDIR}/macmini.pid" 2>/dev/null || echo '')"
if [[ -n "$mac_pid" ]] && ! kill -0 "$mac_pid" 2>/dev/null; then
  log "ERROR: mac_mini stack died shortly after start — see ${WORKDIR}/macmini.log"
  exit 2
fi

# ----------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------

log "✓ all services healthy"
log "  mosquitto:    127.0.0.1:${MQTT_PORT}"
log "  ollama:       127.0.0.1:${OLLAMA_PORT}"
log "  mac_mini:     pid $(cat "${WORKDIR}/macmini.pid")  log: ${WORKDIR}/macmini.log"
log "  rpi (dash):   pid $(cat "${WORKDIR}/rpi.pid")  http://localhost:${DASHBOARD_PORT}/"
log "  rpi (gov):    http://localhost:${GOVERNANCE_PORT}/"
log ""
log "Tail logs:        tail -f ${WORKDIR}/{macmini,rpi}.log"
log "Open dashboard:   open http://localhost:${DASHBOARD_PORT}/"
log "Stop everything:  ${BASH_SOURCE[0]} --stop"
