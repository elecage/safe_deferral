#!/usr/bin/env bash
# ==============================================================================
# Script: 30_install_python_deps_rpi.sh
# Purpose: Install Python dependencies for Raspberry Pi 5 simulation/verification node
# ==============================================================================
set -euo pipefail

echo "==> [30_install_python_deps_rpi] Installing Python dependencies..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
VENV_DIR="${WORKSPACE_DIR}/.venv-rpi"
ENV_FILE="${WORKSPACE_DIR}/.env"

# 1. 가상환경 존재 여부 사전 확인 (Fail-fast)
if [ ! -f "${VENV_DIR}/bin/activate" ]; then
    echo "  [FATAL] Virtual environment not found at ${VENV_DIR}."
    echo "          Please run 20_create_python_venv_rpi.sh first."
    exit 1
fi
echo "  [OK] Virtual environment found."

# 2. Optional feature flags from .env, if available.
if [ -f "${ENV_FILE}" ]; then
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    echo "  [INFO] Loaded optional feature flags from ${ENV_FILE}."
else
    echo "  [INFO] ${ENV_FILE} not found. Optional dashboard/export checks default to disabled."
fi

ENABLE_RPI_DASHBOARD_BACKEND="${ENABLE_RPI_DASHBOARD_BACKEND:-false}"
ENABLE_RPI_RESULT_EXPORT="${ENABLE_RPI_RESULT_EXPORT:-false}"

# 3. 가상환경 활성화 및 기본 도구 업데이트
echo "  [INFO] Activating virtual environment..."
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
pip install --quiet --upgrade pip setuptools wheel

# 4. 요구사항 파일 확인 및 패키지 설치
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements-rpi.txt"

if [ -f "${REQUIREMENTS_FILE}" ]; then
    echo "  [INFO] Installing packages from ${REQUIREMENTS_FILE}..."
    pip install --quiet -r "${REQUIREMENTS_FILE}"

    # 재현성을 위한 Pi 전용 lock 파일 생성
    LOCK_FILE="${WORKSPACE_DIR}/requirements-rpi-lock.txt"
    pip freeze > "${LOCK_FILE}"
    echo "  [OK] Dependencies locked to ${LOCK_FILE}"
else
    echo "  [FATAL] ${REQUIREMENTS_FILE} not found. Core dependencies cannot be installed."
    exit 1
fi

check_required_dist() {
    local dist_name="$1"
    local import_name="$2"

    if ! python -c "import ${import_name}" >/dev/null 2>&1; then
        echo "  [FATAL] Required Python package import failed: ${import_name} (${dist_name})"
        exit 1
    fi

    python -c "from importlib.metadata import version; print('    - ${dist_name}:', version('${dist_name}'))" || {
        echo "  [FATAL] Required Python distribution metadata not found: ${dist_name}"
        exit 1
    }
}

check_optional_dist() {
    local dist_name="$1"
    local import_name="$2"
    local feature_flag="$3"
    local feature_name="$4"

    if python -c "import ${import_name}" >/dev/null 2>&1; then
        python -c "from importlib.metadata import version; print('    - ${dist_name}:', version('${dist_name}'))" || true
        return 0
    fi

    if [ "${feature_flag}" = "true" ]; then
        echo "  [FATAL] Optional package ${dist_name} is required because ${feature_name} is enabled."
        echo "          Missing import: ${import_name}"
        exit 1
    fi

    echo "    - ${dist_name}: not installed (${feature_name} disabled)"
}

# 5. 핵심 패키지 설치 엄격 검증 및 버전 출력 (Hard-fail)
echo "  [INFO] Installed required simulation/verification packages:"
check_required_dist "paho-mqtt" "paho.mqtt.client"
check_required_dist "pytest" "pytest"
check_required_dist "PyYAML" "yaml"
check_required_dist "jsonschema" "jsonschema"

# 6. 선택 패키지 검증: 기능 flag가 켜진 경우에만 Hard-fail
echo "  [INFO] Optional dashboard/export package checks:"
check_optional_dist "fastapi" "fastapi" "${ENABLE_RPI_DASHBOARD_BACKEND}" "ENABLE_RPI_DASHBOARD_BACKEND"
check_optional_dist "uvicorn" "uvicorn" "${ENABLE_RPI_DASHBOARD_BACKEND}" "ENABLE_RPI_DASHBOARD_BACKEND"
check_optional_dist "pandas" "pandas" "${ENABLE_RPI_RESULT_EXPORT}" "ENABLE_RPI_RESULT_EXPORT"

echo "  [INFO] Feature flags:"
echo "    - ENABLE_RPI_DASHBOARD_BACKEND=${ENABLE_RPI_DASHBOARD_BACKEND}"
echo "    - ENABLE_RPI_RESULT_EXPORT=${ENABLE_RPI_RESULT_EXPORT}"

echo "==> [PASS] Python dependencies installed and verified successfully."
