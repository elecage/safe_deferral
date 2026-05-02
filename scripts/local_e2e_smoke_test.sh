#!/usr/bin/env bash
# local_e2e_smoke_test.sh — full-stack E2E plumbing test
#
# What it does:
#   1. Calls local_e2e_launcher.sh to bring up everything
#   2. Creates a virtual context node via the dashboard HTTP API
#   3. Starts a paper-eval sweep with matrix_smoke.json (1 cell × 1 trial)
#   4. Polls until the sweep status reaches 'completed' (or timeout)
#   5. Downloads digest CSV and runs minimal sanity checks on it
#   6. Always tears down what it started, even on failure (trap EXIT)
#
# Usage:
#   ./scripts/local_e2e_smoke_test.sh
#   ./scripts/local_e2e_smoke_test.sh --keep-running   # don't stop stacks at end
#
# Exit codes:
#   0  ✓ smoke test passed
#   1  setup failure (launcher could not start something)
#   2  sweep timeout (didn't reach 'completed' in time)
#   3  verification failure (digest CSV missing rows / wrong content)
#
# Tunables (env):
#   SMOKE_SWEEP_TIMEOUT_S  default 90  — wall-clock budget for the sweep itself
#   SMOKE_NODE_ID          default "smoke-virtual-node"
#   DASHBOARD_PORT         default 8888

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LAUNCHER="${SCRIPT_DIR}/local_e2e_launcher.sh"

DASHBOARD_PORT="${DASHBOARD_PORT:-8888}"
DASHBOARD_BASE="http://localhost:${DASHBOARD_PORT}"

MATRIX_PATH="integration/paper_eval/matrix_smoke.json"
SWEEP_TIMEOUT_S="${SMOKE_SWEEP_TIMEOUT_S:-90}"

KEEP_RUNNING=0
if [[ "${1:-}" == "--keep-running" ]]; then
  KEEP_RUNNING=1
fi

log() { echo "[smoke] $*"; }
fail() { echo "[smoke] FAIL: $*" >&2; exit "${2:-3}"; }

# ----------------------------------------------------------------------
# Cleanup on any exit
# ----------------------------------------------------------------------

cleanup() {
  local rc=$?
  if [[ "$KEEP_RUNNING" == "1" ]]; then
    log "leaving stacks running (--keep-running). Stop later with: $LAUNCHER --stop"
  else
    log "cleanup: stopping stacks"
    "$LAUNCHER" --stop >/dev/null 2>&1 || true
  fi
  exit "$rc"
}
trap cleanup EXIT

# ----------------------------------------------------------------------
# 1. Launcher
# ----------------------------------------------------------------------

log "step 1/5: launching stacks"
if ! "$LAUNCHER"; then
  fail "launcher failed (see /tmp/safe_deferral_e2e/{macmini,rpi}.log)" 1
fi

# ----------------------------------------------------------------------
# 2. Create a virtual node
# ----------------------------------------------------------------------
# The /nodes endpoint ignores any node_id supplied by the caller and
# generates its own UUID — we extract that UUID from the response and
# pass it to the sweep below. (Older smoke versions assumed we could
# pick a friendly node_id; that was wrong.)

log "step 2/5: creating + starting virtual nodes (context + 2 actuator simulators)"

# Helper: POST /nodes + POST /nodes/{id}/start. Returns node_id on stdout.
create_and_start_node() {
  local payload="$1" label="$2" resp nid
  resp="$(curl -sf -X POST "${DASHBOARD_BASE}/nodes" \
           -H 'Content-Type: application/json' -d "$payload" || echo '')"
  [[ -n "$resp" ]] || { fail "POST /nodes (${label}) empty body" 1; return; }
  nid="$(printf '%s' "$resp" | python -c 'import json,sys; print(json.load(sys.stdin).get("node_id",""))')"
  [[ -n "$nid" ]] || { fail "no node_id in /nodes (${label}) response: $resp" 1; return; }
  curl -sf -X POST "${DASHBOARD_BASE}/nodes/${nid}/start" >/dev/null \
    || { fail "POST /nodes/${nid}/start (${label}) failed" 1; return; }
  printf '%s' "$nid"
}

# 1) context_node — runner publishes the trial's pure_context_payload via
#    this node's MQTT identity.
NODE_ID="$(create_and_start_node \
  '{"node_type":"context_node","description":"smoke test context node"}' \
  context_node)"
log "  context: ${NODE_ID}"

# 2+3) actuator_simulator nodes — listen to safe_deferral/actuation/command
#      and ACK back. Without these, dispatched CLASS_1 commands hit
#      ACK timeout (~3s) and escalate to CLASS_2 via the C204 trigger,
#      shifting observed_route_class from CLASS_1 to CLASS_2 and
#      inflating latency to ~8s. Package A's runner definitions list
#      both context_node AND actuator_simulator in required_node_types.
LIVING_ID="$(create_and_start_node \
  '{"node_type":"actuator_simulator","device_target":"living_room_light","description":"smoke test living room actuator"}' \
  actuator_simulator_living)"
