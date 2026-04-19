#!/usr/bin/env bash
# ==============================================================================
# Script: 40_install_time_sync_client_rpi.sh
# Purpose: Ensure Chrony time sync client is active on Raspberry Pi 5
# ==============================================================================
set -euo pipefail

echo "==> [40_install_time_sync_client_rpi] Ensuring Time Sync Client is active..."

# 1. Sudo 권한 사전 확보 (무인 설치 방해 방지)
echo "  [INFO] Requesting sudo privileges upfront..."
sudo -v

# 2. systemctl 존재 여부 사전 확인 (Fail-fast)
if ! command -v systemctl >/dev/null 2>&1; then
    echo "  [FATAL] systemctl is not available on this system."
    echo "          Cannot configure chrony service automatically. Manual setup required."
    exit 1
fi
echo "  [OK] systemctl is available."

# 3. Chrony 서비스 상태 확인 및 기동
# RPi OS (Debian) 서비스명인 'chrony'로 실행
if systemctl is-active --quiet chrony; then
    echo "  [INFO] Chrony (time sync service) is already running."
else
    echo "  [INFO] Starting and enabling Chrony service..."
    sudo systemctl enable chrony > /dev/null 2>&1
    sudo systemctl start chrony

    # 기동 후 정상 실행 여부 방어적 재검증
    if ! systemctl is-active --quiet chrony; then
        echo "  [FATAL] Failed to start Chrony service."
        exit 1
    fi
    echo "  [OK] Chrony service started successfully."
fi

# 4. 버전 출력 확인 (설계 명세 준수)
echo "  [INFO] Installed Time Sync Client Version:"
chronyd --version 2>&1 | awk 'NR==1{print "    - "$0}'

echo "==> [PASS] Time sync client is active. (Target configuration will be done in the configure phase)"
