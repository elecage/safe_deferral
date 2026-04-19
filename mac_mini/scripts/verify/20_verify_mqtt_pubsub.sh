#!/usr/bin/env bash
# ==============================================================================
# Script: 20_verify_mqtt_pubsub.sh
# Purpose: Verify MQTT Broker Pub/Sub functionality (Phase 5)
# ==============================================================================
set -euo pipefail

echo "==> [20_verify_mqtt_pubsub] Testing MQTT Broker Pub/Sub functionality..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

# 1. mosquitto-clients 명령어 존재 여부 확인 (Fail-fast)
if ! command -v mosquitto_pub >/dev/null 2>&1 || ! command -v mosquitto_sub >/dev/null 2>&1; then
    echo "  [FATAL] 'mosquitto_pub' or 'mosquitto_sub' command is not available."
    echo "          Please install mosquitto-clients (e.g., sudo apt-get install mosquitto-clients)."
    exit 1
fi
echo "  [OK] 'mosquitto-clients' tools verified."

# 2. 환경변수 파일 검증 및 로드
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

# 인증 옵션을 배열로 처리 (비어있어도 깔끔하게 무시되며 전개됨)
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

# 3. 백그라운드에서 Subscribe 대기 (-C 1: 1개 메시지 수신 후 종료, -W 3: 3초 타임아웃)
mosquitto_sub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${TEST_TOPIC}" -C 1 -W 3 > "${LOG_FILE}" 2>/dev/null &
SUB_PID=$!

# Subscriber가 브로커에 연결될 수 있도록 잠시 대기
sleep 1

# 4. Publish 실행
echo "  [INFO] Publishing test message: ${TEST_MSG}"
if ! mosquitto_pub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${TEST_TOPIC}" -m "${TEST_MSG}"; then
    echo "  [FATAL] mosquitto_pub command failed."
    echo "          Please check if the broker is reachable and credentials are correct."
    rm -f "${LOG_FILE}"
    kill "${SUB_PID}" 2>/dev/null || true
    exit 1
fi

# Subscriber 정상 종료 또는 타임아웃 대기
wait "${SUB_PID}" || true

# 5. 최종 수신 결과 검증
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
