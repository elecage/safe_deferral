"""Tests for AuditLogger and AuditReader (MM-09)."""

import pytest

from audit_logger.logger import AuditLogger, AuditReader
from audit_logger.models import AuditEvent, AuditSummary, EventGroup

AUDIT_ID = "test_audit_mm09"


@pytest.fixture
def logger():
    """Fresh in-memory logger for each test."""
    lg = AuditLogger(db_path=":memory:")
    yield lg
    lg.close()


@pytest.fixture
def reader(logger):
    return logger.get_reader()


def _event(
    group=EventGroup.ROUTING,
    event_type="policy_router_decision",
    audit_id=AUDIT_ID,
    summary="test event",
    payload=None,
):
    return AuditEvent(
        event_group=group,
        event_type=event_type,
        audit_correlation_id=audit_id,
        summary=summary,
        payload=payload or {},
    )


# ------------------------------------------------------------------
# AuditLogger.log() — basic write
# ------------------------------------------------------------------

class TestAuditLoggerWrite:
    def test_log_returns_event(self, logger):
        event = _event()
        result = logger.log(event)
        assert result is event

    def test_log_assigns_audit_event_id(self, logger):
        event = _event()
        assert event.audit_event_id is None
        logger.log(event)
        assert event.audit_event_id is not None

    def test_log_assigns_timestamp_ms(self, logger):
        event = _event()
        assert event.timestamp_ms is None
        logger.log(event)
        assert isinstance(event.timestamp_ms, int)
        assert event.timestamp_ms > 0

    def test_log_preserves_custom_audit_event_id(self, logger):
        event = _event()
        event.audit_event_id = "my-event-id-001"
        logger.log(event)
        assert event.audit_event_id == "my-event-id-001"

    def test_log_preserves_custom_timestamp(self, logger):
        event = _event()
        event.timestamp_ms = 1710000000000
        logger.log(event)
        assert event.timestamp_ms == 1710000000000

    def test_log_multiple_events(self, logger, reader):
        for i in range(5):
            logger.log(_event(summary=f"event {i}"))
        assert reader.count() == 5

    def test_log_different_groups(self, logger, reader):
        logger.log(_event(group=EventGroup.ROUTING))
        logger.log(_event(group=EventGroup.VALIDATION))
        logger.log(_event(group=EventGroup.DISPATCH))
        assert reader.count() == 3

    def test_log_payload_stored(self, logger, reader):
        event = _event(payload={"route_class": "CLASS_1", "trigger_id": "none"})
        logger.log(event)
        retrieved = reader.get_by_correlation_id(AUDIT_ID)
        assert retrieved[0].payload["route_class"] == "CLASS_1"

    def test_log_authority_note_in_record(self, logger, reader):
        logger.log(_event())
        events = reader.get_by_correlation_id(AUDIT_ID)
        assert "evidence" in events[0].authority_note.lower()

    def test_duplicate_audit_event_id_raises(self, logger):
        e1 = _event()
        e1.audit_event_id = "dup-id"
        e2 = _event()
        e2.audit_event_id = "dup-id"
        logger.log(e1)
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            logger.log(e2)


# ------------------------------------------------------------------
# AuditReader.get_by_correlation_id
# ------------------------------------------------------------------

class TestReaderByCorrelationId:
    def test_returns_matching_events(self, logger, reader):
        logger.log(_event(audit_id="corr-A"))
        logger.log(_event(audit_id="corr-A"))
        logger.log(_event(audit_id="corr-B"))
        events = reader.get_by_correlation_id("corr-A")
        assert len(events) == 2

    def test_returns_empty_for_unknown_id(self, reader):
        assert reader.get_by_correlation_id("no-such-id") == []

    def test_events_ordered_oldest_first(self, logger, reader):
        e1 = _event(audit_id="order-test")
        e1.timestamp_ms = 1000
        e2 = _event(audit_id="order-test")
        e2.timestamp_ms = 2000
        logger.log(e1)
        logger.log(e2)
        events = reader.get_by_correlation_id("order-test")
        assert events[0].timestamp_ms <= events[1].timestamp_ms

    def test_returned_events_have_correct_type(self, logger, reader):
        logger.log(_event())
        events = reader.get_by_correlation_id(AUDIT_ID)
        assert isinstance(events[0], AuditEvent)

    def test_event_group_round_trips(self, logger, reader):
        logger.log(_event(group=EventGroup.ESCALATION, audit_id="grp-test"))
        events = reader.get_by_correlation_id("grp-test")
        assert events[0].event_group == EventGroup.ESCALATION


# ------------------------------------------------------------------
# AuditReader.get_by_event_group
# ------------------------------------------------------------------

