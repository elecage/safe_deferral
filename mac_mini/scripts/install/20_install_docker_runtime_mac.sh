#!/usr/bin/env bash
# ==============================================================================
# Script: 20_install_docker_runtime_mac.sh
# Purpose: Install and verify Docker runtime on Mac mini (Phase 2)
# ==============================================================================
set -euo pipefail

echo "==> [20_install_docker_runtime_mac] Checking Docker runtime..."

# 0. Homebrew prerequisite 확인
if ! command -v brew >/dev/null 2>&1; then
    echo "  [FATAL] Homebrew is not installed. Run mac_mini/scripts/install/00_install_homebrew.sh first."
    exit 1
fi

echo "  [OK] Homebrew is available."

# 1. Docker CLI 및 Desktop App 분리 확인
if ! command -v docker &> /dev/null; then
    if [ -d "/Applications/Docker.app" ]; then
        echo "  [FATAL] Docker.app exists in /Applications but 'docker' CLI is not in PATH."
        echo "          Please open Docker Desktop to install CLI tools or fix your PATH."
        exit 1
    else
        echo "  [INFO] Docker not found. Installing Docker Desktop via Homebrew..."
        brew install --cask docker
        echo "============================================================"
        echo "  [ACTION REQUIRED] Docker Desktop has been installed."
        echo "  Please open Docker Desktop manually to complete the GUI setup"
        echo "  and start the Docker daemon, then re-run this script."
        echo "============================================================"
        exit 1
    fi
fi
echo "  [OK] Docker CLI is available."

# 2. Docker Daemon 실제 실행 여부 검증
if ! docker info &> /dev/null; then
    echo "  [FATAL] Docker daemon is not running."
    echo "          Please launch the Docker Desktop application and wait for the engine to start."
    exit 1
fi
echo "  [OK] Docker daemon is running."

# 3. Docker Compose 플러그인 사용 가능 여부 확인
if ! docker compose version &> /dev/null; then
    echo "  [FATAL] 'docker compose' plugin is not available. Please check your Docker installation."
    exit 1
fi
echo "  [OK] Docker Compose is available."

# 4. Docker 네트워크/볼륨 권한 기본 점검 (설계 명세 반영)
if ! docker network ls &> /dev/null || ! docker volume ls &> /dev/null; then
    echo "  [FATAL] Cannot access Docker networks or volumes. Check daemon permissions."
    exit 1
fi
echo "  [OK] Docker network and volume management are accessible."

# 5. 설치된 버전 출력 (설계 명세 준수)
echo "  [INFO] Installed versions:"
docker --version | awk '{print "    - "$0}'
docker compose version | awk '{print "    - "$0}'

echo "==> [PASS] Docker daemon and compose are running and ready."
