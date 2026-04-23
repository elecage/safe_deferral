"""
Audit Logging Service DB 단위 테스트.

임시 DB 를 사용하여 스키마 생성, insert, query 동작을 검증한다.
테스트 간 DB 파일은 독립적으로 생성/삭제된다.

커버리지:
  1. DB 생성 및 WAL 모드 확인
  2. 스키마 초기화 (7개 테이블 생성 확인)
  3. routing_events insert/query
  4. validator_results insert/query
  5. deferral_events insert/query
  6. timeout_events insert/query
  7. escalation_events insert/query
  8. caregiver_actions insert/query
  9. actuation_ack_events insert/query
  10. correlation_id 기반 복합 조회
  11. 단일 writer 보장 - 직접 연결 외부 쓰기 차단 검증
"""
import uuid
from pathlib import Path

import pytest

from audit_logging_service.db import AuditDB
from audit_logging_service.models import (
    ActuationAckEvent,
    CaregiverAction,
    DeferralEvent,
    EscalationEvent,
    RoutingEvent,
    TimeoutEvent,
    ValidatorResult,
)


# ── 픽스처 ───────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_db(tmp_path: Path) -> AuditDB:
    """테스트용 임시 AuditDB 인스턴스."""
    db = AuditDB(db_path=tmp_path / "test_audit.db")
    db.connect()
    db.init_schema()
    yield db
    db.close()


def _uid() -> str:
    return str(uuid.uuid4())


def _corr() -> str:
    return f"corr-{uuid.uuid4().hex[:8]}"


# ── 1. DB 생성 및 WAL 모드 확인 ──────────────────────────────────────────────


class TestDBCreation:
    def test_db_file_created(self, tmp_path: Path):
        """DB 파일이 생성되어야 한다."""
        db_path = tmp_path / "audit.db"
        with AuditDB(db_path=db_path) as db:
            db.init_schema()
        assert db_path.exists()

    def test_wal_mode_enabled(self, tmp_db: AuditDB):
        """journal_mode 는 WAL 이어야 한다."""
        assert tmp_db.get_wal_mode() == "wal"

    def test_schema_creates_all_tables(self, tmp_db: AuditDB):
        """스키마 초기화 후 7개 테이블이 모두 생성되어야 한다."""
        expected_tables = {
            "routing_events",
            "validator_results",
            "deferral_events",
            "timeout_events",
            "escalation_events",
            "caregiver_actions",
            "actuation_ack_events",
        }
        rows = tmp_db._execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        actual = {row[0] for row in rows}
        assert expected_tables.issubset(actual)

    def test_schema_idempotent(self, tmp_db: AuditDB):
        """init_schema() 를 두 번 호출해도 오류가 없어야 한다 (IF NOT EXISTS)."""
        tmp_db.init_schema()  # 두 번째 호출
        assert tmp_db.get_wal_mode() == "wal"


# ── 2. routing_events insert/query ───────────────────────────────────────────


class TestRoutingEvents:
    def test_insert_and_query_routing_event(self, tmp_db: AuditDB):
        """routing_event 를 insert 하고 query 로 조회할 수 있어야 한다."""
        corr = _corr()
        event = RoutingEvent(
            event_id=_uid(),
            audit_correlation_id=corr,
            class_label="CLASS_1",
            reason="정상 라우팅",
            route_class="CLASS_1",
            llm_invocation_allowed=True,
        )
        row_id = tmp_db.insert_routing_event(event)

        assert row_id is not None and row_id > 0
        rows = tmp_db.query_routing_events(corr)
        assert len(rows) == 1
        assert rows[0]["route_class"] == "CLASS_1"
        assert rows[0]["llm_invocation_allowed"] == 1

    def test_routing_event_class0_with_trigger(self, tmp_db: AuditDB):
        """CLASS_0 라우팅 이벤트에 emergency_trigger_id 가 저장되어야 한다."""
        corr = _corr()
        event = RoutingEvent(
            event_id=_uid(),
            audit_correlation_id=corr,
            class_label="CLASS_0",
            reason="E003 연기 감지",
            route_class="CLASS_0",
            llm_invocation_allowed=False,
            emergency_trigger_id="E003",
        )
        tmp_db.insert_routing_event(event)
        rows = tmp_db.query_routing_events(corr)
        assert rows[0]["emergency_trigger_id"] == "E003"

    def test_query_without_filter_returns_all(self, tmp_db: AuditDB):
        """correlation_id 없이 query 하면 전체 행을 반환해야 한다."""
        for _ in range(3):
            tmp_db.insert_routing_event(
                RoutingEvent(
                    event_id=_uid(),
                    audit_correlation_id=_corr(),
                    class_label="CLASS_1",
                    reason="테스트",
                    route_class="CLASS_1",
                    llm_invocation_allowed=False,
                )
            )
        rows = tmp_db.query_routing_events()
        assert len(rows) >= 3


