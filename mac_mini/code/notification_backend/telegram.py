"""
Telegram Bot API 알림 구현.

httpx 를 사용해 Telegram sendMessage API 를 호출한다.
클라우드 API 를 직접 호출하는 유일한 허용된 아웃바운드 경로이다.
인바운드 접근은 이 모듈에서 허용하지 않는다.

환경 변수:
  TELEGRAM_BOT_TOKEN : Telegram Bot API 토큰
  TELEGRAM_CHAT_ID   : 보호자 채팅 ID
"""
import logging
import os
from typing import Optional

import httpx

from .models import Class0AlertPayload, Class2NotificationPayload, NotificationResult

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"
_REQUEST_TIMEOUT_SECONDS = 10


def _get_token() -> Optional[str]:
    return os.environ.get("TELEGRAM_BOT_TOKEN")


def _get_chat_id() -> Optional[str]:
    return os.environ.get("TELEGRAM_CHAT_ID")


def _send_message(text: str) -> NotificationResult:
    """
    Telegram sendMessage API 를 호출한다.
    토큰 또는 chat_id 가 없으면 실패 결과를 반환한다.
    """
    token = _get_token()
    chat_id = _get_chat_id()

    if not token or not chat_id:
        logger.error(
            "Telegram 설정 누락 | TELEGRAM_BOT_TOKEN=%s TELEGRAM_CHAT_ID=%s",
            "설정됨" if token else "미설정",
            "설정됨" if chat_id else "미설정",
        )
        return NotificationResult(
            success=False,
            channel="telegram",
            error_message="TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 미설정",
        )

    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    try:
        resp = httpx.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        logger.info("Telegram 전송 성공 | status=%d", resp.status_code)
        return NotificationResult(success=True, channel="telegram")
    except httpx.HTTPError as exc:
        logger.error("Telegram 전송 실패: %s", exc)
        return NotificationResult(
            success=False, channel="telegram", error_message=str(exc)
        )


def _format_class0_message(payload: Class0AlertPayload) -> str:
    """CLASS_0 응급 알림 메시지를 포맷한다."""
    actions = ", ".join(payload.emergency_actions) if payload.emergency_actions else "없음"
    return (
        f"🚨 <b>[응급] {payload.emergency_trigger_id}</b>\n\n"
        f"📋 {payload.event_summary}\n\n"
        f"🌡 {payload.context_summary}\n\n"
        f"⚡ 즉시 실행 액션: {actions}\n\n"
        f"🔗 correlation: {payload.audit_correlation_id or 'N/A'}"
    )


def _format_class2_message(payload: Class2NotificationPayload) -> str:
    """CLASS_2 보호자 에스컬레이션 메시지를 포맷한다."""
    return (
        f"⚠️ <b>[보호자 알림] {payload.exception_trigger_id or ''}</b>\n\n"
        f"📋 {payload.event_summary}\n\n"
        f"🏠 {payload.context_summary}\n\n"
        f"❓ 미해결 이유: {payload.unresolved_reason}\n\n"
        f"✅ 확인 방법: {payload.manual_confirmation_path}\n\n"
        f"🔗 correlation: {payload.audit_correlation_id or 'N/A'}"
    )


def send_class0_alert(payload: Class0AlertPayload) -> NotificationResult:
    """CLASS_0 응급 알림을 Telegram 으로 전송한다."""
    text = _format_class0_message(payload)
    return _send_message(text)


def send_class2_escalation(payload: Class2NotificationPayload) -> NotificationResult:
    """CLASS_2 보호자 에스컬레이션 알림을 Telegram 으로 전송한다."""
    text = _format_class2_message(payload)
    return _send_message(text)
