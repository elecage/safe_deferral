"""Tests for CaregiverEscalationBackend (MM-08)."""

import time
import pytest
import jsonschema

from caregiver_escalation.backend import CaregiverEscalationBackend
from caregiver_escalation.models import (
    CaregiverDecision,
    EscalationStatus,
)


# ------------------------------------------------------------------
# Helpers mirroring _build_notification() in main.py
# ------------------------------------------------------------------

def _build_notification(
    event_summary: str,
    context_summary: str,
    unresolved_reason: str,
    audit_id: str,
    exception_trigger_id=None,
) -> dict:
    payload = {
        "event_summary": event_summary,
        "context_summary": context_summary,
        "unresolved_reason": unresolved_reason,
        "manual_confirmation_path": "caregiver_telegram_response",
        "audit_correlation_id": audit_id,
        "timestamp_ms": int(time.time() * 1000),
        "notification_channel": "telegram",
        "source_layer": "system",
    }
    if exception_trigger_id is not None:
        payload["exception_trigger_id"] = exception_trigger_id
    return payload

AUDIT_ID = "test_audit_mm08"


# ------------------------------------------------------------------
# Helpers / fixtures
# ------------------------------------------------------------------

def _valid_payload(
    trigger_id="C206",
    audit_id=AUDIT_ID,
    context_summary="거실 조명 꺼짐, 점유 감지됨",
):
    """Minimal valid class2_notification_payload."""
    return {
        "event_summary": "의도 해석 불충분으로 Class 2 진입",
        "context_summary": context_summary,
        "unresolved_reason": "insufficient_context",
        "manual_confirmation_path": (
            "보호자는 Telegram 또는 대시보드를 통해 검토 후 확인/거부할 수 있습니다."
        ),
        "audit_correlation_id": audit_id,
        "timestamp_ms": 1710000000000,
        "notification_channel": "telegram",
        "source_layer": "class2_clarification_manager",
        "exception_trigger_id": trigger_id,
    }


class _RecordingTelegramSender:
    def __init__(self, message_id: int = 42):
        self.calls: list[dict] = []
        self._message_id = message_id

    def send_message(self, chat_id, text, parse_mode="HTML"):
        self.calls.append({"chat_id": chat_id, "text": text})
        return self._message_id


class _RecordingPublisher:
    def __init__(self):
        self.calls: list[dict] = []

    def publish(self, topic, payload, qos=1):
        self.calls.append({"topic": topic, "payload": payload, "qos": qos})


@pytest.fixture(scope="module")
def backend():
    return CaregiverEscalationBackend()


# ------------------------------------------------------------------
# Schema validation
# ------------------------------------------------------------------

class TestPayloadValidation:
    def test_valid_payload_does_not_raise(self, backend):
        backend.send_notification(_valid_payload())  # no exception

    def test_missing_required_field_raises_validation_error(self, backend):
        bad = _valid_payload()
        del bad["event_summary"]
        with pytest.raises(jsonschema.ValidationError):
            backend.send_notification(bad)

    def test_empty_event_summary_raises_validation_error(self, backend):
        bad = _valid_payload()
        bad["event_summary"] = ""
        with pytest.raises(jsonschema.ValidationError):
            backend.send_notification(bad)

    def test_invalid_notification_channel_raises_validation_error(self, backend):
        bad = _valid_payload()
        bad["notification_channel"] = "whatsapp"
        with pytest.raises(jsonschema.ValidationError):
            backend.send_notification(bad)

    def test_invalid_source_layer_raises_validation_error(self, backend):
        bad = _valid_payload()
        bad["source_layer"] = "unknown_layer"
        with pytest.raises(jsonschema.ValidationError):
            backend.send_notification(bad)

    def test_invalid_exception_trigger_id_raises_validation_error(self, backend):
        bad = _valid_payload()
        bad["exception_trigger_id"] = "C999"
        with pytest.raises(jsonschema.ValidationError):
            backend.send_notification(bad)

    def test_payload_without_optional_fields_is_valid(self, backend):
        minimal = {
            "event_summary": "Class 2 진입",
            "context_summary": "환경 요약",
            "unresolved_reason": "insufficient_context",
            "manual_confirmation_path": "보호자 검토 경로",
        }
        backend.send_notification(minimal)  # no exception


