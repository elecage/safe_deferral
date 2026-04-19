#!/usr/bin/env bash
# ==============================================================================
# Script: 30_install_python_deps_rpi.sh
# Purpose: Install Python dependencies for Raspberry Pi 5 simulation node
# ==============================================================================
set -euo pipefail

echo "==> [30_install_python_deps_rpi] Installing Python dependencies..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
VENV_DIR="${WORKSPACE_DIR}/.venv-rpi"

# 1. 가상환경 존재 여부 사전 확인 (Fail-fast)
if [ ! -f "${VENV_DIR}/bin/activate" ]; then
    echo "  [FATAL] Virtual environment not found at ${VENV_DIR}."
    echo "          Please run 20_create_python_venv_rpi.sh first."
    exit 1
fi
echo "  [OK] Virtual environment found."

# 2. 가상환경 활성화 및 기본 도구 업데이트
echo "  [INFO] Activating virtual environment..."
source "${VENV_DIR}/bin/activate"
pip install --quiet --upgrade pip setuptools wheel

# 3. 요구사항 파일 확인 및 패키지 설치
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements-rpi.txt"

if [ -f "${REQUIREMENTS_FILE}" ]; then
    echo "  [INFO] Installing packages from ${REQUIREMENTS_FILE}..."
    pip install --quiet -r "${REQUIREMENTS_FILE}"

    # 재현성을 위한 Pi 전용 lock 파일 생성
    LOCK_FILE="${WORKSPACE_DIR}/requirements-rpi-lock.txt"
    pip freeze > "${LOCK_FILE}"
    echo "  [OK] Dependencies locked to requirements-rpi-lock.txt"
else
    echo "  [FATAL] ${REQUIREMENTS_FILE} not found. Core dependencies cannot be installed."
    exit 1
fi

# 4. 핵심 패키지 설치 엄격 검증 및 버전 출력 (Hard-fail 적용)
echo "  [INFO] Installed core simulation packages:"
python -c "from importlib.metadata import version; print('    - paho-mqtt:', version('paho-mqtt'))" || { echo "  [FATAL] paho-mqtt is not installed."; exit 1; }
python -c "from importlib.metadata import version; print('    - pytest:', version('pytest'))" || { echo "  [FATAL] pytest is not installed."; exit 1; }
python -c "from importlib.metadata import version; print('    - PyYAML:', version('PyYAML'))" || { echo "  [FATAL] PyYAML is not installed."; exit 1; }
python -c "from importlib.metadata import version; print('    - jsonschema:', version('jsonschema'))" || { echo "  [FATAL] jsonschema is not installed."; exit 1; }

echo "==> [PASS] Python dependencies installed successfully."
