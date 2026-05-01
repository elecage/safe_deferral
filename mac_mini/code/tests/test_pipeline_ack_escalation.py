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
# Post-transition outcome publish (Issues #2, #4)
# ---------------------------------------------------------------------------

class TestPostTransitionOutcomePublish:
    """_execute_class2_transition emits a post-transition dashboard observation
    with validation evidence (CLASS_1) or escalation evidence (CLASS_0)."""

    def _capture_obs(self, pipeline):
        captured: list[dict] = []
        original = pipeline._telemetry._publisher.publish
        def _wrap(topic, payload, qos=1):
            if topic.endswith("/dashboard/observation"):
                captured.append(payload)
            return original(topic, payload, qos)
        pipeline._telemetry._publisher.publish = _wrap
        return captured, original

    def test_class1_outcome_carries_validation_block(self, pipeline):
        """CLASS_1 transition publishes a snapshot with class2 + validation."""
        cr = _make_class2_result("CLASS_1", action_hint="light_on",
                                 target_hint="living_room_light")
        captured, original = self._capture_obs(pipeline)
        original_dispatch = pipeline._dispatcher.dispatch
        def _fake_dispatch(val_result):
            from low_risk_dispatcher.models import DispatchRecord, DispatchResult, DispatchStatus
            rec = DispatchRecord(
                command_id="cmd-pt-001", action="light_on",
                target_device="living_room_light", requires_ack=True,
                audit_correlation_id="audit-pt-001",
                source_decision="validator_output",
                dispatch_status=DispatchStatus.PUBLISHED,
                published_at_ms=int(time.time() * 1000),
                ack_status=None, ack_received_at_ms=None,
                observed_state=None, ack_timeout_ms=5000,
            )
            return DispatchResult(
                command_id="cmd-pt-001", dispatch_status=DispatchStatus.PUBLISHED,
                action="light_on", target_device="living_room_light",
                audit_correlation_id="audit-pt-001",
                command_payload={}, dispatch_record=rec,
            )
        pipeline._dispatcher.dispatch = _fake_dispatch
        try:
            pipeline._execute_class2_transition(cr, "audit-pt-001", "C201")
        finally:
            pipeline._dispatcher.dispatch = original_dispatch
            pipeline._telemetry._publisher.publish = original
            pipeline._pending_acks.pop("cmd-pt-001", None)

        outcome = next(
            (p for p in captured if p.get("class2") and p.get("validation")), None
        )
        assert outcome is not None, f"No post-transition CLASS_1 outcome snapshot in {captured!r}"
        assert outcome["class2"]["transition_target"] == "CLASS_1"
        assert outcome["validation"]["validation_status"] == "approved"
        assert outcome["audit_correlation_id"] == "audit-pt-001"

    def test_class0_outcome_carries_escalation_block(self, pipeline):
        """CLASS_0 transition publishes a snapshot with class2 + escalation."""
        cr = _make_class2_result("CLASS_0")
        captured, original = self._capture_obs(pipeline)
        original_notify = pipeline._caregiver.send_notification
        from caregiver_escalation.models import EscalationStatus, EscalationResult, NotificationRecord
        def _fake_notify(n):
            rec = NotificationRecord(
                confirmation_id="conf-pt-002",
                audit_correlation_id="audit-pt-002",
                notification_channel="telegram",
                notification_payload=n,
                sent_at_ms=int(time.time() * 1000),
                telegram_message_id=None,
                escalation_status=EscalationStatus.PENDING,
            )
            return EscalationResult(
                confirmation_id="conf-pt-002",
                escalation_status=EscalationStatus.PENDING,
                audit_correlation_id="audit-pt-002",
                notification_record=rec,
            )
        pipeline._caregiver.send_notification = _fake_notify
        try:
            pipeline._execute_class2_transition(cr, "audit-pt-002", "EMERGENCY")
        finally:
            pipeline._caregiver.send_notification = original_notify
            pipeline._telemetry._publisher.publish = original

        outcome = next(
            (p for p in captured if p.get("class2") and p.get("escalation")), None
        )
        assert outcome is not None, f"No post-transition CLASS_0 outcome snapshot in {captured!r}"
        assert outcome["class2"]["transition_target"] == "CLASS_0"
        assert outcome["escalation"]["escalation_status"] == "pending"
        assert outcome["escalation"]["notification_channel"] == "telegram"


# ---------------------------------------------------------------------------
# Package A intent-recovery comparison helpers and _handle_class1 dispatch
# ---------------------------------------------------------------------------

class TestIntentRecoveryHelpers:
    """_direct_mapping_candidate and _rule_only_candidate behave deterministically."""

    def test_direct_mapping_known_event(self):
        import main  # noqa: PLC0415
        ctx = {"trigger_event": {"event_code": "single_click"}}
        cand = main._direct_mapping_candidate(ctx)
        assert cand["proposed_action"] == "light_on"
        assert cand["target_device"] == "living_room_light"

    def test_direct_mapping_unknown_event_safe_deferral(self):
        import main  # noqa: PLC0415
        ctx = {"trigger_event": {"event_code": "shrug"}}
        cand = main._direct_mapping_candidate(ctx)
        assert cand["proposed_action"] == "safe_deferral"
        assert cand.get("deferral_reason") == "insufficient_context"

    def test_rule_only_dark_room_proposes_light_on(self):
        import main  # noqa: PLC0415
        ctx = {
            "environmental_context": {"illuminance": 50, "occupancy_detected": True},
            "device_states": {"living_room_light": "off"},
        }
        cand = main._rule_only_candidate(ctx)
        assert cand["proposed_action"] == "light_on"
        assert cand["target_device"] == "living_room_light"

    def test_rule_only_bright_room_safe_deferral(self):
        import main  # noqa: PLC0415
        ctx = {
            "environmental_context": {"illuminance": 800, "occupancy_detected": True},
            "device_states": {"living_room_light": "off"},
        }
        cand = main._rule_only_candidate(ctx)
        assert cand["proposed_action"] == "safe_deferral"

    def test_rule_only_unoccupied_safe_deferral(self):
        import main  # noqa: PLC0415
        ctx = {
            "environmental_context": {"illuminance": 50, "occupancy_detected": False},
            "device_states": {"living_room_light": "off"},
        }
        cand = main._rule_only_candidate(ctx)
        assert cand["proposed_action"] == "safe_deferral"


