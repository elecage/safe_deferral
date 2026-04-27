from dataclasses import dataclass
from typing import Optional

# Shared session / choice types live in safe_deferral_handler.models.
# MM-06 is a higher-level component and may depend on MM-05 session types.
from safe_deferral_handler.models import TransitionTarget


@dataclass
class Class2Result:
    """Output of the Class 2 Clarification Manager after selection or timeout.

    Downstream wiring:
      CLASS_1                              → re-enter Policy Router + Validator
      CLASS_0                              → emergency handler
      SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION → caregiver escalation backend (MM-08)
    """

    transition_target: TransitionTarget
    should_notify_caregiver: bool          # True when escalating to caregiver

    # Set when CLASS_1 transition is confirmed
    action_hint: Optional[str]
    target_hint: Optional[str]

    # schema-compliant dicts for audit / MQTT publish
    clarification_record: dict             # clarification_interaction_schema.json
    notification_payload: Optional[dict]   # class2_notification_payload_schema.json

    @property
    def is_class1_ready(self) -> bool:
        return (
            self.transition_target == TransitionTarget.CLASS_1
            and self.action_hint is not None
            and self.target_hint is not None
        )
