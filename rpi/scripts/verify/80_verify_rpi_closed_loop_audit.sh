#!/usr/bin/env bash
# ==============================================================================
# Script: 80_verify_rpi_closed_loop_audit.sh
# Purpose: Verify Closed-loop Assessment of Fault Injection (Phase 5)
# ==============================================================================
set -euo pipefail

echo "==> [80_verify_rpi_closed_loop_audit] Verifying Closed-loop Safety Assessment..."

# 1. 필수 명령어 존재 여부 확인 (Fail-fast)
# [수정 반영 4] SQLite 필수 의존성 제거 (RPi는 MQTT Audit Stream만으로 폐루프 검증 수행)
if ! command -v jq >/dev/null 2>&1 || ! command -v mosquitto_pub >/dev/null 2>&1 || ! command -v mosquitto_sub >/dev/null 2>&1; then
    echo "  [FATAL] Required tools (jq, mosquitto-clients) are missing."
    echo "          Please ensure they are installed to run the closed-loop assessment."
    exit 1
fi
echo "  [OK] Required CLI tools verified."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

# 2. 환경변수 및 동결 자산 경로 로드
if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"

TARGET_HOST="${MQTT_HOST:-127.0.0.1}"
TARGET_PORT="${MQTT_PORT:-1883}"
POLICY_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"
FAULT_RULES_FILE="${POLICY_DIR}/fault_injection_rules.json"

if [ ! -f "${FAULT_RULES_FILE}" ]; then
    echo "  [FATAL] Fault injection rules not found at ${FAULT_RULES_FILE}."
    exit 1
fi

# [수정 반영 2] MQTT 인증 옵션 반영 (인증형 브로커 대응)
AUTH_ARGS=()
if [ -n "${MQTT_USER:-}" ] && [ -n "${MQTT_PASS:-}" ]; then
    AUTH_ARGS=("-u" "${MQTT_USER}" "-P" "${MQTT_PASS}")
fi

# 3. 동결 자산 기반 동적 검증 (단일 프로파일 선택)
echo "  [INFO] Parsing deterministic fault profile from frozen assets..."

# [수정 반영 1] .env의 FAULT_PROFILE 또는 ACTIVE_FAULT_PROFILE 변수를 통해 단일 프로파일 타겟팅
TARGET_PROFILE="${ACTIVE_FAULT_PROFILE:-${FAULT_PROFILE:-FAULT_MISSING_CONTEXT_01}}"

