"""Tests for TelemetryAdapter (MM-10)."""

import pytest

from audit_logger.logger import AuditLogger
from audit_logger.models import AuditEvent, EventGroup
from caregiver_escalation.backend import CaregiverEscalationBackend
from caregiver_escalation.models import CaregiverDecision
from class2_clarification_manager.manager import Class2ClarificationManager
from deterministic_validator.models import (
    ExecutablePayload,
    RoutingTarget,
    ValidationStatus,
    ValidatorResult,
)
from low_risk_dispatcher.dispatcher import LowRiskDispatcher
from low_risk_dispatcher.models import DispatchStatus
from policy_router.models import PolicyRouterResult, RouteClass
from telemetry_adapter.adapter import TelemetryAdapter
from telemetry_adapter.models import TelemetrySnapshot

AUDIT_ID = "test_audit_mm10"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _router_result(route_class=RouteClass.CLASS_1, trigger_id=None, ts=1710000000000):
    return PolicyRouterResult(
        route_class=route_class,
        trigger_id=trigger_id,
        llm_invocation_allowed=True,
        candidate_generation_allowed=True,
        unresolved_reason=None,
        source_node_id="esp32.bounded_input_node",
        audit_correlation_id=AUDIT_ID,
        network_status="online",
        routed_at_ms=ts,
        pure_context_payload={},
    )


def _validator_result(status=ValidationStatus.APPROVED):
    return ValidatorResult(
        validation_status=status,
        routing_target=RoutingTarget.ACTUATOR_DISPATCHER,
        exception_trigger_id="none",
        executable_payload=ExecutablePayload(
            action="light_on", target_device="living_room_light", requires_ack=True
        ) if status == ValidationStatus.APPROVED else None,
        deferral_reason=None,
        audit_correlation_id=AUDIT_ID,
    )


def _dispatch_record():
    dispatcher = LowRiskDispatcher()
    result = dispatcher.dispatch(_validator_result(), command_id="cmd-tel-001")
    return result.dispatch_record


class _RecordingPublisher:
    def __init__(self):
        self.calls = []

    def publish(self, topic, payload, qos=1):
        self.calls.append({"topic": topic, "payload": payload})


@pytest.fixture
def adapter():
    return TelemetryAdapter()


# ------------------------------------------------------------------
# Initial snapshot — all None
# ------------------------------------------------------------------

class TestInitialSnapshot:
    def test_snapshot_route_is_none_initially(self, adapter):
        snap = adapter.get_snapshot()
        assert snap.route is None

    def test_snapshot_validation_is_none_initially(self, adapter):
        snap = adapter.get_snapshot()
        assert snap.validation is None

    def test_snapshot_ack_is_none_initially(self, adapter):
        snap = adapter.get_snapshot()
        assert snap.ack is None

    def test_snapshot_class2_is_none_initially(self, adapter):
        snap = adapter.get_snapshot()
        assert snap.class2 is None

    def test_snapshot_escalation_is_none_initially(self, adapter):
        snap = adapter.get_snapshot()
        assert snap.escalation is None

    def test_snapshot_has_snapshot_id(self, adapter):
        snap = adapter.get_snapshot()
        assert snap.snapshot_id is not None

    def test_snapshot_has_generated_at_ms(self, adapter):
        snap = adapter.get_snapshot()
        assert isinstance(snap.generated_at_ms, int)
        assert snap.generated_at_ms > 0


# ------------------------------------------------------------------
# update_route
# ------------------------------------------------------------------

class TestUpdateRoute:
    def test_route_class_stored(self, adapter):
        adapter.update_route(_router_result(RouteClass.CLASS_1))
        snap = adapter.get_snapshot()
        assert snap.route.route_class == "CLASS_1"

    def test_class2_route_stored(self, adapter):
        adapter.update_route(_router_result(RouteClass.CLASS_2, trigger_id="C204"))
        snap = adapter.get_snapshot()
        assert snap.route.route_class == "CLASS_2"
        assert snap.route.trigger_id == "C204"

    def test_route_timestamp_preserved(self, adapter):
        adapter.update_route(_router_result(ts=9999000))
        snap = adapter.get_snapshot()
        assert snap.route.timestamp_ms == 9999000


# ------------------------------------------------------------------
# update_validation
# ------------------------------------------------------------------

class TestUpdateValidation:
    def test_approved_status_stored(self, adapter):
        adapter.update_validation(_validator_result(ValidationStatus.APPROVED))
        snap = adapter.get_snapshot()
        assert snap.validation.validation_status == "approved"

    def test_safe_deferral_status_stored(self, adapter):
        adapter.update_validation(_validator_result(ValidationStatus.SAFE_DEFERRAL))
        snap = adapter.get_snapshot()
        assert snap.validation.validation_status == "safe_deferral"

    def test_exception_trigger_id_stored(self, adapter):
        result = _validator_result()
        result.exception_trigger_id = "C202"
        adapter.update_validation(result)
        snap = adapter.get_snapshot()
        assert snap.validation.exception_trigger_id == "C202"


