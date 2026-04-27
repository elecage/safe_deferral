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

from typing import Optional, Protocol


class TelegramSender(Protocol):
    """Minimal interface for sending a Telegram message."""

    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        """Return the Telegram message_id on success, None on failure."""
        ...


class _NoOpTelegramSender:
    """Used when no real Telegram client is injected (test / dry-run)."""

    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        return None


class HttpTelegramSender:
    """Production sender — calls the Telegram Bot API over HTTP.

    Requires `requests` package.  Instantiate with bot_token from environment.
    """

    _API_BASE = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str) -> None:
        self._token = bot_token

    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        import requests  # imported lazily so unit tests never need it

        url = self._API_BASE.format(token=self._token)
        try:
            resp = requests.post(
                url,
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", {}).get("message_id")
        except Exception:
            return None


def format_notification_message(notification_payload: dict) -> str:
    """Convert a class2_notification_payload dict to a Telegram HTML string."""
    event = notification_payload.get("event_summary", "")
    reason = notification_payload.get("unresolved_reason", "")
    context = notification_payload.get("context_summary", "")
    path = notification_payload.get("manual_confirmation_path", "")
    trigger = notification_payload.get("exception_trigger_id") or "—"
    audit_id = notification_payload.get("audit_correlation_id", "")

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
