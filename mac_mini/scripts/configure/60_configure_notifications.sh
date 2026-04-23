#!/usr/bin/env bash
# ==============================================================================
# Script: 60_configure_notifications.sh
# Purpose: Configure Telegram or Mock fallback notifications (Phase 4)
# ==============================================================================
set -euo pipefail

echo "==> [60_configure_notifications] Configuring Notification Interfaces..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"
LOG_DIR="${WORKSPACE_DIR}/logs"
MOCK_LOG="${LOG_DIR}/mock_notifications.log"

mkdir -p "${LOG_DIR}"

# 1. 환경변수 파일 존재 여부 검증
if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    exit 1
fi

# 2. 토큰 및 Chat ID 추출
TELEGRAM_BOT_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "${ENV_FILE}" | cut -d '=' -f2 | tr -d '"' | tr -d "'" || true)
TELEGRAM_CHAT_ID=$(grep "^TELEGRAM_CHAT_ID=" "${ENV_FILE}" | cut -d '=' -f2 | tr -d '"' | tr -d "'" || true)

# [개선 1] 대소문자 무관 Placeholder 정밀 검출 함수
is_placeholder() {
    local val="$1"
    # macOS 기본 bash(3.2) 호환성을 위해 tr 명령어로 소문자 변환 후 검사
    local lower_val=$(echo "${val}" | tr '[:upper:]' '[:lower:]')

    if [ -z "${lower_val}" ] || [[ "${lower_val}" == *"your_"* ]] || [[ "${lower_val}" == *"placeholder"* ]] || [[ "${lower_val}" == *"<"*">"* ]]; then
        return 0
    else
        return 1
    fi
}

# Mock Fallback 활성화 공통 함수
enable_mock_fallback() {
    echo "  [INFO] Activating MOCK Notification Fallback Mode..."
    touch "${MOCK_LOG}"
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] SYSTEM: Mock notification mode activated." >> "${MOCK_LOG}"
    echo "  [OK] Mock log initialized at ${MOCK_LOG}."
    echo "       (Outbound external messages will NOT be sent)"
}

# 3. Notification Mode 분기 및 Fallback 처리
if is_placeholder "${TELEGRAM_BOT_TOKEN}" || is_placeholder "${TELEGRAM_CHAT_ID}"; then
    echo "  [INFO] Telegram credentials are missing or set to placeholders."
    enable_mock_fallback
else
    echo "  [INFO] Valid Telegram credentials found. Activating TELEGRAM Mode..."

    # [개선 3] curl 존재 여부 사전 확인 (Fail-fast)
    if ! command -v curl >/dev/null 2>&1; then
        echo "  [WARNING] 'curl' command is not available."
        echo "            Cannot verify Telegram API. Falling back to Mock mode."
        enable_mock_fallback
    else
        echo "  [INFO] Testing Outbound Telegram connection..."
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST             "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"             -d chat_id="${TELEGRAM_CHAT_ID}"             -d text="✅ [Smart Home Edge] Notification pipeline configured successfully." || echo "000")

        # [개선 2] Telegram API 성공 여부에 따른 자연스러운 Fallback 전환
        if [ "${HTTP_STATUS}" -eq 200 ]; then
            echo "  [OK] Test notification sent successfully. Telegram mode is active."
        else
            echo "  [WARNING] Failed to send test notification (HTTP Status: ${HTTP_STATUS})."
            echo "            Please verify your token, chat ID, or network in .env"
            echo "  [INFO] Gracefully transitioning to Fallback Mode due to API failure..."
            enable_mock_fallback
        fi
    fi
fi

echo "==> [PASS] Notification setup completed."
