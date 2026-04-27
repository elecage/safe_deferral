#!/usr/bin/env bash
# ==============================================================================
# Script: 40_verify_sample_build_esp32.sh
# Purpose: Verify that a sample ESP-IDF project can be built successfully
# Note: This script targets POSIX shell environments (macOS/Linux).
# ==============================================================================
set -euo pipefail

echo "==> [40_verify_sample_build_esp32] Verifying sample ESP-IDF build..."

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
LOG_DIR="${ESP32_BUILD_LOG_DIR:-${WORKSPACE_DIR}/logs}"
BUILD_LOG_FILE="${LOG_DIR}/sample_build.log"
EXPECTED_APP_NAME="${ESP32_EXPECTED_APP_NAME:-${EXPECTED_APP_NAME:-hello_world}}"
EXPECTED_BIN="${SAMPLE_PROJECT_DIR}/build/${EXPECTED_APP_NAME}.bin"
EXPECTED_ELF="${SAMPLE_PROJECT_DIR}/build/${EXPECTED_APP_NAME}.elf"

mkdir -p "${LOG_DIR}"

if [ ! -d "${SAMPLE_PROJECT_DIR}" ]; then
    echo "  [FATAL] Sample project not found at ${SAMPLE_PROJECT_DIR}."
    echo "          Please run 30_prepare_sample_project_esp32.sh first."
    exit 1
fi

# shellcheck disable=SC1090
source "${IDF_PATH}/export.sh" >/dev/null 2>&1

cd "${SAMPLE_PROJECT_DIR}"
echo "  [INFO] Running clean build for target ${TARGET} ..."
echo "  [INFO] Expected app name: ${EXPECTED_APP_NAME}"
idf.py set-target "${TARGET}" >/dev/null
idf.py fullclean >/dev/null 2>&1 || true
idf.py build | tee "${BUILD_LOG_FILE}"

if [ ! -f "${EXPECTED_BIN}" ]; then
    echo "  [FATAL] Expected sample binary was not generated: ${EXPECTED_BIN}"
    echo "          Set ESP32_EXPECTED_APP_NAME or EXPECTED_APP_NAME if the project name is not 'hello_world'."
    echo "          Check ${BUILD_LOG_FILE} for build errors."
    exit 1
fi
if [ ! -f "${EXPECTED_ELF}" ]; then
    echo "  [FATAL] Expected sample ELF was not generated: ${EXPECTED_ELF}"
    echo "          Set ESP32_EXPECTED_APP_NAME or EXPECTED_APP_NAME if the project name is not 'hello_world'."
    echo "          Check ${BUILD_LOG_FILE} for build errors."
    exit 1
fi

echo "  [OK] Sample build artifacts were generated successfully:"
echo "       - ${EXPECTED_BIN}"
echo "       - ${EXPECTED_ELF}"
echo "  [INFO] Build log written to ${BUILD_LOG_FILE}."
echo "==> [PASS] Sample ESP-IDF build verification completed."
