"""
Caregiver Confirmation Backend 단위 테스트.

frozen 정책 파일(low_risk_actions_v1_1_0_FROZEN.json)을 실제로 로드하여 테스트한다.
허용 액션, 타겟 기기 목록을 테스트 내에서 하드코딩하지 않는다.

커버리지:
  1. 허용 목록 내 (action, target) → CONFIRMED_LOW_RISK_ACTION
  2. 허용 목록 밖 action → REJECTED_HIGH_RISK_ACTION
  3. 허용된 action + 허용 외 target → REJECTED_HIGH_RISK_ACTION
  4. 스키마 오류 입력 → ValidationError (INVALID_CONFIRMATION)
  5. Telegram callback_data 파싱 정상 케이스
  6. Telegram callback_data 파싱 오류 케이스
  7. 감사 로그 콜백 호출 검증
"""
import pytest
from pydantic import ValidationError

from caregiver_confirmation_backend.confirmer import (
    confirm,
    parse_telegram_callback,
    set_audit_log_callback,
)
from caregiver_confirmation_backend.models import (
    ConfirmationRequest,
    ConfirmationStatus,
    TelegramCallbackUpdate,
)
from caregiver_confirmation_backend.policy_loader import load_low_risk_actions


# ── 헬퍼 ────────────────────────────────────────────────────────────────────


def _allowed_pairs() -> list:
    """frozen 정책 파일에서 (action, target) 허용 조합 목록을 반환한다."""
    catalog = load_low_risk_actions()
    pairs = []
    for entry in catalog["allowed_actions_taxonomy"]:
        for target in entry["allowed_targets"]:
            pairs.append((entry["action"], target))
    return pairs


def _allowed_actions() -> list:
    """frozen 정책 파일에서 허용 action 이름 목록을 반환한다."""
    catalog = load_low_risk_actions()
    return [entry["action"] for entry in catalog["allowed_actions_taxonomy"]]


def _make_request(action: str, target: str, corr: str = "test-caregiver-001") -> ConfirmationRequest:
    return ConfirmationRequest(
        audit_correlation_id=corr,
        action=action,
        target_device=target,
    )


# ── 1. 허용 목록 내 (action, target) → CONFIRMED_LOW_RISK_ACTION ─────────────


class TestConfirmedLowRiskAction:
    def test_all_allowed_pairs_confirmed(self):
        """허용 목록의 모든 (action, target) 조합이 CONFIRMED 되어야 한다."""
        for action, target in _allowed_pairs():
            req = _make_request(action, target)
            result = confirm(req)
            assert result.status == ConfirmationStatus.CONFIRMED_LOW_RISK_ACTION, (
                f"({action}, {target}) 이 CONFIRMED 되지 않음"
            )

    def test_confirmed_response_contains_action(self):
        """CONFIRMED 결과에는 action 과 target_device 가 포함되어야 한다."""
        action, target = _allowed_pairs()[0]
        result = confirm(_make_request(action, target))

        assert result.status == ConfirmationStatus.CONFIRMED_LOW_RISK_ACTION
        assert result.action == action
        assert result.target_device == target

    def test_confirmed_response_contains_correlation_id(self):
        """CONFIRMED 결과에는 audit_correlation_id 가 유지되어야 한다."""
        action, target = _allowed_pairs()[0]
        corr = "confirm-corr-xyz"
        result = confirm(_make_request(action, target, corr))

        assert result.audit_correlation_id == corr


# ── 2. 허용 목록 밖 action → REJECTED_HIGH_RISK_ACTION ───────────────────────


