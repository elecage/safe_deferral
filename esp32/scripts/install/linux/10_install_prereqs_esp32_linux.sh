#!/usr/bin/env bash
# ==============================================================================
# Script: 10_install_prereqs_esp32_linux.sh
# Purpose: Install prerequisite packages for ESP32 development on Linux
# ==============================================================================
set -euo pipefail

echo "==> [10_install_prereqs_esp32_linux] Installing Linux prerequisites for ESP32 development..."

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

echo "  [INFO] Using package manager: ${PKG_MANAGER}"

case "${PKG_MANAGER}" in
  apt)
    sudo apt-get update -y
    sudo apt-get install -y \
      git wget flex bison gperf python3 python3-pip python3-venv \
      cmake ninja-build ccache dfu-util libusb-1.0-0 libffi-dev libssl-dev
    ;;
  dnf)
    sudo dnf install -y \
      git wget flex bison gperf python3 python3-pip \
      cmake ninja-build ccache dfu-util libusb1-devel libffi-devel openssl-devel
    ;;
  pacman)
    sudo pacman -Syu --noconfirm
    sudo pacman -S --needed --noconfirm \
      git wget flex bison gperf python python-pip \
      cmake ninja ccache dfu-util libusb
    ;;
esac

echo "  [INFO] Installed versions:"
git --version | awk '{print "    - "$0}'
cmake --version | awk 'NR==1{print "    - "$0}'
if command -v ninja >/dev/null 2>&1; then
    ninja --version | awk '{print "    - ninja " $0}'
elif command -v ninja-build >/dev/null 2>&1; then
    ninja-build --version | awk '{print "    - ninja-build " $0}'
fi
python3 --version | awk '{print "    - "$0}'
dfu-util --version 2>&1 | awk 'NR==1{print "    - "$0}'

echo "==> [PASS] Linux prerequisites installed successfully."
