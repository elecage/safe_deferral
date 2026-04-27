#!/usr/bin/env bash
# ==============================================================================
# Script: 30_verify_component_resolution_esp32.sh
# Purpose: Verify CMake reconfigure and managed component resolution
# Note: This script targets POSIX shell environments (macOS/Linux).
# ==============================================================================
set -euo pipefail

echo "==> [30_verify_component_resolution_esp32] Verifying component resolution..."

WORKSPACE_DIR="${HOME}/esp32_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"

if [ -z "${IDF_PATH:-}" ] || [ ! -f "${IDF_PATH}/export.sh" ]; then
    echo "  [FATAL] IDF_PATH is not configured correctly or export.sh is missing."
    exit 1
fi
SAMPLE_PROJECT_DIR="${ESP32_SAMPLE_PROJECT_DIR:-${WORKSPACE_DIR}/samples/hello_idf}"

if [ ! -d "${SAMPLE_PROJECT_DIR}" ]; then
    echo "  [FATAL] Sample project not found at ${SAMPLE_PROJECT_DIR}."
    echo "          Please run 30_prepare_sample_project_esp32.sh first."
    exit 1
fi

# shellcheck disable=SC1090
source "${IDF_PATH}/export.sh" >/dev/null 2>&1

cd "${SAMPLE_PROJECT_DIR}"
echo "  [INFO] Running idf.py reconfigure ..."
idf.py reconfigure >/dev/null

if [ ! -f "${SAMPLE_PROJECT_DIR}/build/CMakeCache.txt" ]; then
    echo "  [FATAL] CMakeCache.txt was not generated during reconfigure."
    exit 1
fi

echo "  [OK] CMake reconfigure completed successfully."
if [ -d "${SAMPLE_PROJECT_DIR}/managed_components" ]; then
    echo "  [INFO] managed_components directory is present."
else
    echo "  [INFO] managed_components directory is not present; no managed dependencies may be required yet."
fi

echo "==> [PASS] Component resolution verification completed."
