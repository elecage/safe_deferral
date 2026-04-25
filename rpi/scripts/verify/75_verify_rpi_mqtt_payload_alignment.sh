#!/usr/bin/env bash
# ==============================================================================
# Script: 75_verify_rpi_mqtt_payload_alignment.sh
# Purpose: Verify RPi MQTT registry and payload contract alignment
# ==============================================================================
set -euo pipefail

echo "==> [75_verify_rpi_mqtt_payload_alignment] Verifying MQTT/payload alignment..."

if ! command -v jq >/dev/null 2>&1; then
    echo "  [FATAL] 'jq' command is required for MQTT/payload alignment verification."
    exit 1
fi

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    echo "          Please run rpi/scripts/configure/10_write_env_files_rpi.sh first."
    exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"

MQTT_DIR="${MQTT_REGISTRY_SYNC_PATH:-${WORKSPACE_DIR}/config/mqtt}"
PAYLOAD_DIR="${PAYLOAD_EXAMPLES_SYNC_PATH:-${WORKSPACE_DIR}/config/payloads}"
SCHEMA_DIR="${SCHEMA_SYNC_PATH:-${WORKSPACE_DIR}/config/schemas}"

TOPIC_REGISTRY="${MQTT_DIR}/topic_registry_v1_0_0.json"
PUBSUB_MATRIX="${MQTT_DIR}/publisher_subscriber_matrix_v1_0_0.md"
TOPIC_CONTRACTS="${MQTT_DIR}/topic_payload_contracts_v1_0_0.md"
CONTEXT_SCHEMA="${SCHEMA_DIR}/context_schema_v1_0_0_FROZEN.json"

FAILURES=0

require_file() {
    local label="$1"
    local file_path="$2"

    if [ ! -f "${file_path}" ]; then
        echo "  [FATAL] Missing ${label}: ${file_path}"
        FAILURES=1
    else
        echo "  [OK] Found ${label}: ${file_path}"
    fi
}

require_dir() {
    local label="$1"
    local dir_path="$2"

    if [ ! -d "${dir_path}" ]; then
        echo "  [FATAL] Missing ${label}: ${dir_path}"
        FAILURES=1
    else
        echo "  [OK] Found ${label}: ${dir_path}"
    fi
}

require_dir "MQTT registry directory" "${MQTT_DIR}"
require_dir "payload examples directory" "${PAYLOAD_DIR}"
require_dir "schema directory" "${SCHEMA_DIR}"

require_file "topic registry" "${TOPIC_REGISTRY}"
require_file "publisher/subscriber matrix" "${PUBSUB_MATRIX}"
require_file "topic-payload contract document" "${TOPIC_CONTRACTS}"
require_file "context schema" "${CONTEXT_SCHEMA}"

if [ "${FAILURES}" -ne 0 ]; then
    echo "==> [FAIL] Required MQTT/payload alignment assets are missing."
    exit 1
fi

echo "  [INFO] Validating JSON syntax for registry/schema assets..."
if ! jq empty "${TOPIC_REGISTRY}" >/dev/null 2>&1; then
    echo "  [FATAL] Invalid JSON syntax: ${TOPIC_REGISTRY}"
    FAILURES=1
else
    echo "  [OK] Topic registry JSON is valid."
fi

if ! jq empty "${CONTEXT_SCHEMA}" >/dev/null 2>&1; then
    echo "  [FATAL] Invalid JSON syntax: ${CONTEXT_SCHEMA}"
    FAILURES=1
else
    echo "  [OK] Context schema JSON is valid."
fi

echo "  [INFO] Checking safe_deferral topic namespace presence..."
if ! grep -RIn 'safe_deferral/' "${MQTT_DIR}" >/tmp/rpi_safe_deferral_topic_hits_$$.txt 2>/dev/null; then
    echo "  [FATAL] No safe_deferral/* topic references found in MQTT registry artifacts."
    FAILURES=1
else
    echo "  [OK] safe_deferral/* topic references found in MQTT registry artifacts."
fi
rm -f /tmp/rpi_safe_deferral_topic_hits_$$.txt

echo "  [INFO] Checking local .env topic namespace alignment..."
if [ "${TOPIC_NAMESPACE:-}" != "safe_deferral" ]; then
    echo "  [FATAL] TOPIC_NAMESPACE must be 'safe_deferral'. Current: '${TOPIC_NAMESPACE:-<unset>}'"
    FAILURES=1
else
    echo "  [OK] TOPIC_NAMESPACE is safe_deferral."
fi

REQUIRED_TOPIC_ENV_KEYS=(
    "SIM_CONTEXT_TOPIC"
    "FAULT_INJECTION_TOPIC"
    "VERIFICATION_AUDIT_TOPIC"
    "VALIDATOR_OUTPUT_TOPIC"
    "EXPERIMENT_PROGRESS_TOPIC"
    "EXPERIMENT_RESULT_TOPIC"
    "DASHBOARD_OBSERVATION_TOPIC"
)