# ------------------------------------------------------------------
# send_notification — return value
# ------------------------------------------------------------------

class TestSendNotification:
    def test_returns_pending_status(self, backend):
        result = backend.send_notification(_valid_payload())
        assert result.escalation_status == EscalationStatus.PENDING

    def test_is_pending_property(self, backend):
        result = backend.send_notification(_valid_payload())
        assert result.is_pending is True

    def test_audit_correlation_id_preserved(self, backend):
        result = backend.send_notification(_valid_payload(audit_id="my-audit-mm08"))
        assert result.audit_correlation_id == "my-audit-mm08"

    def test_custom_confirmation_id_used(self, backend):
        result = backend.send_notification(_valid_payload(), confirmation_id="cid-001")
        assert result.confirmation_id == "cid-001"

    def test_notification_record_present(self, backend):
        result = backend.send_notification(_valid_payload())
        assert result.notification_record is not None

    def test_notification_record_channel_is_telegram(self, backend):
        result = backend.send_notification(_valid_payload())
        assert result.notification_record.notification_channel == "telegram"

    def test_notification_record_payload_preserved(self, backend):
        payload = _valid_payload()
        result = backend.send_notification(payload)
        assert result.notification_record.notification_payload == payload

    def test_confirmation_record_none_until_response(self, backend):
        result = backend.send_notification(_valid_payload())
        assert result.confirmation_record is None

    def test_is_resolved_false_when_pending(self, backend):
        result = backend.send_notification(_valid_payload())
        assert result.is_resolved is False


# ------------------------------------------------------------------
# Telegram sender integration
# ------------------------------------------------------------------

class TestTelegramSender:
    def test_telegram_sender_called_once(self):
        sender = _RecordingTelegramSender()
        b = CaregiverEscalationBackend(telegram_sender=sender, telegram_chat_id="chat-001")
        b.send_notification(_valid_payload())
        assert len(sender.calls) == 1

    def test_telegram_sent_to_correct_chat_id(self):
        sender = _RecordingTelegramSender()
        b = CaregiverEscalationBackend(telegram_sender=sender, telegram_chat_id="chat-999")
        b.send_notification(_valid_payload())
        assert sender.calls[0]["chat_id"] == "chat-999"

    def test_chat_id_override_in_send_call(self):
        sender = _RecordingTelegramSender()
        b = CaregiverEscalationBackend(telegram_sender=sender, telegram_chat_id="default")
        b.send_notification(_valid_payload(), chat_id="override-chat")
        assert sender.calls[0]["chat_id"] == "override-chat"

    def test_telegram_message_id_stored_in_record(self):
        sender = _RecordingTelegramSender(message_id=77)
        b = CaregiverEscalationBackend(telegram_sender=sender)
        result = b.send_notification(_valid_payload())
        assert result.notification_record.telegram_message_id == 77

    def test_message_contains_event_summary(self):
        sender = _RecordingTelegramSender()
        b = CaregiverEscalationBackend(telegram_sender=sender)
        b.send_notification(_valid_payload())
        assert "의도 해석 불충분" in sender.calls[0]["text"]

    def test_message_contains_audit_id(self):
        sender = _RecordingTelegramSender()
        b = CaregiverEscalationBackend(telegram_sender=sender)
        b.send_notification(_valid_payload(audit_id="audit-check-001"))
        assert "audit-check-001" in sender.calls[0]["text"]

    def test_html_special_chars_are_escaped(self):
        """Sensor-originated strings with HTML chars must not appear raw."""
        sender = _RecordingTelegramSender()
        b = CaregiverEscalationBackend(telegram_sender=sender)
        payload = _valid_payload(context_summary="temp=52°C & smoke<threshold>")
        b.send_notification(payload)
        text = sender.calls[0]["text"]
        assert "<threshold>" not in text
        assert "&amp;" in text or "&#x27;" in text or "&lt;" in text
        assert "temp=52°C" in text  # non-HTML chars pass through unchanged

    def test_html_in_event_summary_is_escaped(self):
        sender = _RecordingTelegramSender()
        b = CaregiverEscalationBackend(telegram_sender=sender)
        payload = _valid_payload()
        payload["event_summary"] = "<script>alert(1)</script>"
        b.send_notification(payload)
        text = sender.calls[0]["text"]
        assert "<script>" not in text
        assert "&lt;script&gt;" in text


