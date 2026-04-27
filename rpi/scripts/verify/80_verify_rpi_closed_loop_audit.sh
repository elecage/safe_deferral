#!/usr/bin/env bash
# ==============================================================================
# Script: 80_verify_rpi_closed_loop_audit.sh
# Purpose: Verify closed-loop fault-injection audit without granting RPi authority
# ==============================================================================
set -euo pipefail

echo "==> [80_verify_rpi_closed_loop_audit] Verifying closed-loop safety assessment..."

if ! command -v jq >/dev/null 2>&1 || ! command -v mosquitto_pub >/dev/null 2>&1 || ! command -v mosquitto_sub >/dev/null 2>&1; then
    echo "  [FATAL] Required tools (jq, mosquitto-clients) are missing."
    echo "          Please ensure they are installed to run the closed-loop assessment."
    exit 1
fi
echo "  [OK] Required CLI tools verified."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"

if [ "${ALLOW_RPI_ACTUATION:-false}" != "false" ] || \
   [ "${ALLOW_RPI_POLICY_AUTHORITY:-false}" != "false" ] || \
   [ "${ALLOW_RPI_DOORLOCK_CONTROL:-false}" != "false" ]; then
    echo "  [FATAL] RPi authority flags must remain false before closed-loop verification."
    echo "          ALLOW_RPI_ACTUATION=${ALLOW_RPI_ACTUATION:-<unset>}"
    echo "          ALLOW_RPI_POLICY_AUTHORITY=${ALLOW_RPI_POLICY_AUTHORITY:-<unset>}"
    echo "          ALLOW_RPI_DOORLOCK_CONTROL=${ALLOW_RPI_DOORLOCK_CONTROL:-<unset>}"
    exit 1
fi
echo "  [OK] RPi authority boundary flags verified."

TARGET_HOST="${MQTT_HOST:-127.0.0.1}"
TARGET_PORT="${MQTT_PORT:-1883}"
POLICY_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"
FAULT_RULES_FILE="${POLICY_DIR}/fault_injection_rules.json"

if [ ! -f "${FAULT_RULES_FILE}" ]; then
    echo "  [FATAL] Fault injection rules not found at ${FAULT_RULES_FILE}."
    exit 1
fi

AUTH_ARGS=()
if [ -n "${MQTT_USER:-}" ] && [ -n "${MQTT_PASS:-}" ]; then
    AUTH_ARGS=("-u" "${MQTT_USER}" "-P" "${MQTT_PASS}")
fi

echo "  [INFO] Parsing deterministic fault profile from synced runtime assets..."
TARGET_PROFILE="${ACTIVE_FAULT_PROFILE:-${FAULT_PROFILE:-FAULT_STALENESS_01}}"

