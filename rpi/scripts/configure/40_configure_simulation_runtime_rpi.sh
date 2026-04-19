#!/usr/bin/env bash
# ==============================================================================
# Script: 40_configure_simulation_runtime_rpi.sh
# Purpose: Configure Simulation & Verification Runtime for RPi 5 (Phase 4 / Track B)
# ==============================================================================
set -euo pipefail

echo "==> [40_configure_simulation_runtime_rpi] Preparing Simulation & Verification Runtime..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
SIM_LOG_DIR="${WORKSPACE_DIR}/logs/simulation"
SCENARIO_DIR="${WORKSPACE_DIR}/scenarios"
VERIFY_DIR="${WORKSPACE_DIR}/logs/verification"

# 1. 런타임 디렉터리 생성
echo "  [INFO] Creating runtime directories..."
mkdir -p "${SIM_LOG_DIR}"
mkdir -p "${SCENARIO_DIR}"
mkdir -p "${VERIFY_DIR}"
echo "  [OK] Directories created at ${WORKSPACE_DIR} (logs/simulation, scenarios, logs/verification)."

# 2. .env 파일 검증 및 로드
ENV_FILE="${WORKSPACE_DIR}/.env"
if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] ${ENV_FILE} not found."
    echo "          Cannot configure simulation namespaces. Please run 10_write_env_files_rpi.sh first."
    exit 1
fi
source "${ENV_FILE}"

# 필수 환경변수 존재 여부 명시적 확인 (Fail-fast)
if [ -z "${TOPIC_NAMESPACE:-}" ] || [ -z "${NODE_COUNT:-}" ] || [ -z "${PUBLISH_INTERVAL_MS:-}" ]; then
    echo "  [FATAL] Required simulation parameters (TOPIC_NAMESPACE, NODE_COUNT, PUBLISH_INTERVAL_MS) are missing in .env."
    exit 1
fi
echo "  [OK] Environment variables loaded."

# 3. Python 가상환경 및 필수 라이브러리 가용성 사전 점검 (Fail-fast)
echo "  [INFO] Verifying Python virtual environment and dependencies..."
VENV_DIR="${WORKSPACE_DIR}/.venv-rpi"

if [ ! -f "${VENV_DIR}/bin/activate" ]; then
    echo "  [FATAL] Python virtual environment not found at ${VENV_DIR}."
    echo "          Please run the appropriate installation script first."
    exit 1
fi

# 선생님께서 제안하신 paho-mqtt 모듈 런타임 임포트 검증
if ! "${VENV_DIR}/bin/python" -c "import paho.mqtt.client" >/dev/null 2>&1; then
    echo "  [FATAL] 'paho-mqtt' is not installed in the virtual environment."
    echo "          Simulation nodes cannot publish context data."
    exit 1
fi
echo "  [OK] Virtual environment and 'paho-mqtt' verified."

# 4. 설정 결과 진단 요약 출력
echo "  [INFO] Simulation runtime successfully configured."
echo "         - Namespace: ${TOPIC_NAMESPACE}"
echo "         - Target Nodes: ${NODE_COUNT}"
echo "         - Interval: ${PUBLISH_INTERVAL_MS} ms"
echo "         - Audit Topic: ${VERIFICATION_AUDIT_TOPIC:-audit/log/#}"

echo "==> [PASS] Simulation and Verification runtime directories are ready."
