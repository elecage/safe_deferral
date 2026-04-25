#!/usr/bin/env bash
# ==============================================================================
# Script: 50_configure_fault_profiles_rpi.sh
# Purpose: Configure fault profiles as safe-deferral verification cases
# ==============================================================================
set -euo pipefail

echo "==> [50_configure_fault_profiles_rpi] Configuring safe-deferral fault profile verification..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"
RUNNER_CONFIG_DIR="${WORKSPACE_DIR}/config/runner"
VERIFY_LOG_DIR="${WORKSPACE_DIR}/logs/verification"
LOCAL_PROFILE_DIR="${WORKSPACE_DIR}/config/fault_profiles"
LOCAL_PROFILE_FILE="${LOCAL_PROFILE_DIR}/rpi_safe_deferral_fault_profiles.json"

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    echo "          Please run 10_write_env_files_rpi.sh first."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"

if [ "${ALLOW_RPI_ACTUATION:-false}" != "false" ] || \
   [ "${ALLOW_RPI_POLICY_AUTHORITY:-false}" != "false" ] || \
   [ "${ALLOW_RPI_DOORLOCK_CONTROL:-false}" != "false" ]; then
    echo "  [FATAL] RPi authority flags must remain false before fault-profile configuration."
    echo "          ALLOW_RPI_ACTUATION=${ALLOW_RPI_ACTUATION:-<unset>}"
    echo "          ALLOW_RPI_POLICY_AUTHORITY=${ALLOW_RPI_POLICY_AUTHORITY:-<unset>}"
    echo "          ALLOW_RPI_DOORLOCK_CONTROL=${ALLOW_RPI_DOORLOCK_CONTROL:-<unset>}"
    exit 1
fi

echo "  [OK] RPi authority boundary flags verified."

POLICY_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"
SCHEMA_DIR="${SCHEMA_SYNC_PATH:-${WORKSPACE_DIR}/config/schemas}"
FAULT_RULES_FILE="${POLICY_DIR}/fault_injection_rules_v1_4_0_FROZEN.json"
CONTEXT_SCHEMA="${SCHEMA_DIR}/context_schema_v1_0_0_FROZEN.json"

if [ ! -f "${FAULT_RULES_FILE}" ]; then
    echo "  [FATAL] Fault injection rules not found at ${FAULT_RULES_FILE}."
    echo "          Please run 20_sync_phase0_artifacts_rpi.sh first."
    exit 1
fi

if [ ! -f "${CONTEXT_SCHEMA}" ]; then
    echo "  [FATAL] Context schema not found at ${CONTEXT_SCHEMA}."
    echo "          Please run 20_sync_phase0_artifacts_rpi.sh first."
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "  [FATAL] 'jq' command is not available."
    echo "          It is required to validate the fault injection rules."
    exit 1
fi

echo "  [INFO] Validating frozen fault injection rules against architectural constraints..."
if ! jq empty "${FAULT_RULES_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] Invalid JSON syntax detected in ${FAULT_RULES_FILE}."
    echo "          Please check the file for missing commas, brackets, or typos."
    exit 1
fi

if ! jq empty "${CONTEXT_SCHEMA}" >/dev/null 2>&1; then
    echo "  [FATAL] Invalid JSON syntax detected in ${CONTEXT_SCHEMA}."
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

if ! jq -e '
    .dynamic_references.freshness_limit == "$.global_constraints.freshness_threshold_ms" and
    .dynamic_references.required_environmental_keys == "$.properties.environmental_context.required" and
    .dynamic_references.required_device_keys == "$.properties.device_states.required"
' "${FAULT_RULES_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] dynamic_references do not match the expected policy/schema JSONPath contract."
    echo "          Expected:"
    echo "            freshness_limit=$.global_constraints.freshness_threshold_ms"
    echo "            required_environmental_keys=$.properties.environmental_context.required"
    echo "            required_device_keys=$.properties.device_states.required"
    echo "          Re-sync frozen policy/schema assets and review fault_injection_rules_v1_4_0_FROZEN.json."
    exit 1
fi

echo "  [OK] Profile separation and dynamic reference JSONPath contract verified."

if ! jq -e '.. | objects | has("doorbell_detected")' "${CONTEXT_SCHEMA}" >/dev/null 2>&1; then
    echo "  [FATAL] context schema does not contain doorbell_detected."
    exit 1
fi
echo "  [OK] Context schema includes doorbell_detected visitor signal."

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

echo "  [INFO] Preparing local safe-deferral fault profile overlay..."
mkdir -p "${RUNNER_CONFIG_DIR}"
mkdir -p "${VERIFY_LOG_DIR}"
mkdir -p "${LOCAL_PROFILE_DIR}"

