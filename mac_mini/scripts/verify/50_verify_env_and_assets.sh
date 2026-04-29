#!/usr/bin/env bash
# ==============================================================================
# Script: 50_verify_env_and_assets.sh
# Purpose: Verify essential environment variables and deployed runtime assets
# ==============================================================================
set -euo pipefail

echo "==> [50_verify_env_and_assets] Verifying environment variables and runtime assets..."

if ! command -v jq >/dev/null 2>&1; then
    echo "  [FATAL] 'jq' command is not available."
    echo "          Please ensure the jq package is installed for JSON validation."
    exit 1
fi

VENV_PYTHON="${HOME}/smarthome_workspace/.venv-mac/bin/python"
if [ ! -x "${VENV_PYTHON}" ]; then
    echo "  [FATAL] Mac mini venv not found at ${VENV_PYTHON}."
    echo "          Please run mac_mini/scripts/install/30_setup_python_venv_mac.sh first."
    exit 1
fi

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [FATAL] .env file not found at ${ENV_FILE}."
    echo "          Please run the environment configuration step first."
    exit 1
fi
echo "  [OK] ${ENV_FILE} exists."

# shellcheck disable=SC1090
source "${ENV_FILE}"
echo "  [OK] Environment variables loaded from ${ENV_FILE}."

echo "  [INFO] Checking essential environment variables..."
REQUIRED_VARS=(
    "MQTT_HOST"
    "MQTT_PORT"
    "OLLAMA_HOST"
    "SQLITE_PATH"
    "POLICY_DIR"
    "SCHEMA_DIR"
    "MQTT_REGISTRY_DIR"
    "PAYLOAD_EXAMPLES_DIR"
)

MISSING_VARS=0
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "  [FATAL] Environment variable '${var}' is missing or empty."
        MISSING_VARS=1
    fi
done

if [ "${MISSING_VARS}" -ne 0 ]; then
    echo "  [FATAL] One or more essential environment variables are missing in .env."
    exit 1
fi
echo "  [OK] All essential environment variables are properly set."

POLICY_DIR="${POLICY_DIR:-${WORKSPACE_DIR}/docker/volumes/app/config/policies}"
SCHEMA_DIR="${SCHEMA_DIR:-${WORKSPACE_DIR}/docker/volumes/app/config/schemas}"
MQTT_REGISTRY_DIR="${MQTT_REGISTRY_DIR:-${WORKSPACE_DIR}/docker/volumes/app/config/mqtt}"
PAYLOAD_EXAMPLES_DIR="${PAYLOAD_EXAMPLES_DIR:-${WORKSPACE_DIR}/docker/volumes/app/config/payloads}"

echo "  [INFO] Policy runtime directory: ${POLICY_DIR}"
echo "  [INFO] Schema runtime directory: ${SCHEMA_DIR}"
echo "  [INFO] MQTT reference runtime directory: ${MQTT_REGISTRY_DIR}"
echo "  [INFO] Payload reference runtime directory: ${PAYLOAD_EXAMPLES_DIR}"

for runtime_dir in "${POLICY_DIR}" "${SCHEMA_DIR}" "${MQTT_REGISTRY_DIR}" "${PAYLOAD_EXAMPLES_DIR}"; do
    if [ ! -d "${runtime_dir}" ]; then
        echo "  [FATAL] Runtime directory not found: ${runtime_dir}"
        exit 1
    fi
done

echo "  [INFO] Checking deployed runtime policy assets..."
REQUIRED_POLICY_ASSETS=(
    "policy_table.json"
    "low_risk_actions.json"
    "fault_injection_rules.json"
    "output_profile.json"
)

MISSING_POLICY_ASSETS=0
for asset in "${REQUIRED_POLICY_ASSETS[@]}"; do
    target_file="${POLICY_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] Policy asset missing: ${asset}"
        MISSING_POLICY_ASSETS=1
    elif ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Invalid JSON format detected in policy asset: ${asset}"
        MISSING_POLICY_ASSETS=1
    else
        echo "  [OK] Policy asset present and valid: ${asset}"
    fi
done

