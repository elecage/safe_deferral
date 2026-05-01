"""Tests for Pipeline.handle_ack() ACK FAILURE → C205 escalation path (FIX-A).

paho.mqtt is not installed in the unit-test environment, so we stub the module
in sys.modules before importing main.  This is consistent with how main.py is
structured: MQTT is injected as a _PahoPublisher adapter, so the Pipeline logic
itself has no direct paho calls — only the entry-point main() does.
"""

import sys
import time
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from low_risk_dispatcher.models import AckStatus, DispatchRecord, DispatchStatus

# ---------------------------------------------------------------------------
# Stub paho so that `import main` succeeds without the package installed
# ---------------------------------------------------------------------------
_paho_stub = ModuleType("paho")
_paho_mqtt_stub = ModuleType("paho.mqtt")
_paho_client_stub = ModuleType("paho.mqtt.client")
_paho_client_stub.Client = MagicMock()
_paho_stub.mqtt = _paho_mqtt_stub
_paho_mqtt_stub.client = _paho_client_stub
sys.modules.setdefault("paho", _paho_stub)
sys.modules.setdefault("paho.mqtt", _paho_mqtt_stub)
sys.modules.setdefault("paho.mqtt.client", _paho_client_stub)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _MockPublisher:
    def __init__(self):
        self.calls = []

    def publish(self, topic, payload, qos=1):
        self.calls.append({"topic": topic, "payload": payload})


def _make_record(command_id="cmd-fix-a-001", audit_id="audit-fix-a"):
    return DispatchRecord(
        command_id=command_id,
        action="light_on",
        target_device="living_room_light",
        requires_ack=True,
        audit_correlation_id=audit_id,
        source_decision="validator_output",
        dispatch_status=DispatchStatus.PUBLISHED,
        published_at_ms=int(time.time() * 1000),
        ack_status=None,
        ack_received_at_ms=None,
        observed_state=None,
        ack_timeout_ms=5000,
    )


@pytest.fixture(scope="module")
def pipeline():
    with patch("main.AUDIT_DB_PATH", ":memory:"):
        import main  # noqa: PLC0415
        pub = _MockPublisher()
        p = main.Pipeline(mqtt_publisher=pub)
        yield p


# ---------------------------------------------------------------------------
# ACK FAILURE → C205 escalation
# ---------------------------------------------------------------------------

class TestAckFailureEscalation:
    def test_explicit_failure_status_triggers_c205(self, pipeline):
        record = _make_record("cmd-fa-001")
        pipeline._pending_acks["cmd-fa-001"] = record

        calls = []
        original = pipeline._escalate_c205
        pipeline._escalate_c205 = lambda audit_id: calls.append(audit_id)

        pipeline.handle_ack({"command_id": "cmd-fa-001",
                              "target_device": "living_room_light",
                              "ack_status": "failure"})

        pipeline._escalate_c205 = original
        assert calls == ["audit-fix-a"]

    def test_wrong_observed_state_triggers_c205(self, pipeline):
        """ack_status=success but observed_state mismatch → AckStatus.FAILURE → C205."""
        record = _make_record("cmd-fa-002")
        pipeline._pending_acks["cmd-fa-002"] = record

        calls = []
        original = pipeline._escalate_c205
        pipeline._escalate_c205 = lambda audit_id: calls.append(audit_id)

        pipeline.handle_ack({"command_id": "cmd-fa-002",
                              "target_device": "living_room_light",
                              "ack_status": "success",
                              "observed_state": "off"})   # light_on expects "on"

        pipeline._escalate_c205 = original
        assert len(calls) == 1

    def test_wrong_target_device_triggers_c205(self, pipeline):
        record = _make_record("cmd-fa-003")
        pipeline._pending_acks["cmd-fa-003"] = record

        calls = []
        original = pipeline._escalate_c205
        pipeline._escalate_c205 = lambda audit_id: calls.append(audit_id)

        pipeline.handle_ack({"command_id": "cmd-fa-003",
                              "target_device": "bedroom_light",   # mismatched
                              "ack_status": "success",
                              "observed_state": "on"})

        pipeline._escalate_c205 = original
        assert len(calls) == 1

    def test_ack_success_does_not_trigger_c205(self, pipeline):
        record = _make_record("cmd-fa-004")
        pipeline._pending_acks["cmd-fa-004"] = record

        calls = []
        original = pipeline._escalate_c205
        pipeline._escalate_c205 = lambda audit_id: calls.append(audit_id)

        pipeline.handle_ack({"command_id": "cmd-fa-004",
                              "target_device": "living_room_light",
                              "ack_status": "success",
                              "observed_state": "on"})

        pipeline._escalate_c205 = original
        assert calls == []

    def test_unknown_command_id_does_not_escalate(self, pipeline):
        """ACK for unknown command_id is dropped — no C205."""
        calls = []
        original = pipeline._escalate_c205
        pipeline._escalate_c205 = lambda audit_id: calls.append(audit_id)

        pipeline.handle_ack({"command_id": "NONEXISTENT", "ack_status": "failure"})

        pipeline._escalate_c205 = original
        assert calls == []

    def test_failure_audit_id_passed_to_escalation(self, pipeline):
        record = _make_record("cmd-fa-005", audit_id="specific-audit-xyz")
        pipeline._pending_acks["cmd-fa-005"] = record

        calls = []
        original = pipeline._escalate_c205
        pipeline._escalate_c205 = lambda audit_id: calls.append(audit_id)

        pipeline.handle_ack({"command_id": "cmd-fa-005",
                              "target_device": "living_room_light",
                              "ack_status": "failure"})

        pipeline._escalate_c205 = original
        assert calls == ["specific-audit-xyz"]


