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

echo "  [INFO] Checking serial-port group membership for ESP32 flash/monitor access..."
SERIAL_GROUP_CANDIDATES=(dialout uucp tty plugdev)
USER_GROUPS="$(id -nG "${USER}" 2>/dev/null || groups "${USER}" 2>/dev/null || true)"
HAS_SERIAL_GROUP=false

for group_name in "${SERIAL_GROUP_CANDIDATES[@]}"; do
    if printf '%s\n' "${USER_GROUPS}" | tr ' ' '\n' | grep -qx "${group_name}"; then
        HAS_SERIAL_GROUP=true
        echo "  [OK] User '${USER}' is a member of serial-access group: ${group_name}"
        break
    fi
done

if [ "${HAS_SERIAL_GROUP}" != "true" ]; then
    echo "  [WARNING] User '${USER}' may not have serial-port access for ESP32 flash/monitor."
    echo "            Current groups: ${USER_GROUPS:-<unknown>}"
    case "${PKG_MANAGER}" in
      apt|dnf)
        echo "            Suggested command: sudo usermod -aG dialout ${USER}"
        ;;
      pacman)
        echo "            Suggested command: sudo usermod -aG uucp ${USER}"
        ;;
    esac
    echo "            Log out and back in after changing group membership."
fi

echo "==> [PASS] Linux prerequisites installed successfully."
