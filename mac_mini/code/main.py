"""Mac mini edge hub entry point.

Wires all pipeline components together over MQTT:
  safe_deferral/context/input
      → ContextIntake → PolicyRouter
      → CLASS_0 : CaregiverEscalation (emergency)
      → CLASS_1 : LocalLlmAdapter → DeterministicValidator
                  → APPROVED          : LowRiskDispatcher
                  → SAFE_DEFERRAL     : SafeDeferralHandler → Class2Manager
                  → REJECTED          : Class2Manager → CaregiverEscalation
      → CLASS_2 : Class2Manager → CaregiverEscalation
  safe_deferral/actuation/ack
      → AckHandler

Environment variables (loaded from ~/smarthome_workspace/.env):
  MQTT_HOST          default: localhost
  MQTT_PORT          default: 1883
  MQTT_USER          default: (empty — anonymous)
  MQTT_PASS          default: (empty)
  TELEGRAM_TOKEN              required for live Telegram notifications
  TELEGRAM_CHAT_ID            required for live Telegram notifications
  CAREGIVER_RESPONSE_TIMEOUT_S  CLASS_2 inline-keyboard wait (default: 300)
  OLLAMA_URL         default: http://localhost:11434/api/generate
  OLLAMA_MODEL       default: llama3.2
  AUDIT_DB_PATH      default: ~/smarthome_workspace/audit.db
  TTS_ENABLED        "true" (default) | "false"
  TTS_VOICE          macOS voice name, default "Yuna" (Korean)
  TTS_RATE           words-per-minute for say -r (default: system default)
"""

import json
import logging
import os
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Optional dotenv — graceful if not installed
# ---------------------------------------------------------------------------
_ENV_FILE = Path.home() / "smarthome_workspace" / ".env"
try:
    from dotenv import load_dotenv
    if _ENV_FILE.exists():
        load_dotenv(_ENV_FILE)
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Pipeline imports
# ---------------------------------------------------------------------------
import paho.mqtt.client as mqtt

