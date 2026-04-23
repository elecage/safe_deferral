#!/usr/bin/env bash
# ==============================================================================
# Script: 20_verify_mqtt_pubsub.sh
# Purpose: Verify MQTT Broker Pub/Sub functionality (Phase 5)
# ==============================================================================
set -euo pipefail

echo "==> [20_verify_mqtt_pubsub] Testing MQTT Broker Pub/Sub functionality..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if ! command -v mosquitto_pub >/dev/null 2>&1 || ! command -v mosquitto_sub >/dev/null 2>&1; then
    echo "  [FATAL] 'mosquitto_pub' or 'mosquitto_sub' command is not available."
    echo "          Please install the MQTT client tools via the Mac mini install step or Homebrew."
    exit 1
fi
echo "  [OK] 'mosquitto-clients' tools verified."

if [ -f "${ENV_FILE}" ]; then
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    echo "  [OK] Environment variables loaded from ${ENV_FILE}."
else
    echo "  [FATAL] ${ENV_FILE} not found. Cannot load MQTT configuration."
    exit 1
fi

TARGET_HOST="${MQTT_HOST:-127.0.0.1}"
TARGET_PORT="${MQTT_PORT:-1883}"

AUTH_ARGS=()
if [ -n "${MQTT_USER:-}" ] && [ -n "${MQTT_PASS:-}" ]; then
    AUTH_ARGS=("-u" "${MQTT_USER}" "-P" "${MQTT_PASS}")
    echo "  [INFO] Using MQTT authentication for user '${MQTT_USER}'."
else
    echo "  [INFO] No MQTT authentication credentials provided. Proceeding anonymously."
fi

TEST_TOPIC="smarthome/verify/test"
TEST_MSG="verify_$(date +%s)"
LOG_FILE="/tmp/mqtt_verify_$$.log"

echo "  [INFO] Target Broker: ${TARGET_HOST}:${TARGET_PORT}"
echo "  [INFO] Test Topic: ${TEST_TOPIC}"
echo "  [INFO] Starting background subscriber (Timeout: 3s)..."

mosquitto_sub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${TEST_TOPIC}" -C 1 -W 3 > "${LOG_FILE}" 2>/dev/null &
SUB_PID=$!

sleep 1

echo "  [INFO] Publishing test message: ${TEST_MSG}"
if ! mosquitto_pub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${TEST_TOPIC}" -m "${TEST_MSG}"; then
    echo "  [FATAL] mosquitto_pub command failed."
    echo "          Please check if the broker is reachable and credentials are correct."
    rm -f "${LOG_FILE}"
    kill "${SUB_PID}" 2>/dev/null || true
    exit 1
fi

wait "${SUB_PID}" || true

if grep -q "${TEST_MSG}" "${LOG_FILE}"; then
    echo "  [OK] Subscriber successfully received the test message."
    echo "==> [PASS] MQTT Pub/Sub test successful on ${TARGET_HOST}:${TARGET_PORT}."
    rm -f "${LOG_FILE}"
else
    echo "  [FATAL] MQTT Pub/Sub test failed. Subscriber did not receive the test message."
    echo "          Diagnostic hints:"
    echo "          - Check broker status (is mosquitto running?)"
    echo "          - Check network firewall/ACL rules (if remote)"
    echo "          - Check authentication credentials"
    rm -f "${LOG_FILE}"
    exit 1
fi
