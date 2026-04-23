"""
Notification Backend 단위 테스트.

실제 Telegram API 를 호출하지 않는다. mock 백엔드를 사용한다.

커버리지:
  1. Class2NotificationPayload 검증 (스키마 기반)
  2. Class0AlertPayload 검증
  3. dry-run 모드 동작
  4. send_class0_alert / send_class2_escalation mock 전송
  5. 필수 필드 누락 시 ValidationError
  6. ad hoc 필드 추가 거부 (extra="forbid")
  7. mock fallback 동작 (Telegram 미설정 시)
"""
import os

import pytest
from pydantic import ValidationError

from notification_backend.mock import (
    get_sent_class0,
    get_sent_class2,
    reset_sent_records,
)
from notification_backend.models import (
    Class0AlertPayload,
    Class2NotificationPayload,
    NotificationResult,
)
from notification_backend.notifier import send_class0_alert, send_class2_escalation


# ── 픽스처 ───────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_mock_records():
    """각 테스트 전에 mock 발송 기록을 초기화한다."""
    reset_sent_records()
    yield
    reset_sent_records()


@pytest.fixture(autouse=True)
def ensure_no_telegram_env(monkeypatch):
    """Telegram 환경 변수가 없는 상태를 보장한다 (실제 API 호출 방지)."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("DRY_RUN", raising=False)


def _make_class2_payload(**kwargs) -> Class2NotificationPayload:
    defaults = dict(
        event_summary="버튼 입력 후 clarification 타임아웃",
        context_summary="거실 조명 off, 침실 조명 off, 온도 22.0",
        unresolved_reason="context_integrity_safe_deferral_timeout",
        manual_confirmation_path="Telegram 인라인 버튼으로 확인",
        audit_correlation_id="test-notif-001",
        exception_trigger_id="C201",
        source_layer="context_integrity_safe_deferral_handler",
        notification_channel="telegram",
    )
    defaults.update(kwargs)
    return Class2NotificationPayload(**defaults)


def _make_class0_payload(**kwargs) -> Class0AlertPayload:
    defaults = dict(
        event_summary="연기 감지 - E003 응급 트리거",
        context_summary="smoke_detected=True, 온도 23.0",
        emergency_trigger_id="E003",
        emergency_actions=["activate_siren", "turn_on_all_lights", "dispatch_emergency_alert"],
        audit_correlation_id="test-class0-001",
        notification_channel="telegram",
    )
    defaults.update(kwargs)
    return Class0AlertPayload(**defaults)


# ── 1. Class2NotificationPayload 검증 ────────────────────────────────────────


class TestClass2PayloadValidation:
    """class_2_notification_payload_schema 기반 페이로드 검증."""

    def test_valid_payload_passes(self):
        """필수 4개 필드가 있는 페이로드는 유효해야 한다."""
        payload = _make_class2_payload()
        assert payload.event_summary
        assert payload.context_summary
        assert payload.unresolved_reason
        assert payload.manual_confirmation_path

    def test_missing_event_summary_raises(self):
        """event_summary 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            Class2NotificationPayload(
                context_summary="x",
                unresolved_reason="y",
                manual_confirmation_path="z",
            )

    def test_missing_context_summary_raises(self):
        """context_summary 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            Class2NotificationPayload(
                event_summary="x",
                unresolved_reason="y",
                manual_confirmation_path="z",
            )

    def test_missing_unresolved_reason_raises(self):
        """unresolved_reason 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            Class2NotificationPayload(
                event_summary="x",
                context_summary="y",
                manual_confirmation_path="z",
            )

    def test_missing_manual_confirmation_path_raises(self):
        """manual_confirmation_path 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            Class2NotificationPayload(
                event_summary="x",
                context_summary="y",
                unresolved_reason="z",
            )

    def test_extra_field_rejected(self):
        """스키마에 없는 ad hoc 필드는 거부되어야 한다 (extra='forbid')."""
        with pytest.raises(ValidationError):
            Class2NotificationPayload(
                event_summary="x",
                context_summary="y",
                unresolved_reason="z",
                manual_confirmation_path="w",
                custom_field="should_fail",
            )

    def test_valid_exception_trigger_ids(self):
        """C201~C205 는 모두 유효한 exception_trigger_id 이어야 한다."""
        for trigger_id in ["C201", "C202", "C203", "C204", "C205"]:
            payload = Class2NotificationPayload(
                event_summary="x",
                context_summary="y",
                unresolved_reason="z",
                manual_confirmation_path="w",
                exception_trigger_id=trigger_id,
            )
            assert payload.exception_trigger_id == trigger_id

    def test_invalid_exception_trigger_id_rejected(self):
        """C206 같은 허용 외 trigger_id 는 ValidationError."""
        with pytest.raises(ValidationError):
            Class2NotificationPayload(
                event_summary="x",
                context_summary="y",
                unresolved_reason="z",
                manual_confirmation_path="w",
                exception_trigger_id="C206",
            )

    def test_event_summary_max_length(self):
        """event_summary 는 300자를 초과하면 ValidationError."""
        with pytest.raises(ValidationError):
            Class2NotificationPayload(
                event_summary="x" * 301,
                context_summary="y",
                unresolved_reason="z",
                manual_confirmation_path="w",
            )

    def test_context_summary_max_length(self):
        """context_summary 는 800자를 초과하면 ValidationError."""
        with pytest.raises(ValidationError):
            Class2NotificationPayload(
                event_summary="x",
                context_summary="y" * 801,
                unresolved_reason="z",
                manual_confirmation_path="w",
            )


# ── 2. Class0AlertPayload 검증 ────────────────────────────────────────────────


class TestClass0PayloadValidation:
    def test_valid_class0_payload(self):
        """필수 필드가 있는 CLASS_0 페이로드는 유효해야 한다."""
        payload = _make_class0_payload()
        assert payload.emergency_trigger_id in ("E001", "E002", "E003", "E004", "E005")

    def test_extra_field_rejected(self):
        """Class0AlertPayload 에도 ad hoc 필드는 거부되어야 한다."""
        with pytest.raises(ValidationError):
            Class0AlertPayload(
                event_summary="x",
                context_summary="y",
                emergency_trigger_id="E003",
                custom_field="fail",
            )


# ── 3. dry-run 모드 동작 ──────────────────────────────────────────────────────


class TestDryRunMode:
    def test_class2_dry_run_returns_success(self):
        """dry_run=True 시 CLASS_2 전송이 성공(mock)으로 반환되어야 한다."""
        payload = _make_class2_payload()
        result = send_class2_escalation(payload, dry_run=True)

        assert isinstance(result, NotificationResult)
        assert result.success is True
        assert result.dry_run is True

    def test_class0_dry_run_returns_success(self):
        """dry_run=True 시 CLASS_0 전송이 성공(mock)으로 반환되어야 한다."""
        payload = _make_class0_payload()
        result = send_class0_alert(payload, dry_run=True)

        assert result.success is True
        assert result.dry_run is True

    def test_dry_run_env_var_triggers_mock(self, monkeypatch):
        """DRY_RUN=1 환경 변수가 있으면 mock 모드로 동작해야 한다."""
        monkeypatch.setenv("DRY_RUN", "1")
        payload = _make_class2_payload()
        result = send_class2_escalation(payload)

        assert result.success is True
        assert result.dry_run is True


# ── 4. mock 전송 기록 검증 ────────────────────────────────────────────────────


class TestMockSentRecords:
    def test_class2_mock_records_payload(self):
        """mock 발송 후 get_sent_class2() 에 기록이 남아야 한다."""
        payload = _make_class2_payload(audit_correlation_id="rec-001")
        send_class2_escalation(payload, dry_run=True)

        sent = get_sent_class2()
        assert len(sent) == 1
        assert sent[0].audit_correlation_id == "rec-001"

    def test_class0_mock_records_payload(self):
        """mock 발송 후 get_sent_class0() 에 기록이 남아야 한다."""
        payload = _make_class0_payload(emergency_trigger_id="E001")
        send_class0_alert(payload, dry_run=True)

        sent = get_sent_class0()
        assert len(sent) == 1
        assert sent[0].emergency_trigger_id == "E001"

    def test_multiple_sends_recorded(self):
        """여러 번 발송하면 모두 기록되어야 한다."""
        for trigger in ["C201", "C204"]:
            send_class2_escalation(
                _make_class2_payload(exception_trigger_id=trigger), dry_run=True
            )
        assert len(get_sent_class2()) == 2

    def test_reset_clears_records(self):
        """reset_sent_records() 호출 후 기록이 비어야 한다."""
        send_class2_escalation(_make_class2_payload(), dry_run=True)
        reset_sent_records()
        assert len(get_sent_class2()) == 0


# ── 5. mock fallback (Telegram 미설정) ────────────────────────────────────────


class TestMockFallback:
    def test_no_telegram_config_falls_back_to_mock(self):
        """Telegram 환경 변수 없으면 mock 으로 fallback 해야 한다."""
        # ensure_no_telegram_env fixture 가 환경 변수를 제거한 상태
        payload = _make_class2_payload()
        result = send_class2_escalation(payload)

        # mock fallback 이므로 성공
        assert result.success is True
        # mock channel 은 "mock"
        assert result.channel == "mock"

    def test_fallback_class0_also_uses_mock(self):
        """CLASS_0 도 Telegram 미설정 시 mock 으로 fallback."""
        payload = _make_class0_payload()
        result = send_class0_alert(payload)

        assert result.success is True
        assert result.channel == "mock"
