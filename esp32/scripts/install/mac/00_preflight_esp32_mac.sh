#!/usr/bin/env bash
# ==============================================================================
# Script: 00_preflight_esp32_mac.sh
# Purpose: Preflight checks for ESP32 development on macOS
# ==============================================================================
set -euo pipefail

echo "==> [00_preflight_esp32_mac] Checking macOS ESP32 development prerequisites..."

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "  [FATAL] This script must be run on macOS."
    exit 1
fi
echo "  [OK] Operating system is macOS."

if ! command -v brew >/dev/null 2>&1; then
    echo "  [FATAL] Homebrew is not installed."
    echo "          Please install Homebrew before continuing."
    exit 1
fi
echo "  [OK] Homebrew is available."

if ! command -v git >/dev/null 2>&1; then
    echo "  [WARNING] git is not installed yet. It will be installed in the next step."
else
    echo "  [OK] git is available."
fi

if command -v python3 >/dev/null 2>&1; then
    if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
        echo "  [OK] Python 3.10+ is available."
    else
        echo "  [WARNING] Python is present but below 3.10. A newer version will be installed in the next step."
    fi
else
    echo "  [WARNING] python3 is not installed yet. It will be installed in the next step."
fi

FREE_SPACE_GB=$(df -g "$HOME" | tail -1 | awk '{print $4}')
if [ "${FREE_SPACE_GB}" -lt 10 ]; then
    echo "  [WARNING] Less than 10GB of free space is available (${FREE_SPACE_GB}GB)."
    echo "            ESP-IDF toolchains and build artifacts may require more space."
else
    echo "  [OK] Disk space looks sufficient (${FREE_SPACE_GB}GB available)."
fi

if ping -c 1 github.com >/dev/null 2>&1; then
    echo "  [OK] Network access appears available."
else
    echo "  [WARNING] Network access check failed. Online installation may fail."
fi

echo "==> [PASS] macOS preflight completed."
