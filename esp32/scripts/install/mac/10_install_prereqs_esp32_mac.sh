#!/usr/bin/env bash
# ==============================================================================
# Script: 10_install_prereqs_esp32_mac.sh
# Purpose: Install prerequisite packages for ESP32 development on macOS
# ==============================================================================
set -euo pipefail

echo "==> [10_install_prereqs_esp32_mac] Installing macOS prerequisites for ESP32 development..."

if ! command -v brew >/dev/null 2>&1; then
    echo "  [FATAL] Homebrew is not installed."
    exit 1
fi

BREW_PACKAGES=(
    git
    cmake
    ninja
    python
    dfu-util
    libgcrypt
    glib
    pixman
    sdl2
    libslirp
)

echo "  [INFO] Updating Homebrew..."
brew update >/dev/null

echo "  [INFO] Installing packages: ${BREW_PACKAGES[*]}"
for pkg in "${BREW_PACKAGES[@]}"; do
    if ! brew list "$pkg" >/dev/null 2>&1; then
        echo "  [INFO] Installing $pkg..."
        brew install "$pkg"
    else
        echo "  [OK] $pkg is already installed. Skipping."
    fi
done

echo "  [INFO] Installed versions:"
git --version | awk '{print "    - "$0}'
cmake --version | awk 'NR==1{print "    - "$0}'
ninja --version | awk '{print "    - ninja " $0}'
python3 --version | awk '{print "    - "$0}'
dfu-util --version 2>&1 | awk 'NR==1{print "    - "$0}'

echo "==> [PASS] macOS prerequisites installed successfully."