# ------------------------------------------------------------------
# update_ack
# ------------------------------------------------------------------

class TestUpdateAck:
    def test_ack_dispatch_status_stored(self, adapter):
        record = _dispatch_record()
        adapter.update_ack(record)
        snap = adapter.get_snapshot()
        assert snap.ack.dispatch_status == "published"

    def test_ack_action_stored(self, adapter):
        record = _dispatch_record()
        adapter.update_ack(record)
        snap = adapter.get_snapshot()
        assert snap.ack.action == "light_on"

    def test_ack_target_device_stored(self, adapter):
        record = _dispatch_record()
        adapter.update_ack(record)
        snap = adapter.get_snapshot()
        assert snap.ack.target_device == "living_room_light"


# ------------------------------------------------------------------
# update_class2
# ------------------------------------------------------------------

class TestUpdateClass2:
    def test_class2_transition_target_stored(self, adapter):
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", AUDIT_ID)
        result = mgr.handle_timeout(session)
        adapter.update_class2(result)
        snap = adapter.get_snapshot()
        assert snap.class2.transition_target == "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"

    def test_class2_should_notify_stored(self, adapter):
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", AUDIT_ID)
        result = mgr.handle_timeout(session)
        adapter.update_class2(result)
        snap = adapter.get_snapshot()
        assert snap.class2.should_notify_caregiver is True

    def test_class2_unresolved_reason_stored(self, adapter):
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", AUDIT_ID)
        result = mgr.handle_timeout(session)
        adapter.update_class2(result)
        snap = adapter.get_snapshot()
        assert snap.class2.unresolved_reason == "insufficient_context"


# ------------------------------------------------------------------
# update_escalation
# ------------------------------------------------------------------

class TestUpdateEscalation:
    def _valid_payload(self):
        return {
            "event_summary": "Class 2 진입",
            "context_summary": "테스트 컨텍스트",
            "unresolved_reason": "insufficient_context",
            "manual_confirmation_path": "보호자 검토 경로",
        }

    def test_escalation_status_stored(self, adapter):
        backend = CaregiverEscalationBackend()
        result = backend.send_notification(self._valid_payload())
        adapter.update_escalation(result)
        snap = adapter.get_snapshot()
        assert snap.escalation.escalation_status == "pending"

    def test_escalation_channel_stored(self, adapter):
        backend = CaregiverEscalationBackend()
        result = backend.send_notification(self._valid_payload())
        adapter.update_escalation(result)
        snap = adapter.get_snapshot()
        assert snap.escalation.notification_channel == "telegram"

    def test_escalation_status_updates_after_response(self, adapter):
        backend = CaregiverEscalationBackend()
        result = backend.send_notification(self._valid_payload())
        backend.record_response(result, CaregiverDecision.APPROVED)
        adapter.update_escalation(result)
        snap = adapter.get_snapshot()
        assert snap.escalation.escalation_status == "approved"


# ------------------------------------------------------------------
# Audit event count via AuditReader
# ------------------------------------------------------------------

class TestAuditCount:
    def test_audit_count_zero_without_reader(self, adapter):
        snap = adapter.get_snapshot()
        assert snap.audit_event_count == 0

    def test_audit_count_from_reader(self):
        lg = AuditLogger(db_path=":memory:")
        for _ in range(4):
            lg.log(AuditEvent(
                event_group=EventGroup.ROUTING,
                event_type="test",
                audit_correlation_id=AUDIT_ID,
                summary="test",
            ))
        adapter = TelemetryAdapter(audit_reader=lg.get_reader())
        snap = adapter.get_snapshot()
        assert snap.audit_event_count == 4
        lg.close()


# ------------------------------------------------------------------
# MQTT publish
# ------------------------------------------------------------------

