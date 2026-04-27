"""Tests for LowRiskDispatcher and AckHandler (MM-07)."""

import pytest

from deterministic_validator.models import (
    ExecutablePayload,
    RoutingTarget,
    ValidationStatus,
    ValidatorResult,
)
from low_risk_dispatcher.ack_handler import AckHandler
from low_risk_dispatcher.dispatcher import LowRiskDispatcher
from low_risk_dispatcher.models import AckStatus, DispatchStatus

AUDIT_ID = "test_audit_mm07"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _approved_result(action="light_on", target="living_room_light", requires_ack=True):
    return ValidatorResult(
        validation_status=ValidationStatus.APPROVED,
        routing_target=RoutingTarget.ACTUATOR_DISPATCHER,
        exception_trigger_id="none",
        executable_payload=ExecutablePayload(
            action=action,
            target_device=target,
            requires_ack=requires_ack,
        ),
        deferral_reason=None,
        audit_correlation_id=AUDIT_ID,
    )


def _non_approved_result():
    return ValidatorResult(
        validation_status=ValidationStatus.SAFE_DEFERRAL,
        routing_target=RoutingTarget.SAFE_DEFERRAL_HANDLER,
        exception_trigger_id="none",
        executable_payload=None,
        deferral_reason="ambiguous_target",
        audit_correlation_id=AUDIT_ID,
    )


class _RecordingPublisher:
    def __init__(self):
        self.calls: list[dict] = []

    def publish(self, topic: str, payload: dict, qos: int = 1) -> None:
        self.calls.append({"topic": topic, "payload": payload, "qos": qos})


@pytest.fixture(scope="module")
def dispatcher():
    return LowRiskDispatcher()


@pytest.fixture(scope="module")
def ack_handler():
    return AckHandler()


# ------------------------------------------------------------------
# Dispatcher — happy path
# ------------------------------------------------------------------

class TestDispatch:
    def test_approved_result_returns_published_status(self, dispatcher):
        result = dispatcher.dispatch(_approved_result())
        assert result.dispatch_status == DispatchStatus.PUBLISHED

    def test_command_payload_has_required_fields(self, dispatcher):
        result = dispatcher.dispatch(_approved_result())
        for field in ("command_id", "source_decision", "action", "target_device",
                      "requires_ack", "audit_correlation_id", "authority_note"):
            assert field in result.command_payload, f"missing: {field}"

    def test_command_payload_source_decision_is_validator_output(self, dispatcher):
        result = dispatcher.dispatch(_approved_result())
        assert result.command_payload["source_decision"] == "validator_output"

    def test_command_payload_action_and_target_match(self, dispatcher):
        result = dispatcher.dispatch(_approved_result(action="light_off", target="bedroom_light"))
        assert result.command_payload["action"] == "light_off"
        assert result.command_payload["target_device"] == "bedroom_light"

    def test_command_payload_audit_id_preserved(self, dispatcher):
        result = dispatcher.dispatch(_approved_result())
        assert result.command_payload["audit_correlation_id"] == AUDIT_ID

    def test_custom_command_id_used(self, dispatcher):
        result = dispatcher.dispatch(_approved_result(), command_id="my-cmd-001")
        assert result.command_id == "my-cmd-001"
        assert result.command_payload["command_id"] == "my-cmd-001"

    def test_dispatch_record_initial_state(self, dispatcher):
        result = dispatcher.dispatch(_approved_result())
        r = result.dispatch_record
        assert r.dispatch_status == DispatchStatus.PUBLISHED
        assert r.ack_status is None
        assert r.ack_received_at_ms is None
        assert r.observed_state is None

    def test_dispatch_record_ack_timeout_from_policy(self, dispatcher):
        result = dispatcher.dispatch(_approved_result())
        assert result.dispatch_record.ack_timeout_ms == 5000

    def test_dispatch_record_llm_boundary_correct(self, dispatcher):
        result = dispatcher.dispatch(_approved_result())
        lb = result.dispatch_record.llm_boundary
        assert lb["candidate_generation_only"] is True
        assert lb["final_decision_allowed"] is False
        assert lb["actuation_authority_allowed"] is False
        assert lb["emergency_trigger_authority_allowed"] is False

    def test_mqtt_published_to_correct_topic(self):
        pub = _RecordingPublisher()
        d = LowRiskDispatcher(mqtt_publisher=pub)
        d.dispatch(_approved_result())
        assert len(pub.calls) == 1
        assert pub.calls[0]["topic"] == "safe_deferral/actuation/command"
        assert pub.calls[0]["qos"] == 1

    def test_mqtt_payload_published_matches_command_payload(self):
        pub = _RecordingPublisher()
        d = LowRiskDispatcher(mqtt_publisher=pub)
        result = d.dispatch(_approved_result())
        assert pub.calls[0]["payload"] == result.command_payload

    def test_needs_ack_true_when_requires_ack(self, dispatcher):
        result = dispatcher.dispatch(_approved_result(requires_ack=True))
        assert result.needs_ack is True

    def test_needs_ack_false_when_not_requires_ack(self, dispatcher):
        result = dispatcher.dispatch(_approved_result(requires_ack=False))
        assert result.needs_ack is False


# ------------------------------------------------------------------
# Dispatcher — guard rails
# ------------------------------------------------------------------

class TestDispatchGuards:
    def test_non_approved_raises_value_error(self, dispatcher):
        with pytest.raises(ValueError, match="APPROVED"):
            dispatcher.dispatch(_non_approved_result())

    def test_none_executable_payload_raises_value_error(self, dispatcher):
        result = _approved_result()
        result.executable_payload = None
        with pytest.raises(ValueError):
            dispatcher.dispatch(result)


