#!/usr/bin/env bash
# ==============================================================================
# Script: 00_preflight.sh
# Purpose: Pure pre-flight checks for Mac mini system requirements after Homebrew bootstrap
# ==============================================================================
set -euo pipefail

echo "==> [00_preflight] Checking Mac mini system requirements..."

# 1. OS 확인 (macOS 필수)
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "  [FAIL] This script must be run on macOS."
    exit 1
fi
echo "  [OK] Operating System is macOS."

# 2. Homebrew 존재 여부 확인
if ! command -v brew &> /dev/null; then
    echo "  [FAIL] Homebrew is not installed. Run mac_mini/scripts/install/00_install_homebrew.sh first."
    exit 1
fi
echo "  [OK] Homebrew is installed."

# 3. 디스크 여유 공간 확인 (최소 15GB 권장 - Ollama 모델 및 컨테이너 용량)
FREE_SPACE_GB=$(df -g / | tail -1 | awk '{print $4}')
if [ "$FREE_SPACE_GB" -lt 15 ]; then
    echo "  [FAIL] Insufficient disk space. At least 15GB is required (Available: ${FREE_SPACE_GB}GB)."
    exit 1
fi
echo "  [OK] Disk space is sufficient (${FREE_SPACE_GB}GB available)."

# 4. 네트워크 연결 확인 (Warning으로 완화: 오프라인/폐쇄망 설치 고려)
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    echo "  [WARNING] Network connection is not available. Some download steps may fail."
else
    echo "  [OK] Network is reachable."
fi

# 5. 안내 메시지: Python은 다음 install 단계에서 설치/검증됨
if command -v python3 >/dev/null 2>&1; then
    if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
        echo "  [OK] Python 3.11+ is already available."
    else
        echo "  [INFO] Python is present but will be upgraded/validated in 10_install_homebrew_deps.sh."
    fi
else
    echo "  [INFO] Python 3 is not currently available; it will be installed in 10_install_homebrew_deps.sh."
fi

echo "==> [PASS] All preflight checks completed successfully."
