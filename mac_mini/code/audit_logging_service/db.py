"""
SQLite 단일 writer 감사 로깅 DB 모듈.

핵심 원칙:
  - SQLite 는 반드시 WAL 모드로 동작한다.
  - 이 모듈만이 DB 에 직접 쓰기를 수행한다. 다른 서비스는 절대 직접 쓰지 않는다.
  - 각 insert 함수는 순차적으로 호출되며 단일 writer 보장이 전제된다.

스키마 초기화는 init_schema() 를 호출하거나 init_schema.py 스크립트를 실행한다.
"""
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    ActuationAckEvent,
    AuditEventBase,
    CaregiverAction,
    DeferralEvent,
    EscalationEvent,
    RoutingEvent,
    TimeoutEvent,
    ValidatorResult,
)

logger = logging.getLogger(__name__)

# 기본 DB 경로 (Mac mini 운영 환경 기준)
DEFAULT_DB_PATH = Path.home() / "smarthome_workspace" / "db" / "audit_log.db"


class AuditDB:
    """
    SQLite 단일 writer DB 클래스.
    인스턴스 하나가 전체 audit 쓰기 권한을 독점한다.
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """DB 연결을 열고 WAL 모드를 활성화한다."""
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # WAL 모드 활성화 - 동시 읽기 성능 향상 및 쓰기 안전성 보장
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._conn.commit()
        logger.info("DB 연결 완료 (WAL 모드) | path=%s", self.db_path)

    def close(self) -> None:
        """DB 연결을 닫는다."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("DB 연결 종료")

    def __enter__(self) -> "AuditDB":
        self.connect()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """단일 쿼리를 실행한다. 연결이 없으면 예외를 발생시킨다."""
        if self._conn is None:
            raise RuntimeError("DB 연결이 없습니다. connect() 를 먼저 호출하세요.")
        return self._conn.execute(sql, params)

    # ── 스키마 초기화 ─────────────────────────────────────────────────────────

    def init_schema(self) -> None:
        """
        모든 감사 로그 테이블을 생성한다. 이미 존재하면 건너뛴다.
        각 테이블에는 공통 컬럼(timestamp_ms, event_id, audit_correlation_id,
        class_label, reason, payload_summary)이 포함된다.
        """
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS routing_events (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms          INTEGER NOT NULL,
                event_id              TEXT    NOT NULL,
                audit_correlation_id  TEXT    NOT NULL,
                class_label           TEXT    NOT NULL,
                reason                TEXT    NOT NULL,
                payload_summary       TEXT,
                source_node_id        TEXT,
                route_class           TEXT    NOT NULL,
                llm_invocation_allowed INTEGER NOT NULL DEFAULT 0,
                emergency_trigger_id  TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS validator_results (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms          INTEGER NOT NULL,
                event_id              TEXT    NOT NULL,
                audit_correlation_id  TEXT    NOT NULL,
                class_label           TEXT    NOT NULL,
                reason                TEXT    NOT NULL,
                payload_summary       TEXT,
                validation_status     TEXT    NOT NULL,
                routing_target        TEXT    NOT NULL,
                exception_trigger_id  TEXT    NOT NULL DEFAULT 'none',
                deferral_reason       TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS deferral_events (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms          INTEGER NOT NULL,
                event_id              TEXT    NOT NULL,
                audit_correlation_id  TEXT    NOT NULL,
                class_label           TEXT    NOT NULL,
                reason                TEXT    NOT NULL,
                payload_summary       TEXT,
                deferral_status       TEXT    NOT NULL,
                deferral_reason       TEXT,
                resolved_action       TEXT,
                resolved_target       TEXT,
                options_count         INTEGER NOT NULL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS timeout_events (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms          INTEGER NOT NULL,
                event_id              TEXT    NOT NULL,
                audit_correlation_id  TEXT    NOT NULL,
                class_label           TEXT    NOT NULL,
                reason                TEXT    NOT NULL,
                payload_summary       TEXT,
                timeout_trigger_id    TEXT    NOT NULL DEFAULT 'C201',
                options_presented     INTEGER NOT NULL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS escalation_events (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms          INTEGER NOT NULL,
                event_id              TEXT    NOT NULL,
                audit_correlation_id  TEXT    NOT NULL,
                class_label           TEXT    NOT NULL,
                reason                TEXT    NOT NULL,
                payload_summary       TEXT,
                exception_trigger_id  TEXT    NOT NULL,
                source_layer          TEXT    NOT NULL,
                notification_channel  TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS caregiver_actions (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms          INTEGER NOT NULL,
                event_id              TEXT    NOT NULL,
                audit_correlation_id  TEXT    NOT NULL,
                class_label           TEXT    NOT NULL,
                reason                TEXT    NOT NULL,
                payload_summary       TEXT,
                action_type           TEXT    NOT NULL,
                confirmed_action      TEXT,
                confirmed_target      TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS actuation_ack_events (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms          INTEGER NOT NULL,
                event_id              TEXT    NOT NULL,
                audit_correlation_id  TEXT    NOT NULL,
                class_label           TEXT    NOT NULL,
                reason                TEXT    NOT NULL,
                payload_summary       TEXT,
                action                TEXT    NOT NULL,
                target_device         TEXT    NOT NULL,
                ack_status            TEXT    NOT NULL,
                ack_latency_ms        INTEGER
            )
            """,
        ]

        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_routing_correlation ON routing_events(audit_correlation_id)",
            "CREATE INDEX IF NOT EXISTS idx_validator_correlation ON validator_results(audit_correlation_id)",
            "CREATE INDEX IF NOT EXISTS idx_deferral_correlation ON deferral_events(audit_correlation_id)",
            "CREATE INDEX IF NOT EXISTS idx_timeout_correlation ON timeout_events(audit_correlation_id)",
            "CREATE INDEX IF NOT EXISTS idx_escalation_correlation ON escalation_events(audit_correlation_id)",
            "CREATE INDEX IF NOT EXISTS idx_caregiver_correlation ON caregiver_actions(audit_correlation_id)",
            "CREATE INDEX IF NOT EXISTS idx_ack_correlation ON actuation_ack_events(audit_correlation_id)",
        ]

        for ddl in ddl_statements:
            self._execute(ddl)
        for idx in index_statements:
            self._execute(idx)
        self._conn.commit()
        logger.info("DB 스키마 초기화 완료")

    # ── INSERT 함수 ───────────────────────────────────────────────────────────

    def insert_routing_event(self, event: RoutingEvent) -> int:
        """routing_events 에 라우팅 결정을 기록한다."""
        cur = self._execute(
            """
            INSERT INTO routing_events
              (timestamp_ms, event_id, audit_correlation_id, class_label, reason,
               payload_summary, source_node_id, route_class, llm_invocation_allowed,
               emergency_trigger_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp_ms,
                event.event_id,
                event.audit_correlation_id,
                event.class_label,
                event.reason,
                event.payload_summary,
                event.source_node_id,
                event.route_class,
                int(event.llm_invocation_allowed),
                event.emergency_trigger_id,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def insert_validator_result(self, event: ValidatorResult) -> int:
        """validator_results 에 검증 결과를 기록한다."""
        cur = self._execute(
            """
            INSERT INTO validator_results
              (timestamp_ms, event_id, audit_correlation_id, class_label, reason,
               payload_summary, validation_status, routing_target, exception_trigger_id,
               deferral_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp_ms,
                event.event_id,
                event.audit_correlation_id,
                event.class_label,
                event.reason,
                event.payload_summary,
                event.validation_status,
                event.routing_target,
                event.exception_trigger_id,
                event.deferral_reason,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def insert_deferral_event(self, event: DeferralEvent) -> int:
        """deferral_events 에 safe deferral 세션 이벤트를 기록한다."""
        cur = self._execute(
            """
            INSERT INTO deferral_events
              (timestamp_ms, event_id, audit_correlation_id, class_label, reason,
               payload_summary, deferral_status, deferral_reason, resolved_action,
               resolved_target, options_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp_ms,
                event.event_id,
                event.audit_correlation_id,
                event.class_label,
                event.reason,
                event.payload_summary,
                event.deferral_status,
                event.deferral_reason,
                event.resolved_action,
                event.resolved_target,
                event.options_count,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def insert_timeout_event(self, event: TimeoutEvent) -> int:
        """timeout_events 에 C201 타임아웃 이벤트를 기록한다."""
        cur = self._execute(
            """
            INSERT INTO timeout_events
              (timestamp_ms, event_id, audit_correlation_id, class_label, reason,
               payload_summary, timeout_trigger_id, options_presented)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp_ms,
                event.event_id,
                event.audit_correlation_id,
                event.class_label,
                event.reason,
                event.payload_summary,
                event.timeout_trigger_id,
                event.options_presented,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def insert_escalation_event(self, event: EscalationEvent) -> int:
        """escalation_events 에 CLASS_2 에스컬레이션을 기록한다."""
        cur = self._execute(
            """
            INSERT INTO escalation_events
              (timestamp_ms, event_id, audit_correlation_id, class_label, reason,
               payload_summary, exception_trigger_id, source_layer, notification_channel)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp_ms,
                event.event_id,
                event.audit_correlation_id,
                event.class_label,
                event.reason,
                event.payload_summary,
                event.exception_trigger_id,
                event.source_layer,
                event.notification_channel,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def insert_caregiver_action(self, event: CaregiverAction) -> int:
        """caregiver_actions 에 보호자 개입 이벤트를 기록한다."""
        cur = self._execute(
            """
            INSERT INTO caregiver_actions
              (timestamp_ms, event_id, audit_correlation_id, class_label, reason,
               payload_summary, action_type, confirmed_action, confirmed_target)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp_ms,
                event.event_id,
                event.audit_correlation_id,
                event.class_label,
                event.reason,
                event.payload_summary,
                event.action_type,
                event.confirmed_action,
                event.confirmed_target,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def insert_actuation_ack_event(self, event: ActuationAckEvent) -> int:
        """actuation_ack_events 에 ACK 결과를 기록한다."""
        cur = self._execute(
            """
            INSERT INTO actuation_ack_events
              (timestamp_ms, event_id, audit_correlation_id, class_label, reason,
               payload_summary, action, target_device, ack_status, ack_latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp_ms,
                event.event_id,
                event.audit_correlation_id,
                event.class_label,
                event.reason,
                event.payload_summary,
                event.action,
                event.target_device,
                event.ack_status,
                event.ack_latency_ms,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ── QUERY 함수 ────────────────────────────────────────────────────────────

    def query_routing_events(
        self, correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """routing_events 를 조회한다. correlation_id 로 필터 가능."""
        if correlation_id:
            rows = self._execute(
                "SELECT * FROM routing_events WHERE audit_correlation_id=? ORDER BY timestamp_ms",
                (correlation_id,),
            ).fetchall()
        else:
            rows = self._execute(
                "SELECT * FROM routing_events ORDER BY timestamp_ms"
            ).fetchall()
        return [dict(row) for row in rows]

    def query_validator_results(
        self, correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """validator_results 를 조회한다."""
        if correlation_id:
            rows = self._execute(
                "SELECT * FROM validator_results WHERE audit_correlation_id=? ORDER BY timestamp_ms",
                (correlation_id,),
            ).fetchall()
        else:
            rows = self._execute(
                "SELECT * FROM validator_results ORDER BY timestamp_ms"
            ).fetchall()
        return [dict(row) for row in rows]

    def query_escalation_events(
        self, correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """escalation_events 를 조회한다."""
        if correlation_id:
            rows = self._execute(
                "SELECT * FROM escalation_events WHERE audit_correlation_id=? ORDER BY timestamp_ms",
                (correlation_id,),
            ).fetchall()
        else:
            rows = self._execute(
                "SELECT * FROM escalation_events ORDER BY timestamp_ms"
            ).fetchall()
        return [dict(row) for row in rows]

    def query_by_correlation_id(self, correlation_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        단일 correlation_id 에 연결된 모든 이벤트를 테이블별로 반환한다.
        closed-loop verification 에서 감사 체인 추적에 사용한다.
        """
        return {
            "routing_events": self.query_routing_events(correlation_id),
            "validator_results": self.query_validator_results(correlation_id),
            "escalation_events": self.query_escalation_events(correlation_id),
        }

    def get_wal_mode(self) -> str:
        """현재 journal_mode 를 반환한다 (WAL 확인용)."""
        row = self._execute("PRAGMA journal_mode;").fetchone()
        return row[0] if row else "unknown"