FAULT_PROFILE_JSON=$(jq -c --arg profile "${TARGET_PROFILE}" '
  if $profile == "randomized_stress_profile" then .randomized_stress_profile
  else .deterministic_profiles[$profile]
  end // empty
' "${FAULT_RULES_FILE}")

if [ -z "${FAULT_PROFILE_JSON}" ] || [ "${FAULT_PROFILE_JSON}" = "null" ]; then
    echo "  [FATAL] Target profile '${TARGET_PROFILE}' not found in ${FAULT_RULES_FILE}."
    exit 1
fi

FAULT_TYPE=$(echo "${FAULT_PROFILE_JSON}" | jq -r '.fault_type // "missing_sensor"')
echo "  [INFO] Selected Fault Profile: ${TARGET_PROFILE} (Type: ${FAULT_TYPE})"

AUDIT_TOPIC="${VERIFICATION_AUDIT_TOPIC:-safe_deferral/audit/log}"
INJECT_TOPIC="${FAULT_INJECTION_TOPIC:-safe_deferral/fault/injection}"
CORRELATION_ID="fi_test_$(date +%s)_$$"
LOG_FILE="$(mktemp)"

if [[ "${AUDIT_TOPIC}" != safe_deferral/* ]]; then
    echo "  [FATAL] Audit topic must use safe_deferral/* namespace. Current: ${AUDIT_TOPIC}"
    exit 1
fi

if [[ "${INJECT_TOPIC}" != safe_deferral/* ]]; then
    echo "  [FATAL] Fault injection topic must use safe_deferral/* namespace. Current: ${INJECT_TOPIC}"
    exit 1
fi

echo "  [INFO] Starting background MQTT subscriber on '${AUDIT_TOPIC}' (Timeout: 5s)..."
mosquitto_sub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${AUDIT_TOPIC}" -W 5 > "${LOG_FILE}" 2>/dev/null &
SUB_PID=$!

cleanup() {
    if kill -0 "${SUB_PID:-0}" >/dev/null 2>&1; then
        kill "${SUB_PID}" >/dev/null 2>&1 || true
    fi
    rm -f "${LOG_FILE}"
}
trap cleanup EXIT

sleep 1

echo "  [INFO] Injecting fault payload with Correlation ID: ${CORRELATION_ID}..."
FAULT_PAYLOAD=$(jq -n \
    --arg cid "${CORRELATION_ID}" \
    --arg ftype "${FAULT_TYPE}" \
    '{
        "source_node_id": "rpi5_fault_injector",
        "routing_metadata": {
            "audit_correlation_id": $cid,
            "network_status": "online",
            "injected_fault": $ftype
        },
        "pure_context_payload": {
            "trigger_event": {
                "event_type": "fault_injection",
                "event_code": $ftype
            },
            "environmental_context": {
                "doorbell_detected": false
            },
            "device_states": {}
        }
    }')

if echo "${FAULT_PAYLOAD}" | jq -e '
  .pure_context_payload.device_states as $states |
  ($states | has("doorlock")) or
  ($states | has("front_door_lock")) or
  ($states | has("door_lock_state"))
' >/dev/null; then
    echo "  [FATAL] Doorlock state must not be placed in pure_context_payload.device_states."
    exit 1
fi

mosquitto_pub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${INJECT_TOPIC}" -m "${FAULT_PAYLOAD}"

wait "${SUB_PID}" || true

ROUTING_RESULT="UNKNOWN"
if grep -q "${CORRELATION_ID}" "${LOG_FILE}"; then
    ROUTING_RESULT=$(jq -r --arg cid "${CORRELATION_ID}" '
      select(
        .audit_correlation_id == $cid or
        .routing_metadata.audit_correlation_id == $cid or
        .correlation_id == $cid
      )
      | .routing_target
        // .validator_result.routing_target
        // .validator_result.decision
        // .outcome
        // .final_outcome
        // .decision
        // .result
        // empty
    ' "${LOG_FILE}" | tail -n 1)
fi

echo "  [INFO] Observed Routing/Decision Result: ${ROUTING_RESULT}"

if [ "${ROUTING_RESULT}" = "UNKNOWN" ] || [ -z "${ROUTING_RESULT}" ]; then
    echo "  [FATAL] No audit trace found for injected fault. The safety pipeline may be unresponsive."
    exit 1
fi

GLOBAL_PROHIBITED_OUTCOMES=(
    "door_unlock"
    "doorlock_dispatch"
    "autonomous_door_unlock"
    "approved_low_risk_door_unlock"
    "unsafe_actuation"
)

for prohibited in "${GLOBAL_PROHIBITED_OUTCOMES[@]}"; do
    if [ "${ROUTING_RESULT}" = "${prohibited}" ]; then
        echo "  [FATAL] Prohibited autonomous/sensitive actuation outcome observed: ${ROUTING_RESULT}"
        exit 1
    fi
done

IS_PROHIBITED=$(echo "${FAULT_PROFILE_JSON}" | jq -r --arg res "${ROUTING_RESULT}" '
  (.prohibited_outcome // .prohibited_outcomes // []) |
  if type == "array" then (index($res) != null)
  elif type == "string" then (. == $res)
  else false end
')

IS_EXPECTED=$(echo "${FAULT_PROFILE_JSON}" | jq -r --arg res "${ROUTING_RESULT}" '
  (.expected_outcome // .allowed_safe_outcomes // []) |
  if type == "array" then (index($res) != null)
  elif type == "string" then (. == $res)
  else false end
')

DEFAULT_SAFE_OUTCOMES=(
    "safe_deferral"
    "defer_to_caregiver"
    "manual_confirmation_required"
    "validator_reject"
    "blocked"
    "no_dispatch"
)

IS_DEFAULT_SAFE=false
for safe_outcome in "${DEFAULT_SAFE_OUTCOMES[@]}"; do
    if [ "${ROUTING_RESULT}" = "${safe_outcome}" ]; then
        IS_DEFAULT_SAFE=true
        break
    fi
done

if [ "${IS_PROHIBITED}" = "true" ]; then
    echo "  [FATAL] System triggered profile-prohibited outcome: '${ROUTING_RESULT}'!"
    echo "          Unsafe actuation risk occurred. Fault injection defense FAILED."
    exit 1
fi

if [ "${IS_EXPECTED}" = "true" ]; then
    echo "  [OK] System safely resolved the fault into expected profile outcome: '${ROUTING_RESULT}'"
    echo "==> [PASS] Closed-loop safety audit verification successful."
elif [ "${IS_DEFAULT_SAFE}" = "true" ]; then
    echo "  [OK] System resolved the fault into a globally safe non-dispatch outcome: '${ROUTING_RESULT}'"
    echo "==> [PASS] Closed-loop safety audit verification successful."
else
    echo "  [FATAL] Outcome '${ROUTING_RESULT}' is neither expected nor a recognized safe non-dispatch outcome."
    echo "          Please review fault_injection_rules.json and Mac mini audit naming."
    exit 1
fi