log "  actuator (living_room_light): ${LIVING_ID}"

BEDROOM_ID="$(create_and_start_node \
  '{"node_type":"actuator_simulator","device_target":"bedroom_light","description":"smoke test bedroom actuator"}' \
  actuator_simulator_bedroom)"
log "  actuator (bedroom_light):     ${BEDROOM_ID}"

# ----------------------------------------------------------------------
# 3. Start sweep
# ----------------------------------------------------------------------

log "step 3/5: starting paper-eval sweep with ${MATRIX_PATH}"
SWEEP_PAYLOAD=$(cat <<EOF
{
  "matrix_path": "${MATRIX_PATH}",
  "node_id": "${NODE_ID}",
  "per_trial_timeout_s": 60,
  "poll_interval_s": 1
}
EOF
)
sweep_resp="$(curl -sf -X POST "${DASHBOARD_BASE}/paper_eval/sweeps" \
                -H "Content-Type: application/json" -d "$SWEEP_PAYLOAD" || echo '')"
if [[ -z "$sweep_resp" ]]; then
  fail "sweep start request failed — dashboard not accepting requests" 1
fi
sweep_id="$(printf '%s' "$sweep_resp" | python -c 'import json,sys; print(json.load(sys.stdin).get("sweep_id",""))')"
[[ -n "$sweep_id" ]] || fail "no sweep_id in response: $sweep_resp" 1
log "  sweep_id=${sweep_id}"

# ----------------------------------------------------------------------
# 4. Poll until completed
# ----------------------------------------------------------------------

log "step 4/5: polling until sweep completes (timeout: ${SWEEP_TIMEOUT_S}s)"
deadline=$(($(date +%s) + SWEEP_TIMEOUT_S))
final_status=""
while [[ $(date +%s) -lt $deadline ]]; do
  state="$(curl -sf "${DASHBOARD_BASE}/paper_eval/sweeps/current" || echo '{}')"
  status="$(printf '%s' "$state" | python -c 'import json,sys; print(json.load(sys.stdin).get("status",""))')"
  case "$status" in
    completed)
      final_status="$status"
      break
      ;;
    failed|cancelled)
      log "  sweep ended with status='$status'"
      log "  full state: $state"
      fail "sweep did not complete cleanly (status=${status})" 2
      ;;
    running|cancelling)
      sleep 2
      ;;
    "")
      sleep 1
      ;;
    *)
      sleep 2
      ;;
  esac
done

if [[ "$final_status" != "completed" ]]; then
  fail "sweep did not reach 'completed' within ${SWEEP_TIMEOUT_S}s" 2
fi
log "  ✓ sweep completed"

# ----------------------------------------------------------------------
# 5. Verify artifacts (digest CSV)
# ----------------------------------------------------------------------

log "step 5/5: verifying digest artifacts"
csv="$(curl -sf "${DASHBOARD_BASE}/paper_eval/sweeps/current/digest.csv" || echo '')"
if [[ -z "$csv" ]]; then
  fail "digest CSV download returned empty body" 3
fi

# Header line must include the stable column names that paper code indexes by.
echo "$csv" | head -1 | grep -q '^cell_id,' \
  || fail "digest CSV header missing or malformed: $(echo "$csv" | head -1)"

# Exactly one data row (BASELINE) for the smoke matrix.
data_rows="$(echo "$csv" | tail -n +2 | grep -c . || true)"
[[ "$data_rows" == "1" ]] \
  || fail "expected 1 data row in digest, got ${data_rows}"

# That row should be the BASELINE cell with n_trials=1 and pass_rate=1.0000.
echo "$csv" | tail -n +2 | grep -q '^BASELINE,' \
  || fail "BASELINE row missing from digest CSV"
echo "$csv" | tail -n +2 | grep -E '^BASELINE,.*,1,1\.0000' >/dev/null \
  || log "  WARN: BASELINE row n_trials=1 + pass_rate=1.0000 not exact match. Row: $(echo "$csv" | tail -n +2 | head -1)"

# Markdown digest sanity check.
md="$(curl -sf "${DASHBOARD_BASE}/paper_eval/sweeps/current/digest.md" || echo '')"
echo "$md" | grep -q 'matrix `v1-smoke`' \
  || fail "digest Markdown does not reference v1-smoke matrix"
echo "$md" | grep -q '## Reproducibility' \
  || fail "digest Markdown missing Reproducibility footer"

log "  ✓ digest CSV: 1 row (BASELINE)"
log "  ✓ digest MD : v1-smoke + Reproducibility footer"
log ""
log "✓✓✓ smoke test PASSED"
log "  full state available at: ${DASHBOARD_BASE}/paper_eval/sweeps/current"
log "  digest CSV available at: ${DASHBOARD_BASE}/paper_eval/sweeps/current/digest.csv"
exit 0
