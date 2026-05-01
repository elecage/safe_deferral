"""Data models for the Read-Only Telemetry Adapter (MM-10)."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RouteTelemetry:
    """Route decision summary — experiment-safe subset."""
    route_class: str              # "CLASS_0" | "CLASS_1" | "CLASS_2"
    trigger_id: Optional[str]
    timestamp_ms: int


@dataclass
class ValidationTelemetry:
    """Validator output summary."""
    validation_status: str        # "approved" | "safe_deferral" | "rejected_escalation"
    exception_trigger_id: str
    timestamp_ms: int


@dataclass
class AckTelemetry:
    """ACK resolution summary."""
    dispatch_status: str          # "ack_success" | "ack_failure" | "ack_timeout"
    action: str
    target_device: str
    timestamp_ms: int
    command_id: str = ""
    audit_correlation_id: str = ""


@dataclass
class Class2Telemetry:
    """Class 2 clarification/escalation state summary."""
    transition_target: str        # "CLASS_1" | "CLASS_0" | "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"
    should_notify_caregiver: bool
    unresolved_reason: Optional[str]
    timestamp_ms: int
    post_transition_validator_status: Optional[str] = None  # "approved"|"safe_deferral"|"rejected_escalation"|"not_ready"
    post_transition_dispatched: Optional[bool] = None
    post_transition_escalation_status: Optional[str] = None  # CLASS_0 path: escalation_status value


@dataclass
class EscalationTelemetry:
    """Caregiver escalation status summary."""
    escalation_status: str        # "pending" | "approved" | "denied" | "acknowledged" | "expired"
    notification_channel: str
    timestamp_ms: int


@dataclass
class TelemetrySnapshot:
    """Aggregated read-only system telemetry snapshot.

    Authority note: this snapshot is experiment visibility data only.
    It must not be used to override policy, drive actuator commands,
    edit registry/schema/policy files, or spoof caregiver approval.
    """

    snapshot_id: str
    generated_at_ms: int
    route: Optional[RouteTelemetry] = None
    validation: Optional[ValidationTelemetry] = None
    ack: Optional[AckTelemetry] = None
    class2: Optional[Class2Telemetry] = None
    escalation: Optional[EscalationTelemetry] = None
    audit_correlation_id: str = ""
    audit_event_count: int = 0
    authority_note: str = (
        "Telemetry is read-only experiment visibility data. "
        "It must not be used as policy authority, actuator control, "
        "or caregiver approval."
    )

    def to_dict(self) -> dict:
        def _as(obj):
            if obj is None:
                return None
            return {k: v for k, v in obj.__dict__.items()}

        return {
            "snapshot_id": self.snapshot_id,
            "generated_at_ms": self.generated_at_ms,
            "audit_correlation_id": self.audit_correlation_id,
            "route": _as(self.route),
            "validation": _as(self.validation),
            "ack": _as(self.ack),
            "class2": _as(self.class2),
            "escalation": _as(self.escalation),
            "audit_event_count": self.audit_event_count,
            "authority_note": self.authority_note,
        }
