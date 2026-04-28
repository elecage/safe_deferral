"""Data models for the Caregiver Escalation Backend (MM-08)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EscalationStatus(str, Enum):
    PENDING = "pending"           # notification sent, awaiting response
    SEND_FAILED = "send_failed"   # live delivery failed after retries; no caregiver notified
    ACKNOWLEDGED = "acknowledged" # caregiver acknowledged, no action taken
    APPROVED = "approved"         # caregiver approved the described action
    DENIED = "denied"             # caregiver denied / intervened
    EXPIRED = "expired"           # no response within timeout


class CaregiverDecision(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class NotificationRecord:
    """Evidence record for an outbound caregiver notification."""

    confirmation_id: str
    audit_correlation_id: str
    notification_channel: str          # "telegram"
    notification_payload: dict         # class2_notification_payload_schema.json payload
    sent_at_ms: int
    telegram_message_id: Optional[int] # None in dry-run / test mode
    escalation_status: EscalationStatus = EscalationStatus.PENDING

    def to_dict(self) -> dict:
        return {
            "confirmation_id": self.confirmation_id,
            "audit_correlation_id": self.audit_correlation_id,
            "notification_channel": self.notification_channel,
            "notification_payload": self.notification_payload,
            "sent_at_ms": self.sent_at_ms,
            "telegram_message_id": self.telegram_message_id,
            "escalation_status": self.escalation_status.value,
        }


@dataclass
class ConfirmationRecord:
    """Evidence record for a caregiver response.

    Authority boundary: this record is manual approval evidence.
    It is NOT Class 1 validator approval.  Sensitive actuation requires
    a separately governed manual path (see 02_safety_and_authority_boundaries.md).
    """

    confirmation_id: str
    audit_correlation_id: str
    decision: CaregiverDecision
    approved_by_role: str              # e.g. "caregiver"
    responded_at_ms: int
    authority_note: str = (
        "Caregiver confirmation is manual approval evidence. "
        "It is not autonomous Class 1 validator approval."
    )

    def to_dict(self) -> dict:
        return {
            "confirmation_id": self.confirmation_id,
            "audit_correlation_id": self.audit_correlation_id,
            "decision": self.decision.value,
            "approved_by_role": self.approved_by_role,
            "responded_at_ms": self.responded_at_ms,
            "authority_note": self.authority_note,
        }


@dataclass
class EscalationResult:
    """Returned by CaregiverEscalationBackend.send_notification()."""

    confirmation_id: str
    escalation_status: EscalationStatus
    audit_correlation_id: str
    notification_record: NotificationRecord
    confirmation_record: Optional[ConfirmationRecord] = None   # set after response

    @property
    def is_pending(self) -> bool:
        return self.escalation_status == EscalationStatus.PENDING

    @property
    def is_send_failed(self) -> bool:
        return self.escalation_status == EscalationStatus.SEND_FAILED

    @property
    def is_resolved(self) -> bool:
        return self.escalation_status not in (
            EscalationStatus.PENDING, EscalationStatus.SEND_FAILED, EscalationStatus.EXPIRED
        )