# ------------------------------------------------------------------
# ACK Handler — success
# ------------------------------------------------------------------

class TestAckSuccess:
    def test_matching_ack_success_gives_ack_success(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-ack-001")
        ack_payload = {
            "ack_id": "ack-001",
            "command_id": "cmd-ack-001",
            "target_device": "living_room_light",
            "ack_status": "success",
            "observed_state": "on",
            "audit_correlation_id": AUDIT_ID,
        }
        ack = ack_handler.handle_ack(result.dispatch_record, ack_payload)
        assert ack.ack_status == AckStatus.SUCCESS
        assert ack.observed_state == "on"

    def test_ack_success_updates_dispatch_record(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-ack-002")
        ack_payload = {"command_id": "cmd-ack-002", "ack_status": "success",
                       "observed_state": "on", "audit_correlation_id": AUDIT_ID}
        ack_handler.handle_ack(result.dispatch_record, ack_payload)
        assert result.dispatch_record.dispatch_status == DispatchStatus.ACK_SUCCESS
        assert result.dispatch_record.ack_status == AckStatus.SUCCESS
        assert result.dispatch_record.observed_state == "on"

    def test_ack_result_audit_id_preserved(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-ack-003")
        ack_payload = {"command_id": "cmd-ack-003", "ack_status": "success",
                       "observed_state": "on"}
        ack = ack_handler.handle_ack(result.dispatch_record, ack_payload)
        assert ack.audit_correlation_id == AUDIT_ID

    def test_ack_result_command_id_matches(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-ack-004")
        ack_payload = {"command_id": "cmd-ack-004", "ack_status": "success"}
        ack = ack_handler.handle_ack(result.dispatch_record, ack_payload)
        assert ack.command_id == "cmd-ack-004"


# ------------------------------------------------------------------
# ACK Handler — failure
# ------------------------------------------------------------------

class TestAckFailure:
    def test_ack_status_failure_gives_ack_failure(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-fail-001")
        ack_payload = {"command_id": "cmd-fail-001", "ack_status": "failure",
                       "observed_state": None}
        ack = ack_handler.handle_ack(result.dispatch_record, ack_payload)
        assert ack.ack_status == AckStatus.FAILURE

    def test_ack_failure_updates_record_status(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-fail-002")
        ack_payload = {"command_id": "cmd-fail-002", "ack_status": "failure"}
        ack_handler.handle_ack(result.dispatch_record, ack_payload)
        assert result.dispatch_record.dispatch_status == DispatchStatus.ACK_FAILURE

    def test_mismatched_command_id_treated_as_failure(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-fail-003")
        ack_payload = {"command_id": "WRONG_ID", "ack_status": "success",
                       "observed_state": "on"}
        ack = ack_handler.handle_ack(result.dispatch_record, ack_payload)
        assert ack.ack_status == AckStatus.FAILURE

    def test_unknown_ack_status_string_is_failure(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-fail-004")
        ack_payload = {"command_id": "cmd-fail-004", "ack_status": "unknown_state"}
        ack = ack_handler.handle_ack(result.dispatch_record, ack_payload)
        assert ack.ack_status == AckStatus.FAILURE


# ------------------------------------------------------------------
# ACK Handler — timeout
# ------------------------------------------------------------------

class TestAckTimeout:
    def test_timeout_gives_ack_timeout_status(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-to-001")
        ack = ack_handler.handle_ack_timeout(result.dispatch_record)
        assert ack.ack_status == AckStatus.TIMEOUT

    def test_timeout_updates_record_to_ack_timeout(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-to-002")
        ack_handler.handle_ack_timeout(result.dispatch_record)
        assert result.dispatch_record.dispatch_status == DispatchStatus.ACK_TIMEOUT

    def test_timeout_observed_state_is_none(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-to-003")
        ack = ack_handler.handle_ack_timeout(result.dispatch_record)
        assert ack.observed_state is None

    def test_timeout_audit_id_preserved(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-to-004")
        ack = ack_handler.handle_ack_timeout(result.dispatch_record)
        assert ack.audit_correlation_id == AUDIT_ID


# ------------------------------------------------------------------
# DispatchRecord.to_dict schema shape
# ------------------------------------------------------------------

class TestDispatchRecordSchema:
    def test_to_dict_has_required_fields(self, dispatcher):
        result = dispatcher.dispatch(_approved_result())
        d = result.dispatch_record.to_dict()
        for field in ("command_id", "action", "target_device", "requires_ack",
                      "audit_correlation_id", "source_decision", "dispatch_status",
                      "published_at_ms", "ack_status", "ack_received_at_ms",
                      "observed_state", "ack_timeout_ms", "llm_boundary"):
            assert field in d, f"missing: {field}"

    def test_to_dict_dispatch_status_is_string(self, dispatcher):
        result = dispatcher.dispatch(_approved_result())
        d = result.dispatch_record.to_dict()
        assert isinstance(d["dispatch_status"], str)

    def test_to_dict_after_success_ack(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-dict-001")
        ack_payload = {"command_id": "cmd-dict-001", "ack_status": "success",
                       "observed_state": "on"}
        ack_handler.handle_ack(result.dispatch_record, ack_payload)
        d = result.dispatch_record.to_dict()
        assert d["dispatch_status"] == "ack_success"
        assert d["ack_status"] == "success"
        assert d["observed_state"] == "on"

    def test_to_dict_after_timeout(self, dispatcher, ack_handler):
        result = dispatcher.dispatch(_approved_result(), command_id="cmd-dict-002")
        ack_handler.handle_ack_timeout(result.dispatch_record)
        d = result.dispatch_record.to_dict()
        assert d["dispatch_status"] == "ack_timeout"
        assert d["ack_status"] == "timeout"
