#!/usr/bin/env bash
# ==============================================================================
# Script: 00_preflight_rpi.sh
# Purpose: Pure pre-flight checks for Raspberry Pi 5 system requirements
# ==============================================================================
set -euo pipefail

echo "==> [00_preflight_rpi] Checking Raspberry Pi 5 system requirements..."

# 1. OS 확인 (리눅스 환경 검증)
if [[ "$(uname -s)" != "Linux" ]]; then
    echo "  [FATAL] This script must be run on Linux (Raspberry Pi OS)."
    exit 1
fi
echo "  [OK] Operating System is Linux."

# 2. Python 3.11 이상 실제 버전 검사 (전체 프로젝트 패키지 정합성을 위해 3.11 강제)
if command -v python3 &> /dev/null; then
    if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
        echo "  [FATAL] Python 3.11 or higher is required for project dependencies. Please upgrade Python."
        exit 1
    fi
else
    echo "  [FATAL] Python 3 is not installed."
    exit 1
fi
echo "  [OK] Python 3.11+ is installed."

# 3. 디스크 여유 공간 확인 (최소 5GB 권장)
# 리눅스(RPi) 환경에 맞춰 df -m (메가바이트 단위) 사용 후 GB로 환산
FREE_SPACE_MB=$(df -m / | tail -1 | awk '{print $4}')
FREE_SPACE_GB=$((FREE_SPACE_MB / 1024))
if [ "$FREE_SPACE_GB" -lt 5 ]; then
    echo "  [FATAL] Insufficient disk space. At least 5GB is required (Available: ${FREE_SPACE_GB}GB)."
    exit 1
fi
echo "  [OK] Disk space is sufficient (${FREE_SPACE_GB}GB available)."

# 4. 네트워크 연결 확인 (Warning으로 완화: 오프라인/폐쇄망 설치 고려)
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    echo "  [WARNING] Network connection is not available. Some download steps may fail."
else
    echo "  [OK] Network is reachable."
fi

echo "==> [PASS] All preflight checks completed successfully."