class TestRejectedHighRiskAction:
    def test_unknown_action_rejected(self):
        """허용 목록에 없는 action 은 REJECTED_HIGH_RISK_ACTION 이어야 한다."""
        req = _make_request("door_unlock", "front_door")
        result = confirm(req)

        assert result.status == ConfirmationStatus.REJECTED_HIGH_RISK_ACTION

    def test_siren_action_rejected(self):
        """siren 같은 고위험 액션은 REJECTED 되어야 한다."""
        req = _make_request("activate_siren", "all_zones")
        result = confirm(req)

        assert result.status == ConfirmationStatus.REJECTED_HIGH_RISK_ACTION

    def test_arbitrary_action_rejected(self):
        """임의의 알 수 없는 action 은 모두 REJECTED 되어야 한다."""
        for action in ["delete_data", "open_valve", "cut_power"]:
            result = confirm(_make_request(action, "living_room_light"))
            assert result.status == ConfirmationStatus.REJECTED_HIGH_RISK_ACTION, (
                f"action='{action}' 이 REJECTED 되지 않음"
            )

    def test_rejected_response_contains_reason(self):
        """REJECTED 결과에는 reason 이 있어야 한다."""
        result = confirm(_make_request("door_unlock", "front_door"))

        assert result.status == ConfirmationStatus.REJECTED_HIGH_RISK_ACTION
        assert result.reason


# ── 3. 허용된 action + 허용 외 target → REJECTED_HIGH_RISK_ACTION ────────────


class TestRejectedInvalidTarget:
    def test_allowed_action_with_invalid_target_rejected(self):
        """
        허용된 action 이라도 허용 목록에 없는 target_device 조합은 거부해야 한다.
        예: light_on + kitchen_light (kitchen_light 는 허용 타겟이 아님)
        """
        actions = _allowed_actions()
        assert actions, "허용 액션 목록이 비어 있음"

        # kitchen_light 는 현재 허용 타겟(living_room_light, bedroom_light)에 없음
        result = confirm(_make_request(actions[0], "kitchen_light"))
        assert result.status == ConfirmationStatus.REJECTED_HIGH_RISK_ACTION

    def test_allowed_action_with_none_target_rejected(self):
        """
        허용된 action + target_device='none' 조합은 거부해야 한다.
        'none' 은 safe_deferral 용으로만 쓰이며 caregiver 확인 대상이 아니다.
        """
        actions = _allowed_actions()
        result = confirm(_make_request(actions[0], "none"))
        assert result.status == ConfirmationStatus.REJECTED_HIGH_RISK_ACTION


# ── 4. 스키마 오류 입력 → ValidationError ────────────────────────────────────


class TestSchemaValidation:
    def test_missing_correlation_id_raises(self):
        """audit_correlation_id 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            ConfirmationRequest(action="light_on", target_device="living_room_light")

    def test_missing_action_raises(self):
        """action 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            ConfirmationRequest(
                audit_correlation_id="test-001",
                target_device="living_room_light",
            )

    def test_missing_target_raises(self):
        """target_device 누락 시 ValidationError."""
        with pytest.raises(ValidationError):
            ConfirmationRequest(
                audit_correlation_id="test-001",
                action="light_on",
            )

    def test_extra_field_rejected(self):
        """extra 필드는 거부되어야 한다 (extra='forbid')."""
        with pytest.raises(ValidationError):
            ConfirmationRequest(
                audit_correlation_id="test-001",
                action="light_on",
                target_device="living_room_light",
                unknown_field="fail",
            )

    def test_empty_action_rejected(self):
        """빈 action 문자열은 ValidationError."""
        with pytest.raises(ValidationError):
            ConfirmationRequest(
                audit_correlation_id="test-001",
                action="",
                target_device="living_room_light",
            )


# ── 5. Telegram callback_data 파싱 정상 케이스 ───────────────────────────────


