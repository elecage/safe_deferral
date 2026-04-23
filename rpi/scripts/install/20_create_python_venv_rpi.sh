#!/usr/bin/env bash
# ==============================================================================
# Script: 20_create_python_venv_rpi.sh
# Purpose: Create .venv-rpi and update base Python tools for Raspberry Pi 5
# ==============================================================================
set -euo pipefail

echo "==> [20_create_python_venv_rpi] Preparing Python virtual environment..."

# 1. python3 명령어 존재 여부 및 버전 확인
if ! command -v python3 >/dev/null 2>&1; then
    echo "  [FATAL] python3 is not available in PATH."
    echo "          Please ensure 10_install_system_packages_rpi.sh completed successfully."
    exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "  [FATAL] python3 is available, but version is below 3.11."
    echo "          Current version: $(python3 --version 2>&1)"
    exit 1
fi

echo "  [OK] python3 3.11+ is available."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
VENV_DIR="${WORKSPACE_DIR}/.venv-rpi"

mkdir -p "${WORKSPACE_DIR}"

# 2. Virtual Environment Check & Creation
if [ -d "${VENV_DIR}" ]; then
    if ! "${VENV_DIR}/bin/python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' &> /dev/null; then
        echo "  [WARNING] Existing virtual environment has an outdated Python version. Recreating..."
        rm -rf "${VENV_DIR}"
        python3 -m venv "${VENV_DIR}"
        echo "  [OK] Created new virtual environment with python3 3.11+."
    else
        echo "  [INFO] Valid python3 3.11+ virtual environment already exists."
    fi
else
    python3 -m venv "${VENV_DIR}"
    echo "  [OK] Created new virtual environment at ${VENV_DIR}."
fi

# 3. 가상환경 활성화 및 기본 관리 도구 업데이트
# 일부 배포판에서 ensurepip/venv 초기 설치가 약간 보수적일 수 있으므로 명시적으로 업그레이드한다.
echo "  [INFO] Activating virtual environment and updating base tools..."
source "${VENV_DIR}/bin/activate"
pip install --quiet --upgrade pip setuptools wheel
echo "  [OK] Base Python tools (pip, setuptools, wheel) updated."

# 4. 설치된 버전 출력
echo "  [INFO] Installed Python Environment Versions:"
python --version | awk '{print "    - "$0}'
pip --version | awk '{print "    - "$0}'

echo "==> [PASS] Virtual environment ready at ${VENV_DIR}"
