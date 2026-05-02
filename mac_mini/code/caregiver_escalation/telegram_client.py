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

TelegramPoller provides long-polling for inline keyboard callback_query
responses from the caregiver (CLASS_2 clarification flow).
"""

import html
import logging
import threading
import time
from typing import Callable, Optional, Protocol

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

    def send_message_with_buttons(
        self,
        chat_id: str,
        text: str,
        buttons: list,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        """Send a message with an inline keyboard.

        buttons: list[list[dict]] — Telegram InlineKeyboardMarkup rows.
        Returns message_id on success, None on failure (synchronous).
        """
        ...

    def answer_callback_query(self, callback_query_id: str) -> None:
        """Dismiss the loading spinner on the pressed button (fire-and-forget)."""
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

    def send_message_with_buttons(
        self,
        chat_id: str,
        text: str,
        buttons: list,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        return None

    def answer_callback_query(self, callback_query_id: str) -> None:
        pass


class HttpTelegramSender:
    """Production sender — calls the Telegram Bot API over HTTP.

    send_message() fires the HTTP call in a daemon thread and returns None
    immediately so the pipeline worker thread is never blocked.  Delivery
    failures are logged by the background thread.

    send_message_with_buttons() is synchronous — it blocks until the Bot API
    responds (or timeout).  This is intentional: the CLASS_2 wait loop must
    not start until the inline keyboard is confirmed delivered.

    Requires `requests` package.
    """

    _API_BASE = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, bot_token: str, max_retries: int = 1) -> None:
        self._token = bot_token
        self._max_retries = max_retries

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _url(self, method: str) -> str:
        return self._API_BASE.format(token=self._token, method=method)

    # ------------------------------------------------------------------
    # Async plain text message
    # ------------------------------------------------------------------

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

        url = self._url("sendMessage")
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

    # ------------------------------------------------------------------
    # Synchronous inline-keyboard message
    # ------------------------------------------------------------------

    def send_message_with_buttons(
        self,
        chat_id: str,
        text: str,
        buttons: list,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        """Send a message with an inline keyboard (blocking).

        Returns the Telegram message_id on success, or None on failure.
        Synchronous so the CLASS_2 event-wait loop starts only after delivery.
        """
        import requests  # lazy import

        url = self._url("sendMessage")
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "reply_markup": {"inline_keyboard": buttons},
        }
        last_exc: Exception = Exception("no attempts made")
        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                time.sleep(1)
            try:
                resp = requests.post(url, json=payload, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                message_id = data.get("result", {}).get("message_id")
                log.info("Telegram inline-keyboard message sent: message_id=%s", message_id)
                return message_id
            except Exception as exc:
                last_exc = exc
        log.warning(
            "Telegram inline-keyboard send failed after %d attempt(s): %s",
            self._max_retries + 1, last_exc,
        )
        return None

    # ------------------------------------------------------------------
    # Answer callback query (dismiss spinner)
    # ------------------------------------------------------------------

    def answer_callback_query(self, callback_query_id: str) -> None:
        """Dismiss the button loading spinner (fire-and-forget)."""
        threading.Thread(
            target=self._answer_callback,
            args=(callback_query_id,),
            daemon=True,
            name="telegram-answer-cbq",
        ).start()

    def _answer_callback(self, callback_query_id: str) -> None:
        import requests  # lazy import

        url = self._url("answerCallbackQuery")
        try:
            requests.post(
                url,
                json={"callback_query_id": callback_query_id},
                timeout=10,
            )
        except Exception as exc:
            log.warning("answerCallbackQuery failed: %s", exc)


# ---------------------------------------------------------------------------
# Long-polling receiver for caregiver inline-keyboard responses
# ---------------------------------------------------------------------------

class TelegramPoller:
    """Background long-polling thread for Telegram callback_query updates.

    Polls /getUpdates with a 20-second server-side timeout.  When a
    callback_query arrives its callback_data and callback_query_id are
    forwarded to the registered handler.

    Usage:
        poller = TelegramPoller(token, handler=pipeline.handle_telegram_callback)
        poller.start()   # returns immediately; polling runs in daemon thread

    Handler signature:
        handler(callback_query: dict) -> None
        callback_query keys: id, data, from, message, ...
    """

    _POLL_TIMEOUT_S = 20   # server-side long-poll wait (Bot API timeout param)
    _HTTP_TIMEOUT_S = 30   # socket-level timeout (must be > _POLL_TIMEOUT_S)
    _BACKOFF_S = 5         # sleep after repeated network errors

    def __init__(
        self,
        bot_token: str,
        handler: Callable[[dict], None],
    ) -> None:
        self._token = bot_token
        self._handler = handler
        self._offset: int = 0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the polling daemon thread (idempotent)."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="telegram-poller",
        )
        self._thread.start()
        log.info("TelegramPoller started.")

    def stop(self) -> None:
        """Signal the polling loop to stop (best-effort)."""
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Internal poll loop
    # ------------------------------------------------------------------

    def _poll_loop(self) -> None:
        import requests  # lazy import

        url = f"https://api.telegram.org/bot{self._token}/getUpdates"
        consecutive_errors = 0

        while not self._stop_event.is_set():
            try:
                resp = requests.get(
                    url,
                    params={
                        "offset": self._offset,
                        "timeout": self._POLL_TIMEOUT_S,
                        "allowed_updates": ["callback_query"],
                    },
                    timeout=self._HTTP_TIMEOUT_S,
                )
                resp.raise_for_status()
                updates = resp.json().get("result", [])
                consecutive_errors = 0

                for update in updates:
                    self._offset = update["update_id"] + 1
                    cbq = update.get("callback_query")
                    if cbq:
                        try:
                            self._handler(cbq)
                        except Exception as exc:
                            log.warning("callback_query handler error: %s", exc)

            except Exception as exc:
                consecutive_errors += 1
                log.warning(
                    "TelegramPoller getUpdates error (#%d): %s",
                    consecutive_errors, exc,
                )
                # Exponential-ish backoff, capped at 60s
                sleep_s = min(self._BACKOFF_S * consecutive_errors, 60)
                self._stop_event.wait(timeout=sleep_s)

        log.info("TelegramPoller stopped.")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Caregiver-facing button label mapping
# ---------------------------------------------------------------------------
# choice.prompt is written for the USER (read aloud via TTS to the resident).
# Telegram buttons go to the CAREGIVER, so labels must be from the caregiver's
# perspective: "what action am I approving / directing?"
#
# Primary lookup: candidate_id  (most specific)
# Fallback lookup: candidate_transition_target  (covers unknown future ids)
# Final fallback: choice.prompt with a "✅ " prefix so it is at least visible

_CAREGIVER_LABEL_BY_ID: dict[str, str] = {
    "C1_LIGHTING_ASSISTANCE": "💡 조명 지원 승인",
    "C2_CAREGIVER_HELP":      "👤 보호자 직접 개입",
    "C3_EMERGENCY_HELP":      "🚨 긴급 상황으로 처리",
    # C4 prompt is context-dependent (doc 12 step 2-B): for lighting
    # reasons the user hears '다른 동작이 필요하신가요?', for non-lighting
    # reasons the user hears '취소하고 대기할까요?'. The caregiver-facing
    # label combines both meanings since the underlying SAFE_DEFERRAL
    # transition is the same.
    "C4_CANCEL_OR_WAIT":      "⏸ 취소 / 다른 동작 / 대기",
    "OPT_LIVING_ROOM":        "💡 거실 조명 제어 승인",
    "OPT_BEDROOM":            "💡 침실 조명 제어 승인",
    "OPT_RETRY":              "🔄 재시도 승인",
}

_CAREGIVER_LABEL_BY_TRANSITION: dict[str, str] = {
    "CLASS_1":                              "💡 조명 지원 승인",
    "CLASS_0":                              "🚨 긴급 상황으로 처리",
    "CAREGIVER_CONFIRMATION":               "👤 보호자 직접 개입",
    "SAFE_DEFERRAL":                        "⏸ 취소 / 대기",
    "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION": "⏸ 취소 / 대기",
}


def _caregiver_button_label(choice) -> str:
    """Return a caregiver-facing button label for the given ClarificationChoice."""
    label = _CAREGIVER_LABEL_BY_ID.get(choice.candidate_id)
    if label:
        return label
    label = _CAREGIVER_LABEL_BY_TRANSITION.get(
        getattr(choice, "candidate_transition_target", "")
    )
    return label or f"✅ {choice.prompt}"


def build_inline_keyboard(
    candidates: list,
    clarification_id: str,
) -> list:
    """Build a Telegram InlineKeyboardMarkup rows list from candidate choices.

    Each candidate becomes one button row with a CAREGIVER-facing label
    (not the user-facing TTS prompt stored in choice.prompt).

    callback_data format: "c2:{clarification_id}:{candidate_id}"

    Args:
        candidates: list of ClarificationChoice objects
        clarification_id: session.clarification_id used to route the response back

    Returns:
        list[list[dict]]  — ready to pass as reply_markup["inline_keyboard"]
    """
    rows = []
    for choice in candidates:
        cb_data = f"c2:{clarification_id}:{choice.candidate_id}"
        label = _caregiver_button_label(choice)
        rows.append([{"text": label, "callback_data": cb_data}])
    return rows
