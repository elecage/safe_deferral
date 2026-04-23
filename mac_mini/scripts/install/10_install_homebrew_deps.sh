#!/usr/bin/env bash
# ==============================================================================
# Script: 10_install_homebrew_deps.sh
# Purpose: Install base system dependencies via Homebrew
# ==============================================================================
set -euo pipefail

echo "==> [10_install_homebrew_deps] Installing base dependencies via Homebrew..."

if ! command -v brew &> /dev/null; then
    echo "  [FATAL] Homebrew is not installed. Run mac_mini/scripts/install/00_install_homebrew.sh first."
    exit 1
fi

echo "  [INFO] Updating Homebrew (this may take a while)..."
brew update > /dev/null

# Core CLI dependencies for install/configure/verify flows.
# Dockerized services such as Ollama, Mosquitto broker, and Home Assistant are excluded here.
PACKAGES=("git" "python" "just" "sqlite" "jq" "mosquitto")

echo "  [INFO] Checking and installing packages: ${PACKAGES[*]}"

for pkg in "${PACKAGES[@]}"; do
    if ! brew list --formula "$pkg" >/dev/null 2>&1; then
        echo "  [INFO] Installing $pkg..."
        brew install "$pkg"
    else
        echo "  [OK] $pkg is already installed. Skipping."
    fi
done

# Python 설치/버전 검증은 이 단계의 책임이다.
if ! command -v python3 >/dev/null 2>&1; then
    echo "  [FATAL] python3 is still not available after Homebrew installation."
    echo "          Ensure Homebrew shellenv is applied in the current shell."
    exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "  [FATAL] python3 is available, but version is below 3.11."
    echo "          Current version: $(python3 --version 2>&1)"
    exit 1
fi

echo "  [INFO] Installed versions:"
git --version | awk '{print "    - "$0}'
python3 --version | awk '{print "    - "$0}'
just --version | awk '{print "    - "$0}'
sqlite3 --version | awk '{print "    - SQLite "$1" "$2}'
jq --version | awk '{print "    - "$0}'
mosquitto_pub -h 127.0.0.1 -V mqttv311 --help >/dev/null 2>&1 && echo "    - mosquitto client tools available"

echo "==> [PASS] Homebrew base dependencies installed successfully."
