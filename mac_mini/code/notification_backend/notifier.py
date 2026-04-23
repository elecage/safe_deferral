"""
Notification Backend 공개 인터페이스.

send_class0_alert(payload)  : CLASS_0 응급 알림 전송
send_class2_escalation(payload) : CLASS_2 보호자 에스컬레이션 전송

dry_run=True 이면 mock 백엔드를 사용하고 실제 외부 API 를 호출하지 않는다.
DRY_RUN 환경 변수가 설정되어 있어도 mock 모드로 동작한다.

기본 채널은 Telegram 이다. TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 가
미설정인 경우 자동으로 mock 으로 fallback 한다.

페이로드는 반드시 class_2_notification_payload_schema_v1_0_0_FROZEN.json 에 정의된
필드만 사용한다. ad hoc 필드 추가 금지.
"""
import logging
import os

from .models import Class0AlertPayload, Class2NotificationPayload, NotificationResult
from . import mock as _mock
from . import telegram as _telegram

logger = logging.getLogger(__name__)


def _is_dry_run() -> bool:
    """DRY_RUN 환경 변수가 설정되어 있으면 True 를 반환한다."""
    return os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")


def _telegram_configured() -> bool:
    """Telegram 설정이 완료되어 있으면 True 를 반환한다."""
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN")) and bool(
        os.environ.get("TELEGRAM_CHAT_ID")
    )


def send_class0_alert(
    payload: Class0AlertPayload, dry_run: bool = False
) -> NotificationResult:
    """
    CLASS_0 응급 알림을 전송한다.
    dry_run=True 이거나 DRY_RUN 환경 변수가 설정된 경우 mock 을 사용한다.
    """
    if dry_run or _is_dry_run():
        logger.info("CLASS_0 알림 dry-run | trigger=%s", payload.emergency_trigger_id)
        return _mock.send_class0_alert(payload)

    if not _telegram_configured():
        logger.warning("Telegram 미설정 - mock fallback | trigger=%s", payload.emergency_trigger_id)
        return _mock.send_class0_alert(payload)

    return _telegram.send_class0_alert(payload)


def send_class2_escalation(
    payload: Class2NotificationPayload, dry_run: bool = False
) -> NotificationResult:
    """
    CLASS_2 보호자 에스컬레이션 알림을 전송한다.
    dry_run=True 이거나 DRY_RUN 환경 변수가 설정된 경우 mock 을 사용한다.
    """
    if dry_run or _is_dry_run():
        logger.info(
            "CLASS_2 알림 dry-run | trigger=%s", payload.exception_trigger_id
        )
        return _mock.send_class2_escalation(payload)

    if not _telegram_configured():
        logger.warning(
            "Telegram 미설정 - mock fallback | trigger=%s", payload.exception_trigger_id
        )
        return _mock.send_class2_escalation(payload)

    return _telegram.send_class2_escalation(payload)
