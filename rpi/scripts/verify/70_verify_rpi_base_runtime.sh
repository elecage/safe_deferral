#!/usr/bin/env bash
# ==============================================================================
# Script: 70_verify_rpi_base_runtime.sh
# Purpose: Verify RPi 5 base runtime, authority boundaries, synced assets, and time sync
# ==============================================================================
set -euo pipefail

echo "==> [70_verify_rpi_base_runtime] Verifying RPi 5 base runtime and authority boundaries..."

if ! command -v jq >/dev/null 2>&1 || ! command -v mosquitto_pub >/dev/null 2>&1 || ! command -v ping >/dev/null 2>&1 || ! command -v awk >/dev/null 2>&1 || ! command -v tee >/dev/null 2>&1; then
    echo "  [FATAL] Required tools (jq, mosquitto-clients, ping, awk, tee) are not installed."
    echo "          Please run the RPi base runtime installation step first."
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

echo "  [INFO] Checking local RPi .env for placeholder values..."
if [ "${MAC_MINI_HOST:-}" = "192.168.1.100" ] || [ "${MQTT_HOST:-}" = "192.168.1.100" ]; then
    echo "  [FATAL] Placeholder IP 192.168.1.100 remains in ${ENV_FILE}."
    exit 1
fi

if [ "${MAC_MINI_USER:-}" = "mac_user" ]; then
    echo "  [FATAL] Placeholder MAC_MINI_USER=mac_user remains in ${ENV_FILE}."
    exit 1
fi

if [ "${MQTT_PASS:-}" = "CHANGE_ME" ]; then
    echo "  [WARNING] MQTT_PASS is still CHANGE_ME. This is acceptable only if the broker ignores MQTT credentials."
fi

echo "  [INFO] Verifying Raspberry Pi authority boundary flags..."
if [ "${ALLOW_RPI_ACTUATION:-false}" != "false" ]; then
    echo "  [FATAL] ALLOW_RPI_ACTUATION must be false. RPi must not have actuation authority."
    exit 1
fi

if [ "${ALLOW_RPI_POLICY_AUTHORITY:-false}" != "false" ]; then
    echo "  [FATAL] ALLOW_RPI_POLICY_AUTHORITY must be false. RPi must not have policy authority."
    exit 1
fi

if [ "${ALLOW_RPI_DOORLOCK_CONTROL:-false}" != "false" ]; then
    echo "  [FATAL] ALLOW_RPI_DOORLOCK_CONTROL must be false. RPi must not have doorlock-control authority."
    exit 1
fi

echo "  [OK] RPi authority boundaries are explicitly non-authoritative."

TARGET_HOST="${MQTT_HOST:-}"
TARGET_PORT="${MQTT_PORT:-1883}"

if [ -z "${TARGET_HOST}" ]; then
    echo "  [FATAL] MQTT_HOST is not defined in .env. Cannot test communication."
    exit 1
fi

echo "  [INFO] Checking network reachability to Mac mini (${TARGET_HOST})..."
if ping -c 3 -W 3 "${TARGET_HOST}" >/dev/null 2>&1; then
    echo "  [OK] Mac mini is reachable via ICMP (Ping)."
else
    echo "  [FATAL] Cannot reach Mac mini at ${TARGET_HOST}. Check LAN and firewall."
    exit 1
fi

echo "  [INFO] Testing MQTT publish reachability..."
TEST_TOPIC="${DASHBOARD_OBSERVATION_TOPIC:-safe_deferral/dashboard/observation}"
TEST_MSG="rpi5_ping_$(date +%s)_$$"
AUTH_ARGS=()
if [ -n "${MQTT_USER:-}" ] && [ -n "${MQTT_PASS:-}" ]; then
    AUTH_ARGS=("-u" "${MQTT_USER}" "-P" "${MQTT_PASS}")
fi

