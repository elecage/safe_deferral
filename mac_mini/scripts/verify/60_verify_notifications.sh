#!/usr/bin/env bash
# ==============================================================================
# Script: 60_verify_notifications.sh
# Purpose: Verify Outbound Notification Interface (Telegram or Local Mock) (Phase 5)
# ==============================================================================
set -euo pipefail

echo "==> [60_verify_notifications] Verifying Outbound Notification Interface..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"
LOG_DIR="${WORKSPACE_DIR}/logs"
MOCK_LOG_FILE="${LOG_DIR}/mock_notifications.log"

# 1. 환경변수 파일 검증 및 로드
if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"
echo "  [OK] Environment variables loaded from ${ENV_FILE}."

# 2. 대소문자 무관 및 특수문자(<...>) 포괄 Placeholder 판정 함수
is_placeholder() {
    local val="$1"
    # 값이 비어있으면 placeholder로 간주
    if [ -z "${val}" ]; then return 0; fi

    local val_upper
    val_upper=$(printf '%s' "${val}" | tr '[:lower:]' '[:upper:]')

    case "${val_upper}" in
        *YOUR_*_HERE* | *PLACEHOLDER* | *<*>* ) return 0 ;;
        * ) return 1 ;;
    esac
}

# 3. 유연한 Fallback 라우팅 결정 (Token이나 Chat ID 중 하나라도 불완전하면 Mock 전환)
TELEGRAM_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT="${TELEGRAM_CHAT_ID:-}"

if is_placeholder "${TELEGRAM_TOKEN}" || is_placeholder "${TELEGRAM_CHAT}"; then
    MODE="MOCK"
else
    MODE="TELEGRAM"
fi

echo "  [INFO] Notification Routing Mode: ${MODE}"

# 4. 실제 송신 및 응답 검증 (Closed-loop)
TEST_MESSAGE="[Verify][$$] Smart Home Notification System Test - $(date '+%Y-%m-%d %H:%M:%S')"

if [ "${MODE}" = "TELEGRAM" ]; then
    echo "  [INFO] Executing Telegram API validation..."

    if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
        echo "  [FATAL] 'curl' and 'jq' are required for Telegram mode."
        echo "          Please install them or use Mock mode by leaving credentials blank."
        exit 1
    fi

    API_ENDPOINT="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"

    # curl로 HTTP 요청 (타임아웃 10초 제한) 후 응답 JSON 캡처
    RESPONSE=$(curl -fsS --connect-timeout 5 --max-time 10 -X POST "${API_ENDPOINT}" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\": \"${TELEGRAM_CHAT}\", \"text\": \"${TEST_MESSAGE}\"}" 2>/dev/null || echo "curl_failed")

    if [ "${RESPONSE}" = "curl_failed" ]; then
        echo "  [FATAL] Failed to connect to Telegram API."
        echo "          Please check network connectivity or DNS resolution."
        exit 1
    fi

    # jq를 이용해 Telegram API의 응답 규격인 '.ok' 필드 파싱
    IS_OK=$(echo "${RESPONSE}" | jq -r '.ok // false')

    if [ "${IS_OK}" = "true" ]; then
        echo "  [OK] Telegram message sent successfully to Chat ID: ${TELEGRAM_CHAT}"
    else
        DESCRIPTION=$(echo "${RESPONSE}" | jq -r '.description // "Unknown error"')
        echo "  [FATAL] Telegram API rejected the request: ${DESCRIPTION}"
        echo "          Diagnostic hints:"
        echo "          - Check if TELEGRAM_BOT_TOKEN is valid."
        echo "          - Check if TELEGRAM_CHAT_ID is correct and the bot has started the chat."
        exit 1
    fi

else
    echo "  [INFO] Executing Local Mock Log validation..."

    # 로그 디렉터리가 없으면 생성
    if [ ! -d "${LOG_DIR}" ]; then
        mkdir -p "${LOG_DIR}"
    fi

    echo "  [INFO] Appending test message to ${MOCK_LOG_FILE}..."

    if echo "${TEST_MESSAGE}" >> "${MOCK_LOG_FILE}"; then
        # [최종 교정 반영] tail -n 1을 제거하고 파일 전체에서 고유 메시지(PID 포함)를 빠르고 정확하게 검색
        if grep -Fq "${TEST_MESSAGE}" "${MOCK_LOG_FILE}"; then
            echo "  [OK] Mock notification successfully appended and verified in log."
        else
            echo "  [FATAL] Failed to verify the appended message in ${MOCK_LOG_FILE}."
            exit 1
        fi
    else
        echo "  [FATAL] Cannot write to ${MOCK_LOG_FILE}. Check file/directory permissions."
        exit 1
    fi
fi

echo "==> [PASS] Outbound notification verification successful."
