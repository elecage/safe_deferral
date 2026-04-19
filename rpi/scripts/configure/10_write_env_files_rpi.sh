#!/usr/bin/env bash
# ==============================================================================
# Script: 10_write_env_files_rpi.sh
# Purpose: Generate or append .env configuration for Raspberry Pi 5 Simulation Node
# ==============================================================================
set -euo pipefail

echo "==> [10_write_env_files_rpi] Configuring environment variables for Raspberry Pi 5..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

echo "  [INFO] Ensuring workspace directory exists at ${WORKSPACE_DIR}..."
mkdir -p "${WORKSPACE_DIR}"

# 1. .env 파일 초기화 (존재하지 않을 경우 기본 헤더 생성)
if [ ! -f "${ENV_FILE}" ]; then
    echo "  [INFO] ${ENV_FILE} not found. Creating a new one..."
    cat <<EOF > "${ENV_FILE}"
# ====================================================
# Raspberry Pi 5 Simulation Node Environment Variables
# ====================================================
EOF
else
    echo "  [INFO] ${ENV_FILE} already exists. Appending missing keys to preserve user settings..."
fi

# 2. Append형 멱등성 보장 함수 정의
append_env_var() {
    local key="$1"
    local value="$2"
    local comment="${3:-}"

    # 해당 키(key=)가 파일에 존재하지 않을 때만 Append (사용자 설정 보호)
    if ! grep -q "^${key}=" "${ENV_FILE}"; then
        if [ -n "${comment}" ]; then
            echo "" >> "${ENV_FILE}"
            echo "# ${comment}" >> "${ENV_FILE}"
        fi
        echo "${key}=${value}" >> "${ENV_FILE}"
        echo "  [OK] Appended missing key: ${key}"
    fi
}

# 3. 환경 변수 주입 (이미 존재하는 키는 건너뜀)
append_env_var "MAC_MINI_HOST" "192.168.1.100" "Mac mini Edge Hub Information (Authoritative Source)"

append_env_var "MQTT_HOST" "\$MAC_MINI_HOST" "MQTT Broker Settings"
append_env_var "MQTT_PORT" "1883"
append_env_var "MQTT_USER" "simulator_node"
append_env_var "MQTT_PASS" "YOUR_SECURE_PASSWORD_HERE"

# [수정 반영] SCHEMA_SYNC_PATH 경로를 config/schemas로 지정
append_env_var "SCHEMA_SYNC_PATH" "${WORKSPACE_DIR}/config/schemas" "Phase 0 Artifact Sync Settings"

append_env_var "TOPIC_NAMESPACE" "smarthome/sim" "Simulation Parameters"
append_env_var "NODE_COUNT" "30"
append_env_var "PUBLISH_INTERVAL_MS" "1000"

append_env_var "SCENARIO_PROFILE" "default_stress" "Fault Injection & Time Sync Settings"
append_env_var "FAULT_PROFILE" "deterministic_01"
append_env_var "VERIFICATION_AUDIT_TOPIC" "audit/log/#"
append_env_var "TIME_SYNC_HOST" "\$MAC_MINI_HOST"
append_env_var "TIME_SYNC_TARGET_BOUND_MS" "15"

echo "  [WARNING] ACTION REQUIRED: Please verify MAC_MINI_HOST and MQTT_PASS manually in ${ENV_FILE}."
echo "==> [PASS] RPi 5 environment variables configuration completed."
