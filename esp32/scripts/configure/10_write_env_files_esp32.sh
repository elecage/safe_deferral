#!/usr/bin/env bash
# ==============================================================================
# Script: 10_write_env_files_esp32.sh
# Purpose: Generate or append common ESP32 development environment variables
# Note: This draft targets POSIX shell environments (macOS/Linux).
# ==============================================================================
set -euo pipefail

echo "==> [10_write_env_files_esp32] Configuring common ESP32 environment variables..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
WORKSPACE_DIR="${HOME}/esp32_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"
FIRMWARE_TEMPLATE_DIR="${PROJECT_ROOT}/esp32/firmware/templates/minimal_node"

mkdir -p "${WORKSPACE_DIR}"

if [ ! -f "${ENV_FILE}" ]; then
    cat <<EOF > "${ENV_FILE}"
# ====================================================
# ESP32 Development Environment Variables
# ====================================================
EOF
    echo "  [OK] Created ${ENV_FILE}."
else
    echo "  [INFO] ${ENV_FILE} already exists. Appending only missing keys."
fi

append_env_var() {
    local key="$1"
    local value="$2"
    local comment="${3:-}"

    if ! grep -q "^${key}=" "${ENV_FILE}"; then
        if [ -n "${comment}" ]; then
            echo "" >> "${ENV_FILE}"
            echo "# ${comment}" >> "${ENV_FILE}"
        fi
        echo "${key}=${value}" >> "${ENV_FILE}"
        echo "  [OK] Appended missing key: ${key}"
    fi
}

append_env_var "ESP32_WORKSPACE_DIR" "${WORKSPACE_DIR}" "Common ESP32 Workspace Settings"
append_env_var "ESP_ROOT" "${HOME}/esp"
append_env_var "IDF_PATH" "${HOME}/esp/esp-idf"
append_env_var "IDF_TOOLS_PATH" "${HOME}/.espressif"
append_env_var "ESP_IDF_GIT_REF" "" "Optional ESP-IDF Git Ref (leave empty to use current checked-out ref)"
append_env_var "IDF_TARGET" "esp32" "Default ESP-IDF Build Target"
append_env_var "ESP32_FIRMWARE_TEMPLATE_DIR" "${FIRMWARE_TEMPLATE_DIR}"
append_env_var "ESP32_SAMPLE_PROJECT_DIR" "${WORKSPACE_DIR}/samples/hello_idf"
append_env_var "ESP32_BUILD_LOG_DIR" "${WORKSPACE_DIR}/logs"
append_env_var "ESPPORT" "" "Optional serial port override (for example: /dev/ttyUSB0 or /dev/cu.usbserial-xxxx)"
append_env_var "ESPBAUD" "460800"

echo "  [WARNING] ACTION REQUIRED: Review IDF_PATH, ESP_IDF_GIT_REF, and ESPPORT in ${ENV_FILE}."
echo "==> [PASS] ESP32 common environment variables configured."