# ------------------------------------------------------------------
# MQTT publishing
# ------------------------------------------------------------------

class TestMqttPublishing:
    def test_escalation_topic_published_on_send(self):
        pub = _RecordingPublisher()
        b = CaregiverEscalationBackend(mqtt_publisher=pub)
        b.send_notification(_valid_payload())
        topics = [c["topic"] for c in pub.calls]
        assert "safe_deferral/escalation/class2" in topics

    def test_confirmation_topic_published_on_response(self):
        pub = _RecordingPublisher()
        b = CaregiverEscalationBackend(mqtt_publisher=pub)
        result = b.send_notification(_valid_payload())
        b.record_response(result, CaregiverDecision.APPROVED)
        topics = [c["topic"] for c in pub.calls]
        assert "safe_deferral/caregiver/confirmation" in topics

    def test_escalation_payload_matches_notification_payload(self):
        pub = _RecordingPublisher()
        b = CaregiverEscalationBackend(mqtt_publisher=pub)
        payload = _valid_payload()
        b.send_notification(payload)
        escalation_call = next(c for c in pub.calls
                               if c["topic"] == "safe_deferral/escalation/class2")
        assert escalation_call["payload"] == payload


# ------------------------------------------------------------------
# record_response
# ------------------------------------------------------------------

