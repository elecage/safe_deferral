#!/usr/bin/env bash
# ==============================================================================
# Script: 20_create_python_venv_rpi.sh
# Purpose: Create .venv-rpi and update base Python tools for Raspberry Pi 5
# ==============================================================================
set -euo pipefail

echo "==> [20_create_python_venv_rpi] Preparing Python virtual environment..."

# 1. python3.11 명령어 존재 여부 방어적 이중 확인 (Fail-fast)
if ! command -v python3.11 >/dev/null 2>&1; then
    echo "  [FATAL] python3.11 is not available in PATH."
    echo "          Please ensure 10_install_system_packages_rpi.sh completed successfully."
    exit 1
fi
echo "  [OK] python3.11 is available."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
VENV_DIR="${WORKSPACE_DIR}/.venv-rpi"

mkdir -p "${WORKSPACE_DIR}"

# 2. Virtual Environment Check & Creation
if [ -d "${VENV_DIR}" ]; then
    if ! "${VENV_DIR}/bin/python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' &> /dev/null; then
        echo "  [WARNING] Existing virtual environment has an outdated Python version. Recreating..."
        rm -rf "${VENV_DIR}"
        # 명시적인 3.11 인터프리터 호출
        python3.11 -m venv "${VENV_DIR}"
        echo "  [OK] Created new virtual environment with Python 3.11+."
    else
        echo "  [INFO] Valid Python 3.11+ virtual environment already exists."
    fi
else
    # 명시적인 3.11 인터프리터 호출
    python3.11 -m venv "${VENV_DIR}"
    echo "  [OK] Created new virtual environment at ${VENV_DIR}."
fi

# 3. 가상환경 활성화 및 기본 관리 도구 업데이트 (설계 명세 반영)
echo "  [INFO] Activating virtual environment and updating base tools..."
source "${VENV_DIR}/bin/activate"
pip install --quiet --upgrade pip setuptools wheel
echo "  [OK] Base Python tools (pip, setuptools, wheel) updated."

# 4. 설치된 버전 출력 (설계 명세 준수)
echo "  [INFO] Installed Python Environment Versions:"
python --version | awk '{print "    - "$0}'
pip --version | awk '{print "    - "$0}'

echo "==> [PASS] Virtual environment ready at ${VENV_DIR}"