class TestTelegramCallbackParsing:
    def test_valid_callback_data_parsed(self):
        """정상 callback_data 가 ConfirmationRequest 로 파싱되어야 한다."""
        update = TelegramCallbackUpdate(
            callback_data="confirm:light_on:living_room_light:corr-abc123",
            from_user_id=987654321,
        )
        req = parse_telegram_callback(update)

        assert req.action == "light_on"
        assert req.target_device == "living_room_light"
        assert req.audit_correlation_id == "corr-abc123"
        assert req.confirmed_by == "987654321"

    def test_parsed_request_can_be_confirmed(self):
        """파싱된 요청이 허용 목록 내 액션이면 CONFIRMED 되어야 한다."""
        action, target = _allowed_pairs()[0]
        update = TelegramCallbackUpdate(
            callback_data=f"confirm:{action}:{target}:corr-telegram-001",
        )
        req = parse_telegram_callback(update)
        result = confirm(req)

        assert result.status == ConfirmationStatus.CONFIRMED_LOW_RISK_ACTION

    def test_without_user_id_confirmed_by_is_none(self):
        """from_user_id 없으면 confirmed_by 는 None 이어야 한다."""
        action, target = _allowed_pairs()[0]
        update = TelegramCallbackUpdate(
            callback_data=f"confirm:{action}:{target}:corr-001",
        )
        req = parse_telegram_callback(update)
        assert req.confirmed_by is None


# ── 6. Telegram callback_data 파싱 오류 케이스 ───────────────────────────────


class TestTelegramCallbackParsingErrors:
    def test_wrong_prefix_raises(self):
        """'confirm' 이 아닌 prefix 는 ValueError."""
        update = TelegramCallbackUpdate(
            callback_data="execute:light_on:living_room_light:corr-001"
        )
        with pytest.raises(ValueError):
            parse_telegram_callback(update)

    def test_too_few_parts_raises(self):
        """파트가 4개 미만이면 ValueError."""
        update = TelegramCallbackUpdate(callback_data="confirm:light_on:living_room_light")
        with pytest.raises(ValueError):
            parse_telegram_callback(update)

    def test_too_many_parts_raises(self):
        """파트가 4개 초과이면 ValueError."""
        update = TelegramCallbackUpdate(
            callback_data="confirm:light_on:living_room_light:corr:extra"
        )
        with pytest.raises(ValueError):
            parse_telegram_callback(update)

    def test_empty_action_in_callback_raises(self):
        """callback_data 의 action 파트가 비어 있으면 ValueError."""
        update = TelegramCallbackUpdate(
            callback_data="confirm::living_room_light:corr-001"
        )
        with pytest.raises(ValueError):
            parse_telegram_callback(update)


# ── 7. 감사 로그 콜백 호출 검증 ──────────────────────────────────────────────


class TestAuditLogCallback:
    def test_audit_callback_called_on_confirm(self):
        """CONFIRMED 시 감사 로그 콜백이 호출되어야 한다."""
        audit_events = []

        def mock_callback(event_type: str, event: dict) -> None:
            audit_events.append((event_type, event))

        set_audit_log_callback(mock_callback)
        action, target = _allowed_pairs()[0]
        confirm(_make_request(action, target, "audit-test-001"))

        assert len(audit_events) == 1
        event_type, event = audit_events[0]
        assert event_type == "caregiver_action"
        assert event["audit_correlation_id"] == "audit-test-001"
        assert event["action_type"] == "confirmed"

        # 테스트 후 콜백 해제
        set_audit_log_callback(None)

    def test_audit_callback_called_on_reject(self):
        """REJECTED 시에도 감사 로그 콜백이 호출되어야 한다."""
        audit_events = []

        def mock_callback(event_type: str, event: dict) -> None:
            audit_events.append((event_type, event))

        set_audit_log_callback(mock_callback)
        confirm(_make_request("door_unlock", "front_door", "audit-test-002"))

        assert len(audit_events) == 1
        _, event = audit_events[0]
        assert event["action_type"] == "rejected"
        assert event["audit_correlation_id"] == "audit-test-002"

        set_audit_log_callback(None)

    def test_audit_callback_failure_does_not_affect_result(self):
        """감사 로그 콜백이 예외를 던져도 확인 결과에 영향을 주지 않아야 한다."""
        def failing_callback(event_type: str, event: dict) -> None:
            raise RuntimeError("감사 로그 서비스 장애")

        set_audit_log_callback(failing_callback)
        action, target = _allowed_pairs()[0]
        # 예외가 전파되지 않고 정상 결과가 반환되어야 함
        result = confirm(_make_request(action, target))
        assert result.status == ConfirmationStatus.CONFIRMED_LOW_RISK_ACTION

        set_audit_log_callback(None)
