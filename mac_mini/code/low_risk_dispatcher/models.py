"""Data models for the Low-Risk Dispatcher and ACK Handler (MM-07)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DispatchStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    ACK_SUCCESS = "ack_success"
    ACK_FAILURE = "ack_failure"
    ACK_TIMEOUT = "ack_timeout"


class AckStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


@dataclass
class DispatchRecord:
    """Audit record produced after dispatch + ACK resolution."""

    command_id: str
    action: str
    target_device: str
    requires_ack: bool
    audit_correlation_id: str
    source_decision: str                   # "validator_output"
    dispatch_status: DispatchStatus
    published_at_ms: int
    ack_status: Optional[AckStatus]        # None until ACK received or timeout
    ack_received_at_ms: Optional[int]
    observed_state: Optional[str]          # from ACK payload
    ack_timeout_ms: int
    llm_boundary: dict = field(default_factory=lambda: {
        "candidate_generation_only": True,
        "final_decision_allowed": False,
        "actuation_authority_allowed": False,
        "emergency_trigger_authority_allowed": False,
    })

    def to_dict(self) -> dict:
        return {
            "command_id": self.command_id,
            "action": self.action,
            "target_device": self.target_device,
            "requires_ack": self.requires_ack,
            "audit_correlation_id": self.audit_correlation_id,
            "source_decision": self.source_decision,
            "dispatch_status": self.dispatch_status.value,
            "published_at_ms": self.published_at_ms,
            "ack_status": self.ack_status.value if self.ack_status else None,
            "ack_received_at_ms": self.ack_received_at_ms,
            "observed_state": self.observed_state,
            "ack_timeout_ms": self.ack_timeout_ms,
            "llm_boundary": self.llm_boundary,
        }


@dataclass
class DispatchResult:
    """Return value of LowRiskDispatcher.dispatch()."""

    command_id: str
    dispatch_status: DispatchStatus
    action: str
    target_device: str
    audit_correlation_id: str
    command_payload: dict          # published to safe_deferral/actuation/command
    dispatch_record: DispatchRecord

    @property
    def is_published(self) -> bool:
        return self.dispatch_status == DispatchStatus.PUBLISHED

    @property
    def needs_ack(self) -> bool:
        return self.dispatch_record.requires_ack


@dataclass
class AckResult:
    """Return value of AckHandler.handle_ack() or handle_ack_timeout()."""

    command_id: str
    ack_status: AckStatus
    audit_correlation_id: str
    observed_state: Optional[str]
    resolved_at_ms: int
    dispatch_record: DispatchRecord        # mutated in-place with final status
