"""Audit Logging Service — single-writer SQLite store (MM-09).

Design rules:
  - AuditLogger is the only writer.  No other component writes to the DB.
  - Records are append-only; no UPDATE or DELETE.
  - DB path is injected so the service can use a file path in production
    and ':memory:' in tests.
  - Payload dicts are stored as JSON text.
  - Thread safety: sqlite3 check_same_thread=False is intentional here
    because writes are serialised through the single AuditLogger instance.
    For async use a dedicated writer thread or asyncio queue is recommended.

Authority note: audit records are evidence artifacts only.
They do not grant policy authority, validator approval, or caregiver approval.
"""

import json
import sqlite3
import time
import uuid
from typing import Optional

from audit_logger.models import AuditEvent, AuditSummary, EventGroup

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS audit_events (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_event_id   TEXT    NOT NULL UNIQUE,
    audit_correlation_id TEXT NOT NULL,
    event_group      TEXT    NOT NULL,
    event_type       TEXT    NOT NULL,
    summary          TEXT    NOT NULL,
    payload_json     TEXT    NOT NULL DEFAULT '{}',
    timestamp_ms     INTEGER NOT NULL,
    authority_note   TEXT    NOT NULL
);
"""

_CREATE_IDX_CORR = """
CREATE INDEX IF NOT EXISTS idx_correlation
    ON audit_events (audit_correlation_id);
"""

_CREATE_IDX_TS = """
CREATE INDEX IF NOT EXISTS idx_timestamp
    ON audit_events (timestamp_ms);
"""

_INSERT = """
INSERT INTO audit_events
    (audit_event_id, audit_correlation_id, event_group, event_type,
     summary, payload_json, timestamp_ms, authority_note)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""


class AuditLogger:
    """Single-writer audit logger backed by SQLite.

    Usage:
        logger = AuditLogger()                    # file-backed (default path)
        logger = AuditLogger(db_path=':memory:')  # in-process for tests
        logger.log(AuditEvent(...))
    """

    DEFAULT_DB_PATH = "audit.db"

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._path = db_path if db_path is not None else self.DEFAULT_DB_PATH
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute(_CREATE_TABLE)
        self._conn.execute(_CREATE_IDX_CORR)
        self._conn.execute(_CREATE_IDX_TS)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Public write API
    # ------------------------------------------------------------------

    def log(self, event: AuditEvent) -> AuditEvent:
        """Append an audit event; returns the event with id and timestamp set."""
        event.audit_event_id = event.audit_event_id or str(uuid.uuid4())
        event.timestamp_ms = event.timestamp_ms or int(time.time() * 1000)
        self._conn.execute(
            _INSERT,
            (
                event.audit_event_id,
                event.audit_correlation_id,
                event.event_group.value,
                event.event_type,
                event.summary,
                json.dumps(event.payload),
                event.timestamp_ms,
                event.authority_note,
            ),
        )
        self._conn.commit()
        return event

    # ------------------------------------------------------------------
    # Public read API (read-only helpers — not the primary write path)
    # ------------------------------------------------------------------

    def get_reader(self) -> "AuditReader":
        return AuditReader(self._conn)

    def close(self) -> None:
        self._conn.close()


class AuditReader:
    """Read-only view of the audit store.

    Intended for experiment tools, telemetry adapters, and test assertions.
    Must not be used as an authority source.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_by_correlation_id(self, audit_correlation_id: str) -> list[AuditEvent]:
        """Return all events for a given audit correlation ID, oldest first."""
        rows = self._conn.execute(
            "SELECT audit_event_id, audit_correlation_id, event_group, event_type, "
            "summary, payload_json, timestamp_ms, authority_note "
            "FROM audit_events WHERE audit_correlation_id = ? ORDER BY timestamp_ms ASC",
            (audit_correlation_id,),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def get_by_event_group(self, event_group: EventGroup) -> list[AuditEvent]:
        """Return all events for a given EventGroup, oldest first."""
        rows = self._conn.execute(
            "SELECT audit_event_id, audit_correlation_id, event_group, event_type, "
            "summary, payload_json, timestamp_ms, authority_note "
            "FROM audit_events WHERE event_group = ? ORDER BY timestamp_ms ASC",
            (event_group.value,),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def get_recent(self, limit: int = 50) -> list[AuditEvent]:
        """Return the most recent N events, newest first."""
        rows = self._conn.execute(
            "SELECT audit_event_id, audit_correlation_id, event_group, event_type, "
            "summary, payload_json, timestamp_ms, authority_note "
            "FROM audit_events ORDER BY timestamp_ms DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def get_summary(self, audit_correlation_id: str) -> AuditSummary:
        """Return a lightweight summary for a correlation ID."""
        events = self.get_by_correlation_id(audit_correlation_id)
        if not events:
            return AuditSummary(
                audit_correlation_id=audit_correlation_id,
                event_count=0,
                event_groups=[],
                earliest_ms=None,
                latest_ms=None,
            )
        groups = list(dict.fromkeys(e.event_group.value for e in events))
        return AuditSummary(
            audit_correlation_id=audit_correlation_id,
            event_count=len(events),
            event_groups=groups,
            earliest_ms=events[0].timestamp_ms,
            latest_ms=events[-1].timestamp_ms,
        )

    def count(self) -> int:
        """Total number of audit records in the store."""
        return self._conn.execute(
            "SELECT COUNT(*) FROM audit_events"
        ).fetchone()[0]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_event(row: tuple) -> AuditEvent:
        (eid, corr_id, group_val, etype, summary,
         payload_json, ts_ms, authority_note) = row
        event = AuditEvent(
            event_group=EventGroup(group_val),
            event_type=etype,
            audit_correlation_id=corr_id,
            summary=summary,
            payload=json.loads(payload_json),
            timestamp_ms=ts_ms,
            audit_event_id=eid,
            authority_note=authority_note,
        )
        return event
