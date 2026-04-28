"""Integration tests for Pipeline.handle_ack() ACK failure escalation path."""

import os
import sys
import tempfile
import time
import types
from unittest.mock import MagicMock, patch

import pytest

# paho is not installed in the test environment; stub it before importing main
_paho_stub = types.ModuleType("paho")
_paho_mqtt_stub = types.ModuleType("paho.mqtt")
_paho_client_stub = types.ModuleType("paho.mqtt.client")
_paho_client_stub.Client = MagicMock
sys.modules.setdefault("paho", _paho_stub)
sys.modules.setdefault("paho.mqtt", _paho_mqtt_stub)
sys.modules.setdefault("paho.mqtt.client", _paho_client_stub)

from main import Pipeline  # noqa: E402
from low_risk_dispatcher.models import AckStatus, DispatchRecord, DispatchStatus


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

class _NoOpPublisher:
    def publish(self, topic, payload, qos=1):
        pass


def _make_record(command_id="cmd-test-001", action="light_on",
                 target_device="living_room_light", audit_id="audit-pipeline-test") -> DispatchRecord:
    return DispatchRecord(
        command_id=command_id,
        action=action,
        target_device=target_device,
        requires_ack=True,
        audit_correlation_id=audit_id,
        source_decision="validator_output",
        dispatch_status=DispatchStatus.PUBLISHED,
        published_at_ms=int(time.time() * 1000),
        ack_status=None,
        ack_received_at_ms=None,
        observed_state=None,
        ack_timeout_ms=30_000,
    )


@pytest.fixture(scope="module")
def pipeline():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    with patch("main.AUDIT_DB_PATH", db_path):
        p = Pipeline(mqtt_publisher=_NoOpPublisher())
    yield p
    os.unlink(db_path)


def _insert_pending(pipeline, record: DispatchRecord) -> None:
    with pipeline._ack_lock:
        pipeline._pending_acks[record.command_id] = record


def _good_ack(record: DispatchRecord) -> dict:
    return {
        "command_id": record.command_id,
        "target_device": record.target_device,
        "ack_status": "success",
        "observed_state": "on",
        "audit_correlation_id": record.audit_correlation_id,
    }


def _bad_ack(record: DispatchRecord, **overrides) -> dict:
    payload = {
        "command_id": record.command_id,
        "target_device": record.target_device,
        "ack_status": "failure",
        "observed_state": None,
        "audit_correlation_id": record.audit_correlation_id,
    }
    payload.update(overrides)
    return payload


# ------------------------------------------------------------------
# ACK success — must NOT escalate
# ------------------------------------------------------------------

class TestHandleAckSuccess:
    def test_success_does_not_escalate(self, pipeline):
        record = _make_record(command_id="cmd-ok-001")
        _insert_pending(pipeline, record)
        with patch.object(pipeline, "_escalate_c205") as mock_esc:
            pipeline.handle_ack(_good_ack(record))
            mock_esc.assert_not_called()

    def test_success_removes_from_pending(self, pipeline):
        record = _make_record(command_id="cmd-ok-002")
        _insert_pending(pipeline, record)
        pipeline.handle_ack(_good_ack(record))
        with pipeline._ack_lock:
            assert "cmd-ok-002" not in pipeline._pending_acks


# ------------------------------------------------------------------
# ACK failure — must escalate C205
# ------------------------------------------------------------------

class TestHandleAckFailure:
    def test_explicit_failure_escalates_c205(self, pipeline):
        record = _make_record(command_id="cmd-fail-001")
        _insert_pending(pipeline, record)
        with patch.object(pipeline, "_escalate_c205") as mock_esc:
            pipeline.handle_ack(_bad_ack(record))
            mock_esc.assert_called_once_with(record.audit_correlation_id)

    def test_wrong_target_device_escalates_c205(self, pipeline):
        record = _make_record(command_id="cmd-fail-002")
        _insert_pending(pipeline, record)
        with patch.object(pipeline, "_escalate_c205") as mock_esc:
            pipeline.handle_ack(_bad_ack(record, target_device="bedroom_light",
                                         ack_status="success", observed_state="on"))
            mock_esc.assert_called_once_with(record.audit_correlation_id)

    def test_wrong_observed_state_escalates_c205(self, pipeline):
        record = _make_record(command_id="cmd-fail-003")
        _insert_pending(pipeline, record)
        with patch.object(pipeline, "_escalate_c205") as mock_esc:
            pipeline.handle_ack(_bad_ack(record, ack_status="success", observed_state="off"))
            mock_esc.assert_called_once_with(record.audit_correlation_id)

    def test_wrong_audit_id_escalates_c205(self, pipeline):
        record = _make_record(command_id="cmd-fail-004")
        _insert_pending(pipeline, record)
        with patch.object(pipeline, "_escalate_c205") as mock_esc:
            pipeline.handle_ack(_bad_ack(record, audit_correlation_id="WRONG_AUDIT",
                                         ack_status="success", observed_state="on"))
            mock_esc.assert_called_once_with(record.audit_correlation_id)

    def test_failure_escalation_passes_correct_audit_id(self, pipeline):
        record = _make_record(command_id="cmd-fail-005", audit_id="audit-specific-xyz")
        _insert_pending(pipeline, record)
        with patch.object(pipeline, "_escalate_c205") as mock_esc:
            pipeline.handle_ack(_bad_ack(record))
            mock_esc.assert_called_once_with("audit-specific-xyz")

    def test_failure_removes_from_pending(self, pipeline):
        record = _make_record(command_id="cmd-fail-006")
        _insert_pending(pipeline, record)
        with patch.object(pipeline, "_escalate_c205"):
            pipeline.handle_ack(_bad_ack(record))
        with pipeline._ack_lock:
            assert "cmd-fail-006" not in pipeline._pending_acks

    def test_unknown_command_id_does_not_escalate(self, pipeline):
        """ACK for an unknown command_id must be silently dropped, not escalated."""
        with patch.object(pipeline, "_escalate_c205") as mock_esc:
            pipeline.handle_ack({"command_id": "GHOST_CMD", "ack_status": "failure"})
            mock_esc.assert_not_called()
