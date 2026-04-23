#!/usr/bin/env bash
# ==============================================================================
# Script: 50_deploy_policy_files.sh
# Purpose: Deploy current canonical policy and schema assets into Mac mini runtime
# ==============================================================================
set -euo pipefail

echo "==> [50_deploy_policy_files] Deploying canonical frozen assets..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SOURCE_COMMON_DIR="${PROJECT_ROOT}/common"
WORKSPACE_DIR="${HOME}/smarthome_workspace"
RUNTIME_TARGET_DIR="${WORKSPACE_DIR}/docker/volumes/app/config"

mkdir -p "${RUNTIME_TARGET_DIR}/policies"
mkdir -p "${RUNTIME_TARGET_DIR}/schemas"

cp "${SOURCE_COMMON_DIR}/policies/policy_table_v1_1_2_FROZEN.json" "${RUNTIME_TARGET_DIR}/policies/"
cp "${SOURCE_COMMON_DIR}/policies/low_risk_actions_v1_1_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/policies/"
cp "${SOURCE_COMMON_DIR}/policies/fault_injection_rules_v1_4_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/policies/"
cp "${SOURCE_COMMON_DIR}/policies/output_profile_v1_1_0.json" "${RUNTIME_TARGET_DIR}/policies/"

cp "${SOURCE_COMMON_DIR}/schemas/context_schema_v1_0_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${SOURCE_COMMON_DIR}/schemas/candidate_action_schema_v1_0_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${SOURCE_COMMON_DIR}/schemas/policy_router_input_schema_v1_1_1_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${SOURCE_COMMON_DIR}/schemas/validator_output_schema_v1_1_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${SOURCE_COMMON_DIR}/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"

find "${RUNTIME_TARGET_DIR}/policies" -type f -name "*.json" -exec chmod 444 {} +
find "${RUNTIME_TARGET_DIR}/schemas" -type f -name "*.json" -exec chmod 444 {} +

echo "==> [PASS] Canonical assets deployed read-only."
