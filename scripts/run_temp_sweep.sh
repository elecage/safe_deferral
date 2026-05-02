#!/usr/bin/env bash
# run_temp_sweep.sh — paper-eval temperature × top_p grid sweep
#
# For each (temperature, top_p) combination in the grid, the script:
#   1. Stops the running stack (launcher --stop)
#   2. Updates ~/smarthome_workspace/.env with new OLLAMA_TEMPERATURE
#      and OLLAMA_TOP_P values (preserves all other keys)
#   3. Restarts the stack (launcher) so mac_mini picks up the new env
#   4. Re-uses an existing context_node + 2 actuator_simulator nodes
#      (auto-creates if missing)
#   5. Kicks off a paper-eval sweep with matrix_temp_sweep.json
#   6. Polls until completion
#   7. Archives manifest + aggregated + digest into a per-combo
#      directory under runs_archive/temp_sweep_<ts>/<temp>_<top_p>/
#
# Usage:
#   ./scripts/run_temp_sweep.sh
#   TEMPS="0.0 0.5 1.0" TOP_PS="0.5 0.9" ./scripts/run_temp_sweep.sh
#
# Tunables (env):
#   TEMPS               default "0.2 0.4 0.6 0.8"
#   TOP_PS              default "0.2 0.4 0.6 0.8"
#   MATRIX              default "integration/paper_eval/matrix_temp_sweep.json"
#   PER_TRIAL_TIMEOUT_S default 240  (Class 2 has caregiver-wait headroom)
#   ARCHIVE_LABEL       default "" (becomes part of runs_archive dir name)
#
# Exit codes:
#   0  all combos finished
#   1  setup/launcher failure
#   2  one or more combos failed (the rest still run)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LAUNCHER="${SCRIPT_DIR}/local_e2e_launcher.sh"
ENV_FILE="${HOME}/smarthome_workspace/.env"

TEMPS="${TEMPS:-0.2 0.4 0.6 0.8}"
TOP_PS="${TOP_PS:-0.2 0.4 0.6 0.8}"
MATRIX="${MATRIX:-integration/paper_eval/matrix_temp_sweep.json}"
PER_TRIAL_TIMEOUT_S="${PER_TRIAL_TIMEOUT_S:-240}"
LABEL="${ARCHIVE_LABEL:-}"

DASHBOARD="http://localhost:8888"

ts="$(date +%Y%m%d_%H%M%S)"
ARCHIVE_ROOT="${REPO_ROOT}/integration/paper_eval/runs_archive/temp_sweep_${ts}${LABEL:+_${LABEL}}"
mkdir -p "$ARCHIVE_ROOT"

log() { echo "[temp-sweep] $*"; }

# ----------------------------------------------------------------------
# .env mutation helper — replace OLLAMA_TEMPERATURE + OLLAMA_TOP_P, keep
# everything else. Falls back to appending if the key is missing.
# ----------------------------------------------------------------------

set_env_var() {
  local key="$1" val="$2"
  if grep -qE "^${key}=" "$ENV_FILE" 2>/dev/null; then
    # macOS sed needs '' after -i for in-place. Use a portable wrapper.
    sed -i.bak -E "s|^${key}=.*$|${key}=${val}|" "$ENV_FILE"
    rm -f "${ENV_FILE}.bak"
  else
    printf '\n%s=%s\n' "$key" "$val" >> "$ENV_FILE"
  fi
}

# ----------------------------------------------------------------------
# Per-combo orchestration
# ----------------------------------------------------------------------

