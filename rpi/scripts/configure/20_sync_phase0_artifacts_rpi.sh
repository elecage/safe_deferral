#!/usr/bin/env bash
# ==============================================================================
# Script: 20_sync_phase0_artifacts_rpi.sh
# Purpose: Sync Phase 0 Artifacts (Policies & Schemas) from Mac mini (Phase 4)
# ==============================================================================
set -euo pipefail

echo "==> [20_sync_phase0_artifacts_rpi] Syncing Phase 0 Artifacts from Mac mini Runtime..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

# 1. 환경변수 파일 검증 및 로드
if [ -f "${ENV_FILE}" ]; then
    source "${ENV_FILE}"
    echo "  [OK] Environment variables loaded from ${ENV_FILE}."
else
    echo "  [FATAL] ${ENV_FILE} not found."
    echo "          Please run 10_write_env_files_rpi.sh first."
    exit 1
fi

# [보완 1] MAC_MINI_HOST 명시적 검증 (Fail-fast 및 진단성 향상)
if [ -z "${MAC_MINI_HOST:-}" ]; then
    echo "  [FATAL] MAC_MINI_HOST is missing in ${ENV_FILE}."
    echo "          Please ensure the authoritative source IP is defined."
    exit 1
fi

# 환경변수 연동 및 하드코딩 제거 (미정의 시 안전한 기본값 Fallback 제공)
REMOTE_USER="${MAC_MINI_USER:-mac_user}"
SCHEMA_TARGET_DIR="${SCHEMA_SYNC_PATH:-${WORKSPACE_DIR}/config/schemas}"
POLICY_TARGET_DIR="${POLICY_SYNC_PATH:-${WORKSPACE_DIR}/config/policies}"

mkdir -p "${SCHEMA_TARGET_DIR}" "${POLICY_TARGET_DIR}"

# 정책과 스키마 분리 동기화 원칙 적용 (원격지 및 HTTP Fallback 경로)
REMOTE_SCHEMA_DIR="~/smarthome_workspace/config/schemas"
REMOTE_POLICY_DIR="~/smarthome_workspace/config/policies"

HTTP_FALLBACK_SCHEMA_URL="http://${MAC_MINI_HOST}:8080/config/schemas"
HTTP_FALLBACK_POLICY_URL="http://${MAC_MINI_HOST}:8080/config/policies"

# 동기화 및 검증 대상 8대 핵심 자산 명시
SCHEMA_FILES=(
    "context_schema.json"
    "candidate_action_schema.json"
    "policy_router_input_schema.json"
    "validator_output_schema.json"
)

POLICY_FILES=(
    "policy_table.json"
    "fault_injection_rules.json"
    "low_risk_actions.json"
    "output_profile.json"
)

# 2. rsync를 활용한 자동 동기화 (SSH 키 기반 unattended sync)
echo "  [INFO] Attempting unattended SSH rsync from ${REMOTE_USER}@${MAC_MINI_HOST}..."
SYNC_SUCCESS=true

# Schema 및 Policy 폴더 각각 동기화
if ! rsync -avz -e "ssh -o BatchMode=yes -o ConnectTimeout=5" "${REMOTE_USER}@${MAC_MINI_HOST}:${REMOTE_SCHEMA_DIR}/" "${SCHEMA_TARGET_DIR}/" > /dev/null 2>&1; then
    SYNC_SUCCESS=false
fi
if ! rsync -avz -e "ssh -o BatchMode=yes -o ConnectTimeout=5" "${REMOTE_USER}@${MAC_MINI_HOST}:${REMOTE_POLICY_DIR}/" "${POLICY_TARGET_DIR}/" > /dev/null 2>&1; then
    SYNC_SUCCESS=false
fi

if [ "$SYNC_SUCCESS" = true ]; then
    echo "  [OK] Policies and Schemas synced successfully via SSH."
else
    # 3. HTTP Fallback 로직
    echo "  [WARNING] Unattended SSH rsync failed."
    echo "  [INFO] Attempting HTTP Fallback (Read-only Artifact Server)..."

    # HTTP Fallback 전 curl 명령어 존재 여부 필수 검증 (Fail-fast)
    if ! command -v curl >/dev/null 2>&1; then
        echo "  [FATAL] 'curl' command is not available for HTTP fallback."
        exit 1
    fi

    HTTP_SYNC_SUCCESS=true

    # Schema HTTP Fallback
    for file in "${SCHEMA_FILES[@]}"; do
        if ! curl -s -f --connect-timeout 5 "${HTTP_FALLBACK_SCHEMA_URL}/${file}" -o "${SCHEMA_TARGET_DIR}/${file}"; then
            echo "  [FATAL] HTTP Fallback failed to download '${file}' from ${HTTP_FALLBACK_SCHEMA_URL}."
            HTTP_SYNC_SUCCESS=false
            break
        fi
    done

    # Policy HTTP Fallback (Schema 성공 시에만 진행)
    if [ "$HTTP_SYNC_SUCCESS" = true ]; then
        for file in "${POLICY_FILES[@]}"; do
            if ! curl -s -f --connect-timeout 5 "${HTTP_FALLBACK_POLICY_URL}/${file}" -o "${POLICY_TARGET_DIR}/${file}"; then
                echo "  [FATAL] HTTP Fallback failed to download '${file}' from ${HTTP_FALLBACK_POLICY_URL}."
                HTTP_SYNC_SUCCESS=false
                break
            fi
        done
    fi

    if [ "$HTTP_SYNC_SUCCESS" = true ]; then
        echo "  [OK] Artifacts synced successfully via HTTP Fallback."
    else
        echo "  [FATAL] Both SSH and HTTP sync methods failed."
        echo "          Phase 0 sync is incomplete. Cannot proceed with simulation."
        exit 1
    fi
fi

# 4. 필수 동결 자산 존재 여부 엄격 검증
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

echo "  [OK] All required Phase 0 runtime artifacts (8 files) are present."
echo "==> [PASS] Phase 0 runtime artifacts are synced and verified."
