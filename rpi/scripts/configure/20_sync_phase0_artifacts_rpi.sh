#!/usr/bin/env bash
# ==============================================================================
# Script: 20_sync_phase0_artifacts_rpi.sh
# Purpose: Sync authority mirrors and reference assets from Mac mini runtime
# ==============================================================================
set -euo pipefail

echo "==> [20_sync_phase0_artifacts_rpi] Syncing runtime artifacts from Mac mini..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ -f "${ENV_FILE}" ]; then
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    echo "  [OK] Environment variables loaded from ${ENV_FILE}."
else
    echo "  [FATAL] ${ENV_FILE} not found."
    echo "          Please run 10_write_env_files_rpi.sh first."
    exit 1
fi

if [ -z "${MAC_MINI_HOST:-}" ]; then
    echo "  [FATAL] MAC_MINI_HOST is missing in ${ENV_FILE}."
    echo "          Please ensure the authoritative source host is defined."
    exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
    echo "  [FATAL] 'rsync' command is not available."
    echo "          Please run the RPi system package installation step first."
    exit 1
fi

REMOTE_USER="${MAC_MINI_USER:-mac_user}"
SCHEMA_TARGET_DIR="${SCHEMA_SYNC_PATH:-${WORKSPACE_DIR}/config/schemas}"
POLICY_TARGET_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"
MQTT_TARGET_DIR="${MQTT_REGISTRY_SYNC_PATH:-${WORKSPACE_DIR}/config/mqtt}"
PAYLOAD_TARGET_DIR="${PAYLOAD_EXAMPLES_SYNC_PATH:-${WORKSPACE_DIR}/config/payloads}"

mkdir -p "${SCHEMA_TARGET_DIR}" "${POLICY_TARGET_DIR}" "${MQTT_TARGET_DIR}" "${PAYLOAD_TARGET_DIR}"

# Mac mini current runtime asset paths.
# Policies and schemas are authority mirrors for verification only.
# MQTT registry and payload examples are reference/governance assets only.
REMOTE_SCHEMA_DIR="${REMOTE_SCHEMA_DIR:-~/smarthome_workspace/docker/volumes/app/config/schemas}"
REMOTE_POLICY_DIR="${REMOTE_POLICY_DIR:-~/smarthome_workspace/docker/volumes/app/config/policies}"
REMOTE_MQTT_DIR="${REMOTE_MQTT_DIR:-~/smarthome_workspace/docker/volumes/app/config/mqtt}"
REMOTE_PAYLOADS_DIR="${REMOTE_PAYLOADS_DIR:-~/smarthome_workspace/docker/volumes/app/config/payloads}"

SCHEMA_FILES=(
    "context_schema_v1_0_0_FROZEN.json"
    "candidate_action_schema_v1_0_0_FROZEN.json"
    "policy_router_input_schema_v1_1_1_FROZEN.json"
    "validator_output_schema_v1_1_0_FROZEN.json"
    "class_2_notification_payload_schema_v1_0_0_FROZEN.json"
)

POLICY_FILES=(
    "policy_table_v1_1_2_FROZEN.json"
    "fault_injection_rules_v1_4_0_FROZEN.json"
    "low_risk_actions_v1_1_0_FROZEN.json"
    "output_profile_v1_1_0.json"
)

MQTT_FILES=(
    "topic_registry_v1_0_0.json"
    "publisher_subscriber_matrix_v1_0_0.md"
    "topic_payload_contracts_v1_0_0.md"
)

sync_dir() {
    local label="$1"
    local remote_dir="$2"
    local local_dir="$3"

    echo "  [INFO] Syncing ${label} from ${REMOTE_USER}@${MAC_MINI_HOST}:${remote_dir}..."
    if ! rsync -avz --delete -e "ssh -o BatchMode=yes -o ConnectTimeout=5" \
        "${REMOTE_USER}@${MAC_MINI_HOST}:${remote_dir}/" \
        "${local_dir}/" > /dev/null 2>&1; then
        echo "  [FATAL] SSH rsync failed for ${label} from ${REMOTE_USER}@${MAC_MINI_HOST}:${remote_dir}."
        echo "          Please verify SSH key-based access and the Mac mini runtime path."
        exit 1
    fi
    echo "  [OK] ${label} synced."
}

sync_dir "schema authority mirror" "${REMOTE_SCHEMA_DIR}" "${SCHEMA_TARGET_DIR}"
sync_dir "policy authority mirror" "${REMOTE_POLICY_DIR}" "${POLICY_TARGET_DIR}"
sync_dir "MQTT reference registry" "${REMOTE_MQTT_DIR}" "${MQTT_TARGET_DIR}"
sync_dir "payload reference examples" "${REMOTE_PAYLOADS_DIR}" "${PAYLOAD_TARGET_DIR}"

echo "  [INFO] Verifying existence of synchronized authority and reference artifacts..."
for file in "${SCHEMA_FILES[@]}"; do
    if [ ! -f "${SCHEMA_TARGET_DIR}/${file}" ]; then
        echo "  [FATAL] Required schema artifact '${file}' not found in ${SCHEMA_TARGET_DIR}."
        exit 1
    fi
done

for file in "${POLICY_FILES[@]}"; do
    if [ ! -f "${POLICY_TARGET_DIR}/${file}" ]; then
        echo "  [FATAL] Required policy artifact '${file}' not found in ${POLICY_TARGET_DIR}."
        exit 1
    fi
done

for file in "${MQTT_FILES[@]}"; do
    if [ ! -f "${MQTT_TARGET_DIR}/${file}" ]; then
        echo "  [FATAL] Required MQTT reference artifact '${file}' not found in ${MQTT_TARGET_DIR}."
        exit 1
    fi
done

if [ -z "$(find "${PAYLOAD_TARGET_DIR}" -type f -print -quit)" ]; then
    echo "  [FATAL] Payload reference directory is empty: ${PAYLOAD_TARGET_DIR}"
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "  [WARNING] 'jq' command is not available. JSON syntax validation skipped."
else
    for file in "${SCHEMA_FILES[@]}"; do
        jq empty "${SCHEMA_TARGET_DIR}/${file}" >/dev/null
    done

    for file in "${POLICY_FILES[@]}"; do
        jq empty "${POLICY_TARGET_DIR}/${file}" >/dev/null
    done

    jq empty "${MQTT_TARGET_DIR}/topic_registry_v1_0_0.json" >/dev/null
    echo "  [OK] JSON syntax verified for policy, schema, and topic registry assets."
fi

echo "  [OK] Required policy/schema authority mirrors and MQTT/payload reference assets are present."
echo "  [INFO] RPi copies are for simulation and verification only; they do not grant policy or actuation authority."
echo "==> [PASS] Runtime artifacts synced and verified."
