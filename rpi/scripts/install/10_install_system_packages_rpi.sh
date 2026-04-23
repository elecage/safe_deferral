#!/usr/bin/env bash
# ==============================================================================
# Script: 10_install_system_packages_rpi.sh
# Purpose: Install base system dependencies via APT on Raspberry Pi 5
# ==============================================================================
set -euo pipefail

echo "==> [10_install_system_packages_rpi] Installing system dependencies..."

# 1. Sudo 권한 사전 확보
echo "  [INFO] Requesting sudo privileges upfront..."
sudo -v

# 스크립트 실행 중 sudo 세션 유지
while true; do
    sudo -n true
    sleep 60
    kill -0 "$$" || exit
done 2>/dev/null &
SUDO_KEEP_ALIVE_PID=$!
trap 'kill $SUDO_KEEP_ALIVE_PID 2>/dev/null || true' EXIT

# 2. APT 메타데이터 업데이트
echo "  [INFO] Updating and upgrading APT packages (this may take a while)..."
sudo env DEBIAN_FRONTEND=noninteractive apt-get update -y -qq
sudo env DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq

# 3. 필수 시스템 패키지 설치
# - mosquitto-clients: MQTT pub/sub verify 및 통신 점검
# - chrony: LAN-only 시간 동기화
# - jq: frozen asset 구조 검증
# - rsync, curl: Phase 0 artifact sync
PACKAGES=(
    "python3.11"
    "python3.11-venv"
    "git"
    "mosquitto-clients"
    "chrony"
    "jq"
    "rsync"
    "curl"
)

echo "  [INFO] Checking and installing packages: ${PACKAGES[*]}"

for pkg in "${PACKAGES[@]}"; do
    if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "ok installed"; then
        echo "  [INFO] Installing $pkg..."
        if ! sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y "$pkg" > /dev/null; then
            echo "  [FATAL] Could not install $pkg."
            echo "          Your Raspberry Pi OS image may not provide this package name by default."
            exit 1
        fi
    else
        echo "  [OK] $pkg is already installed. Skipping."
    fi
done

# 4. 설치 결과 출력
echo "  [INFO] Installed versions:"
python3.11 --version | awk '{print "    - "$0}'
git --version | awk '{print "    - "$0}'
mosquitto_pub --help >/dev/null 2>&1 && echo "    - mosquitto client tools available"
chronyd --version 2>&1 | awk 'NR==1{print "    - "$0}'
jq --version | awk '{print "    - "$0}'
rsync --version 2>/dev/null | awk 'NR==1{print "    - "$0}'
curl --version 2>/dev/null | awk 'NR==1{print "    - "$0}'

echo "==> [PASS] System packages installed successfully."
