#!/usr/bin/env bash
# ==============================================================================
# Script: 70_write_env_files.sh
# Purpose: Safely append environment variables for Docker stack and Python Apps
# ==============================================================================
set -euo pipefail

WORKSPACE_DIR="${HOME}/smarthome_workspace"
COMPOSE_DIR="${WORKSPACE_DIR}/docker"
COMPOSE_ENV_FILE="${COMPOSE_DIR}/.env"
PYTHON_ENV_FILE="${WORKSPACE_DIR}/.env"

echo ">>> [Phase 4] Generating Environment Variable Files..."

# 1. 필수 디렉터리 보강 (안전한 파일 생성을 위한 보장)
mkdir -p "${COMPOSE_DIR}"
mkdir -p "${WORKSPACE_DIR}/db"
mkdir -p "${WORKSPACE_DIR}/config/policies"
mkdir -p "${WORKSPACE_DIR}/config/schemas"

# 2. Append형 멱등성 함수 정의 (기존 값이 있으면 보존, 없으면 추가)
append_env() {
    local file=$1
    local key=$2
    local val=$3

    # 파일이 없으면 생성
    touch "${file}"

    if ! grep -q "^${key}=" "${file}"; then
        echo "${key}=${val}" >> "${file}"
        echo "  + Added: ${key}"
    else
        echo "  ~ Skipped (Already exists): ${key}"
    fi
}

# ==============================================================================
# A. Docker Compose용 .env 주입
# ==============================================================================
echo ">>> Updating Docker Compose Environment (${COMPOSE_ENV_FILE})..."
append_env "${COMPOSE_ENV_FILE}" "TIMEZONE" "Asia/Seoul"
append_env "${COMPOSE_ENV_FILE}" "TTS_CONTAINER_IMAGE" "antigravity/local-tts-api:latest"

# ==============================================================================
# B. Python Runtime용 .env 주입 (가상환경 앱 참조용)
# ==============================================================================
echo ">>> Updating Python Application Environment (${PYTHON_ENV_FILE})..."
append_env "${PYTHON_ENV_FILE}" "TIMEZONE" "Asia/Seoul"
append_env "${PYTHON_ENV_FILE}" "DEPLOYMENT_MODE" "production"

# Service Endpoints (Host-based access)
append_env "${PYTHON_ENV_FILE}" "MQTT_HOST" "127.0.0.1"
append_env "${PYTHON_ENV_FILE}" "MQTT_PORT" "1883"
append_env "${PYTHON_ENV_FILE}" "OLLAMA_HOST" "http://127.0.0.1:11434"

# TTS 접근 경로 (Docker의 127.0.0.1:5000:5000 바인딩과 정합성 일치)
append_env "${PYTHON_ENV_FILE}" "TTS_API_BASE_URL" "http://127.0.0.1:5000"

# [수정 완수] 구체화된 설정 자산 경로 및 기존 규격 변수명 일치 (audit_log.db)
append_env "${PYTHON_ENV_FILE}" "SQLITE_PATH" "${WORKSPACE_DIR}/db/audit_log.db"
append_env "${PYTHON_ENV_FILE}" "CONFIG_DIR" "${WORKSPACE_DIR}/config"
append_env "${PYTHON_ENV_FILE}" "POLICY_DIR" "${WORKSPACE_DIR}/config/policies"
append_env "${PYTHON_ENV_FILE}" "SCHEMA_DIR" "${WORKSPACE_DIR}/config/schemas"

# 기존 규격의 알림 및 타임아웃 뼈대 변수 (기본값만 주입)
append_env "${PYTHON_ENV_FILE}" "TELEGRAM_BOT_TOKEN" "YOUR_TOKEN_HERE"
append_env "${PYTHON_ENV_FILE}" "TELEGRAM_CHAT_ID" "YOUR_CHAT_ID_HERE"
append_env "${PYTHON_ENV_FILE}" "ICR_TIMEOUT_MS" "10000"
append_env "${PYTHON_ENV_FILE}" "CLASS0_GRACE_HIGH_MS" "3000"
append_env "${PYTHON_ENV_FILE}" "CLASS0_GRACE_MEDIUM_MS" "5000"

echo ">>> [SUCCESS] Environment files have been updated safely."
