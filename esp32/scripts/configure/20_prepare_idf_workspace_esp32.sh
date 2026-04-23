#!/usr/bin/env bash
# ==============================================================================
# Script: 20_prepare_idf_workspace_esp32.sh
# Purpose: Prepare common ESP32 workspace directories
# Note: This draft targets POSIX shell environments (macOS/Linux).
# ==============================================================================
set -euo pipefail

echo "==> [20_prepare_idf_workspace_esp32] Preparing ESP32 workspace..."

WORKSPACE_DIR="${HOME}/esp32_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    echo "          Please run 10_write_env_files_esp32.sh first."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"

TARGET_WORKSPACE="${ESP32_WORKSPACE_DIR:-${WORKSPACE_DIR}}"
SAMPLE_PROJECT_DIR="${ESP32_SAMPLE_PROJECT_DIR:-${TARGET_WORKSPACE}/samples/hello_idf}"
BUILD_LOG_DIR="${ESP32_BUILD_LOG_DIR:-${TARGET_WORKSPACE}/logs}"
ARTIFACT_DIR="${TARGET_WORKSPACE}/artifacts"
MANAGED_COMPONENTS_CACHE_DIR="${TARGET_WORKSPACE}/managed_components_cache"

mkdir -p "${TARGET_WORKSPACE}" \
         "${TARGET_WORKSPACE}/samples" \
         "${BUILD_LOG_DIR}" \
         "${ARTIFACT_DIR}" \
         "${MANAGED_COMPONENTS_CACHE_DIR}" \
         "${SAMPLE_PROJECT_DIR}"

echo "  [OK] Workspace prepared at ${TARGET_WORKSPACE}."
echo "  [INFO] Sample project path: ${SAMPLE_PROJECT_DIR}"
echo "  [INFO] Build log path: ${BUILD_LOG_DIR}"
echo "  [INFO] Artifact path: ${ARTIFACT_DIR}"
echo "==> [PASS] ESP32 workspace preparation completed."
