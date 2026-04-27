from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ValidationStatus(str, Enum):
    APPROVED = "approved"
    SAFE_DEFERRAL = "safe_deferral"
    REJECTED_ESCALATION = "rejected_escalation"


class RoutingTarget(str, Enum):
    ACTUATOR_DISPATCHER = "actuator_dispatcher"
    SAFE_DEFERRAL_HANDLER = "context_integrity_safe_deferral_handler"
    CLASS_2_ESCALATION = "class_2_escalation"


@dataclass
class ExecutablePayload:
    action: str          # "light_on" | "light_off"
    target_device: str   # "living_room_light" | "bedroom_light"
    requires_ack: bool

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "target_device": self.target_device,
            "requires_ack": self.requires_ack,
        }


@dataclass
class ValidatorResult:
    """Output of the Deterministic Validator.

    Downstream consumers:
      approved            → actuator_dispatcher (via ExecutablePayload)
      safe_deferral       → context_integrity_safe_deferral_handler
      rejected_escalation → class_2_escalation
    """

    validation_status: ValidationStatus
    routing_target: RoutingTarget
    exception_trigger_id: str       # "none" | "C201"–"C207"
    executable_payload: Optional[ExecutablePayload]   # approved only
    deferral_reason: Optional[str]                    # safe_deferral only
    audit_correlation_id: str

    def to_dict(self) -> dict:
        """Serialize to validator_output_schema.json-compliant dict."""
        d: dict = {
            "validation_status": self.validation_status.value,
            "routing_target": self.routing_target.value,
            "exception_trigger_id": self.exception_trigger_id,
        }
        if self.executable_payload is not None:
            d["executable_payload"] = self.executable_payload.to_dict()
        if self.deferral_reason is not None:
            d["deferral_reason"] = self.deferral_reason
        return d
