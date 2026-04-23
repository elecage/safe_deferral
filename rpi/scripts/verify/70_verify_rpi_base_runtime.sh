#!/usr/bin/env bash
# ==============================================================================
# Script: 70_verify_rpi_base_runtime.sh
# Purpose: Verify RPi 5 Network, MQTT Publish Reachability, Synced Assets, and Time Sync
# ==============================================================================
set -euo pipefail

echo "==> [70_verify_rpi_base_runtime] Verifying RPi 5 Base Runtime & Communication..."

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

echo "  [INFO] Testing MQTT Publish Reachability..."
TEST_TOPIC="verify/rpi5/ping"
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
    echo "  [OK] MQTT publish request accepted. Port ${TARGET_PORT} is open."
else
    echo "  [FATAL] MQTT publish failed. Check Mosquitto status and firewall rules on Mac mini."
    exit 1
fi

POLICY_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"
SCHEMA_DIR="${SCHEMA_SYNC_PATH:-${WORKSPACE_DIR}/config/schemas}"

echo "  [INFO] Verifying read-only Phase 0 synced assets..."
if [ ! -d "${POLICY_DIR}" ] || [ ! -d "${SCHEMA_DIR}" ]; then
    echo "  [FATAL] Policy or schema directory not found."
    exit 1
fi

REQUIRED_POLICY_ASSETS=(
    "policy_table_v1_1_2_FROZEN.json"
    "fault_injection_rules_v1_4_0_FROZEN.json"
    "low_risk_actions_v1_1_0_FROZEN.json"
    "output_profile_v1_1_0.json"
)

REQUIRED_SCHEMA_ASSETS=(
    "context_schema_v1_0_0_FROZEN.json"
    "candidate_action_schema_v1_0_0_FROZEN.json"
    "policy_router_input_schema_v1_1_1_FROZEN.json"
    "validator_output_schema_v1_1_0_FROZEN.json"
    "class_2_notification_payload_schema_v1_0_0_FROZEN.json"
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

if [ "${MISSING_ASSETS}" -ne 0 ]; then
    echo "  [FATAL] Phase 0 synced assets are incomplete."
    echo "          Please ensure the artifact sync utility completed successfully."
    exit 1
fi
echo "  [OK] All 9 required Phase 0 synced assets are present and valid."

echo "  [INFO] Measuring Time Sync Offset and Network Jitter..."
LOG_DIR="${WORKSPACE_DIR}/logs"
mkdir -p "${LOG_DIR}"
TIME_LOG_FILE="${LOG_DIR}/time_sync_verification.log"
POLICY_FILE="${POLICY_DIR}/policy_table_v1_1_2_FROZEN.json"

FRESHNESS_LIMIT=$(jq -r '.global_constraints.freshness_threshold_ms // 100' "${POLICY_FILE}" 2>/dev/null || echo "100")
echo "  [INFO] Target Freshness Threshold: ${FRESHNESS_LIMIT} ms (Fallback applied if undefined)" | tee -a "${TIME_LOG_FILE}"

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
        echo "            Caution: Stale fault injection results might become flaky due to narrow margin."
    else
        echo "  [OK] Time offset is well within the acceptable stale margin."
    fi
fi

echo "==> [PASS] Raspberry Pi 5 Base Runtime and Communication verification successful."
