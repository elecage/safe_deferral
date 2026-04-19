#!/usr/bin/env bash
# ==============================================================================
# Script: 10_install_system_packages_rpi.sh
# Purpose: Install base system dependencies via APT on Raspberry Pi 5
# ==============================================================================
set -euo pipefail

echo "==> [10_install_system_packages_rpi] Installing system dependencies..."

# 1. Sudo 권한 사전 확보 (중단 없는 파이프라인 실행을 위한 인증 캐시)
echo "  [INFO] Requesting sudo privileges upfront..."
sudo -v

# 스크립트가 실행되는 동안 sudo 세션이 만료되지 않도록 백그라운드 유지 및 종료 시 안전한 정리
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
SUDO_KEEP_ALIVE_PID=$!
trap 'kill $SUDO_KEEP_ALIVE_PID 2>/dev/null' EXIT

# 2. 대화형 프롬프트로 인한 파이프라인 중단 방지
# env를 사용하여 DEBIAN_FRONTEND 환경변수를 해당 명령어에만 명시적으로 전달
echo "  [INFO] Updating and upgrading APT packages (this may take a while)..."
sudo env DEBIAN_FRONTEND=noninteractive apt-get update -y -qq
sudo env DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq

# 3. 시간 동기화(chrony), MQTT 통신, 그리고 명시적인 Python 3.11 패키지 지정
PACKAGES=("python3.11" "python3.11-venv" "git" "mosquitto-clients" "chrony")

echo "  [INFO] Checking and installing packages: ${PACKAGES[*]}"

# dpkg-query를 이용한 엄격한 패키지 설치 확인
for pkg in "${PACKAGES[@]}"; do
    if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "ok installed"; then
        echo "  [INFO] Installing $pkg..."
        # 설치 실패 시 명확한 사유 안내
        if ! sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y "$pkg" > /dev/null; then
            echo "  [FATAL] Could not install $pkg."
            echo "          Your Raspberry Pi OS image may not provide this package name by default."
            exit 1
        fi
    else
        echo "  [OK] $pkg is already installed. Skipping."
    fi
done

# 4. 설치된 패키지 버전 출력
echo "  [INFO] Installed versions:"
python3.11 --version | awk '{print "    - "$0}'
git --version | awk '{print "    - "$0}'
mosquitto_pub --version 2>&1 | awk 'NR==1{print "    - "$0}' 
chronyd --version 2>&1 | awk 'NR==1{print "    - "$0}'

echo "==> [PASS] System packages installed successfully."
