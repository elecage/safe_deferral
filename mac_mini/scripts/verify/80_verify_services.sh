#!/usr/bin/env bash
# ==============================================================================
# Script: 80_verify_services.sh
# Purpose: Run aggregated verification across Docker, MQTT, Ollama, SQLite, assets, and notifications
# ==============================================================================
set -euo pipefail

echo "==> [80_verify_services] Starting aggregated service verification..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VERIFY_STEPS=(
  "10_verify_docker_services.sh"
  "20_verify_mqtt_pubsub.sh"
  "30_verify_ollama_inference.sh"
  "40_verify_sqlite.sh"
  "50_verify_env_and_assets.sh"
  "60_verify_notifications.sh"
)

for step in "${VERIFY_STEPS[@]}"; do
    TARGET_SCRIPT="${SCRIPT_DIR}/${step}"
    if [ ! -f "${TARGET_SCRIPT}" ]; then
        echo "  [FATAL] Verification step not found: ${TARGET_SCRIPT}"
        exit 1
    fi

    echo "  [INFO] Running ${step}..."
    bash "${TARGET_SCRIPT}"
done

echo "==> [PASS] All aggregated verification steps completed successfully."