class TestReaderByEventGroup:
    def test_returns_only_matching_group(self, logger, reader):
        logger.log(_event(group=EventGroup.DISPATCH, audit_id="g1"))
        logger.log(_event(group=EventGroup.DISPATCH, audit_id="g2"))
        logger.log(_event(group=EventGroup.ACK, audit_id="g3"))
        events = reader.get_by_event_group(EventGroup.DISPATCH)
        assert len(events) == 2
        for e in events:
            assert e.event_group == EventGroup.DISPATCH

    def test_returns_empty_for_unused_group(self, reader):
        assert reader.get_by_event_group(EventGroup.FAILURE) == []


# ------------------------------------------------------------------
# AuditReader.get_recent
# ------------------------------------------------------------------

class TestReaderGetRecent:
    def test_returns_newest_first(self, logger, reader):
        for i in range(5):
            e = _event(summary=f"event {i}")
            e.timestamp_ms = 1000 + i
            logger.log(e)
        events = reader.get_recent(limit=5)
        assert events[0].timestamp_ms >= events[-1].timestamp_ms

    def test_limit_respected(self, logger, reader):
        for _ in range(10):
            logger.log(_event())
        events = reader.get_recent(limit=3)
        assert len(events) == 3

    def test_returns_all_when_fewer_than_limit(self, logger, reader):
        for _ in range(4):
            logger.log(_event())
        events = reader.get_recent(limit=20)
        assert len(events) == 4


# ------------------------------------------------------------------
# AuditReader.get_summary
# ------------------------------------------------------------------

class TestReaderSummary:
    def test_summary_event_count(self, logger, reader):
        for _ in range(3):
            logger.log(_event(audit_id="sum-test"))
        summary = reader.get_summary("sum-test")
        assert summary.event_count == 3

    def test_summary_empty_for_unknown_id(self, reader):
        summary = reader.get_summary("unknown-corr")
        assert summary.event_count == 0
        assert summary.event_groups == []
        assert summary.earliest_ms is None
        assert summary.latest_ms is None

    def test_summary_event_groups_unique(self, logger, reader):
        logger.log(_event(group=EventGroup.ROUTING, audit_id="grp-sum"))
        logger.log(_event(group=EventGroup.ROUTING, audit_id="grp-sum"))
        logger.log(_event(group=EventGroup.VALIDATION, audit_id="grp-sum"))
        summary = reader.get_summary("grp-sum")
        assert len(summary.event_groups) == 2
        assert "routing" in summary.event_groups
        assert "validation" in summary.event_groups

    def test_summary_timestamps(self, logger, reader):
        e1 = _event(audit_id="ts-sum")
        e1.timestamp_ms = 5000
        e2 = _event(audit_id="ts-sum")
        e2.timestamp_ms = 9000
        logger.log(e1)
        logger.log(e2)
        summary = reader.get_summary("ts-sum")
        assert summary.earliest_ms == 5000
        assert summary.latest_ms == 9000

    def test_summary_type(self, logger, reader):
        logger.log(_event(audit_id="type-sum"))
        summary = reader.get_summary("type-sum")
        assert isinstance(summary, AuditSummary)


# ------------------------------------------------------------------
# AuditReader.count
# ------------------------------------------------------------------

class TestReaderCount:
    def test_count_zero_initially(self, reader):
        assert reader.count() == 0

    def test_count_increments(self, logger, reader):
        logger.log(_event())
        logger.log(_event())
        assert reader.count() == 2


# ------------------------------------------------------------------
# AuditEvent.to_dict schema shape
# ------------------------------------------------------------------

class TestAuditEventToDict:
    def test_to_dict_has_required_fields(self, logger, reader):
        logger.log(_event())
        events = reader.get_by_correlation_id(AUDIT_ID)
        d = events[0].to_dict()
        for field in ("audit_event_id", "audit_correlation_id", "event_group",
                      "event_type", "summary", "payload", "timestamp_ms",
                      "authority_note"):
            assert field in d, f"missing: {field}"

    def test_to_dict_event_group_is_string(self, logger, reader):
        logger.log(_event(group=EventGroup.CAREGIVER))
        events = reader.get_by_correlation_id(AUDIT_ID)
        d = events[0].to_dict()
        assert isinstance(d["event_group"], str)
        assert d["event_group"] == "caregiver"

    def test_to_dict_payload_is_dict(self, logger, reader):
        logger.log(_event(payload={"key": "value"}))
        events = reader.get_by_correlation_id(AUDIT_ID)
        d = events[0].to_dict()
        assert isinstance(d["payload"], dict)


# ------------------------------------------------------------------
# All EventGroup values can be logged and retrieved
# ------------------------------------------------------------------

class TestAllEventGroups:
    def test_all_groups_roundtrip(self, logger, reader):
        for group in EventGroup:
            logger.log(_event(group=group, audit_id=f"grp-{group.value}"))
        for group in EventGroup:
            events = reader.get_by_correlation_id(f"grp-{group.value}")
            assert len(events) == 1
            assert events[0].event_group == group
