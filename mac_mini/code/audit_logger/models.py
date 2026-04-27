"""Data models for the Audit Logging Service (MM-09)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EventGroup(str, Enum):
    ROUTING = "routing"
    VALIDATION = "validation"
    LLM = "llm"
    DEFERRAL = "deferral"
    CLARIFICATION = "clarification"
    DISPATCH = "dispatch"
    ACK = "ack"
    ESCALATION = "escalation"
    CAREGIVER = "caregiver"
    TIMEOUT = "timeout"
    FAILURE = "failure"
    SYSTEM = "system"


@dataclass
class AuditEvent:
    """A single immutable audit record.

    Authority note: audit records are evidence and traceability artifacts.
    They do not grant operational authority, override policy, or constitute
    validator or caregiver approval.
    """

    event_group: EventGroup
    event_type: str                          # e.g. "policy_router_decision"
    audit_correlation_id: str
    summary: str
    payload: dict = field(default_factory=dict)
    timestamp_ms: Optional[int] = None      # set by AuditLogger if None
    audit_event_id: Optional[str] = None    # set by AuditLogger on insert
    authority_note: str = (
        "Audit records are evidence and traceability artifacts, not policy truth."
    )

    def to_dict(self) -> dict:
        return {
            "audit_event_id": self.audit_event_id,
            "audit_correlation_id": self.audit_correlation_id,
            "event_group": self.event_group.value,
            "event_type": self.event_type,
            "summary": self.summary,
            "payload": self.payload,
            "timestamp_ms": self.timestamp_ms,
            "authority_note": self.authority_note,
        }


@dataclass
class AuditSummary:
    """Lightweight read result for a set of audit events."""

    audit_correlation_id: str
    event_count: int
    event_groups: list[str]
    earliest_ms: Optional[int]
    latest_ms: Optional[int]
