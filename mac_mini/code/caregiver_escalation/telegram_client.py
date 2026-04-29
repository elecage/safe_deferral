"""Telegram notification client (MM-08).

Formats Class 2 notification payloads into human-readable Telegram messages
and sends them via the Bot API.

Authority boundary (02_safety_and_authority_boundaries.md §8):
  Telegram is outbound notification and response-collection transport ONLY.
  It is not a remote-control channel, direct actuator interface, doorlock
  console, or replacement for policy routing, validation, dispatch, ACK, or
  audit on the Mac mini.

TelegramSender is injected as a protocol so the backend can be unit-tested
without network access.
"""

import html
import logging
import threading
import time
from typing import Optional, Protocol

log = logging.getLogger("sd.telegram")


class TelegramSendError(Exception):
    """Raised by HttpTelegramSender when delivery fails after all retries."""


class TelegramSender(Protocol):
    """Minimal interface for sending a Telegram message."""

    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        """Return the Telegram message_id on success, or None.

        May raise TelegramSendError on synchronous delivery failure
        (e.g. test mocks).  HttpTelegramSender never raises — it sends
        asynchronously and logs failures in the background thread.
        """
        ...


class NoOpTelegramSender:
    """Used when no real Telegram client is injected (test / dry-run).

    Returns None rather than raising — PENDING is the correct status for
    dry-run/test mode where delivery is intentionally skipped.
    """

    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        return None


class HttpTelegramSender:
    """Production sender — calls the Telegram Bot API over HTTP.

    send_message() fires the HTTP call in a daemon thread and returns None
    immediately so the pipeline worker thread is never blocked.  Delivery
    failures are logged by the background thread.

    Requires `requests` package.
    """

    _API_BASE = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, max_retries: int = 1) -> None:
        self._token = bot_token
        self._max_retries = max_retries

    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        """Launch the HTTP send in a daemon thread; return None immediately."""
        threading.Thread(
            target=self._send_with_retry,
            args=(chat_id, text, parse_mode),
            daemon=True,
            name="telegram-sender",
        ).start()
        return None  # EscalationStatus stays PENDING; background thread logs failure

    def _send_with_retry(self, chat_id: str, text: str, parse_mode: str) -> None:
        import requests  # lazy import so unit tests never need it

        url = self._API_BASE.format(token=self._token)
        last_exc: Exception = Exception("no attempts made")
        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                time.sleep(1)
            try:
                resp = requests.post(
                    url,
                    json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                    timeout=10,
                )
                resp.raise_for_status()
                return
            except Exception as exc:
                last_exc = exc
        log.warning(
            "Telegram delivery failed after %d attempt(s): %s",
            self._max_retries + 1, last_exc,
        )


def format_notification_message(notification_payload: dict) -> str:
    """Convert a class2_notification_payload dict to a Telegram HTML string."""
    event   = html.escape(notification_payload.get("event_summary", ""))
    reason  = html.escape(notification_payload.get("unresolved_reason", ""))
    context = html.escape(notification_payload.get("context_summary", ""))
    path    = html.escape(notification_payload.get("manual_confirmation_path", ""))
    trigger = html.escape(notification_payload.get("exception_trigger_id") or "—")
    audit_id = html.escape(notification_payload.get("audit_correlation_id", ""))

    lines = [
        "🔔 <b>보호자 에스컬레이션 알림</b>",
        "",
        f"<b>이벤트:</b> {event}",
        f"<b>미해결 이유:</b> {reason}",
        f"<b>트리거 ID:</b> {trigger}",
        "",
        f"<b>컨텍스트 요약:</b>",
        context,
        "",
        f"<b>수동 확인 경로:</b>",
        path,
        "",
        f"<i>감사 ID: {audit_id}</i>",
    ]
    return "\n".join(lines)
