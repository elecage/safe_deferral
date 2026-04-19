#!/usr/bin/env bash
# ==============================================================================
# Script: 30_setup_python_venv_mac.sh
# Purpose: Create .venv-mac and install Python dependencies (Phase 3)
# ==============================================================================
set -euo pipefail

echo "==> [30_setup_python_venv_mac] Checking .venv-mac and installing dependencies..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
VENV_DIR="${WORKSPACE_DIR}/.venv-mac"

mkdir -p "${WORKSPACE_DIR}"

# 1. Virtual Environment Check & Creation
if [ -d "${VENV_DIR}" ]; then
    if ! "${VENV_DIR}/bin/python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' &> /dev/null; then
        echo "  [WARNING] Existing virtual environment has an outdated Python version. Recreating..."
        rm -rf "${VENV_DIR}"
        python3 -m venv "${VENV_DIR}"
        echo "  [OK] Created new Python 3.11+ virtual environment."
    else
        echo "  [INFO] Valid Python 3.11+ virtual environment already exists. Will synchronize packages."
    fi
else
    python3 -m venv "${VENV_DIR}"
    echo "  [OK] Created new virtual environment at ${VENV_DIR}."
fi

# 2. Activate and update base tools
echo "  [INFO] Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

echo "  [INFO] Upgrading pip, setuptools, and wheel..."
pip install --quiet --upgrade pip setuptools wheel

# 3. Install Requirements
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements-mac.txt"

if [ -f "${REQUIREMENTS_FILE}" ]; then
    echo "  [INFO] Installing packages from ${REQUIREMENTS_FILE}..."
    pip install -r "${REQUIREMENTS_FILE}"

    # 4. Lock Dependencies
    LOCK_FILE="${WORKSPACE_DIR}/requirements-mac-lock.txt"
    pip freeze > "${LOCK_FILE}"
    echo "  [OK] Dependencies locked to requirements-mac-lock.txt"
else
    echo "  [FATAL] ${REQUIREMENTS_FILE} not found. Core dependencies cannot be installed."
    exit 1
fi

# 5. Verify Installation (설계 명세 준수: 설치 후 버전 출력)
echo "  [INFO] Installed Python Environment Versions:"
python --version | awk '{print "    - "$0}'
pip --version | awk '{print "    - "$0}'

echo "==> [PASS] Python virtual environment ready at ${VENV_DIR}"
