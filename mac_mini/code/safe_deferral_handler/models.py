import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SessionStatus(str, Enum):
    PENDING = "pending"
    SELECTED = "selected"
    TIMED_OUT = "timed_out"


class TransitionTarget(str, Enum):
    CLASS_0 = "CLASS_0"
    CLASS_1 = "CLASS_1"
    SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION = "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"


@dataclass
class ClarificationChoice:
    """A single bounded option presented to the user during safe deferral.

    candidate_transition_target tells downstream which routing path
    this choice leads to if confirmed.
    action_hint / target_hint carry the CLASS_1 action info so Policy
    Router re-entry can be constructed without re-running the LLM.
    """

    candidate_id: str
    prompt: str
    candidate_transition_target: str   # "CLASS_1" | "CLASS_0" | "SAFE_DEFERRAL" | …
    action_hint: Optional[str] = None  # "light_on" | "light_off"  (CLASS_1 only)
    target_hint: Optional[str] = None  # "living_room_light" | "bedroom_light" (CLASS_1 only)

    def to_schema_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "prompt": self.prompt,
            "candidate_transition_target": self.candidate_transition_target,
            "requires_confirmation": True,
        }


@dataclass
class ClarificationSession:
    """Mutable state of one safe-deferral clarification attempt."""

    clarification_id: str
    audit_correlation_id: str
    deferral_reason: str                      # from ValidatorResult
    candidate_choices: list                   # list[ClarificationChoice]
    presentation_channel: str
    timeout_ms: int
    created_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    attempt_number: int = 1
    status: SessionStatus = SessionStatus.PENDING


@dataclass
class DeferralHandlerResult:
    """Output of the Safe Deferral Handler after selection or timeout.

    Downstream wiring:
      CLASS_1                              → re-enter Policy Router with action_hint/target_hint
      CLASS_0                              → emergency handler
      SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION → Class 2 Clarification Manager (MM-06)
    """

    transition_target: TransitionTarget
    should_escalate_to_class2: bool           # True when timeout / no-response
    selected_candidate: Optional[ClarificationChoice]
    action_hint: Optional[str]                # set when CLASS_1
    target_hint: Optional[str]                # set when CLASS_1
    clarification_record: dict                # schema-compliant, for audit / MQTT

    @property
    def is_class1_ready(self) -> bool:
        return (
            self.transition_target == TransitionTarget.CLASS_1
            and self.action_hint is not None
            and self.target_hint is not None
        )
