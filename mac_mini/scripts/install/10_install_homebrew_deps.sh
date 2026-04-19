#!/usr/bin/env bash
# ==============================================================================
# Script: 10_install_homebrew_deps.sh
# Purpose: Install base system dependencies via Homebrew (Phase 2)
# ==============================================================================
set -euo pipefail

echo "==> [10_install_homebrew_deps] Installing base dependencies via Homebrew..."

# 1. Homebrew 명령어 존재 여부 재확인 (안전장치)
if ! command -v brew &> /dev/null; then
    echo "  [FATAL] Homebrew is not installed. Run 00_preflight.sh first."
    exit 1
fi

echo "  [INFO] Updating Homebrew (this may take a while)..."
brew update > /dev/null

# 2. 필수 패키지 목록
# 주의: ollama, mosquitto, homeassistant 등 핵심 서비스는 Docker Compose로 격리 구동하므로 제외
PACKAGES=("git" "python" "just" "sqlite")

echo "  [INFO] Checking and installing packages: ${PACKAGES[*]}"

for pkg in "${PACKAGES[@]}"; do
    if ! brew list --formula "$pkg" >/dev/null 2>&1; then
        echo "  [INFO] Installing $pkg..."
        brew install "$pkg"
    else
        echo "  [OK] $pkg is already installed. Skipping."
    fi
done

# 3. 설치된 도구들의 버전 출력 (설계 명세 준수)
echo "  [INFO] Installed versions:"
git --version | awk '{print "    - "$0}'
python3 --version | awk '{print "    - "$0}'
just --version | awk '{print "    - "$0}'
sqlite3 --version | awk '{print "    - SQLite "$1" "$2}'

echo "==> [PASS] Homebrew base dependencies installed successfully."