PUB_CMD=(mosquitto_pub -h "${TARGET_HOST}" -p "${TARGET_PORT}")
if [ ${#AUTH_ARGS[@]} -gt 0 ]; then
    PUB_CMD+=("${AUTH_ARGS[@]}")
fi
PUB_CMD+=(-t "${TEST_TOPIC}" -m "${TEST_MSG}")

if "${PUB_CMD[@]}"; then
    echo "  [OK] MQTT publish request accepted on non-authoritative observation topic: ${TEST_TOPIC}"
else
    echo "  [FATAL] MQTT publish failed. Check Mosquitto status and firewall rules on Mac mini."
    exit 1
fi

POLICY_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"
SCHEMA_DIR="${SCHEMA_SYNC_PATH:-${WORKSPACE_DIR}/config/schemas}"
MQTT_DIR="${MQTT_REGISTRY_SYNC_PATH:-${WORKSPACE_DIR}/config/mqtt}"
PAYLOAD_DIR="${PAYLOAD_EXAMPLES_SYNC_PATH:-${WORKSPACE_DIR}/config/payloads}"

echo "  [INFO] Verifying read-only authority mirrors and reference assets..."
if [ ! -d "${POLICY_DIR}" ] || [ ! -d "${SCHEMA_DIR}" ]; then
    echo "  [FATAL] Policy or schema directory not found."
    exit 1
fi

if [ ! -d "${MQTT_DIR}" ]; then
    echo "  [FATAL] MQTT registry reference directory not found: ${MQTT_DIR}"
    exit 1
fi

if [ ! -d "${PAYLOAD_DIR}" ]; then
    echo "  [FATAL] Payload examples reference directory not found: ${PAYLOAD_DIR}"
    exit 1
fi

REQUIRED_POLICY_ASSETS=(
    "policy_table.json"
    "fault_injection_rules.json"
    "low_risk_actions.json"
    "output_profile.json"
)

REQUIRED_SCHEMA_ASSETS=(
    "context_schema.json"
    "candidate_action_schema.json"
    "policy_router_input_schema.json"
    "validator_output_schema.json"
    "class2_notification_payload_schema.json"
)

REQUIRED_MQTT_ASSETS=(
    "topic_registry.json"
    "publisher_subscriber_matrix.md"
    "topic_payload_contracts.md"
)

MISSING_ASSETS=0
for asset in "${REQUIRED_POLICY_ASSETS[@]}"; do
    target_file="${POLICY_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] Policy asset missing: ${asset}"
        MISSING_ASSETS=1
    elif ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Policy asset is corrupted or invalid JSON: ${asset}"
        MISSING_ASSETS=1
    fi
done

for asset in "${REQUIRED_SCHEMA_ASSETS[@]}"; do
    target_file="${SCHEMA_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] Schema asset missing: ${asset}"
        MISSING_ASSETS=1
    elif ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Schema asset is corrupted or invalid JSON: ${asset}"
        MISSING_ASSETS=1
    fi
done

for asset in "${REQUIRED_MQTT_ASSETS[@]}"; do
    target_file="${MQTT_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] MQTT reference asset missing: ${asset}"
        MISSING_ASSETS=1
    elif [[ "${asset}" == *.json ]] && ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] MQTT reference asset is corrupted or invalid JSON: ${asset}"
        MISSING_ASSETS=1
    fi
done

if [ -z "$(find "${PAYLOAD_DIR}" -type f -print -quit)" ]; then
    echo "  [FATAL] Payload examples reference directory is empty: ${PAYLOAD_DIR}"
    MISSING_ASSETS=1
fi

if [ "${MISSING_ASSETS}" -ne 0 ]; then
    echo "  [FATAL] Synced authority/reference assets are incomplete."
    echo "          Please ensure the artifact sync utility completed successfully."
    exit 1
fi

echo "  [OK] Policy/schema authority mirrors and MQTT/payload reference assets are present."

CONTEXT_SCHEMA="${SCHEMA_DIR}/context_schema.json"
echo "  [INFO] Verifying context schema alignment for doorbell context..."
if ! jq -e 'any(.. | objects; has("doorbell_detected"))' "${CONTEXT_SCHEMA}" >/dev/null 2>&1; then
    echo "  [FATAL] context schema does not contain doorbell_detected. Re-sync schema runtime assets."
    exit 1
fi
echo "  [OK] context schema includes doorbell_detected."

echo "  [INFO] Scanning payload examples for doorlock state misuse..."
DOORLOCK_STATE_HITS="$(find "${PAYLOAD_DIR}" -type f \( -name "*.json" -o -name "*.jsonl" \) -print0 | xargs -0 grep -nE '"(doorlock|front_door_lock|door_lock_state)"' 2>/dev/null || true)"
if [ -n "${DOORLOCK_STATE_HITS}" ]; then
    if printf '%s\n' "${DOORLOCK_STATE_HITS}" | grep -E 'pure_context_payload|device_states' >/dev/null 2>&1; then
        echo "  [FATAL] Doorlock-like state fields appear near pure_context_payload/device_states in payload examples."
        printf '%s\n' "${DOORLOCK_STATE_HITS}" | sed 's/^/    /'
        exit 1
    fi
    echo "  [WARNING] Doorlock-related terms found in payload examples. Review sensitive-actuation semantics:"
    printf '%s\n' "${DOORLOCK_STATE_HITS}" | sed 's/^/    /'
else
    echo "  [OK] No doorlock state field names found in payload examples."
fi

echo "  [INFO] Checking local RPi .env for legacy topic namespace drift..."
if grep -q '^TOPIC_NAMESPACE=smarthome/' "${ENV_FILE}" || grep -q '^VERIFICATION_AUDIT_TOPIC=smarthome/' "${ENV_FILE}"; then
    echo "  [FATAL] Legacy smarthome/* topic values remain in ${ENV_FILE}."
    echo "          Update TOPIC_NAMESPACE and VERIFICATION_AUDIT_TOPIC to safe_deferral/* values."
    exit 1
fi

echo "  [OK] Local .env does not retain legacy smarthome/* topic defaults for core namespace/audit keys."

echo "  [INFO] Measuring time sync offset and network RTT..."
LOG_DIR="${WORKSPACE_DIR}/logs"
mkdir -p "${LOG_DIR}"
TIME_LOG_FILE="${LOG_DIR}/time_sync_verification.log"
POLICY_FILE="${POLICY_DIR}/policy_table.json"

FRESHNESS_LIMIT=$(jq -r '.global_constraints.freshness_threshold_ms // 100' "${POLICY_FILE}" 2>/dev/null || echo "100")
echo "  [INFO] Target Freshness Threshold: ${FRESHNESS_LIMIT} ms (fallback applied if undefined)" | tee -a "${TIME_LOG_FILE}"

PING_OUT=$(ping -c 5 -q "${TARGET_HOST}" | tail -n 1 || echo "")
if [[ "${PING_OUT}" == *"/"* ]]; then
    AVG_RTT=$(printf '%s' "${PING_OUT}" | awk -F'/' '{print $5}')
    MAX_RTT=$(printf '%s' "${PING_OUT}" | awk -F'/' '{print $6}')
    echo "  [INFO] Network RTT to Mac mini (Avg/Max): ${AVG_RTT} ms / ${MAX_RTT} ms" | tee -a "${TIME_LOG_FILE}"
else
    echo "  [WARNING] Could not parse ping RTT statistics." | tee -a "${TIME_LOG_FILE}"
fi

OFFSET_MS="N/A"
if command -v chronyc >/dev/null 2>&1; then
    RAW_OFFSET=$(chronyc -c tracking 2>/dev/null | awk -F',' '{print $4}' || echo "0")
    OFFSET_MS=$(awk -v off="${RAW_OFFSET}" 'BEGIN {printf "%.3f", sqrt(off*off) * 1000}')
    echo "  [INFO] Chrony System Time Offset: ${OFFSET_MS} ms" | tee -a "${TIME_LOG_FILE}"
elif command -v timedatectl >/dev/null 2>&1 && timedatectl timesync-status >/dev/null 2>&1; then
    RAW_OFFSET=$(timedatectl timesync-status 2>/dev/null | grep -i "Offset:" | awk '{print $2}' || echo "0")
    OFFSET_MS=$(printf '%s' "${RAW_OFFSET}" | sed 's/[a-zA-Z]*//g' | awk '{printf "%.3f", sqrt($1*$1)}')
    echo "  [INFO] systemd-timesyncd Offset: ${OFFSET_MS} ms" | tee -a "${TIME_LOG_FILE}"
else
    echo "  [WARNING] Neither 'chronyc' nor 'systemd-timesyncd' is available. Offset measurement skipped." | tee -a "${TIME_LOG_FILE}"
fi

if [ "${OFFSET_MS}" != "N/A" ]; then
    MARGIN_CHECK=$(awk -v off="${OFFSET_MS}" -v lim="${FRESHNESS_LIMIT}" 'BEGIN { if(off > lim/2) print "WARNING"; else print "OK" }')
    if [ "${MARGIN_CHECK}" = "WARNING" ]; then
        echo "  [WARNING] Time offset (${OFFSET_MS} ms) is consuming >50% of the freshness threshold (${FRESHNESS_LIMIT} ms)!"
        echo "            Caution: stale fault injection results might become flaky due to narrow margin."
    else
        echo "  [OK] Time offset is well within the acceptable stale margin."
    fi
fi

echo "==> [PASS] Raspberry Pi 5 base runtime, authority boundary, and reference asset verification successful."
