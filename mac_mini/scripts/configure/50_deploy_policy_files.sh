#!/usr/bin/env bash
# ==============================================================================
# Script: 50_deploy_policy_files.sh
# Purpose: Phase 0에서 동결된 핵심 정책 및 스키마 자산들을 Mac mini 런타임 환경으로 배포
# ==============================================================================

set -euo pipefail

echo "=========================================================================="
echo "[Phase 4] Mac mini: Deploying Phase 0 Frozen Assets (Immutability Enforced)"
echo "=========================================================================="

# 1. 경로 설정
PROJECT_ROOT=$(pwd)
PHASE0_SOURCE_DIR="${PROJECT_ROOT}/common"
RUNTIME_TARGET_DIR="${PROJECT_ROOT}/compose/volumes/app/config"

# 2. 런타임 타겟 디렉터리 준비 (멱등성 보장)
echo "[INFO] Preparing runtime directories for frozen assets..."
mkdir -p "${RUNTIME_TARGET_DIR}/policies"
mkdir -p "${RUNTIME_TARGET_DIR}/schemas"

# 3. 정책 자산 (Policy Assets) 배포
echo "[INFO] Deploying Policy Assets..."
cp "${PHASE0_SOURCE_DIR}/policies/policy_table_v1_1_2_FROZEN.json" "${RUNTIME_TARGET_DIR}/policies/"
cp "${PHASE0_SOURCE_DIR}/policies/fault_injection_rules_v1_4_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/policies/"
cp "${PHASE0_SOURCE_DIR}/policies/low_risk_actions_v1_0_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/policies/"

# 4. 스키마 자산 (Schema Assets) 배포
echo "[INFO] Deploying Schema Assets..."
cp "${PHASE0_SOURCE_DIR}/schemas/context_schema_v1_0_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${PHASE0_SOURCE_DIR}/schemas/candidate_action_schema_v1_0_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${PHASE0_SOURCE_DIR}/schemas/policy_router_input_schema_v1_1_1_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"
cp "${PHASE0_SOURCE_DIR}/schemas/validator_output_schema_v1_0_0_FROZEN.json" "${RUNTIME_TARGET_DIR}/schemas/"

# 5. 런타임 불변성(Immutability) 적용 (보안/프라이버시 원칙)
# 배포된 파일들이 실행 중인 앱이나 외부 접근에 의해 수정되지 않도록 읽기 전용(Read-only)으로 권한 강제
echo "[INFO] Enforcing strict read-only permissions (chmod 444) on deployed assets..."
find "${RUNTIME_TARGET_DIR}/policies" -type f -name "*.json" -exec chmod 444 {} +
find "${RUNTIME_TARGET_DIR}/schemas" -type f -name "*.json" -exec chmod 444 {} +

echo "=========================================================================="
echo "[SUCCESS] Policy and Schema files deployed and locked successfully."
echo "=========================================================================="