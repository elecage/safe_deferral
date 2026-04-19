#!/usr/bin/env bash
# ==============================================================================
# Script: 70_verify_rpi_base_runtime.sh
# Purpose: Verify RPi 5 Network, MQTT Publish Reachability, Synced Assets, and Time Sync
# ==============================================================================
set -euo pipefail

echo "==> [70_verify_rpi_base_runtime] Verifying RPi 5 Base Runtime & Communication..."

# 1. 필수 명령어 존재 여부 확인 (Fail-fast)
# [보완 반영] awk, tee 등 스크립트 의존성 도구를 명시적으로 추가 점검
if ! command -v jq >/dev/null 2>&1 || ! command -v mosquitto_pub >/dev/null 2>&1 ||    ! command -v ping >/dev/null 2>&1 || ! command -v awk >/dev/null 2>&1 || ! command -v tee >/dev/null 2>&1; then
    echo "  [FATAL] Required tools (jq, mosquitto-clients, ping, awk, tee) are not installed."
    echo "          Please run the RPi 5 base runtime installation script first."
    exit 1
fi
echo "  [OK] Required CLI tools verified."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

# 2. 환경변수 로드 및 검증
if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"

TARGET_HOST="${MQTT_HOST:-}"
TARGET_PORT="${MQTT_PORT:-1883}"

if [ -z "${TARGET_HOST}" ]; then
    echo "  [FATAL] MQTT_HOST is not defined in .env. Cannot test communication."
    exit 1
fi

# 3. 로컬 브로커 통신 가능성 확인 (Ping 및 MQTT Publish Reachability)
echo "  [INFO] Checking network reachability to Mac mini (${TARGET_HOST})..."
if ping -c 3 -W 3 "${TARGET_HOST}" >/dev/null 2>&1; then
    echo "  [OK] Mac mini is reachable via ICMP (Ping)."
else
    echo "  [FATAL] Cannot reach Mac mini at ${TARGET_HOST}. Check LAN and firewall."
    exit 1
fi

# [수정 반영 5] 폐루프(Closed-loop)가 아님을 명확히 하고 "Publish 가능성 확인"으로 명칭 하향
echo "  [INFO] Testing MQTT Publish Reachability..."
TEST_TOPIC="verify/rpi5/ping"
TEST_MSG="rpi5_ping_$(date +%s)_$$"
AUTH_ARGS=()
if [ -n "${MQTT_USER:-}" ] && [ -n "${MQTT_PASS:-}" ]; then
    AUTH_ARGS=("-u" "${MQTT_USER}" "-P" "${MQTT_PASS}")
fi

if mosquitto_pub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${TEST_TOPIC}" -m "${TEST_MSG}" -W 3; then
    echo "  [OK] MQTT publish request accepted. Port ${TARGET_PORT} is open."
else
    echo "  [FATAL] MQTT publish failed. Check Mosquitto status and firewall rules on Mac mini."
    exit 1
fi

# 4. 읽기 전용 동결 자산(Read-only Synced Assets) 확인
# [수정 반영 1] 동결된 동기화 스크립트 아키텍처에 맞게 Policy와 Schema 디렉터리 분리
POLICY_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"
SCHEMA_DIR="${SCHEMA_SYNC_PATH:-${WORKSPACE_DIR}/config/schemas}"

echo "  [INFO] Verifying read-only Phase 0 synced assets..."

if [ ! -d "${POLICY_DIR}" ] || [ ! -d "${SCHEMA_DIR}" ]; then
    echo "  [FATAL] Policy or Schema directory not found."
    exit 1
fi

# [수정 반영 2] 동결된 전체 8개 자산(정책 4개, 스키마 4개)으로 검증 대상 확대
REQUIRED_POLICY_ASSETS=(
    "policy_table.json"
    "fault_injection_rules.json"
    "low_risk_actions.json"
    "output_profile.json"
)

REQUIRED_SCHEMA_ASSETS=(
    "context_schema.json"
    "candidate_action_schema.json"
    "policy_router_input_schema.json"
    "validator_output_schema.json"
)

MISSING_ASSETS=0
for asset in "${REQUIRED_POLICY_ASSETS[@]}"; do
    target_file="${POLICY_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] Policy asset missing: ${asset}"
        MISSING_ASSETS=1
    elif ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Policy asset is corrupted or invalid JSON: ${asset}"
        MISSING_ASSETS=1
    fi
done

for asset in "${REQUIRED_SCHEMA_ASSETS[@]}"; do
    target_file="${SCHEMA_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] Schema asset missing: ${asset}"
        MISSING_ASSETS=1
    elif ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Schema asset is corrupted or invalid JSON: ${asset}"
        MISSING_ASSETS=1
    fi