# ---------------------------------------------------------------------------
# _execute_class2_transition()
# ---------------------------------------------------------------------------

def _make_class2_result(transition_target_str, action_hint=None, target_hint=None):
    """Build a minimal Class2Result for testing _execute_class2_transition()."""
    from safe_deferral_handler.models import TransitionTarget
    from class2_clarification_manager.models import Class2Result

    tt_map = {
        "CLASS_1": TransitionTarget.CLASS_1,
        "CLASS_0": TransitionTarget.CLASS_0,
        "SAFE_DEFERRAL": TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION,
    }
    tt = tt_map[transition_target_str]
    notify = tt == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
    return Class2Result(
        transition_target=tt,
        should_notify_caregiver=notify,
        action_hint=action_hint,
        target_hint=target_hint,
        clarification_record={
            "clarification_id": "cid-test",
            "unresolved_reason": "caregiver_required_sensitive_path",
            "transition_target": transition_target_str,
        },
        notification_payload=None,
    )


class TestExecuteClass2Transition:
    """_execute_class2_transition() dispatches correctly for each TransitionTarget."""

    def test_class1_is_class1_ready_dispatches(self, pipeline):
        """CLASS_1 with action_hint + target_hint → validates and dispatches."""
        cr = _make_class2_result("CLASS_1", action_hint="light_on",
                                 target_hint="living_room_light")
        dispatched = []
        original_dispatch = pipeline._dispatcher.dispatch

        def _fake_dispatch(val_result):
            from low_risk_dispatcher.models import DispatchRecord, DispatchResult, DispatchStatus
            rec = DispatchRecord(
                command_id="cmd-c2-001",
                action="light_on",
                target_device="living_room_light",
                requires_ack=True,
                audit_correlation_id="audit-c2-001",
                source_decision="validator_output",
                dispatch_status=DispatchStatus.PUBLISHED,
                published_at_ms=int(time.time() * 1000),
                ack_status=None,
                ack_received_at_ms=None,
                observed_state=None,
                ack_timeout_ms=5000,
            )
            result = DispatchResult(
                command_id="cmd-c2-001",
                dispatch_status=DispatchStatus.PUBLISHED,
                action="light_on",
                target_device="living_room_light",
                audit_correlation_id="audit-c2-001",
                command_payload={},
                dispatch_record=rec,
            )
            dispatched.append(result)
            return result

        pipeline._dispatcher.dispatch = _fake_dispatch
        try:
            pipeline._execute_class2_transition(cr, "audit-c2-001", "C201")
        finally:
            pipeline._dispatcher.dispatch = original_dispatch

        assert len(dispatched) == 1
        assert "cmd-c2-001" in pipeline._pending_acks
        pipeline._pending_acks.pop("cmd-c2-001", None)

    def test_class1_not_ready_no_dispatch(self, pipeline):
        """CLASS_1 without target_hint → is_class1_ready=False — no dispatch."""
        cr = _make_class2_result("CLASS_1", action_hint="light_on", target_hint=None)
        dispatched = []
        original_dispatch = pipeline._dispatcher.dispatch
        pipeline._dispatcher.dispatch = lambda v: dispatched.append(v)
        try:
            pipeline._execute_class2_transition(cr, "audit-c2-002", "C201")
        finally:
            pipeline._dispatcher.dispatch = original_dispatch
        assert dispatched == []

    def test_class0_sends_caregiver_notification(self, pipeline):
        """CLASS_0 → caregiver.send_notification() is called once."""
        cr = _make_class2_result("CLASS_0")
        notifications = []
        original_notify = pipeline._caregiver.send_notification
        pipeline._caregiver.send_notification = lambda n: notifications.append(n) or MagicMock()
        try:
            pipeline._execute_class2_transition(cr, "audit-c2-003", "EMERGENCY_BUTTON")
        finally:
            pipeline._caregiver.send_notification = original_notify
        assert len(notifications) == 1
        assert notifications[0]["unresolved_reason"] == "emergency_event"

    def test_class0_trigger_id_in_summary(self, pipeline):
        """CLASS_0 notification event_summary contains the trigger_id."""
        cr = _make_class2_result("CLASS_0")
        summaries = []
        original_notify = pipeline._caregiver.send_notification
        pipeline._caregiver.send_notification = lambda n: summaries.append(
            n.get("event_summary", "")
        ) or MagicMock()
        try:
            pipeline._execute_class2_transition(cr, "audit-c2-004", "MY_TRIGGER_C0")
        finally:
            pipeline._caregiver.send_notification = original_notify
        assert any("MY_TRIGGER_C0" in s for s in summaries)

    def test_safe_deferral_no_dispatch_no_notify(self, pipeline):
        """SAFE_DEFERRAL → no dispatch and no caregiver notification from transition."""
        cr = _make_class2_result("SAFE_DEFERRAL")
        dispatched = []
        notifications = []
        original_dispatch = pipeline._dispatcher.dispatch
        original_notify = pipeline._caregiver.send_notification
        pipeline._dispatcher.dispatch = lambda v: dispatched.append(v)
        pipeline._caregiver.send_notification = lambda n: notifications.append(n)
        try:
            pipeline._execute_class2_transition(cr, "audit-c2-005", "C207")
        finally:
            pipeline._dispatcher.dispatch = original_dispatch
            pipeline._caregiver.send_notification = original_notify
        assert dispatched == []
        assert notifications == []


