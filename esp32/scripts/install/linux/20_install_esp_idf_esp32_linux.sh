#!/usr/bin/env bash
# ==============================================================================
# Script: 20_install_esp_idf_esp32_linux.sh
# Purpose: Install ESP-IDF on Linux using the standard CLI setup path
# ==============================================================================
set -euo pipefail

echo "==> [20_install_esp_idf_esp32_linux] Installing ESP-IDF on Linux..."

if ! command -v git >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
    echo "  [FATAL] git and python3 are required."
    echo "          Please run 10_install_prereqs_esp32_linux.sh first."
    exit 1
fi

WORKSPACE_DIR="${HOME}/esp32_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ -f "${ENV_FILE}" ]; then
    echo "  [INFO] Loading ESP32 environment variables from ${ENV_FILE}..."
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
else
    echo "  [INFO] ${ENV_FILE} not found. Using built-in ESP-IDF install defaults."
fi

ESP_ROOT="${ESP_ROOT:-$HOME/esp}"
IDF_PATH="${IDF_PATH:-$ESP_ROOT/esp-idf}"
ESP_IDF_GIT_REF="${ESP_IDF_GIT_REF:-}"
IDF_TOOLS_PATH="${IDF_TOOLS_PATH:-$HOME/.espressif}"

mkdir -p "${ESP_ROOT}"
export IDF_TOOLS_PATH

echo "  [INFO] Effective ESP-IDF install settings:"
echo "         - ESP_ROOT=${ESP_ROOT}"
echo "         - IDF_PATH=${IDF_PATH}"
echo "         - IDF_TOOLS_PATH=${IDF_TOOLS_PATH}"
echo "         - ESP_IDF_GIT_REF=${ESP_IDF_GIT_REF:-<current checkout>}"

if [ ! -d "${IDF_PATH}/.git" ]; then
    echo "  [INFO] Cloning ESP-IDF into ${IDF_PATH}..."
    git clone --recursive https://github.com/espressif/esp-idf.git "${IDF_PATH}"
else
    echo "  [INFO] ESP-IDF repository already exists at ${IDF_PATH}."
fi

cd "${IDF_PATH}"

if [ -n "${ESP_IDF_GIT_REF}" ]; then
    echo "  [INFO] Checking out requested ESP-IDF ref: ${ESP_IDF_GIT_REF}"
    git fetch --all --tags
    git checkout "${ESP_IDF_GIT_REF}"
    git submodule update --init --recursive
else
    echo "  [WARNING] ESP_IDF_GIT_REF is not set. Using the repository's current checked-out ref."
fi

if [ ! -f "./install.sh" ]; then
    echo "  [FATAL] install.sh not found in ${IDF_PATH}."
    exit 1
fi

echo "  [INFO] Running ESP-IDF install.sh..."
./install.sh

if [ ! -f "./export.sh" ]; then
    echo "  [FATAL] export.sh was not found after installation."
    exit 1
fi

echo "  [OK] ESP-IDF installed."
echo "  [INFO] To activate the environment in the current shell, run:"
echo "         . ${IDF_PATH}/export.sh"

echo "==> [PASS] ESP-IDF installation completed for Linux."