done

if [ "${MISSING_ASSETS}" -ne 0 ]; then
    echo "  [FATAL] Phase 0 synced assets are incomplete."
    echo "          Please ensure the artifact sync utility completed successfully."
    exit 1
fi
echo "  [OK] All 8 required Phase 0 synced assets are present and valid."

# 5. 시간 동기화(Time Sync) 오프셋 측정 및 로깅
echo "  [INFO] Measuring Time Sync Offset and Network Jitter..."

LOG_DIR="${WORKSPACE_DIR}/logs"
mkdir -p "${LOG_DIR}"
TIME_LOG_FILE="${LOG_DIR}/time_sync_verification.log"
POLICY_FILE="${POLICY_DIR}/policy_table.json"

# [보완 반영] 구조 확정 전 대비 보수적 fallback 및 명시적 메시지 출력
FRESHNESS_LIMIT=$(jq -r '.global_constraints.freshness_threshold_ms // 100' "${POLICY_FILE}" 2>/dev/null || echo "100")
echo "  [INFO] Target Freshness Threshold: ${FRESHNESS_LIMIT} ms (Fallback applied if undefined)" | tee -a "${TIME_LOG_FILE}"

# 네트워크 지터(Jitter) 측정을 위해 Ping RTT 추출
PING_OUT=$(ping -c 5 -q "${TARGET_HOST}" | tail -n 1 || echo "")
if [[ "${PING_OUT}" == *"/"* ]]; then
    AVG_RTT=$(printf '%s' "${PING_OUT}" | awk -F'/' '{print $5}')
    MAX_RTT=$(printf '%s' "${PING_OUT}" | awk -F'/' '{print $6}')
    echo "  [INFO] Network RTT to Mac mini (Avg/Max): ${AVG_RTT} ms / ${MAX_RTT} ms" | tee -a "${TIME_LOG_FILE}"
else
    echo "  [WARNING] Could not parse ping RTT statistics." | tee -a "${TIME_LOG_FILE}"
fi

# 실제 Time Offset (ms) 추출 로직
OFFSET_MS="N/A"
if command -v chronyc >/dev/null 2>&1; then
    # [수정 반영 3] 기존 동결본 해석에 맞춰 System time offset인 4번째 필드($4)로 올바르게 참조
    RAW_OFFSET=$(chronyc -c tracking 2>/dev/null | awk -F',' '{print $4}' || echo "0")
    OFFSET_MS=$(awk -v off="${RAW_OFFSET}" 'BEGIN {printf "%.3f", sqrt(off*off) * 1000}')
    echo "  [INFO] Chrony System Time Offset: ${OFFSET_MS} ms" | tee -a "${TIME_LOG_FILE}"
elif command -v timedatectl >/dev/null 2>&1 && timedatectl timesync-status >/dev/null 2>&1; then
    RAW_OFFSET=$(timedatectl timesync-status 2>/dev/null | grep -i "Offset:" | awk '{print $2}' || echo "0")
    OFFSET_MS=$(printf '%s' "${RAW_OFFSET}" | sed 's/[a-zA-Z]*//g' | awk '{printf "%.3f", sqrt($1*$1)}')
    echo "  [INFO] systemd-timesyncd Offset: ${OFFSET_MS} ms" | tee -a "${TIME_LOG_FILE}"
else
    # [수정 반영 4] 프로젝트 표준에 맞춰 [WARN]을 [WARNING]으로 통일
    echo "  [WARNING] Neither 'chronyc' nor 'systemd-timesyncd' is available. Offset measurement skipped." | tee -a "${TIME_LOG_FILE}"
fi

# Stale Margin 여유폭(Margin) 경고 처리 (Hard Fail 대신 Warning)
if [ "${OFFSET_MS}" != "N/A" ]; then
    MARGIN_CHECK=$(awk -v off="${OFFSET_MS}" -v lim="${FRESHNESS_LIMIT}" 'BEGIN { if(off > lim/2) print "WARNING"; else print "OK" }')
    if [ "${MARGIN_CHECK}" = "WARNING" ]; then
        echo "  [WARNING] Time offset (${OFFSET_MS} ms) is consuming >50% of the freshness threshold (${FRESHNESS_LIMIT} ms)!"
        echo "            Caution: Stale fault injection results might become flaky due to narrow margin."
    else
        echo "  [OK] Time offset is well within the acceptable stale margin."
    fi
fi

echo "==> [PASS] Raspberry Pi 5 Base Runtime and Communication verification successful."