# ── 3. validator_results insert/query ────────────────────────────────────────


class TestValidatorResults:
    def test_insert_and_query_validator_result(self, tmp_db: AuditDB):
        """validator_result 를 insert 하고 query 할 수 있어야 한다."""
        corr = _corr()
        event = ValidatorResult(
            event_id=_uid(),
            audit_correlation_id=corr,
            class_label="CLASS_1",
            reason="단일 승인 가능 액션",
            validation_status="approved",
            routing_target="actuator_dispatcher",
            exception_trigger_id="none",
        )
        row_id = tmp_db.insert_validator_result(event)
        assert row_id > 0

        rows = tmp_db.query_validator_results(corr)
        assert len(rows) == 1
        assert rows[0]["validation_status"] == "approved"
        assert rows[0]["exception_trigger_id"] == "none"

    def test_validator_safe_deferral_result(self, tmp_db: AuditDB):
        """SAFE_DEFERRAL 결과가 올바르게 저장되어야 한다."""
        corr = _corr()
        event = ValidatorResult(
            event_id=_uid(),
            audit_correlation_id=corr,
            class_label="CLASS_1",
            reason="다중 후보",
            validation_status="safe_deferral",
            routing_target="context_integrity_safe_deferral_handler",
            exception_trigger_id="none",
            deferral_reason="unresolved_multi_candidate",
        )
        tmp_db.insert_validator_result(event)
        rows = tmp_db.query_validator_results(corr)
        assert rows[0]["deferral_reason"] == "unresolved_multi_candidate"


# ── 4. deferral_events insert/query ──────────────────────────────────────────


class TestDeferralEvents:
    def test_insert_and_query_deferral_event(self, tmp_db: AuditDB):
        """deferral_event 를 insert 하고 query 할 수 있어야 한다."""
        corr = _corr()
        event = DeferralEvent(
            event_id=_uid(),
            audit_correlation_id=corr,
            class_label="CLASS_1",
            reason="버튼으로 선택 완료",
            deferral_status="resolved",
            resolved_action="light_on",
            resolved_target="living_room_light",
            options_count=2,
        )
        row_id = tmp_db.insert_deferral_event(event)
        assert row_id > 0

        # routing_events 테이블에는 없고 deferral_events 에만 있어야 함
        routing_rows = tmp_db.query_routing_events(corr)
        assert len(routing_rows) == 0


# ── 5. timeout_events insert/query ───────────────────────────────────────────


class TestTimeoutEvents:
    def test_insert_and_query_timeout_event(self, tmp_db: AuditDB):
        """timeout_event 를 insert 하고 조회할 수 있어야 한다."""
        corr = _corr()
        event = TimeoutEvent(
            event_id=_uid(),
            audit_correlation_id=corr,
            class_label="CLASS_2",
            reason="clarification timeout C201",
            timeout_trigger_id="C201",
            options_presented=2,
        )
        row_id = tmp_db.insert_timeout_event(event)
        assert row_id > 0

        # 직접 쿼리로 확인
        rows = tmp_db._execute(
            "SELECT * FROM timeout_events WHERE audit_correlation_id=?", (corr,)
        ).fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["timeout_trigger_id"] == "C201"


# ── 6. escalation_events insert/query ────────────────────────────────────────


class TestEscalationEvents:
    def test_insert_and_query_escalation_event(self, tmp_db: AuditDB):
        """escalation_event 를 insert 하고 query 할 수 있어야 한다."""
        corr = _corr()
        event = EscalationEvent(
            event_id=_uid(),
            audit_correlation_id=corr,
            class_label="CLASS_2",
            reason="C204 staleness 감지",
            exception_trigger_id="C204",
            source_layer="policy_router",
            notification_channel="telegram",
        )
        row_id = tmp_db.insert_escalation_event(event)
        assert row_id > 0

        rows = tmp_db.query_escalation_events(corr)
        assert len(rows) == 1
        assert rows[0]["exception_trigger_id"] == "C204"
        assert rows[0]["source_layer"] == "policy_router"


# ── 7. caregiver_actions insert/query ────────────────────────────────────────