class TestHandleClass1ExperimentMode:
    """_handle_class1 must select intent-recovery branch by experiment_mode."""

    def _make_route_result(self, mode):
        from policy_router.models import PolicyRouterResult, RouteClass
        return PolicyRouterResult(
            route_class=RouteClass.CLASS_1,
            trigger_id=None,
            llm_invocation_allowed=True,
            candidate_generation_allowed=True,
            unresolved_reason=None,
            source_node_id="test-node",
            audit_correlation_id="audit-em-001",
            network_status="online",
            routed_at_ms=1,
            pure_context_payload={
                "trigger_event": {"event_code": "single_click", "event_type": "button",
                                   "timestamp_ms": 0},
                "environmental_context": {
                    "illuminance": 50, "occupancy_detected": True,
                    "temperature": 25.0, "smoke_detected": False,
                    "gas_detected": False, "doorbell_detected": False,
                },
                "device_states": {
                    "living_room_light": "off", "bedroom_light": "off",
                    "living_room_blind": "open", "tv_main": "off",
                },
            },
            experiment_mode=mode,
        )

    def test_direct_mapping_skips_llm(self, pipeline):
        """direct_mapping mode must not invoke the LLM adapter."""
        rr = self._make_route_result("direct_mapping")
        called = []
        original_llm = pipeline._llm.generate_candidate
        original_validate = pipeline._validator.validate
        original_dispatch = pipeline._dispatcher.dispatch
        pipeline._llm.generate_candidate = lambda *a, **kw: called.append("llm") or original_llm(*a, **kw)
        pipeline._validator.validate = lambda c, **kw: called.append(("val", c)) or MagicMock(
            validation_status=MagicMock(value="safe_deferral"),
            routing_target=MagicMock(value="safe_deferral"),
        )
        pipeline._dispatcher.dispatch = lambda v: called.append("dispatch")
        try:
            pipeline._handle_class1(rr)
        finally:
            pipeline._llm.generate_candidate = original_llm
            pipeline._validator.validate = original_validate
            pipeline._dispatcher.dispatch = original_dispatch
        assert "llm" not in called
        # Validator must still be called
        validator_calls = [c for c in called if isinstance(c, tuple) and c[0] == "val"]
        assert len(validator_calls) == 1
        # The candidate passed to validator is from direct mapping
        cand = validator_calls[0][1]
        assert cand["proposed_action"] == "light_on"
        assert cand["target_device"] == "living_room_light"

    def test_rule_only_skips_llm(self, pipeline):
        """rule_only mode must not invoke the LLM adapter."""
        rr = self._make_route_result("rule_only")
        called = []
        original_llm = pipeline._llm.generate_candidate
        original_validate = pipeline._validator.validate
        original_dispatch = pipeline._dispatcher.dispatch
        pipeline._llm.generate_candidate = lambda *a, **kw: called.append("llm") or original_llm(*a, **kw)
        pipeline._validator.validate = lambda c, **kw: called.append(("val", c)) or MagicMock(
            validation_status=MagicMock(value="safe_deferral"),
            routing_target=MagicMock(value="safe_deferral"),
        )
        pipeline._dispatcher.dispatch = lambda v: called.append("dispatch")
        try:
            pipeline._handle_class1(rr)
        finally:
            pipeline._llm.generate_candidate = original_llm
            pipeline._validator.validate = original_validate
            pipeline._dispatcher.dispatch = original_dispatch
        assert "llm" not in called
        validator_calls = [c for c in called if isinstance(c, tuple) and c[0] == "val"]
        assert len(validator_calls) == 1

    def test_llm_assisted_invokes_llm(self, pipeline):
        """llm_assisted mode (and the None default) must invoke the LLM adapter."""
        rr = self._make_route_result("llm_assisted")
        called = []
        original_llm = pipeline._llm.generate_candidate
        original_validate = pipeline._validator.validate
        original_dispatch = pipeline._dispatcher.dispatch
        pipeline._llm.generate_candidate = lambda *a, **kw: called.append("llm") or original_llm(*a, **kw)
        pipeline._validator.validate = lambda c, **kw: called.append("val") or MagicMock(
            validation_status=MagicMock(value="safe_deferral"),
            routing_target=MagicMock(value="safe_deferral"),
        )
        pipeline._dispatcher.dispatch = lambda v: called.append("dispatch")
        try:
            pipeline._handle_class1(rr)
        finally:
            pipeline._llm.generate_candidate = original_llm
            pipeline._validator.validate = original_validate
            pipeline._dispatcher.dispatch = original_dispatch
        assert "llm" in called
