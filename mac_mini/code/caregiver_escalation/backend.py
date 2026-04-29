"""Caregiver Escalation Backend (MM-08).

Responsibilities:
  1. Validate a class2_notification_payload against the canonical schema.
  2. Format and send the notification via Telegram (or injected sender).
  3. Optionally publish to safe_deferral/escalation/class2 (MQTT).
  4. Accept caregiver response and record a ConfirmationRecord.
  5. Optionally publish to safe_deferral/caregiver/confirmation (MQTT).

Authority boundary (02_safety_and_authority_boundaries.md §8):
  - Telegram is transport only — not a control channel.
  - CaregiverConfirmationRecord is manual approval evidence only.
  - It is NOT Class 1 validator approval or emergency authority.
  - Sensitive actuation (doorlock) requires a separately governed manual path.
"""

import time
import uuid
from typing import Optional, Protocol

import jsonschema

from caregiver_escalation.models import (
    CaregiverDecision,
    ConfirmationRecord,
    EscalationResult,
    EscalationStatus,
    NotificationRecord,
)
from caregiver_escalation.telegram_client import (
    TelegramSendError,
    TelegramSender,
    NoOpTelegramSender,
    format_notification_message,
)
from shared.asset_loader import AssetLoader

class MqttPublisher(Protocol):
    def publish(self, topic: str, payload: dict, qos: int = 1) -> None: ...


class _NoOpPublisher:
    def publish(self, topic: str, payload: dict, qos: int = 1) -> None:
        pass


class CaregiverEscalationBackend:
    """Send escalation notifications and record caregiver responses.

    Typical usage:
        result = backend.send_notification(notification_payload, chat_id)
        # … caregiver replies via Telegram callback or dashboard …
        backend.record_response(result, CaregiverDecision.APPROVED, "caregiver")
    """

    def __init__(
        self,
        telegram_sender: Optional[TelegramSender] = None,
        mqtt_publisher: Optional[MqttPublisher] = None,
        asset_loader: Optional[AssetLoader] = None,
        telegram_chat_id: str = "",
    ) -> None:
        loader = asset_loader or AssetLoader()
        self._schema = loader.load_schema("class2_notification_payload_schema.json")
        self._resolver = loader.make_schema_resolver()
        self._escalation_topic: str = loader.get_topic("safe_deferral/escalation/class2")
        self._confirmation_topic: str = loader.get_topic("safe_deferral/caregiver/confirmation")
        self._sender: TelegramSender = telegram_sender or NoOpTelegramSender()
        self._publisher: MqttPublisher = mqtt_publisher or _NoOpPublisher()
        self._chat_id = telegram_chat_id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_notification(
        self,
        notification_payload: dict,
        chat_id: Optional[str] = None,
        confirmation_id: Optional[str] = None,
        timestamp_ms: Optional[int] = None,
    ) -> EscalationResult:
        """Validate, format, and send a Class 2 escalation notification.

        Returns an EscalationResult with status=PENDING until a caregiver
        responds via record_response().

        Raises jsonschema.ValidationError if the payload violates the schema.
        """
        self._validate_payload(notification_payload)

        cid = confirmation_id or str(uuid.uuid4())
        ts = timestamp_ms or int(time.time() * 1000)
        audit_id = notification_payload.get("audit_correlation_id", "")
        target_chat = chat_id or self._chat_id

        message_text = format_notification_message(notification_payload)
        send_failed = False
        message_id: Optional[int] = None
        try:
            message_id = self._sender.send_message(target_chat, message_text)
        except TelegramSendError:
            send_failed = True

        escalation_status = (
            EscalationStatus.SEND_FAILED if send_failed else EscalationStatus.PENDING
        )

        record = NotificationRecord(
            confirmation_id=cid,
            audit_correlation_id=audit_id,
            notification_channel="telegram",
            notification_payload=notification_payload,
            sent_at_ms=ts,
            telegram_message_id=message_id,
            escalation_status=escalation_status,
        )

        self._publisher.publish(self._escalation_topic, notification_payload, qos=1)

        return EscalationResult(
            confirmation_id=cid,
            escalation_status=escalation_status,
            audit_correlation_id=audit_id,
            notification_record=record,
        )

    def record_response(
        self,
        escalation_result: EscalationResult,
        decision: CaregiverDecision,
        approved_by_role: str = "caregiver",
        timestamp_ms: Optional[int] = None,
    ) -> ConfirmationRecord:
        """Record a caregiver decision and update the EscalationResult in place.

        Publishes a confirmation record to safe_deferral/caregiver/confirmation.
        Returns the ConfirmationRecord for downstream audit use.
        """
        ts = timestamp_ms or int(time.time() * 1000)

        confirmation = ConfirmationRecord(
            confirmation_id=escalation_result.confirmation_id,
            audit_correlation_id=escalation_result.audit_correlation_id,
            decision=decision,
            approved_by_role=approved_by_role,
            responded_at_ms=ts,
        )

        escalation_result.confirmation_record = confirmation
        escalation_result.escalation_status = EscalationStatus(decision.value)
        escalation_result.notification_record.escalation_status = EscalationStatus(
            decision.value
        )

        self._publisher.publish(self._confirmation_topic, confirmation.to_dict(), qos=1)

        return confirmation

    def handle_expired(
        self,
        escalation_result: EscalationResult,
        timestamp_ms: Optional[int] = None,
    ) -> None:
        """Mark the escalation as expired (no response received in time)."""
        escalation_result.escalation_status = EscalationStatus.EXPIRED
        escalation_result.notification_record.escalation_status = EscalationStatus.EXPIRED

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_payload(self, payload: dict) -> None:
        validator = jsonschema.Draft7Validator(self._schema, resolver=self._resolver)
        errors = list(validator.iter_errors(payload))
        if errors:
            raise jsonschema.ValidationError(
                f"notification_payload schema validation failed: "
                f"{errors[0].message}"
            )