class TestPublish:
    def test_publish_sends_to_observation_topic(self):
        pub = _RecordingPublisher()
        adapter = TelemetryAdapter(mqtt_publisher=pub)
        adapter.publish()
        assert len(pub.calls) == 1
        assert pub.calls[0]["topic"] == "safe_deferral/dashboard/observation"

    def test_publish_returns_snapshot(self):
        adapter = TelemetryAdapter()
        snap = adapter.publish()
        assert isinstance(snap, TelemetrySnapshot)

    def test_publish_payload_has_authority_note(self):
        pub = _RecordingPublisher()
        adapter = TelemetryAdapter(mqtt_publisher=pub)
        adapter.publish()
        payload = pub.calls[0]["payload"]
        assert "authority_note" in payload
        assert "read-only" in payload["authority_note"].lower()

    def test_publish_ack_only_sends_to_observation_topic(self):
        pub = _RecordingPublisher()
        adapter = TelemetryAdapter(mqtt_publisher=pub)
        adapter.publish_ack_only(_dispatch_record())
        assert len(pub.calls) == 1
        assert pub.calls[0]["topic"] == "safe_deferral/dashboard/observation"

    def test_publish_ack_only_snapshot_has_ack_no_route(self):
        """ACK-only snapshot must not carry route/validation from shared state."""
        pub = _RecordingPublisher()
        adapter = TelemetryAdapter(mqtt_publisher=pub)
        # Simulate leftover route state from a previous CLASS_0 event
        adapter.update_route(_router_result(RouteClass.CLASS_0, trigger_id="E001"))
        # Late ACK arrives — must publish isolated snapshot
        adapter.publish_ack_only(_dispatch_record())
        payload = pub.calls[0]["payload"]
        assert payload["ack"] is not None
        assert payload["ack"]["action"] == "light_on"
        assert payload["route"] is None       # must NOT carry CLASS_0 route
        assert payload["validation"] is None

    def test_publish_ack_only_does_not_modify_shared_state(self):
        """publish_ack_only must not mutate the adapter's shared fields."""
        adapter = TelemetryAdapter()
        adapter.update_route(_router_result(RouteClass.CLASS_0))
        adapter.publish_ack_only(_dispatch_record())
        # Shared route state must be unchanged
        assert adapter.get_snapshot().route is not None
        assert adapter.get_snapshot().route.route_class == "CLASS_0"

    def test_publish_ack_only_contains_command_id_and_audit_id(self):
        """ACK-only snapshot must carry command_id and audit_correlation_id for traceability."""
        pub = _RecordingPublisher()
        adapter = TelemetryAdapter(mqtt_publisher=pub)
        adapter.publish_ack_only(_dispatch_record())
        payload = pub.calls[0]["payload"]
        assert payload["ack"]["command_id"] == "cmd-tel-001"
        assert payload["ack"]["audit_correlation_id"] == AUDIT_ID

    def test_publish_c205_snapshot_carries_audit_correlation_id(self):
        """C205 snapshot must carry audit_correlation_id for traceability."""
        pub = _RecordingPublisher()
        adapter = TelemetryAdapter(mqtt_publisher=pub)

        mgr = Class2ClarificationManager()
        session = mgr.start_session("C205", AUDIT_ID)
        class2_result = mgr.handle_timeout(session, trigger_id="C205")

        backend = CaregiverEscalationBackend()
        esc_result = backend.send_notification({
            "event_summary": "Class 2 진입: C205 (actuation_ack_timeout)",
            "context_summary": "액추에이션 ACK 미수신",
            "unresolved_reason": "actuation_ack_timeout",
            "manual_confirmation_path": "caregiver_telegram_response",
        })
        adapter.publish_c205_snapshot(class2_result, esc_result, audit_correlation_id=AUDIT_ID)
        payload = pub.calls[0]["payload"]
        assert payload["audit_correlation_id"] == AUDIT_ID

    def test_publish_c205_snapshot_has_class2_and_escalation_no_route(self):
        """C205 snapshot must not carry route/validation from shared state."""
        pub = _RecordingPublisher()
        adapter = TelemetryAdapter(mqtt_publisher=pub)
        adapter.update_route(_router_result(RouteClass.CLASS_1))

        mgr = Class2ClarificationManager()
        session = mgr.start_session("C205", AUDIT_ID)
        class2_result = mgr.handle_timeout(session, trigger_id="C205")

        backend = CaregiverEscalationBackend()
        esc_result = backend.send_notification({
            "event_summary": "Class 2 진입: C205 (actuation_ack_timeout)",
            "context_summary": "액추에이션 ACK 미수신",
            "unresolved_reason": "actuation_ack_timeout",
            "manual_confirmation_path": "caregiver_telegram_response",
        })
        adapter.publish_c205_snapshot(class2_result, esc_result, audit_correlation_id=AUDIT_ID)

        payload = pub.calls[0]["payload"]
        assert payload["class2"] is not None
        assert payload["escalation"] is not None
        assert payload["escalation"]["escalation_status"] == "pending"
        assert payload["route"] is None       # must NOT carry CLASS_1 route
        assert payload["validation"] is None


# ------------------------------------------------------------------
# reset
# ------------------------------------------------------------------

