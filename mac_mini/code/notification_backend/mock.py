"""
Mock 알림 백엔드.

실제 외부 API 를 호출하지 않고 로그에만 기록한다.
dry-run 모드 테스트, CI 환경, Telegram 토큰 미설정 상황에서 사용한다.
"""
import logging
from typing import List

from .models import Class0AlertPayload, Class2NotificationPayload, NotificationResult

logger = logging.getLogger(__name__)

# 테스트에서 검증할 수 있도록 발송 기록을 보관한다
_sent_class0: List[Class0AlertPayload] = []
_sent_class2: List[Class2NotificationPayload] = []


def reset_sent_records() -> None:
    """테스트 간 발송 기록을 초기화한다."""
    _sent_class0.clear()
    _sent_class2.clear()


def get_sent_class0() -> List[Class0AlertPayload]:
    """발송된 CLASS_0 알림 목록을 반환한다."""
    return list(_sent_class0)


def get_sent_class2() -> List[Class2NotificationPayload]:
    """발송된 CLASS_2 알림 목록을 반환한다."""
    return list(_sent_class2)


def send_class0_alert(payload: Class0AlertPayload) -> NotificationResult:
    """CLASS_0 응급 알림을 mock 으로 발송한다 (로그에만 기록)."""
    _sent_class0.append(payload)
    logger.warning(
        "[MOCK] CLASS_0 응급 알림 | trigger=%s summary=%s correlation=%s",
        payload.emergency_trigger_id,
        payload.event_summary,
        payload.audit_correlation_id,
    )
    return NotificationResult(success=True, channel="mock", dry_run=True)


def send_class2_escalation(payload: Class2NotificationPayload) -> NotificationResult:
    """CLASS_2 보호자 에스컬레이션 알림을 mock 으로 발송한다 (로그에만 기록)."""
    _sent_class2.append(payload)
    logger.warning(
        "[MOCK] CLASS_2 에스컬레이션 | trigger=%s reason=%s correlation=%s",
        payload.exception_trigger_id,
        payload.unresolved_reason,
        payload.audit_correlation_id,
    )
    return NotificationResult(success=True, channel="mock", dry_run=True)