class TestRecordResponse:
    def test_approved_decision_updates_status(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.record_response(result, CaregiverDecision.APPROVED)
        assert result.escalation_status == EscalationStatus.APPROVED

    def test_denied_decision_updates_status(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.record_response(result, CaregiverDecision.DENIED)
        assert result.escalation_status == EscalationStatus.DENIED

    def test_acknowledged_decision_updates_status(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.record_response(result, CaregiverDecision.ACKNOWLEDGED)
        assert result.escalation_status == EscalationStatus.ACKNOWLEDGED

    def test_is_resolved_true_after_response(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.record_response(result, CaregiverDecision.APPROVED)
        assert result.is_resolved is True

    def test_confirmation_record_set_after_response(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.record_response(result, CaregiverDecision.DENIED)
        assert result.confirmation_record is not None

    def test_confirmation_record_decision_matches(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.record_response(result, CaregiverDecision.APPROVED)
        assert result.confirmation_record.decision == CaregiverDecision.APPROVED

    def test_confirmation_record_audit_id_preserved(self, backend):
        result = backend.send_notification(_valid_payload(audit_id="resp-audit-001"))
        backend.record_response(result, CaregiverDecision.APPROVED)
        assert result.confirmation_record.audit_correlation_id == "resp-audit-001"

    def test_confirmation_record_approved_by_role(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.record_response(result, CaregiverDecision.APPROVED, approved_by_role="nurse")
        assert result.confirmation_record.approved_by_role == "nurse"

    def test_confirmation_record_authority_note_present(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.record_response(result, CaregiverDecision.APPROVED)
        note = result.confirmation_record.authority_note
        assert "Class 1 validator approval" in note

    def test_notification_record_status_synced(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.record_response(result, CaregiverDecision.DENIED)
        assert result.notification_record.escalation_status == EscalationStatus.DENIED


# ------------------------------------------------------------------
# handle_expired
# ------------------------------------------------------------------

class TestHandleExpired:
    def test_expired_sets_status(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.handle_expired(result)
        assert result.escalation_status == EscalationStatus.EXPIRED

    def test_expired_notification_record_status_synced(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.handle_expired(result)
        assert result.notification_record.escalation_status == EscalationStatus.EXPIRED

    def test_expired_is_not_resolved(self, backend):
        result = backend.send_notification(_valid_payload())
        backend.handle_expired(result)
        assert result.is_resolved is False


# ------------------------------------------------------------------
# ConfirmationRecord.to_dict schema shape
# ------------------------------------------------------------------

class TestConfirmationRecordSchema:
    def test_to_dict_has_required_fields(self, backend):
        result = backend.send_notification(_valid_payload())
        cr = backend.record_response(result, CaregiverDecision.APPROVED)
        d = cr.to_dict()
        for field in ("confirmation_id", "audit_correlation_id", "decision",
                      "approved_by_role", "responded_at_ms", "authority_note"):
            assert field in d, f"missing: {field}"

    def test_to_dict_decision_is_string(self, backend):
        result = backend.send_notification(_valid_payload())
        cr = backend.record_response(result, CaregiverDecision.DENIED)
        assert isinstance(cr.to_dict()["decision"], str)


# ------------------------------------------------------------------
# _build_notification schema compliance
# ------------------------------------------------------------------

class TestBuildNotificationSchemaCompliance:
    """Verify that _build_notification() outputs pass schema validation."""

    def test_class0_emergency_payload_passes_schema(self):
        """CLASS_0 path: no exception_trigger_id, source_layer='system'."""
        b = CaregiverEscalationBackend()
        payload = _build_notification(
            event_summary="긴급 상황 감지: E002",
            context_summary="CLASS_0 emergency trigger — immediate caregiver notification.",
            unresolved_reason="emergency_event",
            audit_id="audit-e002-test",
        )
        b.send_notification(payload)  # must not raise ValidationError

    def test_class0_source_layer_is_system(self):
        payload = _build_notification(
            event_summary="긴급 상황 감지: E001",
            context_summary="test",
            unresolved_reason="emergency_event",
            audit_id="audit-e001-test",
        )
        assert payload["source_layer"] == "system"

    def test_class0_no_exception_trigger_id(self):
        payload = _build_notification(
            event_summary="긴급 상황 감지: E003",
            context_summary="test",
            unresolved_reason="emergency_event",
            audit_id="audit-e003-test",
        )
        assert "exception_trigger_id" not in payload

    def test_class2_c206_payload_passes_schema(self):
        """CLASS_2 path: C-series trigger ID included."""
        b = CaregiverEscalationBackend()
        payload = _build_notification(
            event_summary="Class 2 진입: C206",
            context_summary="insufficient context",
            unresolved_reason="insufficient_context",
            audit_id="audit-c206-test",
            exception_trigger_id="C206",
        )
        b.send_notification(payload)

    def test_class2_c205_payload_passes_schema(self):
        b = CaregiverEscalationBackend()
        payload = _build_notification(
            event_summary="Class 2 진입: C205 (actuation_ack_timeout)",
            context_summary="액추에이션 ACK 미수신",
            unresolved_reason="actuation_ack_timeout",
            audit_id="audit-c205-test",
            exception_trigger_id="C205",
        )
        b.send_notification(payload)

    def test_deferral_timeout_mapped_to_c207_passes_schema(self):
        """deferral_timeout must be sent as C207, not the raw internal string."""
        b = CaregiverEscalationBackend()
        payload = _build_notification(
            event_summary="Class 2 진입: C207 (deferral_timeout)",
            context_summary="사용자 응답 없음으로 safe deferral 만료",
            unresolved_reason="user_selection_timeout",
            audit_id="audit-c207-deferral-test",
            exception_trigger_id="C207",
        )
        b.send_notification(payload)  # must not raise ValidationError

    def test_deferral_timeout_raw_string_raises_validation_error(self):
        """Confirm that passing the raw 'deferral_timeout' string would fail schema."""
        b = CaregiverEscalationBackend()
        bad_payload = _build_notification(
            event_summary="Class 2 진입: deferral_timeout",
            context_summary="test",
            unresolved_reason="user_selection_timeout",
            audit_id="audit-bad-deferral",
            exception_trigger_id="deferral_timeout",
        )
        with pytest.raises(jsonschema.ValidationError):
            b.send_notification(bad_payload)

    def test_e_series_trigger_id_raises_validation_error(self):
        """Confirm that passing an E-series ID would fail schema — so omitting it is correct."""
        b = CaregiverEscalationBackend()
        bad_payload = _build_notification(
            event_summary="긴급",
            context_summary="test",
            unresolved_reason="emergency_event",
            audit_id="audit-bad",
            exception_trigger_id="E002",
        )
        with pytest.raises(jsonschema.ValidationError):
            b.send_notification(bad_payload)
