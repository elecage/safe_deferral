#!/usr/bin/env bash
# ==============================================================================
# Script: 21_prepare_compose_stack_mac.sh
# Purpose: Prepare Docker Compose workspace and volume directories for Mac mini
# ==============================================================================
set -euo pipefail

echo "==> [21_prepare_compose_stack_mac] Preparing Docker Compose workspace..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
WORKSPACE_DIR="${HOME}/smarthome_workspace"
COMPOSE_DIR="${WORKSPACE_DIR}/docker"
TEMPLATE_FILE="${PROJECT_ROOT}/mac_mini/scripts/templates/docker-compose.template.yml"
TARGET_COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.yml"

mkdir -p "${COMPOSE_DIR}"

VOLUMES=(
  "volumes/homeassistant/config"
  "volumes/mosquitto/config"
  "volumes/mosquitto/data"
  "volumes/mosquitto/log"
  "volumes/ollama/data"
  "volumes/app/config/policies"
  "volumes/app/config/schemas"
  "volumes/app/config/mqtt"
  "volumes/app/config/payloads"
  "volumes/sqlite/db"
)

echo "  [INFO] Creating compose volume directories..."
for vol in "${VOLUMES[@]}"; do
  mkdir -p "${COMPOSE_DIR}/${vol}"
  echo "    - ${COMPOSE_DIR}/${vol}"
done

echo "  [INFO] Applying local permissions..."
chmod 700 "${COMPOSE_DIR}/volumes/sqlite/db"

if [ ! -f "${TEMPLATE_FILE}" ]; then
  echo "  [FATAL] Template file not found at ${TEMPLATE_FILE}"
  exit 1
fi

cp "${TEMPLATE_FILE}" "${TARGET_COMPOSE_FILE}"
echo "  [OK] docker-compose.yml refreshed from template."

echo "  [INFO] MQTT and payload reference directories were created for later configure/deploy steps:"
echo "    - ${COMPOSE_DIR}/volumes/app/config/mqtt"
echo "    - ${COMPOSE_DIR}/volumes/app/config/payloads"

echo "==> [PASS] Docker Compose workspace prepared."