for key in "${REQUIRED_TOPIC_ENV_KEYS[@]}"; do
    value="${!key:-}"
    if [ -z "${value}" ]; then
        echo "  [FATAL] ${key} is unset."
        FAILURES=1
    elif [[ "${value}" != safe_deferral/* ]]; then
        echo "  [FATAL] ${key} must use safe_deferral/* namespace. Current: ${value}"
        FAILURES=1
    else
        echo "  [OK] ${key}=${value}"
    fi
done

echo "  [INFO] Checking for legacy smarthome/* topic namespace drift..."
LEGACY_HITS="$(grep -RIn 'smarthome/' "${MQTT_DIR}" "${ENV_FILE}" 2>/dev/null || true)"
if [ -n "${LEGACY_HITS}" ]; then
    echo "  [FATAL] Legacy smarthome/* topic references detected:"
    printf '%s\n' "${LEGACY_HITS}" | sed 's/^/    /'
    FAILURES=1
else
    echo "  [OK] No legacy smarthome/* topic references detected in MQTT artifacts or .env."
fi

echo "  [INFO] Checking context schema for required doorbell context signal..."
if ! jq -e '.. | objects | has("doorbell_detected")' "${CONTEXT_SCHEMA}" >/dev/null 2>&1; then
    echo "  [FATAL] context schema does not contain doorbell_detected."
    FAILURES=1
else
    echo "  [OK] context schema contains doorbell_detected."
fi

echo "  [INFO] Validating payload example JSON files..."
PAYLOAD_JSON_COUNT=0
while IFS= read -r -d '' payload_file; do
    PAYLOAD_JSON_COUNT=$((PAYLOAD_JSON_COUNT + 1))
    if ! jq empty "${payload_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Invalid payload example JSON: ${payload_file}"
        FAILURES=1
    fi
done < <(find "${PAYLOAD_DIR}" -type f -name "*.json" -print0)

if [ "${PAYLOAD_JSON_COUNT}" -eq 0 ]; then
    echo "  [WARNING] No *.json payload examples found under ${PAYLOAD_DIR}."
else
    echo "  [OK] Validated ${PAYLOAD_JSON_COUNT} JSON payload example file(s)."
fi

echo "  [INFO] Checking payload examples for doorbell_detected representation..."
if grep -RIn '"doorbell_detected"' "${PAYLOAD_DIR}" >/tmp/rpi_doorbell_payload_hits_$$.txt 2>/dev/null; then
    echo "  [OK] payload examples include doorbell_detected."
else
    echo "  [WARNING] payload examples do not include doorbell_detected. Schema contains it, but example coverage should be reviewed."
fi
rm -f /tmp/rpi_doorbell_payload_hits_$$.txt

echo "  [INFO] Checking for prohibited doorlock state fields under pure_context_payload.device_states..."
DOORLOCK_STATE_VIOLATIONS="$(find "${PAYLOAD_DIR}" -type f -name "*.json" -print0 | xargs -0 jq -r '
    def paths_to_strings:
      paths(scalars) | map(tostring) | join(".");
    select(
      .pure_context_payload.device_states? != null and
      (
        .pure_context_payload.device_states | has("doorlock") or
        .pure_context_payload.device_states | has("front_door_lock") or
        .pure_context_payload.device_states | has("door_lock_state")
      )
    )
    | input_filename
' 2>/dev/null | sort -u || true)"

if [ -n "${DOORLOCK_STATE_VIOLATIONS}" ]; then
    echo "  [FATAL] Doorlock state fields found under pure_context_payload.device_states:"
    printf '%s\n' "${DOORLOCK_STATE_VIOLATIONS}" | sed 's/^/    /'
    FAILURES=1
else
    echo "  [OK] No doorlock state fields found under pure_context_payload.device_states."
fi

echo "  [INFO] Checking for doorlock-sensitive terms outside prohibited state paths..."
DOORLOCK_TERM_HITS="$(grep -RInE '"(doorlock|front_door_lock|door_lock_state)"|door_unlock|doorlock_dispatch|autonomous_door_unlock' "${PAYLOAD_DIR}" "${MQTT_DIR}" 2>/dev/null || true)"
if [ -n "${DOORLOCK_TERM_HITS}" ]; then
    echo "  [WARNING] Doorlock-sensitive terms found. Confirm these are blocked/escalated sensitive-action cases only:"
    printf '%s\n' "${DOORLOCK_TERM_HITS}" | sed 's/^/    /'
else
    echo "  [OK] No doorlock-sensitive terms found in MQTT/payload reference assets."
fi

if [ "${FAILURES}" -ne 0 ]; then
    echo "==> [FAIL] MQTT/payload alignment verification failed."
    exit 1
fi

echo "==> [PASS] MQTT registry and payload contract alignment verification successful."
