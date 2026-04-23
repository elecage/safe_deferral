#!/usr/bin/env bash
# ==============================================================================
# Script: 80_verify_rpi_closed_loop_audit.sh
# Purpose: Verify Closed-loop Assessment of Fault Injection (Phase 5)
# ==============================================================================
set -euo pipefail

echo "==> [80_verify_rpi_closed_loop_audit] Verifying Closed-loop Safety Assessment..."

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

TARGET_HOST="${MQTT_HOST:-127.0.0.1}"
TARGET_PORT="${MQTT_PORT:-1883}"
POLICY_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"
FAULT_RULES_FILE="${POLICY_DIR}/fault_injection_rules_v1_4_0_FROZEN.json"

if [ ! -f "${FAULT_RULES_FILE}" ]; then
    echo "  [FATAL] Fault injection rules not found at ${FAULT_RULES_FILE}."
    exit 1
fi

AUTH_ARGS=()
if [ -n "${MQTT_USER:-}" ] && [ -n "${MQTT_PASS:-}" ]; then
    AUTH_ARGS=("-u" "${MQTT_USER}" "-P" "${MQTT_PASS}")
fi

echo "  [INFO] Parsing deterministic fault profile from frozen assets..."
TARGET_PROFILE="${ACTIVE_FAULT_PROFILE:-${FAULT_PROFILE:-FAULT_STALENESS_01}}"

FAULT_PROFILE_JSON=$(jq -c --arg profile "${TARGET_PROFILE}" '
  if $profile == "randomized_stress_profile" then .randomized_stress_profile
  else .deterministic_profiles[$profile]
  end // empty
' "${FAULT_RULES_FILE}")

if [ -z "${FAULT_PROFILE_JSON}" ]; then
    echo "  [FATAL] Target profile '${TARGET_PROFILE}' not found in ${FAULT_RULES_FILE}."
    exit 1
fi

FAULT_TYPE=$(echo "${FAULT_PROFILE_JSON}" | jq -r '.fault_type // "missing_sensor"')
echo "  [INFO] Selected Fault Profile: ${TARGET_PROFILE} (Type: ${FAULT_TYPE})"

AUDIT_TOPIC="${VERIFICATION_AUDIT_TOPIC:-smarthome/audit/validator_output}"
INJECT_TOPIC="${INJECT_TOPIC:-smarthome/context/raw}"
CORRELATION_ID="fi_test_$(date +%s)_$$"
LOG_FILE="/tmp/audit_result_$$.log"

echo "  [INFO] Starting background MQTT subscriber on '${AUDIT_TOPIC}' (Timeout: 5s)..."
mosquitto_sub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${AUDIT_TOPIC}" -W 5 > "${LOG_FILE}" 2>/dev/null &
SUB_PID=$!

sleep 1

echo "  [INFO] Injecting fault payload with Correlation ID: ${CORRELATION_ID}..."
FAULT_PAYLOAD=$(jq -n \
    --arg cid "${CORRELATION_ID}" \
    --arg ftype "${FAULT_TYPE}" \
    '{
        "source_node_id": "rpi5_fault_injector",
        "routing_metadata": { "audit_correlation_id": $cid, "network_status": "online", "injected_fault": $ftype },
        "pure_context_payload": { "environmental_context": {}, "device_states": {} }
    }')

mosquitto_pub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${INJECT_TOPIC}" -m "${FAULT_PAYLOAD}"

wait "${SUB_PID}" || true

ROUTING_RESULT="UNKNOWN"
if grep -q "${CORRELATION_ID}" "${LOG_FILE}"; then
    ROUTING_RESULT=$(jq -r "select(.audit_correlation_id == \"${CORRELATION_ID}\") | .routing_target" "${LOG_FILE}" | tail -n 1)
fi
rm -f "${LOG_FILE}"

echo "  [INFO] Observed Routing Target: ${ROUTING_RESULT}"

if [ "${ROUTING_RESULT}" = "UNKNOWN" ] || [ -z "${ROUTING_RESULT}" ]; then
    echo "  [FATAL] No audit trace found for injected fault. The safety pipeline may be unresponsive."
    exit 1
fi

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

if [ "${IS_PROHIBITED}" = "true" ]; then
    echo "  [FATAL] System triggered PROHIBITED outcome: '${ROUTING_RESULT}'!"
    echo "          UNSAFE ACTUATION (UAR) occurred. Fault injection defense FAILED."
    exit 1
fi

if [ "${IS_EXPECTED}" = "true" ]; then
    echo "  [OK] System safely resolved the fault into expected outcome: '${ROUTING_RESULT}'"
    echo "==> [PASS] Closed-loop Safety Audit verification successful. The Smart Home is SAFE."
else
    echo "  [WARNING] Outcome '${ROUTING_RESULT}' is neither expected nor strictly prohibited."
    echo "            Please review fault_injection_rules_v1_4_0_FROZEN.json."
    exit 1
fi
