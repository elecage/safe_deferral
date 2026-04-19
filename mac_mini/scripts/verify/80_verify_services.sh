#!/usr/bin/env bash
# ==============================================================================
# Script: 80_verify_services.sh
# Purpose: STRICTLY verify the health and functionality of all deployed services
# ==============================================================================
set -euo pipefail

WORKSPACE_DIR="${HOME}/smarthome_workspace"
PYTHON_ENV_FILE="${WORKSPACE_DIR}/.env"

echo ">>> [Phase 5] Starting Strict Service Verification..."

# ==============================================================================
# 0. Load and Verify Environment Variables
# ==============================================================================
if [ -f "${PYTHON_ENV_FILE}" ]; then
    source "${PYTHON_ENV_FILE}"
    echo "  [INFO] Loaded environment variables from ${PYTHON_ENV_FILE}"
else
    echo "  [FATAL] .env file not found at ${PYTHON_ENV_FILE}. Run configure step first."
    exit 1
fi

# [Strict Rule 1] 필수 환경변수 명시적 검사
REQUIRED_VARS=("OLLAMA_HOST" "TTS_API_BASE_URL" "SQLITE_PATH" "MQTT_HOST" "MQTT_PORT")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "  [FATAL] Required environment variable is missing or empty: ${var}"
        exit 1
    fi
done

# ==============================================================================
# 1. Docker Container Health Check
# ==============================================================================
echo ">>> 1. Checking Docker Container Health..."
CONTAINERS=("homeassistant" "mosquitto" "ollama" "local_tts_engine")

for container in "${CONTAINERS[@]}"; do
    if [ "$(docker inspect -f '{{.State.Running}}' "${container}" 2>/dev/null)" == "true" ]; then
        HEALTH=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}NoHealthCheck{{end}}' "${container}")

        # [Strict Rule 2] NoHealthCheck를 허용하지 않고 오직 'healthy'만 통과시킴
        if [ "$HEALTH" == "healthy" ]; then
            echo "  [OK] ${container} is running and healthy."
        else
            echo "  [FATAL] ${container} health status is: ${HEALTH}. (Expected: healthy)"
            exit 1
        fi
    else
        echo "  [FATAL] ${container} is NOT running!"
        exit 1
    fi
done

# ==============================================================================
# 2. Service Endpoint Checks (HTTP/API)
# ==============================================================================
echo ">>> 2. Verifying Service Endpoints (HTTP/API)..."

# 2.1 Home Assistant
if curl -s -f -o /dev/null "http://localhost:8123/"; then
    echo "  [OK] Home Assistant UI is accessible."
else
    echo "  [FATAL] Home Assistant UI is not responding."
    exit 1
fi

# 2.2 Ollama API & Model Check
if curl -s -f -o /dev/null "${OLLAMA_HOST}/api/tags"; then
    echo "  [OK] Ollama API is accessible (${OLLAMA_HOST})."
    if curl -s "${OLLAMA_HOST}/api/tags" | grep -q "llama3.1"; then
        echo "  [OK] Ollama model 'llama3.1' is pulled and ready."
    else
        echo "  [FATAL] Ollama model 'llama3.1' not found. Please pull it manually."
        exit 1
    fi
else
    echo "  [FATAL] Ollama API is not responding at ${OLLAMA_HOST}."
    exit 1
fi

# 2.3 Local TTS API
if curl -s -f -o /dev/null "${TTS_API_BASE_URL}/health"; then
    echo "  [OK] Local TTS API is accessible (${TTS_API_BASE_URL})."
else
    echo "  [FATAL] Local TTS API is not responding at ${TTS_API_BASE_URL}."
    exit 1
fi

# ==============================================================================
# 3. MQTT Broker Pub/Sub Test
# ==============================================================================
echo ">>> 3. Verifying MQTT Broker (Mosquitto)..."

# [Strict Rule 3] 테스트 도구 누락 시 skip 금지 및 강제 종료
if ! command -v mosquitto_sub &> /dev/null || ! command -v mosquitto_pub &> /dev/null; then
    echo "  [FATAL] 'mosquitto-clients' package is not installed."
    echo "          Strict verification requires real MQTT pub/sub testing. ABORTING."
    exit 1
fi

TEST_TOPIC="antigravity/verify/test"
TEST_MSG="verify_$(date +%s)"
TEMP_MQTT_OUT=$(mktemp /tmp/mqtt_test_out.XXXXXX)

# 백그라운드 프로세스가 타임아웃으로 종료되어도 메인 스크립트가 죽지 않도록 방어
mosquitto_sub -h "${MQTT_HOST}" -p "${MQTT_PORT}" -t "${TEST_TOPIC}" -C 1 -W 3 > "${TEMP_MQTT_OUT}" &
SUB_PID=$!
sleep 1

mosquitto_pub -h "${MQTT_HOST}" -p "${MQTT_PORT}" -t "${TEST_TOPIC}" -m "${TEST_MSG}"
wait $SUB_PID || true

if grep -q "${TEST_MSG}" "${TEMP_MQTT_OUT}"; then
    echo "  [OK] MQTT Pub/Sub test successful."
else
    echo "  [FATAL] MQTT Pub/Sub test failed. Broker did not relay the message."
    rm -f "${TEMP_MQTT_OUT}"
    exit 1
fi
rm -f "${TEMP_MQTT_OUT}"

# ==============================================================================
# 4. SQLite Database Check
# ==============================================================================
echo ">>> 4. Verifying SQLite Database (Audit Logger)..."
if [ -f "${SQLITE_PATH}" ]; then
    echo "  [OK] Database file exists at ${SQLITE_PATH}."
    if command -v sqlite3 &> /dev/null; then
        TABLES=$(sqlite3 "${SQLITE_PATH}" ".tables" || true)
        if [ -n "$TABLES" ]; then
            echo "  [OK] Database tables found: ${TABLES}"
        else
            echo "  [WARNING] Database exists but no tables found. (Will be migrated by Audit Logger)"
        fi
    fi
else
    echo "  [WARNING] Database file not found at ${SQLITE_PATH}. (Will be created on first run of Audit Logger)"
fi

echo ">>> [SUCCESS] All STRICT verification steps passed. The environment is READY for Phase 6."
