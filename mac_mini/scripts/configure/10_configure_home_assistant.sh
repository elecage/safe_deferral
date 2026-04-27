#!/usr/bin/env bash
# ==============================================================================
# Script: 10_configure_home_assistant.sh
# Purpose: Configure Home Assistant and apply optional configuration templates
# ==============================================================================
set -euo pipefail

echo "==> [10_configure_home_assistant] Configuring Home Assistant..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
WORKSPACE_DIR="${HOME}/smarthome_workspace"

HA_CONFIG_DIR="${WORKSPACE_DIR}/docker/volumes/homeassistant/config"
TEMPLATE_FILE="${PROJECT_ROOT}/mac_mini/scripts/templates/configuration.yaml.template"
TARGET_FILE="${HA_CONFIG_DIR}/configuration.yaml"

echo "  [INFO] Ensuring target configuration directory exists at ${HA_CONFIG_DIR}..."
mkdir -p "${HA_CONFIG_DIR}"

# 1. 덮어쓰기 방지: 파일이 이미 존재하면 복사 생략 (사용자 설정 보존)
if [ ! -f "${TARGET_FILE}" ]; then
    if [ -f "${TEMPLATE_FILE}" ]; then
        cp "${TEMPLATE_FILE}" "${TARGET_FILE}"
        echo "  [OK] configuration.yaml deployed to target compose volume path."
    else
        echo "  [WARNING] Template not found at ${TEMPLATE_FILE}. Skipping injection."
        echo "  [INFO] Home Assistant will create default configuration on first container start."
    fi
else
    echo "  [INFO] configuration.yaml already exists. Skipping overwrite to preserve user settings."
fi

# 2. Deployment mode-dependent restart (Compose 파일 및 서비스 정밀 확인)
echo "  [INFO] Applying changes by restarting Home Assistant container..."
if [ -d "${WORKSPACE_DIR}/docker" ]; then
    cd "${WORKSPACE_DIR}/docker"

    # 2-1. Docker Compose 공식 지원 파일명 4종 포괄적 확인
    if [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ] || [ -f "compose.yml" ] || [ -f "compose.yaml" ]; then
        # 2-2. 서비스가 compose 파일에 정의 및 생성되어 있는지 정밀 일치 검사 (-qx)
        if docker compose ps -a --services 2>/dev/null | grep -qx "homeassistant"; then
            docker compose restart homeassistant > /dev/null 2>&1
            echo "  [OK] Home Assistant container restarted successfully."
        else
            echo "  [WARNING] 'homeassistant' service is not found or not created yet. Configuration will apply on first start."
        fi
    else
        echo "  [WARNING] docker-compose stack file not found in ${WORKSPACE_DIR}/docker. Skipping restart."
    fi
else
    echo "  [WARNING] Docker workspace not found at ${WORKSPACE_DIR}/docker. Skipping restart."
fi

echo "==> [PASS] Home Assistant configuration applied."
