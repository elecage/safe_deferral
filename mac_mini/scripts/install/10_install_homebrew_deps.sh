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
# IMPORTANT:
# - macOS system python3 may remain older (e.g. 3.9.x)
# - therefore we explicitly install a Homebrew-managed Python 3.11+ formula
PACKAGES=("git" "python@3.12" "just" "sqlite" "jq" "mosquitto")

echo "  [INFO] Checking and installing packages: ${PACKAGES[*]}"

for pkg in "${PACKAGES[@]}"; do
    if ! brew list --formula "$pkg" >/dev/null 2>&1; then
        echo "  [INFO] Installing $pkg..."
        brew install "$pkg"
    else
        echo "  [OK] $pkg is already installed. Skipping."
    fi
done

# Homebrew Python 3.11+ 경로 결정
PYTHON_BIN=""
for candidate in \
    "$(brew --prefix python@3.12 2>/dev/null)/bin/python3.12" \
    "$(brew --prefix python@3.11 2>/dev/null)/bin/python3.11" \
    "$(brew --prefix python 2>/dev/null)/bin/python3"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
        if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON_BIN" ]]; then
    echo "  [FATAL] Could not find a Homebrew-managed Python 3.11+ interpreter after installation."
    echo "          Check brew formula installation state and shellenv configuration."
    exit 1
fi

if command -v python3 >/dev/null 2>&1; then
    CURRENT_PYTHON="$(command -v python3)"
    CURRENT_VERSION="$(python3 --version 2>&1 || true)"
    echo "  [INFO] Current shell python3: ${CURRENT_PYTHON} (${CURRENT_VERSION})"
fi

echo "  [OK] Selected Homebrew Python: ${PYTHON_BIN}"

if ! "$PYTHON_BIN" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "  [FATAL] Selected Homebrew Python is below 3.11."
    echo "          Selected version: $(${PYTHON_BIN} --version 2>&1)"
    exit 1
fi

echo "  [INFO] Installed versions:"
git --version | awk '{print "    - "$0}'
"$PYTHON_BIN" --version | awk '{print "    - Homebrew "$0}'
just --version | awk '{print "    - "$0}'
sqlite3 --version | awk '{print "    - SQLite "$1" "$2}'
jq --version | awk '{print "    - "$0}'
mosquitto_pub -h 127.0.0.1 -V mqttv311 --help >/dev/null 2>&1 && echo "    - mosquitto client tools available"

echo "  [INFO] If your shell still resolves python3 to an older system interpreter, apply Homebrew shellenv or call the Homebrew Python path explicitly."

echo "==> [PASS] Homebrew base dependencies installed successfully."
