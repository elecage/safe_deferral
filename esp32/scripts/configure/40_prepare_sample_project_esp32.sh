#!/usr/bin/env bash
# ==============================================================================
# Script: 40_prepare_sample_project_esp32.sh
# Purpose: Prepare a sample ESP-IDF project for environment verification
# Note: This draft targets POSIX shell environments (macOS/Linux).
# ==============================================================================
set -euo pipefail

echo "==> [40_prepare_sample_project_esp32] Preparing sample ESP-IDF project..."

WORKSPACE_DIR="${HOME}/esp32_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    echo "          Please run 10_write_env_files_esp32.sh first."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"

IDF_PATH_VALUE="${IDF_PATH:-}"
SAMPLE_PROJECT_DIR="${ESP32_SAMPLE_PROJECT_DIR:-${WORKSPACE_DIR}/samples/hello_idf}"

if [ -z "${IDF_PATH_VALUE}" ] || [ ! -d "${IDF_PATH_VALUE}" ]; then
    echo "  [FATAL] IDF_PATH is not set correctly in ${ENV_FILE}."
    echo "          Please install ESP-IDF first."
    exit 1
fi

HELLO_WORLD_TEMPLATE="${IDF_PATH_VALUE}/examples/get-started/hello_world"
if [ ! -d "${HELLO_WORLD_TEMPLATE}" ]; then
    echo "  [FATAL] Could not find hello_world example in ${HELLO_WORLD_TEMPLATE}."
    exit 1
fi

mkdir -p "$(dirname "${SAMPLE_PROJECT_DIR}")"
rm -rf "${SAMPLE_PROJECT_DIR}"
cp -R "${HELLO_WORLD_TEMPLATE}" "${SAMPLE_PROJECT_DIR}"

echo "  [OK] Sample project copied to ${SAMPLE_PROJECT_DIR}."
echo "==> [PASS] Sample ESP-IDF project preparation completed."
