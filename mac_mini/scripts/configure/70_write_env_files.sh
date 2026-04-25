#!/usr/bin/env bash
# ==============================================================================
# Script: 70_write_env_files.sh
# Purpose: Safely write deployment-local environment variables
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
WORKSPACE_DIR="${HOME}/smarthome_workspace"
COMPOSE_DIR="${WORKSPACE_DIR}/docker"
COMPOSE_ENV_FILE="${COMPOSE_DIR}/.env"
PYTHON_ENV_FILE="${WORKSPACE_DIR}/.env"
SQLITE_DB_DIR="${WORKSPACE_DIR}/docker/volumes/sqlite/db"
SQLITE_DB_FILE="${SQLITE_DB_DIR}/audit_log.db"

echo ">>> [70_write_env_files] Writing deployment-local environment files..."

mkdir -p "${COMPOSE_DIR}"
mkdir -p "${SQLITE_DB_DIR}"
mkdir -p "${WORKSPACE_DIR}/docker/volumes/app/config/policies"
mkdir -p "${WORKSPACE_DIR}/docker/volumes/app/config/schemas"

append_env() {
    local file="$1"
    local key="$2"
    local val="$3"

    touch "${file}"

    if ! grep -q "^${key}=" "${file}"; then
        echo "${key}=${val}" >> "${file}"
        echo "  + Added: ${key}"
    else
        echo "  ~ Skipped: ${key}"
    fi
}

echo ">>> Updating Docker Compose environment..."
append_env "${COMPOSE_ENV_FILE}" "TZ" "Asia/Seoul"
append_env "${COMPOSE_ENV_FILE}" "SAFE_DEFERRAL_REPO_ROOT" "${PROJECT_ROOT}"

echo ">>> Updating Python/runtime environment..."
append_env "${PYTHON_ENV_FILE}" "TIMEZONE" "Asia/Seoul"
append_env "${PYTHON_ENV_FILE}" "DEPLOYMENT_MODE" "production"
append_env "${PYTHON_ENV_FILE}" "MQTT_HOST" "127.0.0.1"
append_env "${PYTHON_ENV_FILE}" "MQTT_PORT" "1883"
append_env "${PYTHON_ENV_FILE}" "OLLAMA_HOST" "http://127.0.0.1:11434"
append_env "${PYTHON_ENV_FILE}" "SQLITE_PATH" "${SQLITE_DB_FILE}"
append_env "${PYTHON_ENV_FILE}" "POLICY_DIR" "${WORKSPACE_DIR}/docker/volumes/app/config/policies"
append_env "${PYTHON_ENV_FILE}" "SCHEMA_DIR" "${WORKSPACE_DIR}/docker/volumes/app/config/schemas"
append_env "${PYTHON_ENV_FILE}" "SAFE_DEFERRAL_REPO_ROOT" "${PROJECT_ROOT}"
append_env "${PYTHON_ENV_FILE}" "TELEGRAM_BOT_TOKEN" "YOUR_TOKEN_HERE"
append_env "${PYTHON_ENV_FILE}" "TELEGRAM_CHAT_ID" "YOUR_CHAT_ID_HERE"

echo ">>> [PASS] Deployment-local environment files updated."
