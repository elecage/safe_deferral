#!/usr/bin/env bash
# ==============================================================================
# Script: 50_configure_fault_profiles_rpi.sh
# Purpose: Configure Fault Injection Profiles & Verification Engine (Phase 4)
# ==============================================================================
set -euo pipefail

echo "==> [50_configure_fault_profiles_rpi] Configuring Fault Injection Profiles..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"
RUNNER_CONFIG_DIR="${WORKSPACE_DIR}/config/runner"
VERIFY_LOG_DIR="${WORKSPACE_DIR}/logs/verification"

# 1. 환경변수 파일 검증 및 로드
if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    echo "          Please run 10_write_env_files_rpi.sh first."
    exit 1
fi
source "${ENV_FILE}"

POLICY_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"
FAULT_RULES_FILE="${POLICY_DIR}/fault_injection_rules.json"

# 2. Phase 0 동결 자산 존재 여부 확인 (SSOT 원칙)
if [ ! -f "${FAULT_RULES_FILE}" ]; then
    echo "  [FATAL] Fault injection rules not found at ${FAULT_RULES_FILE}."
    echo "          Please run 20_sync_phase0_artifacts_rpi.sh first."
    exit 1
fi

# 3. jq 명령어 존재 여부 확인
if ! command -v jq >/dev/null 2>&1; then
    echo "  [FATAL] 'jq' command is not available."
    echo "          It is required to validate the fault injection rules."
    exit 1
fi

echo "  [INFO] Validating fault injection rules against architectural constraints..."

# JSON 문법 자체의 유효성 우선 검증 (불친절한 에러 방지)
if ! jq empty "${FAULT_RULES_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] Invalid JSON syntax detected in ${FAULT_RULES_FILE}."
    echo "          Please check the file for missing commas, brackets, or typos."
    exit 1
fi

# 테스트 프로파일 분리 원칙 및 정확한 타입(Type) 검증
if ! jq -e '.deterministic_profiles | type == "array" and length > 0' "${FAULT_RULES_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] 'deterministic_profiles' must be a non-empty array."
    exit 1
fi

if ! jq -e '.randomized_stress_profile | type == "object" and length > 0' "${FAULT_RULES_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] 'randomized_stress_profile' must be a non-empty object."
    exit 1
fi
echo "  [OK] Profile separation and structural types verified."

# 구조적 규약 준수 여부 검증 (dynamic_references 존재 및 비어있지 않음 엄격 검증)
HAS_VALID_REFS=$(jq '[.deterministic_profiles[] | has("dynamic_references") and (.dynamic_references | type != "null" and length > 0)] | all' "${FAULT_RULES_FILE}")
if [ "${HAS_VALID_REFS}" != "true" ]; then
    echo "  [FATAL] Architectural rule violation detected: one or more deterministic profiles lack a valid, non-empty 'dynamic_references'."
    exit 1
fi

# expected_outcome 존재 및 유효성(비어있지 않은지) 검증
HAS_VALID_OUTCOMES=$(jq '[.deterministic_profiles[] | has("expected_outcome") and (.expected_outcome | type != "null" and length > 0)] | all' "${FAULT_RULES_FILE}")
if [ "${HAS_VALID_OUTCOMES}" != "true" ]; then
    echo "  [FATAL] Verification gap! One or more deterministic profiles lack a valid, non-empty 'expected_outcome'."
    exit 1
fi
echo "  [OK] Structural rules (dynamic_references) and expected outcomes verified."

# [최종 교정 반영] FAULT_PROFILE이 실제 룰 내부에 존재하는지 런타임 사전 정밀 검증
TARGET_PROFILE="${FAULT_PROFILE:-deterministic_01}"
PROFILE_EXISTS=$(jq --arg prof "${TARGET_PROFILE}" '
    if $prof == "randomized_stress_profile" then true
    else ([.deterministic_profiles[] | [.id, .profile_id, .name, .profile_name] | .[] | values] | index($prof) != null)
    end
' "${FAULT_RULES_FILE}")

if [ "${PROFILE_EXISTS}" != "true" ]; then
    echo "  [FATAL] Active fault profile '${TARGET_PROFILE}' not found in ${FAULT_RULES_FILE}."
    echo "          Please ensure FAULT_PROFILE in .env matches an existing profile ID or 'randomized_stress_profile'."
    exit 1
fi
echo "  [OK] Target active profile '${TARGET_PROFILE}' mapped successfully."

# 6. 폐루프 자동 검증(Closed-loop Verification) 실행 환경 준비
echo "  [INFO] Preparing closed-loop verification environment..."
mkdir -p "${RUNNER_CONFIG_DIR}"
mkdir -p "${VERIFY_LOG_DIR}"

cat <<EOF > "${RUNNER_CONFIG_DIR}/fault_runner.json"
{
    "fault_rules_path": "${FAULT_RULES_FILE}",
    "verification_log_dir": "${VERIFY_LOG_DIR}",
    "audit_stream_topic": "${VERIFICATION_AUDIT_TOPIC:-audit/log/#}",
    "active_fault_profile": "${TARGET_PROFILE}"
}
EOF
echo "  [OK] Fault runner configuration generated at ${RUNNER_CONFIG_DIR}/fault_runner.json"

echo "==> [PASS] Fault injection profiles configured and verified successfully."