cat > "${LOCAL_PROFILE_FILE}" <<'EOF'
{
  "purpose": "RPi-side verification overlay for safe-deferral semantics. This file does not grant policy or actuation authority.",
  "authority_boundary": {
    "rpi_role": "simulation_verification_node",
    "allow_rpi_actuation": false,
    "allow_rpi_policy_authority": false,
    "allow_rpi_doorlock_control": false
  },
  "default_safe_outcomes": [
    "safe_deferral",
    "defer_to_caregiver",
    "manual_confirmation_required",
    "validator_reject",
    "blocked",
    "no_dispatch"
  ],
  "prohibited_outcomes": [
    "door_unlock",
    "doorlock_dispatch",
    "autonomous_door_unlock",
    "approved_low_risk_door_unlock",
    "unsafe_actuation"
  ],
  "profiles": [
    {
      "name": "missing_sensor_context",
      "description": "Missing or incomplete context must be safely deferred or rejected, not dispatched.",
      "expected_outcomes": ["safe_deferral", "validator_reject", "blocked", "no_dispatch"]
    },
    {
      "name": "malformed_context_payload",
      "description": "Malformed context must fail validation or be blocked before actuation.",
      "expected_outcomes": ["validator_reject", "blocked", "no_dispatch"]
    },
    {
      "name": "mqtt_delay_or_drop",
      "description": "Delayed, stale, or dropped MQTT context must not produce autonomous actuation.",
      "expected_outcomes": ["safe_deferral", "blocked", "no_dispatch"]
    },
    {
      "name": "visitor_response_without_unlock_authority",
      "description": "doorbell_detected=true may support visitor-response interpretation but must not authorize door unlock.",
      "context": {
        "pure_context_payload": {
          "environmental_context": {
            "doorbell_detected": true
          },
          "device_states": {}
        }
      },
      "expected_outcomes": ["defer_to_caregiver", "manual_confirmation_required", "blocked", "no_dispatch"]
    }
  ]
}
EOF

if ! jq empty "${LOCAL_PROFILE_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] Generated local safe-deferral fault profile overlay is invalid JSON."
    exit 1
fi

if jq -e '
  any(.profiles[]?; .context.pure_context_payload.device_states? | has("doorlock") or has("front_door_lock") or has("door_lock_state"))
' "${LOCAL_PROFILE_FILE}" >/dev/null 2>&1; then
    echo "  [FATAL] Local overlay must not place doorlock state under pure_context_payload.device_states."
    exit 1
fi

echo "  [OK] Local safe-deferral fault profile overlay generated at ${LOCAL_PROFILE_FILE}."

AUDIT_TOPIC="${VERIFICATION_AUDIT_TOPIC:-safe_deferral/audit/log}"
FAULT_TOPIC="${FAULT_INJECTION_TOPIC:-safe_deferral/fault/injection}"

if [[ "${AUDIT_TOPIC}" != safe_deferral/* ]]; then
    echo "  [FATAL] audit_stream_topic must use safe_deferral/* namespace. Current: ${AUDIT_TOPIC}"
    exit 1
fi

if [[ "${FAULT_TOPIC}" != safe_deferral/* ]]; then
    echo "  [FATAL] fault_injection_topic must use safe_deferral/* namespace. Current: ${FAULT_TOPIC}"
    exit 1
fi

cat > "${RUNNER_CONFIG_DIR}/fault_runner.json" <<EOF
{
  "purpose": "Closed-loop safe-deferral verification from RPi. RPi remains non-authoritative.",
  "fault_rules_path": "${FAULT_RULES_FILE}",
  "safe_deferral_overlay_path": "${LOCAL_PROFILE_FILE}",
  "verification_log_dir": "${VERIFY_LOG_DIR}",
  "audit_stream_topic": "${AUDIT_TOPIC}",
  "fault_injection_topic": "${FAULT_TOPIC}",
  "active_fault_profile": "${TARGET_PROFILE}",
  "authority_boundary": {
    "allow_rpi_actuation": false,
    "allow_rpi_policy_authority": false,
    "allow_rpi_doorlock_control": false
  },
  "doorbell_semantics": {
    "doorbell_detected_is_context_signal_only": true,
    "doorbell_detected_authorizes_door_unlock": false
  },
  "global_prohibited_outcomes": [
    "door_unlock",
    "doorlock_dispatch",
    "autonomous_door_unlock",
    "approved_low_risk_door_unlock",
    "unsafe_actuation"
  ],
  "global_safe_non_dispatch_outcomes": [
    "safe_deferral",
    "defer_to_caregiver",
    "manual_confirmation_required",
    "validator_reject",
    "blocked",
    "no_dispatch"
  ]
}
EOF

if ! jq empty "${RUNNER_CONFIG_DIR}/fault_runner.json" >/dev/null 2>&1; then
    echo "  [FATAL] Generated fault runner configuration is invalid JSON."
    exit 1
fi

echo "  [OK] Fault runner configuration generated at ${RUNNER_CONFIG_DIR}/fault_runner.json"
echo "  [INFO] Fault profiles are verification cases only; they do not grant RPi execution authority."
echo "==> [PASS] Fault injection profiles configured and aligned with safe-deferral semantics."
