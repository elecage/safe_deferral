#!/usr/bin/env bash
# ==============================================================================
# Script: 50_verify_env_and_assets.sh
# Purpose: Verify essential environment variables and deployed runtime assets (Phase 5)
# ==============================================================================
set -euo pipefail

echo "==> [50_verify_env_and_assets] Verifying Environment Variables and Runtime Assets..."

# 0. jq 명령어 존재 여부 확인 (Fail-fast)
if ! command -v jq >/dev/null 2>&1; then
    echo "  [FATAL] 'jq' command is not available."
    echo "          Please ensure the jq package is installed for JSON validation."
    exit 1
fi

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

# 1. .env 파일 존재 여부 확인 (Fail-fast)
if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    echo "          Please run the environment configuration step first."
    exit 1
fi
echo "  [OK] ${ENV_FILE} exists."

# shellcheck disable=SC1090
source "${ENV_FILE}"
echo "  [OK] Environment variables loaded from ${ENV_FILE}."

# 2. 필수 환경변수 값 할당 여부 검증
echo "  [INFO] Checking essential environment variables..."

# [수정 반영] Fallback이 지원되는 선택적 변수(OLLAMA_MODEL, TELEGRAM_BOT_TOKEN) 제외
REQUIRED_VARS=(
    "MQTT_HOST"
    "MQTT_PORT"
    "OLLAMA_HOST"
    "SQLITE_PATH"
)

MISSING_VARS=0
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "  [FATAL] Environment variable '${var}' is missing or empty."
        MISSING_VARS=1
    fi
done

if [ "${MISSING_VARS}" -ne 0 ]; then
    echo "  [FATAL] One or more essential environment variables are missing in .env."
    exit 1
fi
echo "  [OK] All essential environment variables are properly set."

# 3. 런타임 정책/스키마 디렉터리 결정
POLICY_DIR="${POLICY_DIR:-${WORKSPACE_DIR}/config/policies}"
SCHEMA_DIR="${SCHEMA_DIR:-${WORKSPACE_DIR}/config/schemas}"

echo "  [INFO] Policy runtime directory: ${POLICY_DIR}"
echo "  [INFO] Schema runtime directory: ${SCHEMA_DIR}"

if [ ! -d "${POLICY_DIR}" ]; then
    echo "  [FATAL] Policy directory not found at ${POLICY_DIR}."
    exit 1
fi

if [ ! -d "${SCHEMA_DIR}" ]; then
    echo "  [FATAL] Schema directory not found at ${SCHEMA_DIR}."
    exit 1
fi

# 4. 런타임 정규화 자산 존재 및 무결성(Integrity) 검증
echo "  [INFO] Checking deployed runtime policy assets..."
REQUIRED_POLICY_ASSETS=(
    "policy_table.json"
    "low_risk_actions.json"
    "fault_injection_rules.json"
    "output_profile.json"
)

MISSING_POLICY_ASSETS=0
for asset in "${REQUIRED_POLICY_ASSETS[@]}"; do
    target_file="${POLICY_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] Policy asset missing: ${asset}"
        MISSING_POLICY_ASSETS=1
    elif ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Invalid JSON format detected in policy asset: ${asset}"
        MISSING_POLICY_ASSETS=1
    fi
done

echo "  [INFO] Checking deployed runtime schema assets..."
REQUIRED_SCHEMA_ASSETS=(
    "context_schema.json"
    "candidate_action_schema.json"
    "policy_router_input_schema.json"
    "validator_output_schema.json"
)

MISSING_SCHEMA_ASSETS=0
for asset in "${REQUIRED_SCHEMA_ASSETS[@]}"; do
    target_file="${SCHEMA_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] Schema asset missing: ${asset}"
        MISSING_SCHEMA_ASSETS=1
    elif ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Invalid JSON format detected in schema asset: ${asset}"
        MISSING_SCHEMA_ASSETS=1
    fi
done

if [ "${MISSING_POLICY_ASSETS}" -ne 0 ] || [ "${MISSING_SCHEMA_ASSETS}" -ne 0 ]; then
    echo "  [FATAL] One or more runtime assets are missing or corrupted."
    echo "          Please ensure the deployment script completed successfully."
    exit 1
fi

echo "  [OK] All required runtime policy and schema assets are present and valid."
echo "==> [PASS] Environment and runtime assets verification successful."
