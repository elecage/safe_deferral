#!/usr/bin/env bash
# ==============================================================================
# Script: 30_setup_python_venv_mac.sh
# Purpose: Create .venv-mac and install Python dependencies
# ==============================================================================
set -euo pipefail

echo "==> [30_setup_python_venv_mac] Checking .venv-mac and installing dependencies..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
VENV_DIR="${WORKSPACE_DIR}/.venv-mac"

mkdir -p "${WORKSPACE_DIR}"

if ! command -v brew >/dev/null 2>&1; then
    echo "  [FATAL] Homebrew is not installed. Run mac_mini/scripts/install/00_install_homebrew.sh first."
    exit 1
fi

# 0. 사용할 Homebrew Python 3.11+ 선택
PYTHON_BIN=""
for candidate in \
    "$(brew --prefix python@3.12 2>/dev/null)/bin/python3.12" \
    "$(brew --prefix python@3.11 2>/dev/null)/bin/python3.11" \
    "$(brew --prefix python 2>/dev/null)/bin/python3"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
        if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON_BIN" ]]; then
    echo "  [FATAL] Could not locate a Homebrew-managed Python 3.11+ interpreter."
    echo "          Run mac_mini/scripts/install/10_install_homebrew_deps.sh first."
    exit 1
fi

echo "  [OK] Using Homebrew Python: ${PYTHON_BIN}"

# 1. Virtual Environment Check & Creation
if [ -d "${VENV_DIR}" ]; then
    if ! "${VENV_DIR}/bin/python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' &> /dev/null; then
        echo "  [WARNING] Existing virtual environment has an outdated Python version. Recreating..."
        rm -rf "${VENV_DIR}"
        "$PYTHON_BIN" -m venv "${VENV_DIR}"
        echo "  [OK] Created new Homebrew Python 3.11+ virtual environment."
    else
        echo "  [INFO] Valid Python 3.11+ virtual environment already exists. Will synchronize packages."
    fi
else
    "$PYTHON_BIN" -m venv "${VENV_DIR}"
    echo "  [OK] Created new virtual environment at ${VENV_DIR}."
fi

# 2. Activate and update base tools
echo "  [INFO] Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

echo "  [INFO] Upgrading pip, setuptools, and wheel..."
python -m pip install --quiet --upgrade pip setuptools wheel

# 3. Install Requirements
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements-mac.txt"

if [ -f "${REQUIREMENTS_FILE}" ]; then
    echo "  [INFO] Installing packages from ${REQUIREMENTS_FILE}..."
    python -m pip install -r "${REQUIREMENTS_FILE}"

    # 4. Lock Dependencies
    LOCK_FILE="${WORKSPACE_DIR}/requirements-mac-lock.txt"
    python -m pip freeze > "${LOCK_FILE}"
    echo "  [OK] Dependencies locked to requirements-mac-lock.txt"
else
    echo "  [FATAL] ${REQUIREMENTS_FILE} not found. Core dependencies cannot be installed."
    exit 1
fi

# 5. Verify Installation
echo "  [INFO] Installed Python Environment Versions:"
python --version | awk '{print "    - "$0}'
python -m pip --version | awk '{print "    - "$0}'

echo "==> [PASS] Python virtual environment ready at ${VENV_DIR}"
