#!/usr/bin/env bash
# ==============================================================================
# Script: 00_install_homebrew.sh
# Purpose: Ensure Homebrew is installed on macOS before the rest of install flow
# ==============================================================================
set -euo pipefail

echo "==> [00_install_homebrew] Ensuring Homebrew is installed..."

# 1. macOS 필수
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "  [FAIL] This script must be run on macOS."
    exit 1
fi

echo "  [OK] Operating System is macOS."

# 1a. Homebrew는 root로 설치하면 안 됨
if [[ "$(id -u)" -eq 0 ]]; then
    echo "  [FAIL] Do not run Homebrew installation as root."
    echo "  [INFO] Re-run this script as the normal macOS user account that will operate the Mac mini hub."
    exit 1
fi

# 1b. 관리자 권한 안내. Homebrew 설치 과정에서 sudo/admin 권한이 필요할 수 있음
if ! id -Gn | grep -qw admin; then
    echo "  [WARN] Current user may not have macOS admin privileges."
    echo "  [INFO] Homebrew installation may fail if sudo/admin access is unavailable."
else
    echo "  [OK] Current user appears to be in the macOS admin group."
fi

# 2. 이미 설치되어 있으면 종료
if command -v brew >/dev/null 2>&1; then
    echo "  [OK] Homebrew is already installed. Skipping installation."
    brew --version | head -1 | awk '{print "  [INFO] "$0}'
    exit 0
fi

# 3. 네트워크 확인
if ! curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh >/dev/null; then
    echo "  [FAIL] Unable to reach the Homebrew install script URL. Check network connectivity first."
    exit 1
fi

echo "  [INFO] Download source for Homebrew installer is reachable."

echo "  [INFO] Running official Homebrew installer..."
NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 4. 현재 셸에서 brew 경로 적용 시도
if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
fi

# 5. 설치 확인
if ! command -v brew >/dev/null 2>&1; then
    echo "  [FAIL] Homebrew installation finished but 'brew' is still not available in the current shell."
    echo "  [INFO] Open a new shell or run the shellenv command printed by the installer, then rerun 00_preflight.sh."
    exit 1
fi

echo "  [OK] Homebrew installation completed successfully."
brew --version | head -1 | awk '{print "  [INFO] "$0}'

echo "  [INFO] If the installer suggested adding brew shellenv to ~/.zprofile or ~/.bash_profile, apply that change before future sessions."
echo "==> [PASS] Homebrew is ready for the remaining install flow."