class TestReset:
    def test_reset_clears_route(self, adapter):
        adapter.update_route(_router_result())
        adapter.reset()
        assert adapter.get_snapshot().route is None

    def test_reset_clears_validation(self, adapter):
        adapter.update_validation(_validator_result())
        adapter.reset()
        assert adapter.get_snapshot().validation is None

    def test_reset_clears_ack(self, adapter):
        adapter.update_ack(_dispatch_record())
        adapter.reset()
        assert adapter.get_snapshot().ack is None

    def test_reset_clears_class2(self, adapter):
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", AUDIT_ID)
        adapter.update_class2(mgr.handle_timeout(session))
        adapter.reset()
        assert adapter.get_snapshot().class2 is None

    def test_reset_clears_escalation(self, adapter):
        backend = CaregiverEscalationBackend()
        result = backend.send_notification({
            "event_summary": "test",
            "context_summary": "test ctx",
            "unresolved_reason": "insufficient_context",
            "manual_confirmation_path": "path",
        })
        adapter.update_escalation(result)
        adapter.reset()
        assert adapter.get_snapshot().escalation is None

    def test_reset_clears_all_fields_at_once(self, adapter):
        """Simulate CLASS_1 event, then reset: all fields must be None."""
        adapter.update_route(_router_result(RouteClass.CLASS_1))
        adapter.update_validation(_validator_result(ValidationStatus.APPROVED))
        adapter.update_ack(_dispatch_record())
        adapter.reset()
        snap = adapter.get_snapshot()
        assert snap.route is None
        assert snap.validation is None
        assert snap.ack is None
        assert snap.class2 is None
        assert snap.escalation is None


class TestCrossEventIsolation:
    """Snapshot must not carry state from a previous event into the next."""

    def test_class1_validation_not_visible_after_class0_reset(self, adapter):
        """After CLASS_1 event, reset, then CLASS_0 route: validation must be None."""
        # Simulate CLASS_1 completion
        adapter.update_route(_router_result(RouteClass.CLASS_1))
        adapter.update_validation(_validator_result(ValidationStatus.APPROVED))
        adapter.update_ack(_dispatch_record())

        # New event starts — reset happens first
        adapter.reset()
        adapter.update_route(_router_result(RouteClass.CLASS_0, trigger_id="E001"))

        snap = adapter.get_snapshot()
        assert snap.route.route_class == "CLASS_0"
        assert snap.validation is None  # must NOT carry CLASS_1 approved state
        assert snap.ack is None         # must NOT carry CLASS_1 published state

    def test_class0_escalation_not_visible_after_class1_reset(self, adapter):
        """After CLASS_0 escalation, reset, then CLASS_1 route: escalation must be None."""
        backend = CaregiverEscalationBackend()
        esc_result = backend.send_notification({
            "event_summary": "긴급 상황 감지",
            "context_summary": "CLASS_0 emergency",
            "unresolved_reason": "emergency_event",
            "manual_confirmation_path": "path",
        })
        adapter.update_route(_router_result(RouteClass.CLASS_0, trigger_id="E001"))
        adapter.update_escalation(esc_result)

        # New event starts — reset happens first
        adapter.reset()
        adapter.update_route(_router_result(RouteClass.CLASS_1))
        adapter.update_validation(_validator_result(ValidationStatus.APPROVED))

        snap = adapter.get_snapshot()
        assert snap.route.route_class == "CLASS_1"
        assert snap.escalation is None  # must NOT carry CLASS_0 escalation state

    def test_class0_escalation_visible_in_same_event_snapshot(self, adapter):
        """CLASS_0 escalation must be reflected in the same event's snapshot."""
        backend = CaregiverEscalationBackend()
        esc_result = backend.send_notification({
            "event_summary": "긴급 상황 감지: E002",
            "context_summary": "CLASS_0 emergency trigger — immediate caregiver notification.",
            "unresolved_reason": "emergency_event",
            "manual_confirmation_path": "caregiver_telegram_response",
        })
        adapter.update_route(_router_result(RouteClass.CLASS_0, trigger_id="E002"))
        adapter.update_escalation(esc_result)

        snap = adapter.get_snapshot()
        assert snap.route.route_class == "CLASS_0"
        assert snap.escalation is not None
        assert snap.escalation.escalation_status == "pending"
        assert snap.escalation.notification_channel == "telegram"


# ------------------------------------------------------------------
# TelemetrySnapshot.to_dict schema shape
# ------------------------------------------------------------------

class TestSnapshotToDict:
    def test_to_dict_has_required_keys(self, adapter):
        d = adapter.get_snapshot().to_dict()
        for key in ("snapshot_id", "generated_at_ms", "audit_correlation_id",
                    "route", "validation", "ack", "class2", "escalation",
                    "audit_event_count", "authority_note"):
            assert key in d, f"missing: {key}"

    def test_to_dict_route_none_when_not_set(self, adapter):
        d = adapter.get_snapshot().to_dict()
        assert d["route"] is None

    def test_to_dict_route_is_dict_when_set(self, adapter):
        adapter.update_route(_router_result())
        d = adapter.get_snapshot().to_dict()
        assert isinstance(d["route"], dict)
        assert "route_class" in d["route"]