# ---------------------------------------------------------------------------
# publish_class2_transition_result()
# ---------------------------------------------------------------------------

class TestPublishClass2TransitionResult:
    """TelemetryAdapter.publish_class2_transition_result() emits a snapshot with
    post_transition_validator_status and post_transition_dispatched set."""

    def _make_adapter(self):
        with patch("main.AUDIT_DB_PATH", ":memory:"):
            import main  # noqa: PLC0415
            from telemetry_adapter.adapter import TelemetryAdapter
        pub = _MockPublisher()
        from shared.asset_loader import AssetLoader
        adapter = TelemetryAdapter(
            mqtt_publisher=pub,
            asset_loader=AssetLoader(),
        )
        return adapter, pub

    def _make_cr(self, action_hint="light_on", target_hint="living_room_light"):
        return _make_class2_result("CLASS_1", action_hint=action_hint, target_hint=target_hint)

    def test_approved_fields_in_published_snapshot(self):
        adapter, pub = self._make_adapter()
        cr = self._make_cr()
        adapter.publish_class2_transition_result(
            "audit-ptr-001", cr,
            post_transition_validator_status="approved",
            post_transition_dispatched=True,
        )
        assert len(pub.calls) == 1
        payload = pub.calls[0]["payload"]
        class2 = payload.get("class2") or {}
        assert class2.get("post_transition_validator_status") == "approved"
        assert class2.get("post_transition_dispatched") is True

    def test_not_ready_fields_in_published_snapshot(self):
        adapter, pub = self._make_adapter()
        cr = self._make_cr(target_hint=None)
        adapter.publish_class2_transition_result(
            "audit-ptr-002", cr,
            post_transition_validator_status="not_ready",
            post_transition_dispatched=False,
        )
        payload = pub.calls[0]["payload"]
        class2 = payload.get("class2") or {}
        assert class2.get("post_transition_validator_status") == "not_ready"
        assert class2.get("post_transition_dispatched") is False

    def test_audit_correlation_id_in_snapshot(self):
        adapter, pub = self._make_adapter()
        cr = self._make_cr()
        adapter.publish_class2_transition_result(
            "audit-ptr-003", cr,
            post_transition_validator_status="approved",
            post_transition_dispatched=True,
        )
        assert pub.calls[0]["payload"].get("audit_correlation_id") == "audit-ptr-003"


