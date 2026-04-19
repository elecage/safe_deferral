#!/usr/bin/env bash
# ==============================================================================
# Script: 40_configure_sqlite.sh
# Purpose: Initialize SQLite DB and WAL Mode for Audit Logging (Phase 4)
# ==============================================================================
set -euo pipefail

echo "==> [40_configure_sqlite] Initializing SQLite DB and WAL Mode..."

# 0. 새로 생성되는 파일(WAL, SHM 등)과 디렉터리의 기본 권한을 소유자 전용으로 강제
umask 077

WORKSPACE_DIR="${HOME}/smarthome_workspace"
DB_DIR="${WORKSPACE_DIR}/db"
DB_FILE="${DB_DIR}/audit_log.db"

# 1. sqlite3 CLI 존재 여부 확인 (Fail-fast)
if ! command -v sqlite3 >/dev/null 2>&1; then
    echo "  [FATAL] 'sqlite3' command is not available."
    echo "          Please ensure sqlite3 is installed on the host system."
    exit 1
fi

echo "  [INFO] Ensuring database directory exists at ${DB_DIR}..."
mkdir -p "${DB_DIR}"
# 디렉터리 권한 강화 (umask로 기본 적용되나 명시적 보완)
chmod 700 "${DB_DIR}"

# 2. 데이터베이스가 없을 때만 샘플 인서트를 포함하여 초기화 진행 (멱등성 확보)
if [ ! -f "${DB_FILE}" ]; then
    sqlite3 "${DB_FILE}" <<EOF
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS routing_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT,
    assigned_class TEXT
);

CREATE TABLE IF NOT EXISTS validator_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    validation_status TEXT,
    routing_target TEXT,
    deferral_reason TEXT,
    exception_trigger_id TEXT
);

CREATE TABLE IF NOT EXISTS timeout_and_ack_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT,
    target_device TEXT
);

INSERT INTO routing_events (event_type, assigned_class) VALUES ('system_init', 'N/A');
EOF
    echo "  [OK] SQLite DB created and initialized with sample data at ${DB_FILE}."
else
    # 이미 존재하면 WAL 모드와 스키마 검증만 수행
    sqlite3 "${DB_FILE}" <<EOF
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS routing_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT,
    assigned_class TEXT
);

CREATE TABLE IF NOT EXISTS validator_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    validation_status TEXT,
    routing_target TEXT,
    deferral_reason TEXT,
    exception_trigger_id TEXT
);

CREATE TABLE IF NOT EXISTS timeout_and_ack_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT,
    target_device TEXT
);
EOF
    echo "  [INFO] SQLite DB already exists. Ensured schema and WAL mode without duplicate inserts."
fi

# 3. 단일 작성자 지향 권한 강화 (Single-writer-oriented permission hardening)
echo "  [INFO] Applying single-writer-oriented permission hardening..."
chmod 600 "${DB_FILE}"
echo "  [OK] Database directory (700) and file (600) permissions secured."

echo "==> [PASS] SQLite configuration applied."
