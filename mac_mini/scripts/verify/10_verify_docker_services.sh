#!/usr/bin/env bash
# ==============================================================================
# Script: 10_verify_docker_services.sh
# Purpose: Verify that core Docker Compose services are running
# ==============================================================================
set -euo pipefail

echo "==> [10_verify_docker_services] Checking Docker Compose services..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
COMPOSE_DIR="${WORKSPACE_DIR}/docker"

if ! docker compose version >/dev/null 2>&1; then
    echo "  [FATAL] 'docker compose' command is not available."
    echo "          Please ensure Docker and the Compose V2 plugin are installed."
    exit 1
fi
echo "  [OK] Docker Compose V2 plugin verified."

if [ ! -d "${COMPOSE_DIR}" ]; then
    echo "  [FATAL] Docker compose directory (${COMPOSE_DIR}) does not exist."
    exit 1
fi

cd "${COMPOSE_DIR}"

COMPOSE_FILE_FOUND=false
for file in "compose.yaml" "compose.yml" "docker-compose.yaml" "docker-compose.yml"; do
    if [ -f "${file}" ]; then
        COMPOSE_FILE_FOUND=true
        echo "  [INFO] Found compose file: ${file}"
        break
    fi
done

if [ "${COMPOSE_FILE_FOUND}" = false ]; then
    echo "  [FATAL] No valid compose file found in ${COMPOSE_DIR}."
    exit 1
fi

SERVICES=("homeassistant" "mosquitto" "ollama" "edge_controller_app")

for service in "${SERVICES[@]}"; do
    if [ -n "$(docker compose ps --status running -q "${service}" 2>/dev/null)" ]; then
        echo "  [OK] ${service} service is running."
    else
        echo "  [FATAL] ${service} service is not in the 'running' state."
        echo "          Diagnostic hint: Run 'docker compose logs ${service}' to check for errors."
        exit 1
    fi
done

echo "==> [PASS] All required Docker Compose services are up and running."
