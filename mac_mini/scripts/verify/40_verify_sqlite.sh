#!/usr/bin/env bash
# ==============================================================================
# Script: 40_verify_sqlite.sh
# Purpose: Verify Audit Logging SQLite Database integrity and WAL mode (Phase 5)
# ==============================================================================
set -euo pipefail

echo "==> [40_verify_sqlite] Verifying SQLite Database and WAL mode..."

# 1. sqlite3 명령어 존재 여부 확인 (Fail-fast)
if ! command -v sqlite3 >/dev/null 2>&1; then
    echo "  [FATAL] 'sqlite3' command is not available."
    echo "          Please ensure the sqlite3 package is installed."
    exit 1
fi
echo "  [OK] 'sqlite3' CLI tool verified."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

# 2. 환경변수 파일 검증 및 로드
if [ -f "${ENV_FILE}" ]; then
    source "${ENV_FILE}"
    echo "  [OK] Environment variables loaded from ${ENV_FILE}."
else
    echo "  [FATAL] ${ENV_FILE} not found. Cannot load database configuration."
    exit 1
fi

DB_FILE="${SQLITE_PATH:-${WORKSPACE_DIR}/db/audit_log.db}"
echo "  [INFO] Target Database: ${DB_FILE}"

# 3. 데이터베이스 파일 존재 여부 점검
if [ ! -f "${DB_FILE}" ]; then
    echo "  [FATAL] Database file not found at ${DB_FILE}."
    echo "          Please run the SQLite configuration script first."
    exit 1
fi
echo "  [OK] Database file exists."

# 4. WAL 모드 작동 여부 검증
WAL_MODE=$(sqlite3 "${DB_FILE}" "PRAGMA journal_mode;" 2>/dev/null || echo "error")

# [최종 교정 반영] echo 대신 printf '%s'를 사용하여 안전하게 문자열 전달
WAL_MODE_LOWER=$(printf '%s' "${WAL_MODE}" | tr '[:upper:]' '[:lower:]')

if [ "${WAL_MODE_LOWER}" = "wal" ]; then
    echo "  [OK] SQLite database is correctly operating in WAL mode."
else
    echo "  [FATAL] SQLite database is not in WAL mode (Current mode: ${WAL_MODE})."
    echo "          WAL mode is required for the Audit Logger Service's single-writer architecture."
    exit 1
fi

# 5. 무결성 및 접근 상태 점검
echo "  [INFO] Performing database integrity and read access check..."

INTEGRITY_RESULT=$(sqlite3 "${DB_FILE}" "PRAGMA integrity_check;" 2>/dev/null || echo "error")

if [ "${INTEGRITY_RESULT}" != "ok" ]; then
    echo "  [FATAL] Database integrity check failed. The file may be corrupted."
    echo "          Result: ${INTEGRITY_RESULT}"
    exit 1
fi

# [최종 교정 반영] 읽기 실패 원인을 포괄하는 중립적이고 정확한 메시지 적용
if ! sqlite3 "${DB_FILE}" "SELECT count(name) FROM sqlite_master;" >/dev/null 2>&1; then
    echo "  [FATAL] Database read access check failed."
    echo "          Cannot read from the database (e.g., locked, permission denied, or corrupted)."
    exit 1
fi
echo "  [OK] Database is accessible and passes integrity checks."

echo "==> [PASS] SQLite database verification successful."