run_one_combo() {
  local temp="$1" top_p="$2"
  local combo_dir="${ARCHIVE_ROOT}/temp_${temp}_top_p_${top_p}"
  mkdir -p "$combo_dir"

  log "=== combo temperature=${temp} top_p=${top_p} ==="

  # 1. Stop stack
  "$LAUNCHER" --stop >/dev/null 2>&1 || true

  # 2. Mutate .env
  set_env_var OLLAMA_TEMPERATURE "$temp"
  set_env_var OLLAMA_TOP_P "$top_p"

  # 3. Restart stack
  if ! "$LAUNCHER" >/dev/null 2>&1; then
    log "  FAIL: launcher could not bring up stack"
    echo "launcher_failed" > "${combo_dir}/STATUS"
    return 1
  fi
  # Brief settle so mac_mini's MQTT subscriber is ready before we POST.
  sleep 2

  # 4. Create / re-use nodes. Each launcher restart wipes RPi state, so
  #    we always create fresh nodes per combo.
  local ctx liv bed
  ctx="$(curl -sf -X POST "${DASHBOARD}/nodes" \
          -H 'Content-Type: application/json' \
          -d '{"node_type":"context_node","description":"temp-sweep ctx"}' \
          | python -c 'import json,sys; print(json.load(sys.stdin)["node_id"])')"
  curl -sf -X POST "${DASHBOARD}/nodes/${ctx}/start" >/dev/null
  liv="$(curl -sf -X POST "${DASHBOARD}/nodes" \
          -H 'Content-Type: application/json' \
          -d '{"node_type":"actuator_simulator","device_target":"living_room_light"}' \
          | python -c 'import json,sys; print(json.load(sys.stdin)["node_id"])')"
  curl -sf -X POST "${DASHBOARD}/nodes/${liv}/start" >/dev/null
  bed="$(curl -sf -X POST "${DASHBOARD}/nodes" \
          -H 'Content-Type: application/json' \
          -d '{"node_type":"actuator_simulator","device_target":"bedroom_light"}' \
          | python -c 'import json,sys; print(json.load(sys.stdin)["node_id"])')"
  curl -sf -X POST "${DASHBOARD}/nodes/${bed}/start" >/dev/null

  # 5. Start sweep
  local sweep_resp sweep_id
  sweep_resp="$(curl -sf -X POST "${DASHBOARD}/paper_eval/sweeps" \
                -H 'Content-Type: application/json' \
                -d "{\"matrix_path\":\"${MATRIX}\",\"node_id\":\"${ctx}\",\"per_trial_timeout_s\":${PER_TRIAL_TIMEOUT_S},\"poll_interval_s\":1}")"
  sweep_id="$(printf '%s' "$sweep_resp" | python -c 'import json,sys; print(json.load(sys.stdin).get("sweep_id",""))')"
  if [[ -z "$sweep_id" ]]; then
    log "  FAIL: sweep did not start: $sweep_resp"
    echo "sweep_start_failed" > "${combo_dir}/STATUS"
    return 1
  fi
  log "  sweep_id=${sweep_id}"

  # 6. Poll until completion (per-combo budget = 30 min hard cap).
  local deadline=$(( $(date +%s) + 1800 ))
  local status="" attempt=0
  while [[ $(date +%s) -lt $deadline ]]; do
    sleep 5
    status="$(curl -sf "${DASHBOARD}/paper_eval/sweeps/current" \
               | python -c 'import json,sys; print(json.load(sys.stdin).get("status",""))' 2>/dev/null || echo '')"
    attempt=$((attempt + 1))
    if (( attempt % 6 == 0 )); then
      log "  polling… status=${status} elapsed=$(( $(date +%s) - (deadline - 1800) ))s"
    fi
    case "$status" in
      completed|failed|cancelled) break ;;
    esac
  done

  if [[ "$status" != "completed" ]]; then
    log "  FAIL: sweep ended with status='${status}' (or polling timed out)"
    echo "$status" > "${combo_dir}/STATUS"
    # Still try to archive whatever we have.
  fi

  # 7. Archive
  curl -sf "${DASHBOARD}/paper_eval/sweeps/current/manifest" > "${combo_dir}/sweep_manifest.json" || true
  curl -sf "${DASHBOARD}/paper_eval/sweeps/current/aggregated" > "${combo_dir}/aggregated_matrix.json" || true
  curl -sf "${DASHBOARD}/paper_eval/sweeps/current/digest.csv" > "${combo_dir}/digest.csv" || true
  curl -sf "${DASHBOARD}/paper_eval/sweeps/current/digest.md" > "${combo_dir}/digest.md" || true
  echo "$status" > "${combo_dir}/STATUS"

  log "  combo done (status=${status})  archive: ${combo_dir}"
  return 0
}

# ----------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------

log "starting temp×top_p grid sweep"
log "  TEMPS:  ${TEMPS}"
log "  TOP_PS: ${TOP_PS}"
log "  matrix: ${MATRIX}"
log "  archive root: ${ARCHIVE_ROOT}"

n_total=0
n_failed=0
for temp in $TEMPS; do
  for top_p in $TOP_PS; do
    n_total=$((n_total + 1))
    if ! run_one_combo "$temp" "$top_p"; then
      n_failed=$((n_failed + 1))
    fi
  done
done

# Restore env to defaults so the next plain launcher run is unsurprising.
set_env_var OLLAMA_TEMPERATURE "0.2"
set_env_var OLLAMA_TOP_P ""
"$LAUNCHER" --stop >/dev/null 2>&1 || true

log ""
log "=== grid sweep done ==="
log "  combos run: ${n_total}"
log "  failed:     ${n_failed}"
log "  archive:    ${ARCHIVE_ROOT}"

[[ "$n_failed" == "0" ]] && exit 0 || exit 2