from audit_logger.logger import AuditLogger
from audit_logger.models import AuditEvent, EventGroup
from caregiver_escalation.backend import CaregiverEscalationBackend
from caregiver_escalation.telegram_client import (
    HttpTelegramSender,
    NoOpTelegramSender,
    TelegramPoller,
    build_inline_keyboard,
)
from class2_clarification_manager.manager import Class2ClarificationManager
from context_intake.intake import ContextIntake
from context_intake.models import IntakeStatus
from deterministic_validator.models import ValidationStatus
from deterministic_validator.validator import DeterministicValidator
from local_llm_adapter.adapter import LocalLlmAdapter
from local_llm_adapter.llm_client import OllamaClient, MockLlmClient
from low_risk_dispatcher.ack_handler import AckHandler
from low_risk_dispatcher.dispatcher import LowRiskDispatcher
from low_risk_dispatcher.models import AckStatus, DispatchRecord
from policy_router.models import RouteClass
from policy_router.router import PolicyRouter
from safe_deferral_handler.handler import SafeDeferralHandler
from shared.asset_loader import AssetLoader
from telemetry_adapter.adapter import TelemetryAdapter
from tts.speaker import (
    make_speaker,
    announce_dispatch,
    announce_emergency,
    announce_deferral,
    announce_class2,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("sd.main")

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "") or os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
CAREGIVER_RESPONSE_TIMEOUT_S = int(os.environ.get("CAREGIVER_RESPONSE_TIMEOUT_S", "300"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
AUDIT_DB_PATH = os.environ.get(
    "AUDIT_DB_PATH",
    str(Path.home() / "smarthome_workspace" / "audit.db"),
)


# ---------------------------------------------------------------------------
# MQTT publisher adapter
# ---------------------------------------------------------------------------
class _PahoPublisher:
    def __init__(self, client: mqtt.Client) -> None:
        self._client = client

    def publish(self, topic: str, payload: dict, qos: int = 1) -> None:
        self._client.publish(topic, json.dumps(payload), qos=qos)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
class Pipeline:
    def __init__(self, mqtt_publisher) -> None:
        log.info("Initialising pipeline components …")

        _loader = AssetLoader()
        self.topic_context_input: str = _loader.get_topic("safe_deferral/context/input")
        self.topic_ack: str = _loader.get_topic("safe_deferral/actuation/ack")

        self._audit = AuditLogger(db_path=AUDIT_DB_PATH)

        self._intake = ContextIntake(audit_logger=self._audit)
        self._router = PolicyRouter()

        llm_client = (
            OllamaClient(model=OLLAMA_MODEL, base_url=OLLAMA_URL)
            if OLLAMA_URL
            else MockLlmClient()
        )
        self._llm = LocalLlmAdapter(llm_client=llm_client)
        self._validator = DeterministicValidator()
        self._dispatcher = LowRiskDispatcher(mqtt_publisher=mqtt_publisher, asset_loader=_loader)
        self._ack_handler = AckHandler()
        self._deferral = SafeDeferralHandler()
        self._class2 = Class2ClarificationManager()

        self._telegram_sender = (
            HttpTelegramSender(TELEGRAM_TOKEN)
            if TELEGRAM_TOKEN
            else NoOpTelegramSender()
        )
        self._caregiver = CaregiverEscalationBackend(
            telegram_sender=self._telegram_sender,
            mqtt_publisher=mqtt_publisher,
            telegram_chat_id=TELEGRAM_CHAT_ID,
            asset_loader=_loader,
        )
        self._telemetry = TelemetryAdapter(mqtt_publisher=mqtt_publisher, asset_loader=_loader)
        self._tts = make_speaker()

        # Pending ACK records: command_id → DispatchRecord
        self._pending_acks: dict[str, DispatchRecord] = {}
        self._ack_lock = threading.Lock()

        # CLASS_2 two-phase response tracking
        # Phase 1 — user selection via MQTT button (class2_clarification_timeout_ms)
        # clarification_id → {"session", "event", "trigger_id", "audit_id", "selection"}
        self._pending_user_class2: dict[str, dict] = {}
        self._user_class2_lock = threading.Lock()
        # User-phase timeout from policy (class2_clarification_timeout_ms / 1000)
        self._class2_user_timeout_s: float = self._class2._timeout_ms / 1000.0

        # Phase 2 — caregiver inline-keyboard response (CAREGIVER_RESPONSE_TIMEOUT_S)
        # clarification_id → threading.Event (set when caregiver presses a button)
        self._pending_class2: dict[str, threading.Event] = {}
        # clarification_id → selected candidate_id
        self._class2_selections: dict[str, str] = {}
        self._class2_lock = threading.Lock()

        # Telegram long-poll for caregiver inline-keyboard responses
        if TELEGRAM_TOKEN:
            self._poller = TelegramPoller(
                bot_token=TELEGRAM_TOKEN,
                handler=self.handle_telegram_callback,
            )
            self._poller.start()
        else:
            self._poller = None

        threading.Thread(
            target=self._sweep_ack_timeouts,
            daemon=True,
            name="ack-timeout-sweep",
        ).start()

        log.info("Pipeline ready.")

    # ------------------------------------------------------------------
    # Context input path
    # ------------------------------------------------------------------
    def handle_context(self, raw: dict) -> None:
        # If a CLASS_2 user-wait phase is active, try to treat this MQTT
        # message as the user's selection before running the normal pipeline.
        if self._try_handle_as_user_selection(raw):
            return

        self._telemetry.reset()
        # 1. Intake
        intake_result = self._intake.process(raw)
        if intake_result.status != IntakeStatus.ACCEPTED:
            log.warning("Intake %s: %s", intake_result.status.value, intake_result.rejection_reason)
            return

        # 2. Route — override ingest_timestamp_ms with locally observed time so
        # the staleness check cannot be spoofed via the payload field.
        payload_to_route = {
            **intake_result.raw_payload,
            "routing_metadata": {
                **intake_result.raw_payload["routing_metadata"],
                "ingest_timestamp_ms": intake_result.ingest_timestamp_ms,
            },
        }
        route_result = self._router.route(payload_to_route)
        self._telemetry.update_route(route_result)
        log.info("Route: %s (trigger=%s)", route_result.route_class.value, route_result.trigger_id)

        if route_result.route_class == RouteClass.CLASS_0:
            self._handle_emergency(route_result)
        elif route_result.route_class == RouteClass.CLASS_1:
            self._handle_class1(route_result)
        else:
            self._handle_class2(route_result.trigger_id or "C206", route_result)

        self._telemetry.publish()

    # ------------------------------------------------------------------
    # CLASS_0 — emergency
    # ------------------------------------------------------------------
    def _handle_emergency(self, route_result) -> None:
        log.warning("CLASS_0 emergency: %s", route_result.trigger_id)
        announce_emergency(self._tts, route_result.trigger_id or "")
        notification = _build_notification(
            event_summary=f"긴급 상황 감지: {route_result.trigger_id}",
            context_summary="CLASS_0 emergency trigger — immediate caregiver notification.",
            unresolved_reason="emergency_event",
            audit_id=route_result.audit_correlation_id,
        )
        esc_result = self._caregiver.send_notification(notification)
        self._telemetry.update_escalation(esc_result)

    # ------------------------------------------------------------------
    # CLASS_1 — LLM → Validator → Dispatcher
    # ------------------------------------------------------------------
    def _handle_class1(self, route_result) -> None:
        ctx = route_result.pure_context_payload
        audit_id = route_result.audit_correlation_id

        # LLM candidate
        llm_result = self._llm.generate_candidate(ctx, audit_correlation_id=audit_id)
        log.info("LLM candidate: action=%s target=%s fallback=%s",
                 llm_result.proposed_action, llm_result.target_device, llm_result.is_fallback)

        candidate: dict = {
            "proposed_action": llm_result.proposed_action,
            "target_device":   llm_result.target_device,
        }
        rationale = llm_result.candidate.get("rationale_summary", "")
        if rationale:
            candidate["rationale_summary"] = rationale
        if llm_result.is_safe_deferral:
            candidate["deferral_reason"] = (
                llm_result.candidate.get("deferral_reason") or "insufficient_context"
            )

        # Validate
        val_result = self._validator.validate(candidate, audit_correlation_id=audit_id)
        self._telemetry.update_validation(val_result)
        log.info("Validation: %s (target=%s)", val_result.validation_status.value,
                 val_result.routing_target.value)

        if val_result.validation_status == ValidationStatus.APPROVED:
            dispatch_result = self._dispatcher.dispatch(val_result)
            with self._ack_lock:
                self._pending_acks[dispatch_result.dispatch_record.command_id] = (
                    dispatch_result.dispatch_record
                )
            self._telemetry.update_ack(dispatch_result.dispatch_record)
            announce_dispatch(
                self._tts,
                dispatch_result.dispatch_record.action,
                dispatch_result.dispatch_record.target_device,
            )
            log.info("Dispatched command_id=%s", dispatch_result.dispatch_record.command_id)

        elif val_result.validation_status == ValidationStatus.SAFE_DEFERRAL:
            self._handle_deferral(val_result, route_result)

        else:  # REJECTED_ESCALATION
            self._handle_class2(
                val_result.exception_trigger_id or "C203", route_result
            )

    # ------------------------------------------------------------------
    # Safe deferral (Class 1 → Class 2 escalation path)
    # ------------------------------------------------------------------
    def _handle_deferral(self, val_result, route_result) -> None:
        log.info("Safe deferral: %s", val_result.deferral_reason)
        announce_deferral(self._tts, val_result.deferral_reason or "")
        self._handle_class2("C207", route_result)

    # ------------------------------------------------------------------
    # CLASS_2 — clarification manager → user wait → caregiver escalation
    # ------------------------------------------------------------------
    def _handle_class2(self, trigger_id: str, route_result) -> None:
        """Start a CLASS_2 clarification session (two-phase wait).

        Phase 1 (user, %.0fs): TTS announces candidate choices.  If an MQTT
        button press arrives within class2_clarification_timeout_ms the user's
        selection is processed and the caregiver is NOT involved.

        Phase 2 (caregiver, %ds): only reached when the user does not respond.
        A Telegram inline keyboard is sent to the caregiver.  If the caregiver
        responds the selection is processed; otherwise a plain escalation
        notification is sent.

        Both phases run in a daemon background thread so the pipeline worker
        returns immediately and telemetry is published promptly.
        """ % (self._class2_user_timeout_s, CAREGIVER_RESPONSE_TIMEOUT_S)
        log.info("CLASS_2: trigger=%s", trigger_id)
        session = self._class2.start_session(
            trigger_id=trigger_id,
            audit_correlation_id=route_result.audit_correlation_id,
        )

        # Step 1: announce candidate choices to the USER via TTS
        announce_class2(self._tts, session.candidate_choices)

        # Step 2: publish telemetry immediately (pipeline worker must not block)
        self._telemetry.escalate_to_class2()
        class2_result = self._class2.handle_timeout(
            session=session, trigger_id=trigger_id
        )
        self._telemetry.update_class2(class2_result)

        # Step 3: spawn two-phase background waiter and return
        threading.Thread(
            target=self._await_user_then_caregiver,
            args=(session, trigger_id, route_result.audit_correlation_id),
            daemon=True,
            name=f"class2-waiter-{session.clarification_id[:8]}",
        ).start()
        log.info(
            "CLASS_2 announced — phase-1 user wait started "
            "(user_timeout=%.0fs clarification_id=%s)",
            self._class2_user_timeout_s, session.clarification_id,
        )

    # ------------------------------------------------------------------
    # Background two-phase waiter: user (15s) → caregiver (300s)
    # ------------------------------------------------------------------
    def _await_user_then_caregiver(
        self,
        session,
        trigger_id: str,
        audit_correlation_id: str,
    ) -> None:
        """Two-phase CLASS_2 response wait.

        Phase 1 — user (class2_clarification_timeout_ms):
          Register the session so handle_context() can intercept the next
          button press as a user selection.  If the user selects within the
          timeout, process the selection and return — no caregiver involved.

        Phase 2 — caregiver (CAREGIVER_RESPONSE_TIMEOUT_S):
          User did not respond.  Send a Telegram inline keyboard to the
          caregiver and wait.  Process caregiver selection or send a final
          escalation notification on timeout.
        """
        # ---- Phase 1: user response ----
        user_event = threading.Event()
        entry: dict = {
            "session": session,
            "event": user_event,
            "trigger_id": trigger_id,
            "audit_id": audit_correlation_id,
            "selection": None,
        }
        with self._user_class2_lock:
            self._pending_user_class2[session.clarification_id] = entry

        log.info(
            "CLASS_2 phase-1: waiting %.0fs for user button press (clarification_id=%s)",
            self._class2_user_timeout_s, session.clarification_id,
        )
        user_event.wait(timeout=self._class2_user_timeout_s)

        with self._user_class2_lock:
            self._pending_user_class2.pop(session.clarification_id, None)
            user_selected_id = entry.get("selection")

        if user_selected_id:
            log.info(
                "CLASS_2 phase-1: user selected %s (clarification_id=%s)",
                user_selected_id, session.clarification_id,
            )
            self._class2.submit_selection(
                session=session,
                selected_candidate_id=user_selected_id,
                selection_source="user_mqtt_button",
                trigger_id=trigger_id,
            )
            return  # User handled it — caregiver not involved

        # ---- Phase 2: caregiver Telegram ----
        log.info(
            "CLASS_2 phase-1 timeout — escalating to caregiver "
            "(clarification_id=%s)", session.clarification_id,
        )

        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID and session.candidate_choices:
            keyboard_rows = build_inline_keyboard(
                session.candidate_choices, session.clarification_id
            )
            notification_payload = self._class2._build_notification(
                session, trigger_id, context_summary=""
            )
            msg_text = _format_class2_keyboard_message(notification_payload, session)
            sent = self._telegram_sender.send_message_with_buttons(
                chat_id=TELEGRAM_CHAT_ID,
                text=msg_text,
                buttons=keyboard_rows,
            )
            if sent is not None:
                caregiver_event = threading.Event()
                with self._class2_lock:
                    self._pending_class2[session.clarification_id] = caregiver_event

                log.info(
                    "CLASS_2 phase-2: Telegram keyboard sent — waiting %ds for caregiver "
                    "(clarification_id=%s)",
                    CAREGIVER_RESPONSE_TIMEOUT_S, session.clarification_id,
                )
                caregiver_event.wait(timeout=CAREGIVER_RESPONSE_TIMEOUT_S)

                with self._class2_lock:
                    self._pending_class2.pop(session.clarification_id, None)
                    caregiver_selected_id = self._class2_selections.pop(
                        session.clarification_id, None
                    )

                if caregiver_selected_id:
                    log.info(
                        "CLASS_2 phase-2: caregiver selected %s (clarification_id=%s)",
                        caregiver_selected_id, session.clarification_id,
                    )
                    self._class2.submit_selection(
                        session=session,
                        selected_candidate_id=caregiver_selected_id,
                        selection_source="caregiver_telegram_inline_keyboard",
                        trigger_id=trigger_id,
                    )
                    return

                log.info(
                    "CLASS_2 phase-2: no caregiver response within %ds — "
                    "sending final escalation notification",
                    CAREGIVER_RESPONSE_TIMEOUT_S,
                )
            else:
                log.warning(
                    "CLASS_2 phase-2: Telegram keyboard delivery failed — "
                    "sending plain escalation notification"
                )

        # Final fallback: plain escalation notification
        timeout_result = self._class2.handle_timeout(
            session=session, trigger_id=trigger_id
        )
        if timeout_result.notification_payload:
            self._caregiver.send_notification(timeout_result.notification_payload)
        else:
            notification = _build_notification(
                event_summary=f"Class 2 무응답 타임아웃: {trigger_id}",
                context_summary="사용자 및 보호자 모두 응답하지 않아 에스컬레이션합니다.",
                unresolved_reason="timeout_or_no_response",
                audit_id=audit_correlation_id,
                exception_trigger_id=trigger_id,
            )
            self._caregiver.send_notification(notification)

    # ------------------------------------------------------------------
    # User button-press → CLASS_2 selection interceptor
    # ------------------------------------------------------------------
    def _try_handle_as_user_selection(self, raw: dict) -> bool:
        """If a CLASS_2 user-wait phase is active, try to map the incoming
        MQTT button event to a candidate selection and wake the waiter.

        Returns True if the message was consumed as a user selection (the
        normal pipeline should NOT process it further).
        Returns False otherwise (normal pipeline proceeds).

        Mapping rules (simple, deterministic):
          single_click → first candidate in the session's choice list
          triple_hit   → first CLASS_0-targeted candidate (emergency)
          other codes  → not recognised; pipeline runs normally
        """
        with self._user_class2_lock:
            if not self._pending_user_class2:
                return False
            # Use the most recently started user-phase session
            clarification_id = next(iter(self._pending_user_class2))
            entry = self._pending_user_class2.get(clarification_id)

        if entry is None:
            return False

        ctx = raw.get("pure_context_payload", {})
        trigger = ctx.get("trigger_event", {})
        event_type = trigger.get("event_type", "")
        event_code = trigger.get("event_code", "")

        if event_type != "button":
            return False  # Only button presses are user selections

        session = entry["session"]
        selected_id: Optional[str] = None

        if event_code == "single_click" and session.candidate_choices:
            # single_click → first candidate (typically C1_LIGHTING_ASSISTANCE)
            selected_id = session.candidate_choices[0].candidate_id
        elif event_code == "triple_hit":
            # Emergency confirmation → CLASS_0-targeted candidate
            selected_id = next(
                (c.candidate_id for c in session.candidate_choices
                 if c.candidate_transition_target == "CLASS_0"),
                None,
            )

        if selected_id is None:
            return False  # Not a recognised selection code; run normal pipeline

        with self._user_class2_lock:
            live_entry = self._pending_user_class2.get(clarification_id)
            if live_entry is None:
                return False  # Session expired between checks
            live_entry["selection"] = selected_id
            live_entry["event"].set()

        log.info(
            "CLASS_2 user selection intercepted: event_code=%s → candidate=%s "
            "(clarification_id=%s)",
            event_code, selected_id, clarification_id,
        )
        return True

    # ------------------------------------------------------------------
    # Telegram callback_query handler (called from TelegramPoller thread)
    # ------------------------------------------------------------------
    def handle_telegram_callback(self, callback_query: dict) -> None:
        """Process a caregiver inline-keyboard button press.

        Expected callback_data format: "c2:{clarification_id}:{candidate_id}"
        Answers the callback immediately to dismiss the button spinner, then
        signals the waiting _handle_class2 thread.
        """
        cbq_id = callback_query.get("id", "")
        data = callback_query.get("data", "")

        # Dismiss the loading spinner on the button
        if cbq_id:
            self._telegram_sender.answer_callback_query(cbq_id)

        if not data.startswith("c2:"):
            log.debug("Ignoring non-CLASS2 callback_query data: %r", data)
            return

        parts = data.split(":", 2)  # ["c2", clarification_id, candidate_id]
        if len(parts) != 3:
            log.warning("Malformed CLASS_2 callback_data: %r", data)
            return

        _, clarification_id, candidate_id = parts
        with self._class2_lock:
            event = self._pending_class2.get(clarification_id)
            if event is None:
                # Normal when caregiver presses a button from a previous/expired
                # session (e.g. old Telegram message after 300s timeout or
                # after a re-run).  Not an error — log at INFO level.
                log.info(
                    "callback_query ignored: clarification_id=%s already expired or from a previous session",
                    clarification_id,
                )
                return
            self._class2_selections[clarification_id] = candidate_id
            event.set()
        log.info(
            "Caregiver callback received: clarification_id=%s candidate=%s",
            clarification_id, candidate_id,
        )

    # ------------------------------------------------------------------
    # ACK path
    # ------------------------------------------------------------------
    def handle_ack(self, ack_payload: dict) -> None:
        command_id = ack_payload.get("command_id", "")
        with self._ack_lock:
            record = self._pending_acks.pop(command_id, None)
        if record is None:
            log.warning("ACK received for unknown command_id=%s", command_id)
            return
        ack_result = self._ack_handler.handle_ack(record, ack_payload)
        self._telemetry.publish_ack_only(record)
        log.info("ACK resolved: command_id=%s status=%s", command_id, ack_result.ack_status.value)
        if ack_result.ack_status == AckStatus.FAILURE:
            log.warning("ACK failure command_id=%s — escalating C205", command_id)
            self._escalate_c205(record.audit_correlation_id)

    # ------------------------------------------------------------------
    # ACK timeout sweep (C205 escalation path)
    # ------------------------------------------------------------------
    def _sweep_ack_timeouts(self) -> None:
        """Background thread: detect timed-out pending ACKs and escalate C205."""
        while True:
            time.sleep(1)
            now_ms = int(time.time() * 1000)
            timed_out = []
            with self._ack_lock:
                for command_id, record in list(self._pending_acks.items()):
                    if now_ms - record.published_at_ms > record.ack_timeout_ms:
                        timed_out.append(self._pending_acks.pop(command_id))
            for record in timed_out:
                log.warning("ACK timeout: command_id=%s audit=%s",
                            record.command_id, record.audit_correlation_id)
                self._ack_handler.handle_ack_timeout(record)
                self._telemetry.publish_ack_only(record)
                self._escalate_c205(record.audit_correlation_id)

    def _escalate_c205(self, audit_correlation_id: str) -> None:
        """Trigger C205 (actuation_ack_timeout) Class 2 escalation."""
        session = self._class2.start_session(
            trigger_id="C205",
            audit_correlation_id=audit_correlation_id,
        )
        class2_result = self._class2.handle_timeout(session=session, trigger_id="C205")
        if class2_result.notification_payload:
            esc_result = self._caregiver.send_notification(class2_result.notification_payload)
        else:
            notification = _build_notification(
                event_summary="Class 2 진입: C205 (actuation_ack_timeout)",
                context_summary="액추에이션 ACK 미수신",
                unresolved_reason="actuation_ack_timeout",
                audit_id=audit_correlation_id,
                exception_trigger_id="C205",
            )
            esc_result = self._caregiver.send_notification(notification)
        self._telemetry.publish_c205_snapshot(class2_result, esc_result, audit_correlation_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _format_class2_keyboard_message(notification_payload: dict, session) -> str:
    """Format the Telegram message that accompanies CLASS_2 inline keyboard buttons.

    Combines the standard escalation notification text with an instruction
    line so the caregiver knows to tap a button below.
    """
    import html as _html
    event   = _html.escape(notification_payload.get("event_summary", ""))
    reason  = _html.escape(notification_payload.get("unresolved_reason", ""))
    trigger = _html.escape(notification_payload.get("exception_trigger_id") or "—")
    audit_id = _html.escape(notification_payload.get("audit_correlation_id", ""))

    lines = [
        "🔔 <b>보호자 확인 요청</b>",
        "",
        f"<b>이벤트:</b> {event}",
        f"<b>미해결 이유:</b> {reason}",
        f"<b>트리거 ID:</b> {trigger}",
        "",
        "아래 버튼 중 하나를 선택해 주세요:",
        "",
        f"<i>감사 ID: {audit_id}</i>",
    ]
    return "\n".join(lines)


def _build_notification(
    event_summary: str,
    context_summary: str,
    unresolved_reason: str,
    audit_id: str,
    exception_trigger_id: Optional[str] = None,
) -> dict:
    payload: dict = {
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    log.info("Safe Deferral — Mac mini hub starting …")
    log.info("MQTT broker: %s:%s", MQTT_HOST, MQTT_PORT)
    log.info("Audit DB: %s", AUDIT_DB_PATH)
    log.info(
        "Telegram: %s (caregiver response timeout: %ds)",
        "configured" if TELEGRAM_TOKEN else "NoOp (TELEGRAM_BOT_TOKEN not set)",
        CAREGIVER_RESPONSE_TIMEOUT_S,
    )
    log.info("LLM: %s @ %s", OLLAMA_MODEL, OLLAMA_URL)
    log.info("TTS: enabled=%s voice=%s", os.environ.get("TTS_ENABLED", "true"), os.environ.get("TTS_VOICE", "Yuna"))

    # Create MQTT client; publish via a holder so Pipeline can reference it
    # before on_connect fires.
    # Use CallbackAPIVersion.VERSION2 to avoid Paho deprecation warning.
    try:
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="sd-mac-mini-hub",
            clean_session=True,
        )
    except AttributeError:
        # Paho < 2.0 installed — fall back to legacy constructor
        client = mqtt.Client(client_id="sd-mac-mini-hub", clean_session=True)
    publisher = _PahoPublisher(client)
    pipeline = Pipeline(mqtt_publisher=publisher)

    work_queue: queue.Queue = queue.Queue()

    def on_connect(c, userdata, flags, reason_code, properties=None):
        # VERSION2 passes a ReasonCode object; treat 0 / "Success" as connected.
        rc_value = getattr(reason_code, "value", reason_code)
        if rc_value == 0:
            log.info("MQTT connected to %s:%s", MQTT_HOST, MQTT_PORT)
            c.subscribe(pipeline.topic_context_input, qos=1)
            c.subscribe(pipeline.topic_ack, qos=1)
        else:
            log.error("MQTT connect failed rc=%s", reason_code)

    def on_disconnect(c, userdata, flags, reason_code=None, properties=None):
        log.warning("MQTT disconnected rc=%s — will auto-reconnect", reason_code)

    def on_message(c, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            work_queue.put((msg.topic, payload))
        except Exception as exc:
            log.error("MQTT parse error on %s: %s", msg.topic, exc)

    def worker():
        while True:
            topic, payload = work_queue.get()
            try:
                if topic == pipeline.topic_context_input:
                    pipeline.handle_context(payload)
                elif topic == pipeline.topic_ack:
                    pipeline.handle_ack(payload)
            except Exception as exc:
                log.exception("Pipeline error [%s]: %s", topic, exc)
            finally:
                work_queue.task_done()

    threading.Thread(target=worker, daemon=True, name="pipeline-worker").start()

    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS or None)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=2, max_delay=30)

    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    except Exception as exc:
        log.error("Could not connect to MQTT broker: %s", exc)
        sys.exit(1)

    log.info("Entering main loop …")
    client.loop_forever()


if __name__ == "__main__":
    main()
