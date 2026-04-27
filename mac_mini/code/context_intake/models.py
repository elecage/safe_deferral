"""Data models for the Operational MQTT Context Intake (MM-01)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IntakeStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"       # schema-invalid, cannot be forwarded
    QUARANTINED = "quarantined" # structurally parseable but fails semantic checks


@dataclass
class IntakeResult:
    """Result of processing one incoming context payload.

    Authority note:
      - ACCEPTED payloads are forwarded to the Policy Router.
      - REJECTED / QUARANTINED payloads must never be treated as Class 1
        executable requests or emergency evidence.
      - doorbell_detected is visitor presence context only — not doorlock auth.
    """

    status: IntakeStatus
    source_node_id: str
    audit_correlation_id: str
    ingest_timestamp_ms: int
    pure_context_payload: Optional[dict]   # None when rejected/quarantined
    routing_metadata: Optional[dict]       # None when rejected/quarantined
    rejection_reason: Optional[str]        # set for REJECTED / QUARANTINED
    raw_payload: dict = field(default_factory=dict)

    @property
    def is_accepted(self) -> bool:
        return self.status == IntakeStatus.ACCEPTED

    def to_audit_dict(self) -> dict:
        return {
            "status": self.status.value,
            "source_node_id": self.source_node_id,
            "audit_correlation_id": self.audit_correlation_id,
            "ingest_timestamp_ms": self.ingest_timestamp_ms,
            "rejection_reason": self.rejection_reason,
            "authority_note": (
                "Intake records are evidence artifacts. "
                "Rejected or quarantined payloads must not be treated as "
                "executable requests or emergency evidence."
            ),
        }