echo "  [INFO] Checking deployed runtime schema assets..."
REQUIRED_SCHEMA_ASSETS=(
    "context_schema.json"
    "candidate_action_schema.json"
    "policy_router_input_schema.json"
    "validator_output_schema.json"
    "class2_notification_payload_schema.json"
)

MISSING_SCHEMA_ASSETS=0
for asset in "${REQUIRED_SCHEMA_ASSETS[@]}"; do
    target_file="${SCHEMA_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] Schema asset missing: ${asset}"
        MISSING_SCHEMA_ASSETS=1
    elif ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Invalid JSON format detected in schema asset: ${asset}"
        MISSING_SCHEMA_ASSETS=1
    else
        echo "  [OK] Schema asset present and valid: ${asset}"
    fi
done

echo "  [INFO] Checking deployed MQTT reference assets..."
REQUIRED_MQTT_ASSETS=(
    "README.md"
    "topic_registry.json"
    "publisher_subscriber_matrix.md"
    "topic_payload_contracts.md"
)

MISSING_MQTT_ASSETS=0
for asset in "${REQUIRED_MQTT_ASSETS[@]}"; do
    target_file="${MQTT_REGISTRY_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] MQTT reference asset missing: ${asset}"
        MISSING_MQTT_ASSETS=1
    elif [[ "${asset}" == *.json ]] && ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Invalid JSON format detected in MQTT reference asset: ${asset}"
        MISSING_MQTT_ASSETS=1
    else
        echo "  [OK] MQTT reference asset present: ${asset}"
    fi
done

echo "  [INFO] Checking deployed payload reference assets..."
REQUIRED_PAYLOAD_ASSETS=(
    "README.md"
    "examples/policy_router_input_non_visitor.json"
    "examples/policy_router_input_visitor_doorbell.json"
    "examples/policy_router_input_emergency_temperature.json"
    "examples/candidate_action_light_on.json"
    "examples/validator_output_execute_approved_light.json"
    "examples/class_2_notification_doorlock_sensitive.json"
    "templates/scenario_fixture_template.json"
)

MISSING_PAYLOAD_ASSETS=0
for asset in "${REQUIRED_PAYLOAD_ASSETS[@]}"; do
    target_file="${PAYLOAD_EXAMPLES_DIR}/${asset}"
    if [ ! -f "${target_file}" ]; then
        echo "  [FATAL] Payload reference asset missing: ${asset}"
        MISSING_PAYLOAD_ASSETS=1
    elif [[ "${asset}" == *.json ]] && ! jq empty "${target_file}" >/dev/null 2>&1; then
        echo "  [FATAL] Invalid JSON format detected in payload reference asset: ${asset}"
        MISSING_PAYLOAD_ASSETS=1
    else
        echo "  [OK] Payload reference asset present: ${asset}"
    fi
done

if [ "${MISSING_POLICY_ASSETS}" -ne 0 ] || \
   [ "${MISSING_SCHEMA_ASSETS}" -ne 0 ] || \
   [ "${MISSING_MQTT_ASSETS}" -ne 0 ] || \
   [ "${MISSING_PAYLOAD_ASSETS}" -ne 0 ]; then
    echo "  [FATAL] One or more runtime assets are missing or corrupted."
    echo "          Please ensure the deployment script completed successfully."
    exit 1
fi

TOPIC_REGISTRY_FILE="${MQTT_REGISTRY_DIR}/topic_registry.json"
echo "  [INFO] Checking topic registry referenced example payload files..."

