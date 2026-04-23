#!/usr/bin/env bash
# ==============================================================================
# Script: 00_preflight_esp32_linux.sh
# Purpose: Preflight checks for ESP32 development on Linux
# ==============================================================================
set -euo pipefail

echo "==> [00_preflight_esp32_linux] Checking Linux ESP32 development prerequisites..."

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "  [FATAL] This script must be run on Linux."
    exit 1
fi
echo "  [OK] Operating system is Linux."

PKG_MANAGER=""
if command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt"
elif command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER="dnf"
elif command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"
else
    echo "  [FATAL] Supported package manager not found (apt, dnf, pacman)."
    exit 1
fi
echo "  [OK] Detected package manager: ${PKG_MANAGER}"

if command -v python3 >/dev/null 2>&1; then
    if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
        echo "  [OK] Python 3.10+ is available."
    else
        echo "  [WARNING] Python is present but below 3.10. A newer version may be required."
    fi
else
    echo "  [WARNING] python3 is not installed yet. It will be installed in the next step."
fi

if command -v git >/dev/null 2>&1; then
    echo "  [OK] git is available."
else
    echo "  [WARNING] git is not installed yet. It will be installed in the next step."
fi

FREE_SPACE_GB=$(df -BG "$HOME" | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "${FREE_SPACE_GB}" -lt 10 ]; then
    echo "  [WARNING] Less than 10GB of free space is available (${FREE_SPACE_GB}GB)."
else
    echo "  [OK] Disk space looks sufficient (${FREE_SPACE_GB}GB available)."
fi

if ping -c 1 github.com >/dev/null 2>&1; then
    echo "  [OK] Network access appears available."
else
    echo "  [WARNING] Network access check failed. Online installation may fail."
fi

echo "==> [PASS] Linux preflight completed."
