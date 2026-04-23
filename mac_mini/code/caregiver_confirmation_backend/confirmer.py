"""
Caregiver Confirmation Backend 핵심 확인 로직.

허용 액션 목록은 low_risk_actions_v1_1_0_FROZEN.json 에서 읽어온다. 하드코딩 금지.
확인 결과는 audit_logging_service 의 단일 writer 를 통해 기록한다.
직접 SQLite 에 쓰지 않는다.

처리 순서:
  1. 요청 형식 검증 (Pydantic 이 입력 진입 시 자동 처리)
  2. (action, target_device) 쌍이 허용 목록에 있는지 확인
     - 없으면 REJECTED_HIGH_RISK_ACTION
  3. 허용 목록에 있으면 CONFIRMED_LOW_RISK_ACTION
  4. 결과를 audit_logging_service 채널로 기록
"""
import logging
from typing import Any, Callable, Dict, Optional, Set, Tuple

from .models import (
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationStatus,
    TelegramCallbackUpdate,
)
from .policy_loader import load_low_risk_actions

logger = logging.getLogger(__name__)

_LOW_RISK_ACTIONS: Dict[str, Any] = {}

# 감사 로깅 콜백 - 기본값은 logger 출력 (실제 운영 시 audit_logging_service 로 교체)
# 직접 SQLite 쓰기를 방지하기 위해 의존성 주입 패턴 사용
_audit_log_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None


def set_audit_log_callback(
    callback: Callable[[str, Dict[str, Any]], None]
) -> None:
    """
    감사 로그 콜백을 설정한다.
    callback(event_type, event_dict) 형태로 호출된다.
    audit_logging_service.log_caregiver_action 을 주입하면
    단일 writer 규칙을 준수하면서 감사 기록을 남길 수 있다.
    """
    global _audit_log_callback
    _audit_log_callback = callback


def _ensure_policy_loaded() -> None:
    global _LOW_RISK_ACTIONS
    if not _LOW_RISK_ACTIONS:
        _LOW_RISK_ACTIONS = load_low_risk_actions()
        logger.info(
            "low_risk_actions 로드 완료 | version=%s", _LOW_RISK_ACTIONS.get("version")
        )


def _build_allowed_set() -> Set[Tuple[str, str]]:
    """(action, target_device) 허용 조합 집합을 반환한다."""
    allowed: Set[Tuple[str, str]] = set()
    for entry in _LOW_RISK_ACTIONS.get("allowed_actions_taxonomy", []):
        action = entry.get("action")
        for target in entry.get("allowed_targets", []):
            allowed.add((action, target))
    return allowed


def _get_allowed_actions() -> Set[str]:
    """허용된 action 이름 집합만 반환한다 (target 무관)."""
    return {
        entry.get("action")
        for entry in _LOW_RISK_ACTIONS.get("allowed_actions_taxonomy", [])
    }


def _emit_audit(action_type: str, response: ConfirmationResponse, request: ConfirmationRequest) -> None:
    """확인 결과를 감사 채널로 기록한다."""
    event = {
        "event_type": "caregiver_action",
        "audit_correlation_id": request.audit_correlation_id,
        "action_type": action_type,
        "confirmed_action": request.action,
        "confirmed_target": request.target_device,
        "status": response.status.value,
        "reason": response.reason,
    }
    if _audit_log_callback:
        try:
            _audit_log_callback("caregiver_action", event)
        except Exception as exc:
            # 감사 로그 실패가 확인 결과에 영향을 주면 안 된다
            logger.error("감사 로그 기록 실패: %s", exc)
    else:
        logger.info(
            "감사 이벤트 | %s correlation_id=%s action=%s target=%s",
            action_type,
            request.audit_correlation_id,
            request.action,
            request.target_device,
        )


def confirm(request: ConfirmationRequest) -> ConfirmationResponse:
    """
    보호자 확인 요청을 처리한다.

    (action, target_device) 쌍이 frozen low_risk_actions catalog 안에 있으면
    CONFIRMED_LOW_RISK_ACTION 을 반환한다.
    허용 목록 밖 액션(고위험 포함)은 REJECTED_HIGH_RISK_ACTION 으로 거부한다.
    """
    _ensure_policy_loaded()

    allowed_set = _build_allowed_set()
    allowed_actions = _get_allowed_actions()

    pair = (request.action, request.target_device)

    # ── action 자체가 허용 목록에 없음 → 고위험 거부 ──────────────────────
    if request.action not in allowed_actions:
        response = ConfirmationResponse(
            status=ConfirmationStatus.REJECTED_HIGH_RISK_ACTION,
            audit_correlation_id=request.audit_correlation_id,
            action=request.action,
            target_device=request.target_device,
            reason=(
                f"action '{request.action}' 이 허용 목록에 없음 - "
                "고위험 액션 거부"
            ),
        )
        logger.warning(
            "REJECTED_HIGH_RISK_ACTION | correlation_id=%s action=%s",
            request.audit_correlation_id,
            request.action,
        )
        _emit_audit("rejected", response, request)
        return response

    # ── (action, target_device) 조합이 허용 목록에 없음 → 거부 ────────────
    if pair not in allowed_set:
        response = ConfirmationResponse(
            status=ConfirmationStatus.REJECTED_HIGH_RISK_ACTION,
            audit_correlation_id=request.audit_correlation_id,
            action=request.action,
            target_device=request.target_device,
            reason=(
                f"target_device '{request.target_device}' 이 "
                f"action '{request.action}' 의 허용 타겟에 없음"
            ),
        )
        logger.warning(
            "REJECTED_HIGH_RISK_ACTION | correlation_id=%s action=%s target=%s",
            request.audit_correlation_id,
            request.action,
            request.target_device,
        )
        _emit_audit("rejected", response, request)
        return response

    # ── 허용 목록 내 저위험 액션 확인 완료 ────────────────────────────────
    response = ConfirmationResponse(
        status=ConfirmationStatus.CONFIRMED_LOW_RISK_ACTION,
        audit_correlation_id=request.audit_correlation_id,
        action=request.action,
        target_device=request.target_device,
        reason="허용된 저위험 액션 확인 완료",
    )
    logger.info(
        "CONFIRMED_LOW_RISK_ACTION | correlation_id=%s action=%s target=%s",
        request.audit_correlation_id,
        request.action,
        request.target_device,
    )
    _emit_audit("confirmed", response, request)
    return response


def parse_telegram_callback(update: TelegramCallbackUpdate) -> ConfirmationRequest:
    """
    Telegram inline button callback_data 를 파싱해 ConfirmationRequest 로 변환한다.
    callback_data 포맷: "confirm:<action>:<target_device>:<correlation_id>"

    포맷이 맞지 않으면 ValueError 를 발생시킨다.
    """
    parts = update.callback_data.split(":")
    # "confirm", action, target_device, correlation_id → 4개 파트
    if len(parts) != 4 or parts[0] != "confirm":
        raise ValueError(
            f"잘못된 callback_data 포맷: '{update.callback_data}'. "
            "예상 포맷: 'confirm:<action>:<target_device>:<correlation_id>'"
        )

    _, action, target_device, correlation_id = parts

    if not action or not target_device or not correlation_id:
        raise ValueError("callback_data 파트에 빈 값이 있음")

    return ConfirmationRequest(
        audit_correlation_id=correlation_id,
        action=action,
        target_device=target_device,
        confirmed_by=str(update.from_user_id) if update.from_user_id else None,
    )
