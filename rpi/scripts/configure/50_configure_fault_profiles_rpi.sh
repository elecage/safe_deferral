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

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    echo "          Please run 10_write_env_files_rpi.sh first."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"

POLICY_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"
FAULT_RULES_FILE="${POLICY_DIR}/fault_injection_rules_v1_4_0_FROZEN.json"

if [ ! -f "${FAULT_RULES_FILE}" ]; then
    echo "  [FATAL] Fault injection rules not found at ${FAULT_RULES_FILE}."
    echo "          Please run 20_sync_phase0_artifacts_rpi.sh first."
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "  [FATAL] 'jq' command is not available."
    echo "          It is required to validate the fault injection rules."
    exit 1
fi

echo "  [INFO] Validating fault injection rules against architectural constraints..."
if ! jq empty "${FAULT_RULES_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] Invalid JSON syntax detected in ${FAULT_RULES_FILE}."
    echo "          Please check the file for missing commas, brackets, or typos."
    exit 1
fi

if ! jq -e '.deterministic_profiles | type == "object" and length > 0' "${FAULT_RULES_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] 'deterministic_profiles' must be a non-empty object."
    exit 1
fi

if ! jq -e '.randomized_stress_profile | type == "object" and length > 0' "${FAULT_RULES_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] 'randomized_stress_profile' must be a non-empty object."
    exit 1
fi

if ! jq -e '.dynamic_references | type == "object" and length > 0' "${FAULT_RULES_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] Top-level 'dynamic_references' must be a non-empty object."
    exit 1
fi

echo "  [OK] Profile separation and top-level dynamic references verified."

HAS_VALID_SAFE_OUTCOMES=$(jq '[.deterministic_profiles[] | ((has("allowed_safe_outcomes") and (.allowed_safe_outcomes | type == "array" and length > 0)) or (has("expected_outcome") and (.expected_outcome | type == "string" and length > 0)))] | all' "${FAULT_RULES_FILE}")
if [ "${HAS_VALID_SAFE_OUTCOMES}" != "true" ]; then
    echo "  [FATAL] One or more deterministic profiles lack a valid expected safe outcome definition."
    exit 1
fi
echo "  [OK] Deterministic profiles include valid expected safe outcome definitions."

TARGET_PROFILE="${FAULT_PROFILE:-FAULT_STALENESS_01}"
if [ "${TARGET_PROFILE}" = "randomized_stress_profile" ]; then
    PROFILE_EXISTS=$(jq -e 'has("randomized_stress_profile")' "${FAULT_RULES_FILE}" >/dev/null 2>&1 && echo true || echo false)
else
    PROFILE_EXISTS=$(jq -r --arg prof "${TARGET_PROFILE}" '.deterministic_profiles | has($prof)' "${FAULT_RULES_FILE}")
fi

if [ "${PROFILE_EXISTS}" != "true" ]; then
    echo "  [FATAL] Active fault profile '${TARGET_PROFILE}' not found in ${FAULT_RULES_FILE}."
    echo "          Please ensure FAULT_PROFILE in .env matches an existing deterministic profile key or 'randomized_stress_profile'."
    exit 1
fi
echo "  [OK] Target active profile '${TARGET_PROFILE}' mapped successfully."

echo "  [INFO] Preparing closed-loop verification environment..."
mkdir -p "${RUNNER_CONFIG_DIR}"
mkdir -p "${VERIFY_LOG_DIR}"

cat <<EOF > "${RUNNER_CONFIG_DIR}/fault_runner.json"
{
    "fault_rules_path": "${FAULT_RULES_FILE}",
    "verification_log_dir": "${VERIFY_LOG_DIR}",
    "audit_stream_topic": "${VERIFICATION_AUDIT_TOPIC:-smarthome/audit/validator_output}",
    "active_fault_profile": "${TARGET_PROFILE}"
}
EOF

echo "  [OK] Fault runner configuration generated at ${RUNNER_CONFIG_DIR}/fault_runner.json"
echo "==> [PASS] Fault injection profiles configured and verified successfully."
