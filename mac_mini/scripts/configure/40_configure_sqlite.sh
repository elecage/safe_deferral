#!/usr/bin/env bash
# ==============================================================================
# Script: 40_configure_sqlite.sh
# Purpose: Initialize SQLite DB and WAL mode for single-writer audit logging
# ==============================================================================
set -euo pipefail

echo "==> [40_configure_sqlite] Initializing SQLite DB and WAL mode..."

umask 077

WORKSPACE_DIR="${HOME}/smarthome_workspace"
DB_DIR="${WORKSPACE_DIR}/db"
DB_FILE="${DB_DIR}/audit_log.db"

if ! command -v sqlite3 >/dev/null 2>&1; then
    echo "  [FATAL] 'sqlite3' command is not available."
    echo "          Please ensure sqlite3 is installed on the host system."
    exit 1
fi

echo "  [INFO] Ensuring database directory exists at ${DB_DIR}..."
mkdir -p "${DB_DIR}"
chmod 700 "${DB_DIR}"

echo "  [INFO] Applying schema and WAL settings to ${DB_FILE}..."
sqlite3 "${DB_FILE}" <<'EOF'
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS routing_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    audit_correlation_id TEXT,
    source_node_id TEXT,
    route_class TEXT,
    route_reason TEXT,
    llm_invocation_allowed INTEGER,
    policy_constraints_summary TEXT,
    payload_summary TEXT
);

CREATE TABLE IF NOT EXISTS validator_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    audit_correlation_id TEXT,
    validation_status TEXT,
    routing_target TEXT,
    target_device TEXT,
    approved_action TEXT,
    deferral_reason TEXT,
    exception_trigger_id TEXT,
    payload_summary TEXT
);

CREATE TABLE IF NOT EXISTS deferral_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    audit_correlation_id TEXT,
    deferral_reason TEXT,
    candidate_options_summary TEXT,
    payload_summary TEXT
);

CREATE TABLE IF NOT EXISTS timeout_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    audit_correlation_id TEXT,
    timeout_source TEXT,
    related_trigger_id TEXT,
    payload_summary TEXT
);

CREATE TABLE IF NOT EXISTS escalation_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    audit_correlation_id TEXT,
    source_layer TEXT,
    exception_trigger_id TEXT,
    notification_channel TEXT,
    unresolved_reason TEXT,
    payload_summary TEXT
);

CREATE TABLE IF NOT EXISTS caregiver_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    audit_correlation_id TEXT,
    caregiver_action TEXT,
    target_device TEXT,
    action_status TEXT,
    payload_summary TEXT
);

CREATE TABLE IF NOT EXISTS actuation_ack_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    audit_correlation_id TEXT,
    target_device TEXT,
    approved_action TEXT,
    ack_status TEXT,
    payload_summary TEXT
);
EOF

echo "  [INFO] Applying single-writer-oriented permission hardening..."
chmod 600 "${DB_FILE}"
echo "  [OK] Database directory (700) and file (600) permissions secured."

echo "==> [PASS] SQLite configuration applied."