# ---------------------------------------------------------------------------
# C1_LIGHTING_ASSISTANCE default candidate has target_hint set (Issue 1)
# ---------------------------------------------------------------------------

class TestDefaultCandidatesTargetHint:
    """C1_LIGHTING_ASSISTANCE in _DEFAULT_CANDIDATES must have target_hint set so
    is_class1_ready=True and CLASS_2→CLASS_1 dispatch fires in practice."""

    def test_insufficient_context_c1_has_target_hint(self):
        from class2_clarification_manager.manager import _DEFAULT_CANDIDATES
        c1 = next(
            c for c in _DEFAULT_CANDIDATES["insufficient_context"]
            if c["candidate_id"] == "C1_LIGHTING_ASSISTANCE"
        )
        assert c1["target_hint"] == "living_room_light"
        assert c1["action_hint"] == "light_on"

    def test_missing_policy_input_c1_has_target_hint(self):
        from class2_clarification_manager.manager import _DEFAULT_CANDIDATES
        c1 = next(
            c for c in _DEFAULT_CANDIDATES["missing_policy_input"]
            if c["candidate_id"] == "C1_LIGHTING_ASSISTANCE"
        )
        assert c1["target_hint"] == "living_room_light"

    def test_unresolved_conflict_opt_living_room_is_class1_ready(self):
        from class2_clarification_manager.manager import _DEFAULT_CANDIDATES
        opt = next(
            c for c in _DEFAULT_CANDIDATES["unresolved_context_conflict"]
            if c["candidate_id"] == "OPT_LIVING_ROOM"
        )
        assert opt["action_hint"] == "light_on"
        assert opt["target_hint"] == "living_room_light"

    def test_unresolved_conflict_opt_bedroom_is_class1_ready(self):
        from class2_clarification_manager.manager import _DEFAULT_CANDIDATES
        opt = next(
            c for c in _DEFAULT_CANDIDATES["unresolved_context_conflict"]
            if c["candidate_id"] == "OPT_BEDROOM"
        )
        assert opt["action_hint"] == "light_on"
        assert opt["target_hint"] == "bedroom_light"


class TestPublishClass2TransitionResultClass0:
    """publish_class2_transition_result() CLASS_0 path emits post_transition_escalation_status."""

    def test_class0_escalation_status_in_snapshot(self, pipeline):
        cr = _make_class2_result("CLASS_0")
        pub_calls = []
        original = pipeline._telemetry._publisher.publish
        pipeline._telemetry._publisher.publish = lambda t, p, qos=1: pub_calls.append(p)
        try:
            pipeline._telemetry.publish_class2_transition_result(
                "audit-c0-001", cr,
                post_transition_escalation_status="pending",
            )
        finally:
            pipeline._telemetry._publisher.publish = original
        assert len(pub_calls) == 1
        class2 = pub_calls[0].get("class2") or {}
        assert class2.get("post_transition_escalation_status") == "pending"
        assert class2.get("post_transition_validator_status") is None

    def test_class0_escalation_none_when_not_set(self, pipeline):
        cr = _make_class2_result("CLASS_0")
        pub_calls = []
        original = pipeline._telemetry._publisher.publish
        pipeline._telemetry._publisher.publish = lambda t, p, qos=1: pub_calls.append(p)
        try:
            pipeline._telemetry.publish_class2_transition_result("audit-c0-002", cr)
        finally:
            pipeline._telemetry._publisher.publish = original
        assert len(pub_calls) == 1
        class2 = pub_calls[0].get("class2") or {}
        assert class2.get("post_transition_escalation_status") is None
