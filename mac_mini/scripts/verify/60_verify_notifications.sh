#!/usr/bin/env bash
# ==============================================================================
# Script: 60_verify_notifications.sh
# Purpose: Verify outbound notification channel availability (Telegram or local mock fallback)
# ==============================================================================
set -euo pipefail

echo "==> [60_verify_notifications] Verifying outbound notification interface..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"
LOG_DIR="${WORKSPACE_DIR}/logs"
MOCK_LOG_FILE="${LOG_DIR}/mock_notifications.log"

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"
echo "  [OK] Environment variables loaded from ${ENV_FILE}."

is_placeholder() {
    local val="$1"
    if [ -z "${val}" ]; then return 0; fi

    local val_upper
    val_upper=$(printf '%s' "${val}" | tr '[:lower:]' '[:upper:]')

    case "${val_upper}" in
        *YOUR_*_HERE* | *PLACEHOLDER* | *<*>* ) return 0 ;;
        * ) return 1 ;;
    esac
}

TELEGRAM_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT="${TELEGRAM_CHAT_ID:-}"

if is_placeholder "${TELEGRAM_TOKEN}" || is_placeholder "${TELEGRAM_CHAT}"; then
    MODE="MOCK"
else
    MODE="TELEGRAM"
fi

echo "  [INFO] Notification Routing Mode: ${MODE}"

TEST_MESSAGE="[Verify][$$] Smart Home Notification Channel Test - $(date '+%Y-%m-%d %H:%M:%S')"

if [ "${MODE}" = "TELEGRAM" ]; then
    echo "  [INFO] Executing Telegram API validation..."

    if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
        echo "  [FATAL] 'curl' and 'jq' are required for Telegram mode."
        echo "          Please install them via the Mac mini install step or Homebrew, or use Mock mode by leaving credentials blank."
        exit 1
    fi

    API_ENDPOINT="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"

    RESPONSE=$(curl -fsS --connect-timeout 5 --max-time 10 -X POST "${API_ENDPOINT}" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\": \"${TELEGRAM_CHAT}\", \"text\": \"${TEST_MESSAGE}\"}" 2>/dev/null || echo "curl_failed")

    if [ "${RESPONSE}" = "curl_failed" ]; then
        echo "  [FATAL] Failed to connect to Telegram API."
        echo "          Please check network connectivity or DNS resolution."
        exit 1
    fi

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
    echo "  [INFO] Executing local mock log validation..."

    if [ ! -d "${LOG_DIR}" ]; then
        mkdir -p "${LOG_DIR}"
    fi

    echo "  [INFO] Appending test message to ${MOCK_LOG_FILE}..."

    if echo "${TEST_MESSAGE}" >> "${MOCK_LOG_FILE}"; then
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

echo "==> [PASS] Outbound notification channel verification successful."
