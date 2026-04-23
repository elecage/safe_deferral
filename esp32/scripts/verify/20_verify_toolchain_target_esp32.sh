#!/usr/bin/env bash
# ==============================================================================
# Script: 20_verify_toolchain_target_esp32.sh
# Purpose: Verify target selection for the sample ESP-IDF project
# Note: This draft targets POSIX shell environments (macOS/Linux).
# ==============================================================================
set -euo pipefail

echo "==> [20_verify_toolchain_target_esp32] Verifying ESP-IDF target selection..."

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
TARGET="${IDF_TARGET:-esp32}"

if [ ! -d "${SAMPLE_PROJECT_DIR}" ]; then
    echo "  [FATAL] Sample project not found at ${SAMPLE_PROJECT_DIR}."
    echo "          Please run 40_prepare_sample_project_esp32.sh first."
    exit 1
fi

# shellcheck disable=SC1090
source "${IDF_PATH}/export.sh" >/dev/null 2>&1

cd "${SAMPLE_PROJECT_DIR}"
echo "  [INFO] Running idf.py set-target ${TARGET} ..."
idf.py set-target "${TARGET}" >/dev/null

echo "  [OK] Target '${TARGET}' was applied successfully."
echo "==> [PASS] ESP-IDF target toolchain verification completed."
