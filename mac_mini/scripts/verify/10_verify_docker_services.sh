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

CORE_SERVICES=("homeassistant" "mosquitto" "ollama")
OPTIONAL_SERVICES=("edge_controller_app")

SERVICE_LIST="$(docker compose config --services 2>/dev/null || true)"
if [ -z "${SERVICE_LIST}" ]; then
    echo "  [FATAL] Unable to read services from Docker Compose configuration."
    echo "          Run 'docker compose config' in ${COMPOSE_DIR} for details."
    exit 1
fi

echo "  [INFO] Verifying required core services..."
for service in "${CORE_SERVICES[@]}"; do
    if ! printf '%s\n' "${SERVICE_LIST}" | grep -qx "${service}"; then
        echo "  [FATAL] Required core service '${service}' is not defined in the compose file."
        exit 1
    fi

    if [ -n "$(docker compose ps --status running -q "${service}" 2>/dev/null)" ]; then
        echo "  [OK] ${service} service is running."
    else
        echo "  [FATAL] Required core service '${service}' is not in the 'running' state."
        echo "          Diagnostic hint: Run 'docker compose logs ${service}' to check for errors."
        exit 1
    fi
done

echo "  [INFO] Checking optional application services..."
for service in "${OPTIONAL_SERVICES[@]}"; do
    if ! printf '%s\n' "${SERVICE_LIST}" | grep -qx "${service}"; then
        echo "  [WARN] Optional service '${service}' is not defined in the compose file."
        echo "         This is acceptable before the edge controller application image is finalized."
        continue
    fi

    if [ -n "$(docker compose ps --status running -q "${service}" 2>/dev/null)" ]; then
        echo "  [OK] Optional service '${service}' is running."
    else
        echo "  [WARN] Optional service '${service}' is defined but not running."
        echo "         This is acceptable during early bring-up if mac_mini/code/Dockerfile or app runtime is not finalized."
        echo "         Diagnostic hint: Run 'docker compose logs ${service}' when app verification becomes required."
    fi
done

echo "==> [PASS] Required Docker Compose core services are up and running."
