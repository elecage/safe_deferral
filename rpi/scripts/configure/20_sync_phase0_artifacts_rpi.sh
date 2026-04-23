#!/usr/bin/env bash
# ==============================================================================
# Script: 20_sync_phase0_artifacts_rpi.sh
# Purpose: Sync Phase 0 Artifacts (Policies & Schemas) from Mac mini Runtime
# ==============================================================================
set -euo pipefail

echo "==> [20_sync_phase0_artifacts_rpi] Syncing Phase 0 Artifacts from Mac mini Runtime..."

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
    echo "          Please ensure the authoritative source IP is defined."
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

mkdir -p "${SCHEMA_TARGET_DIR}" "${POLICY_TARGET_DIR}"

# Mac mini current runtime asset paths
REMOTE_SCHEMA_DIR="~/smarthome_workspace/docker/volumes/app/config/schemas"
REMOTE_POLICY_DIR="~/smarthome_workspace/docker/volumes/app/config/policies"

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

echo "  [INFO] Attempting unattended SSH rsync from ${REMOTE_USER}@${MAC_MINI_HOST}..."
if ! rsync -avz -e "ssh -o BatchMode=yes -o ConnectTimeout=5" "${REMOTE_USER}@${MAC_MINI_HOST}:${REMOTE_SCHEMA_DIR}/" "${SCHEMA_TARGET_DIR}/" > /dev/null 2>&1; then
    echo "  [FATAL] SSH rsync failed for schema artifacts from ${REMOTE_USER}@${MAC_MINI_HOST}:${REMOTE_SCHEMA_DIR}."
    echo "          Please verify SSH key-based access and the Mac mini runtime path."
    exit 1
fi

if ! rsync -avz -e "ssh -o BatchMode=yes -o ConnectTimeout=5" "${REMOTE_USER}@${MAC_MINI_HOST}:${REMOTE_POLICY_DIR}/" "${POLICY_TARGET_DIR}/" > /dev/null 2>&1; then
    echo "  [FATAL] SSH rsync failed for policy artifacts from ${REMOTE_USER}@${MAC_MINI_HOST}:${REMOTE_POLICY_DIR}."
    echo "          Please verify SSH key-based access and the Mac mini runtime path."
    exit 1
fi

echo "  [OK] Policies and schemas synced successfully via SSH."

echo "  [INFO] Verifying existence of synchronized artifacts..."
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

echo "  [OK] All required Phase 0 runtime artifacts (9 files) are present."
echo "==> [PASS] Phase 0 runtime artifacts are synced and verified."
