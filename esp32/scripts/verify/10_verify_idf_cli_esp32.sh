#!/usr/bin/env bash
# ==============================================================================
# Script: 10_verify_idf_cli_esp32.sh
# Purpose: Verify ESP-IDF CLI and core build tools
# Note: This draft targets POSIX shell environments (macOS/Linux).
# ==============================================================================
set -euo pipefail

echo "==> [10_verify_idf_cli_esp32] Verifying ESP-IDF CLI and core tools..."

WORKSPACE_DIR="${HOME}/esp32_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    echo "          Please run configure scripts first."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"

if [ -z "${IDF_PATH:-}" ] || [ ! -f "${IDF_PATH}/export.sh" ]; then
    echo "  [FATAL] IDF_PATH is not configured correctly or export.sh is missing."
    echo "          Please install ESP-IDF first."
    exit 1
fi

# shellcheck disable=SC1090
source "${IDF_PATH}/export.sh" >/dev/null 2>&1

if ! command -v idf.py >/dev/null 2>&1; then
    echo "  [FATAL] idf.py is not available after sourcing export.sh."
    exit 1
fi
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    echo "  [FATAL] Python is not available."
    exit 1
fi
if ! command -v cmake >/dev/null 2>&1; then
    echo "  [FATAL] cmake is not available."
    exit 1
fi
if ! command -v ninja >/dev/null 2>&1 && ! command -v ninja-build >/dev/null 2>&1; then
    echo "  [FATAL] ninja is not available."
    exit 1
fi
if ! command -v esptool.py >/dev/null 2>&1 && ! python -m esptool version >/dev/null 2>&1 2>/dev/null; then
    echo "  [FATAL] esptool is not available."
    exit 1
fi

echo "  [INFO] Tool versions:"
idf.py --version | awk '{print "    - "$0}'
python3 --version 2>/dev/null | awk '{print "    - "$0}' || python --version | awk '{print "    - "$0}'
cmake --version | awk 'NR==1{print "    - "$0}'
if command -v ninja >/dev/null 2>&1; then
    ninja --version | awk '{print "    - ninja " $0}'
else
    ninja-build --version | awk '{print "    - ninja-build " $0}'
fi
if command -v esptool.py >/dev/null 2>&1; then
    esptool.py version | awk '{print "    - "$0}'
else
    python -m esptool version | awk '{print "    - "$0}'
fi

echo "==> [PASS] ESP-IDF CLI verification completed successfully."