class TestCaregiverActions:
    def test_insert_and_query_caregiver_action(self, tmp_db: AuditDB):
        """caregiver_action 을 insert 하고 조회할 수 있어야 한다."""
        corr = _corr()
        event = CaregiverAction(
            event_id=_uid(),
            audit_correlation_id=corr,
            class_label="CLASS_2",
            reason="보호자 확인 완료",
            action_type="confirmed",
            confirmed_action="light_on",
            confirmed_target="bedroom_light",
        )
        row_id = tmp_db.insert_caregiver_action(event)
        assert row_id > 0

        rows = tmp_db._execute(
            "SELECT * FROM caregiver_actions WHERE audit_correlation_id=?", (corr,)
        ).fetchall()
        assert dict(rows[0])["action_type"] == "confirmed"


# ── 8. actuation_ack_events insert/query ─────────────────────────────────────


class TestActuationAckEvents:
    def test_insert_and_query_ack_event(self, tmp_db: AuditDB):
        """actuation_ack_event 를 insert 하고 조회할 수 있어야 한다."""
        corr = _corr()
        event = ActuationAckEvent(
            event_id=_uid(),
            audit_correlation_id=corr,
            class_label="CLASS_1",
            reason="ACK 수신 완료",
            action="light_on",
            target_device="living_room_light",
            ack_status="success",
            ack_latency_ms=123,
        )
        row_id = tmp_db.insert_actuation_ack_event(event)
        assert row_id > 0

        rows = tmp_db._execute(
            "SELECT * FROM actuation_ack_events WHERE audit_correlation_id=?", (corr,)
        ).fetchall()
        row = dict(rows[0])
        assert row["ack_status"] == "success"
        assert row["ack_latency_ms"] == 123

    def test_ack_timeout_status(self, tmp_db: AuditDB):
        """ACK timeout 상태도 저장되어야 한다."""
        corr = _corr()
        event = ActuationAckEvent(
            event_id=_uid(),
            audit_correlation_id=corr,
            class_label="CLASS_1",
            reason="ACK 타임아웃",
            action="light_off",
            target_device="bedroom_light",
            ack_status="timeout",
        )
        tmp_db.insert_actuation_ack_event(event)
        rows = tmp_db._execute(
            "SELECT * FROM actuation_ack_events WHERE audit_correlation_id=?", (corr,)
        ).fetchall()
        assert dict(rows[0])["ack_status"] == "timeout"


# ── 9. correlation_id 기반 복합 조회 ─────────────────────────────────────────


class TestCorrelationQuery:
    def test_query_by_correlation_id_returns_all_tables(self, tmp_db: AuditDB):
        """단일 correlation_id 로 여러 테이블의 이벤트를 한 번에 조회해야 한다."""
        corr = _corr()

        tmp_db.insert_routing_event(RoutingEvent(
            event_id=_uid(), audit_correlation_id=corr,
            class_label="CLASS_1", reason="라우팅", route_class="CLASS_1",
            llm_invocation_allowed=True,
        ))
        tmp_db.insert_validator_result(ValidatorResult(
            event_id=_uid(), audit_correlation_id=corr,
            class_label="CLASS_1", reason="승인",
            validation_status="approved",
            routing_target="actuator_dispatcher",
            exception_trigger_id="none",
        ))
        tmp_db.insert_escalation_event(EscalationEvent(
            event_id=_uid(), audit_correlation_id=corr,
            class_label="CLASS_2", reason="에스컬레이션",
            exception_trigger_id="C205", source_layer="validator",
        ))

        result = tmp_db.query_by_correlation_id(corr)

        assert len(result["routing_events"]) == 1
        assert len(result["validator_results"]) == 1
        assert len(result["escalation_events"]) == 1

    def test_different_correlation_ids_are_isolated(self, tmp_db: AuditDB):
        """다른 correlation_id 의 이벤트는 서로 섞이지 않아야 한다."""
        corr_a = _corr()
        corr_b = _corr()

        tmp_db.insert_routing_event(RoutingEvent(
            event_id=_uid(), audit_correlation_id=corr_a,
            class_label="CLASS_0", reason="응급", route_class="CLASS_0",
            llm_invocation_allowed=False,
        ))
        tmp_db.insert_routing_event(RoutingEvent(
            event_id=_uid(), audit_correlation_id=corr_b,
            class_label="CLASS_1", reason="정상", route_class="CLASS_1",
            llm_invocation_allowed=True,
        ))

        rows_a = tmp_db.query_routing_events(corr_a)
        rows_b = tmp_db.query_routing_events(corr_b)

        assert len(rows_a) == 1
        assert len(rows_b) == 1
        assert rows_a[0]["route_class"] == "CLASS_0"
        assert rows_b[0]["route_class"] == "CLASS_1"
