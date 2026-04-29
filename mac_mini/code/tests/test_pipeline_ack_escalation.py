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
