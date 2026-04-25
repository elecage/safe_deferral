#!/usr/bin/env bash
# ==============================================================================
# Script: 30_prepare_managed_components_esp32.sh
# Purpose: Prepare managed component cache and optional project-level placeholder
# Note: This script targets POSIX shell environments (macOS/Linux).
# ==============================================================================
set -euo pipefail

echo "==> [30_prepare_managed_components_esp32] Preparing managed component workspace..."

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
MANAGED_COMPONENTS_CACHE_DIR="${TARGET_WORKSPACE}/managed_components_cache"
COMPONENT_PLACEHOLDER_FILE="${SAMPLE_PROJECT_DIR}/idf_component.yml"

mkdir -p "${MANAGED_COMPONENTS_CACHE_DIR}"

if [ ! -d "${SAMPLE_PROJECT_DIR}" ]; then
    echo "  [FATAL] Sample project directory not found: ${SAMPLE_PROJECT_DIR}"
    echo "          Please run 40_prepare_sample_project_esp32.sh before this script."
    exit 1
fi

if [ ! -f "${SAMPLE_PROJECT_DIR}/CMakeLists.txt" ] || [ ! -d "${SAMPLE_PROJECT_DIR}/main" ]; then
    echo "  [FATAL] Sample project does not look like a prepared ESP-IDF project: ${SAMPLE_PROJECT_DIR}"
    echo "          Please run 40_prepare_sample_project_esp32.sh before this script."
    exit 1
fi

if [ ! -f "${COMPONENT_PLACEHOLDER_FILE}" ]; then
    cat <<EOF > "${COMPONENT_PLACEHOLDER_FILE}"
# Placeholder managed component manifest for future bounded node firmware.
dependencies:
EOF
    echo "  [OK] Created placeholder ${COMPONENT_PLACEHOLDER_FILE}."
else
    echo "  [INFO] ${COMPONENT_PLACEHOLDER_FILE} already exists. Leaving it unchanged."
fi

echo "  [OK] Managed component cache directory prepared at ${MANAGED_COMPONENTS_CACHE_DIR}."
echo "  [INFO] This script is intended to run after 40_prepare_sample_project_esp32.sh."
echo "==> [PASS] Managed component workspace preparation completed."
