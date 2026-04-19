#!/usr/bin/env bash
# ==============================================================================
# Script: 10_verify_docker_services.sh
# Purpose: Verify that core Docker Compose services (HA, Mosquitto) are running
# ==============================================================================
set -euo pipefail

echo "==> [10_verify_docker_services] Checking Docker Compose services..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
COMPOSE_DIR="${WORKSPACE_DIR}/docker"

# [보완 2] Docker Compose V2 가용성 및 버전 사전 점검 (Fail-fast)
if ! docker compose version >/dev/null 2>&1; then
    echo "  [FATAL] 'docker compose' command is not available."
    echo "          Please ensure Docker and the Compose V2 plugin are installed."
    exit 1
fi
echo "  [OK] Docker Compose V2 plugin verified."

# Compose 디렉터리 존재 여부 점검
if [ ! -d "${COMPOSE_DIR}" ]; then
    echo "  [FATAL] Docker compose directory (${COMPOSE_DIR}) does not exist."
    exit 1
fi

cd "${COMPOSE_DIR}"

# [보완 1] 공식 허용되는 4종의 compose 파일명 포괄 탐색
COMPOSE_FILE_FOUND=false
for file in "compose.yaml" "compose.yml" "docker-compose.yaml" "docker-compose.yml"; do
    if [ -f "${file}" ]; then
        COMPOSE_FILE_FOUND=true
        echo "  [INFO] Found compose file: ${file}"
        break
    fi
done

if [ "${COMPOSE_FILE_FOUND}" = false ]; then
    echo "  [FATAL] No valid compose file (compose.y(a)ml or docker-compose.y(a)ml) found in ${COMPOSE_DIR}."
    exit 1
fi

echo "  [INFO] Verifying core services in ${COMPOSE_DIR}..."

# [보완 3] 상태 진단 메시지를 실제 검사 수준(running)에 맞게 교정
# Home Assistant 상태 확인
if [ -n "$(docker compose ps --status running -q homeassistant 2>/dev/null)" ]; then
    echo "  [OK] Home Assistant service is running."
else
    echo "  [FATAL] Home Assistant service is not in the 'running' state."
    echo "          Diagnostic hint: Run 'docker compose logs homeassistant' to check for errors."
    exit 1
fi

# Mosquitto 상태 확인
if [ -n "$(docker compose ps --status running -q mosquitto 2>/dev/null)" ]; then
    echo "  [OK] Mosquitto MQTT Broker service is running."
else
    echo "  [FATAL] Mosquitto service is not in the 'running' state."
    echo "          Diagnostic hint: Run 'docker compose logs mosquitto' to check for errors."
    exit 1
fi

echo "==> [PASS] All required Docker Compose services are up and running."