# jq를 사용하여 object 내 key 매칭 또는 array 내 ID 매칭으로 단일 프로파일 추출
FAULT_PROFILE=$(jq -c --arg profile "${TARGET_PROFILE}" '
  .deterministic_profiles | 
  if type == "object" then .[$profile] 
  else .[] | select(.profile_name == $profile or .profile_id == $profile or .id == $profile) end 
  // empty
' "${FAULT_RULES_FILE}")

if [ -z "${FAULT_PROFILE}" ]; then
    echo "  [FATAL] Target profile '${TARGET_PROFILE}' not found in ${FAULT_RULES_FILE}."
    exit 1
fi

FAULT_TYPE=$(echo "${FAULT_PROFILE}" | jq -r '.fault_type // "missing_sensor"')
echo "  [INFO] Selected Fault Profile: ${TARGET_PROFILE} (Type: ${FAULT_TYPE})"

# 4. 폐루프 자동 판정 (Closed-loop Assessment) 준비
# [수정 반영 3] 하드코딩 제거: .env 또는 config 기반의 Audit Topic 설정 반영
AUDIT_TOPIC="${VERIFICATION_AUDIT_TOPIC:-smarthome/audit/validator_output}"
INJECT_TOPIC="${INJECT_TOPIC:-smarthome/context/raw}"
CORRELATION_ID="fi_test_$(date +%s)_$$"
LOG_FILE="/tmp/audit_result_$$.log"

echo "  [INFO] Starting background MQTT subscriber on '${AUDIT_TOPIC}' (Timeout: 5s)..."
# [수정 반영 2] mosquitto_sub에도 AUTH_ARGS 적용
mosquitto_sub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${AUDIT_TOPIC}" -W 5 > "${LOG_FILE}" 2>/dev/null &
SUB_PID=$!

# Subscriber 연결 대기
sleep 1

# 5. 결함 페이로드 생성 및 주입 (Fault Injection)
echo "  [INFO] Injecting fault payload with Correlation ID: ${CORRELATION_ID}..."
FAULT_PAYLOAD=$(jq -n \
    --arg cid "${CORRELATION_ID}" \
    --arg ftype "${FAULT_TYPE}" \
    '{
        "source_node_id": "rpi5_fault_injector",
        "routing_metadata": { "audit_correlation_id": $cid, "network_status": "online", "injected_fault": $ftype },
        "pure_context_payload": { "environmental_context": {}, "device_states": {} }
    }')

# [수정 반영 2] mosquitto_pub에도 AUTH_ARGS 적용
mosquitto_pub -h "${TARGET_HOST}" -p "${TARGET_PORT}" "${AUTH_ARGS[@]}" -t "${INJECT_TOPIC}" -m "${FAULT_PAYLOAD}"

# 안전 파이프라인 처리 후 Subscriber가 종료될 때까지 대기
wait "${SUB_PID}" || true

# 6. 결과 판독 (MQTT 로그 스트림)
ROUTING_RESULT="UNKNOWN"
if grep -q "${CORRELATION_ID}" "${LOG_FILE}"; then
    # 상관관계 ID가 일치하는 로그에서 최종 라우팅 타겟 추출
    ROUTING_RESULT=$(jq -r "select(.audit_correlation_id == \"${CORRELATION_ID}\") | .routing_target" "${LOG_FILE}" | tail -n 1)
fi
rm -f "${LOG_FILE}"

echo "  [INFO] Observed Routing Target: ${ROUTING_RESULT}"

if [ "${ROUTING_RESULT}" = "UNKNOWN" ] || [ -z "${ROUTING_RESULT}" ]; then
    echo "  [FATAL] No audit trace found for injected fault. The safety pipeline may be unresponsive."
    exit 1
fi

# 7. 최종 단언 (Assertion)
# [수정 반영 5] 공백 분리가 아닌 jq 배열 정규화를 통한 정확한 결과 매칭 (Robust Array Comparison)
IS_PROHIBITED=$(echo "${FAULT_PROFILE}" | jq -r --arg res "${ROUTING_RESULT}" '
  (.prohibited_outcome // .prohibited_outcomes // []) | 
  if type == "array" then (index($res) != null) 
  elif type == "string" then (. == $res) 
  else false end
')

IS_EXPECTED=$(echo "${FAULT_PROFILE}" | jq -r --arg res "${ROUTING_RESULT}" '
  (.expected_outcome // .allowed_safe_outcomes // []) | 
  if type == "array" then (index($res) != null) 
  elif type == "string" then (. == $res) 
  else false end
')

# 7-1. 금지 귀결(Prohibited) 검사 - Sentinel 방식
if [ "${IS_PROHIBITED}" = "true" ]; then
    echo "  [FATAL] System triggered PROHIBITED outcome: '${ROUTING_RESULT}'!"
    echo "          UNSAFE ACTUATION (UAR) occurred. Fault injection defense FAILED."
    exit 1
fi

# 7-2. 기대 귀결(Expected) 검사
if [ "${IS_EXPECTED}" = "true" ]; then
    echo "  [OK] System safely resolved the fault into expected outcome: '${ROUTING_RESULT}'"
    echo "==> [PASS] Closed-loop Safety Audit verification successful. The Smart Home is SAFE."
else
    echo "  [WARNING] Outcome '${ROUTING_RESULT}' is neither expected nor strictly prohibited."
    echo "            Please review fault_injection_rules_v1_4_0_FROZEN.json."
    exit 1
fi
