#!/usr/bin/env bash
# ==============================================================================
# Script: 50_deploy_policy_files.sh
# Purpose: Deploy canonical policy/schema assets and communication reference assets
#          into the Mac mini runtime config volume
# ==============================================================================
set -euo pipefail

echo "==> [50_deploy_policy_files] Deploying canonical runtime reference assets..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SOURCE_COMMON_DIR="${PROJECT_ROOT}/common"
WORKSPACE_DIR="${HOME}/smarthome_workspace"
RUNTIME_TARGET_DIR="${WORKSPACE_DIR}/docker/volumes/app/config"

copy_dir_sync() {
    local src="$1"
    local dst="$2"

    if [ ! -d "${src}" ]; then
        echo "  [FATAL] Source directory not found: ${src}"
        exit 1
    fi

    mkdir -p "${dst}"

    if command -v rsync >/dev/null 2>&1; then
        rsync -a --delete "${src}/" "${dst}/"
    else
        echo "  [WARN] rsync is not available. Falling back to rm/cp directory sync."
        rm -rf "${dst:?}/"*
        cp -R "${src}/." "${dst}/"
    fi
}

mkdir -p "${RUNTIME_TARGET_DIR}/policies"
mkdir -p "${RUNTIME_TARGET_DIR}/schemas"
mkdir -p "${RUNTIME_TARGET_DIR}/mqtt"
mkdir -p "${RUNTIME_TARGET_DIR}/payloads"

# 1. Deploy policy assets explicitly so the frozen runtime surface remains reviewable.
cp "${SOURCE_COMMON_DIR}/policies/policy_table_v1_1_2_FROZEN.json" "${RUNTIME_TARGET_DIR}/policies/"
cp "${SOURCE_COMMON_DIR}/policies/low_risk_actions_v1_1_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/policies/"
cp "${SOURCE_COMMON_DIR}/policies/fault_injection_rules_v1_4_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/policies/"
cp "${SOURCE_COMMON_DIR}/policies/output_profile_v1_1_0.json" "${RUNTIME_TARGET_DIR}/policies/"

# 2. Deploy schema assets explicitly so the frozen validation surface remains reviewable.
cp "${SOURCE_COMMON_DIR}/schemas/context_schema_v1_0_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${SOURCE_COMMON_DIR}/schemas/candidate_action_schema_v1_0_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${SOURCE_COMMON_DIR}/schemas/policy_router_input_schema_v1_1_1_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${SOURCE_COMMON_DIR}/schemas/validator_output_schema_v1_1_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${SOURCE_COMMON_DIR}/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"

# 3. Deploy MQTT/payload communication reference assets for runtime loading,
#    Package G checks, and governance support. These are references, not authority.
copy_dir_sync "${SOURCE_COMMON_DIR}/mqtt" "${RUNTIME_TARGET_DIR}/mqtt"
copy_dir_sync "${SOURCE_COMMON_DIR}/payloads" "${RUNTIME_TARGET_DIR}/payloads"

# 4. Harden runtime reference asset permissions.
find "${RUNTIME_TARGET_DIR}/policies" -type f -exec chmod 444 {} +
find "${RUNTIME_TARGET_DIR}/schemas" -type f -exec chmod 444 {} +
find "${RUNTIME_TARGET_DIR}/mqtt" -type f -exec chmod 444 {} +
find "${RUNTIME_TARGET_DIR}/payloads" -type f -exec chmod 444 {} +
find "${RUNTIME_TARGET_DIR}/policies" -type d -exec chmod 555 {} +
find "${RUNTIME_TARGET_DIR}/schemas" -type d -exec chmod 555 {} +
find "${RUNTIME_TARGET_DIR}/mqtt" -type d -exec chmod 555 {} +
find "${RUNTIME_TARGET_DIR}/payloads" -type d -exec chmod 555 {} +

echo "  [OK] Policies deployed to ${RUNTIME_TARGET_DIR}/policies"
echo "  [OK] Schemas deployed to ${RUNTIME_TARGET_DIR}/schemas"
echo "  [OK] MQTT references deployed to ${RUNTIME_TARGET_DIR}/mqtt"
echo "  [OK] Payload references deployed to ${RUNTIME_TARGET_DIR}/payloads"
echo "==> [PASS] Canonical runtime reference assets deployed read-only."
