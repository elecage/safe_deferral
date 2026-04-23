#!/usr/bin/env bash
# ==============================================================================
# Script: 40_verify_sqlite.sh
# Purpose: Verify SQLite database health, WAL mode, and audit schema readiness
# ==============================================================================
set -euo pipefail

echo "==> [40_verify_sqlite] Verifying SQLite database health and schema readiness..."

if ! command -v sqlite3 >/dev/null 2>&1; then
    echo "  [FATAL] 'sqlite3' command is not available."
    echo "          Please ensure the sqlite3 package is installed."
    exit 1
fi
echo "  [OK] 'sqlite3' CLI tool verified."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ -f "${ENV_FILE}" ]; then
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    echo "  [OK] Environment variables loaded from ${ENV_FILE}."
else
    echo "  [FATAL] ${ENV_FILE} not found. Cannot load database configuration."
    exit 1
fi

DB_FILE="${SQLITE_PATH:-${WORKSPACE_DIR}/db/audit_log.db}"
echo "  [INFO] Target Database: ${DB_FILE}"

if [ ! -f "${DB_FILE}" ]; then
    echo "  [FATAL] Database file not found at ${DB_FILE}."
    echo "          Please run the SQLite configuration script first."
    exit 1
fi
echo "  [OK] Database file exists."

WAL_MODE=$(sqlite3 "${DB_FILE}" "PRAGMA journal_mode;" 2>/dev/null || echo "error")
WAL_MODE_LOWER=$(printf '%s' "${WAL_MODE}" | tr '[:upper:]' '[:lower:]')

if [ "${WAL_MODE_LOWER}" = "wal" ]; then
    echo "  [OK] SQLite database is correctly operating in WAL mode."
else
    echo "  [FATAL] SQLite database is not in WAL mode (Current mode: ${WAL_MODE})."
    exit 1
fi

INTEGRITY_RESULT=$(sqlite3 "${DB_FILE}" "PRAGMA integrity_check;" 2>/dev/null || echo "error")
if [ "${INTEGRITY_RESULT}" != "ok" ]; then
    echo "  [FATAL] Database integrity check failed. Result: ${INTEGRITY_RESULT}"
    exit 1
fi
echo "  [OK] Database integrity check passed."

REQUIRED_TABLES=(
    "routing_events"
    "validator_results"
    "deferral_events"
    "timeout_events"
    "escalation_events"
    "caregiver_actions"
    "actuation_ack_events"
)

MISSING_TABLES=0
for table in "${REQUIRED_TABLES[@]}"; do
    if sqlite3 "${DB_FILE}" "SELECT name FROM sqlite_master WHERE type='table' AND name='${table}';" | grep -qx "${table}"; then
        echo "  [OK] Found required table: ${table}"
    else
        echo "  [FATAL] Missing required table: ${table}"
        MISSING_TABLES=1
    fi
done

if [ "${MISSING_TABLES}" -ne 0 ]; then
    echo "  [FATAL] SQLite audit schema readiness check failed."
    exit 1
fi

echo "==> [PASS] SQLite database verification successful."