MISSING_REFERENCED_EXAMPLES=0
while IFS= read -r example_path; do
    [ -z "${example_path}" ] && continue

    case "${example_path}" in
        common/payloads/*)
            relative_payload_path="${example_path#common/payloads/}"
            runtime_example_file="${PAYLOAD_EXAMPLES_DIR}/${relative_payload_path}"
            ;;
        *)
            echo "  [WARN] Example path does not use common/payloads prefix: ${example_path}"
            continue
            ;;
    esac

    if [ ! -f "${runtime_example_file}" ]; then
        echo "  [FATAL] Topic registry references missing payload example: ${example_path}"
        echo "          Expected runtime file: ${runtime_example_file}"
        MISSING_REFERENCED_EXAMPLES=1
    else
        echo "  [OK] Topic registry referenced example exists: ${example_path}"
    fi
done < <(jq -r '.topics[] | select(.example_payload != null) | .example_payload' "${TOPIC_REGISTRY_FILE}")

if [ "${MISSING_REFERENCED_EXAMPLES}" -ne 0 ]; then
    echo "  [FATAL] Topic registry example-payload reference check failed."
    exit 1
fi

echo "  [INFO] Validating schema-governed payload examples..."
"${VENV_PYTHON}" - "${SCHEMA_DIR}" "${PAYLOAD_EXAMPLES_DIR}" <<'PY'
import json
import sys
from pathlib import Path

try:
    import jsonschema
except Exception as exc:  # pragma: no cover - shell-facing diagnostic
    print("  [FATAL] Python package 'jsonschema' is not available.")
    print("          Run mac_mini/scripts/install/30_setup_python_venv_mac.sh or install requirements-mac.txt.")
    print(f"          Import error: {exc}")
    sys.exit(1)

schema_dir = Path(sys.argv[1])
payload_dir = Path(sys.argv[2])

checks = [
    (
        "policy_router_input_schema.json",
        "examples/policy_router_input_non_visitor.json",
        "policy_router_input_non_visitor",
    ),
    (
        "policy_router_input_schema.json",
        "examples/policy_router_input_visitor_doorbell.json",
        "policy_router_input_visitor_doorbell",
    ),
    (
        "policy_router_input_schema.json",
        "examples/policy_router_input_emergency_temperature.json",
        "policy_router_input_emergency_temperature",
    ),
    (
        "candidate_action_schema.json",
        "examples/candidate_action_light_on.json",
        "candidate_action_light_on",
    ),
    (
        "validator_output_schema.json",
        "examples/validator_output_execute_approved_light.json",
        "validator_output_execute_approved_light",
    ),
    (
        "class2_notification_payload_schema.json",
        "examples/class_2_notification_doorlock_sensitive.json",
        "class_2_notification_doorlock_sensitive",
    ),
]

for schema_name, payload_rel, label in checks:
    schema_path = schema_dir / schema_name
    payload_path = payload_dir / payload_rel
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    with payload_path.open("r", encoding="utf-8") as f:
        instance = json.load(f)
    try:
        jsonschema.Draft7Validator(schema).validate(instance)
    except jsonschema.ValidationError as exc:
        print(f"  [FATAL] Schema validation failed for {label}: {exc.message}")
        print(f"          schema={schema_path}")
        print(f"          payload={payload_path}")
        sys.exit(1)
    print(f"  [OK] Schema validation passed: {label}")

for payload_rel in [
    "examples/policy_router_input_non_visitor.json",
    "examples/policy_router_input_visitor_doorbell.json",
    "examples/policy_router_input_emergency_temperature.json",
    "templates/scenario_fixture_template.json",
]:
    payload_path = payload_dir / payload_rel
    with payload_path.open("r", encoding="utf-8") as f:
        instance = json.load(f)

    if "input_payload" in instance:
        context = instance["input_payload"].get("pure_context_payload", {})
    else:
        context = instance.get("pure_context_payload", {})

    env_context = context.get("environmental_context", {})
    if "doorbell_detected" not in env_context:
        print(f"  [FATAL] Missing environmental_context.doorbell_detected in {payload_rel}")
        sys.exit(1)

    device_states = context.get("device_states", {})
    forbidden = {"doorlock", "front_door_lock", "door_lock_state"}.intersection(device_states.keys())
    if forbidden:
        print(f"  [FATAL] Forbidden doorlock state fields in pure_context_payload.device_states for {payload_rel}: {sorted(forbidden)}")
        sys.exit(1)

    print(f"  [OK] Context boundary check passed: {payload_rel}")
PY

echo "  [OK] All required runtime policy, schema, MQTT, and payload reference assets are present and valid."
echo "==> [PASS] Environment and runtime assets verification successful."
