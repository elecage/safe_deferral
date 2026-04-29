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

FAULT_TYPE=$(echo "${FAULT_PROFILE_JSON}" | jq -r '.fault_type // "staleness"')
echo "  [INFO] Selected Fault Profile: ${TARGET_PROFILE} (Type: ${FAULT_TYPE})"

# Mac mini subscribes only to safe_deferral/context/input for context payloads.
# Telemetry snapshots are published to safe_deferral/dashboard/observation.
# The old inject topic (safe_deferral/fault/injection) and audit topic
# (safe_deferral/audit/log) do not exist in the running pipeline.
INJECT_TOPIC="${SIM_CONTEXT_TOPIC:-safe_deferral/context/input}"
OBSERVE_TOPIC="${DASHBOARD_OBSERVATION_TOPIC:-safe_deferral/dashboard/observation}"
CORRELATION_ID="fi_test_$(date +%s)_$$"
LOG_FILE="$(mktemp)"

if [[ "${INJECT_TOPIC}" != safe_deferral/* ]]; then
    echo "  [FATAL] Inject topic must use safe_deferral/* namespace. Current: ${INJECT_TOPIC}"
    exit 1
fi

if [[ "${OBSERVE_TOPIC}" != safe_deferral/* ]]; then
    echo "  [FATAL] Observation topic must use safe_deferral/* namespace. Current: ${OBSERVE_TOPIC}"
    exit 1
fi

SUB_PID=""
cleanup() {
    if [ -n "${SUB_PID}" ] && kill -0 "${SUB_PID}" >/dev/null 2>&1; then
        kill "${SUB_PID}" >/dev/null 2>&1 || true
    fi
    rm -f "${LOG_FILE}"
}
trap cleanup EXIT

echo "  [INFO] Starting background MQTT subscriber on '${OBSERVE_TOPIC}' (Timeout: 15s)..."
mosquitto_sub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" \
    -t "${OBSERVE_TOPIC}" -W 15 > "${LOG_FILE}" 2>/dev/null &
SUB_PID=$!

sleep 1

# Build a schema-valid payload (policy_router_input_schema + context_schema).
# Mac mini intake rejects invalid payloads without publishing any telemetry,
# so this payload must pass full schema validation to exercise the pipeline.
#
# For staleness faults: trigger_event.timestamp_ms is set 30 seconds in the
# past. Mac mini overrides ingest_timestamp_ms with local time on arrival, so
# the Policy Router sees a stale context and routes to CLASS_2 (safe deferral).
NOW_MS=$(date +%s%3N)
STALE_TRIGGER_MS=$(( NOW_MS - 30000 ))

echo "  [INFO] Injecting schema-valid fault payload to '${INJECT_TOPIC}' (Correlation ID: ${CORRELATION_ID})..."
FAULT_PAYLOAD=$(jq -n \
    --arg cid "${CORRELATION_ID}" \
    --argjson now "${NOW_MS}" \
    --argjson stale "${STALE_TRIGGER_MS}" \
    '{
        "source_node_id": "rpi5_fault_injector",
        "routing_metadata": {
            "audit_correlation_id": $cid,
            "ingest_timestamp_ms": $now,
            "network_status": "online"
        },
        "pure_context_payload": {
            "trigger_event": {
                "event_type": "sensor",
                "event_code": "state_changed",
                "timestamp_ms": $stale
            },
            "environmental_context": {
                "temperature": 21.5,
                "illuminance": 320.0,
                "occupancy_detected": false,
                "smoke_detected": false,
                "gas_detected": false,
                "doorbell_detected": false
            },
            "device_states": {
                "living_room_light": "off",
                "bedroom_light": "off",
                "living_room_blind": "closed",
                "tv_main": "standby"
            }
        }
    }')

if echo "${FAULT_PAYLOAD}" | jq -e '
  .pure_context_payload.device_states as $states |
  ($states | has("doorlock")) or
  ($states | has("front_door_lock")) or
  ($states | has("door_lock_state"))
' >/dev/null 2>&1; then
    echo "  [FATAL] Doorlock state must not be placed in pure_context_payload.device_states."
    exit 1
fi

mosquitto_pub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" \
    -t "${INJECT_TOPIC}" -m "${FAULT_PAYLOAD}"

wait "${SUB_PID}" || true

# Parse each received JSON line looking for our correlation_id.
# The telemetry snapshot has: audit_correlation_id, route.route_class,
# validation.validation_status at the top level.
ROUTE_CLASS=""
VALIDATION_STATUS=""
MATCHED_LINE=""

while IFS= read -r line; do
    [ -z "${line}" ] && continue
    cid=$(echo "${line}" | jq -r '.audit_correlation_id // empty' 2>/dev/null || true)
    if [ "${cid}" = "${CORRELATION_ID}" ]; then
        MATCHED_LINE="${line}"
        ROUTE_CLASS=$(echo "${line}" | jq -r '.route.route_class // empty' 2>/dev/null || true)
        VALIDATION_STATUS=$(echo "${line}" | jq -r '.validation.validation_status // empty' 2>/dev/null || true)
        break
    fi
done < "${LOG_FILE}"

if [ -z "${MATCHED_LINE}" ]; then
    echo "  [FATAL] No telemetry snapshot found for correlation ID '${CORRELATION_ID}'."
    echo "          The safety pipeline may be unresponsive, or Mac mini main.py is not running."
    echo "          Confirm: docker compose logs mac_mini_pipeline | tail -20"
    exit 1
fi

echo "  [INFO] Matched telemetry snapshot. route_class='${ROUTE_CLASS}' validation_status='${VALIDATION_STATUS}'"

# Map pipeline telemetry fields to a safety outcome string that can be compared
# against fault_injection_rules.json expected/prohibited outcome lists.
ROUTING_RESULT="UNKNOWN"
case "${ROUTE_CLASS}" in
    CLASS_0)
        ROUTING_RESULT="defer_to_caregiver"
        ;;
    CLASS_2)
        ROUTING_RESULT="safe_deferral"
        ;;
    CLASS_1)
        case "${VALIDATION_STATUS}" in
            safe_deferral)          ROUTING_RESULT="safe_deferral" ;;
            rejected_escalation)    ROUTING_RESULT="validator_reject" ;;
            approved)               ROUTING_RESULT="approved_low_risk" ;;
            *)                      ROUTING_RESULT="UNKNOWN" ;;
        esac
        ;;
    *)
        ROUTING_RESULT="UNKNOWN"
        ;;
esac

echo "  [INFO] Derived safety outcome: '${ROUTING_RESULT}'"

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
    echo "          route_class='${ROUTE_CLASS}' validation_status='${VALIDATION_STATUS}'"
    echo "          Please review fault_injection_rules.json and Mac mini telemetry snapshot structure."
    exit 1
fi
