"""Refinement templates for the Class 2 multi-turn path (doc 11 Phase 6.0).

Each parent candidate_id can map to ONE refinement turn that follows the
user's initial selection. Refinement candidates respect the same authority
boundaries as _DEFAULT_CANDIDATES (no new low-risk actions, no escalation
to CLASS_0, no doorlock authority).

State-aware refinement (doc 12 step 2-B): when a refinement target maps to
a lighting device, the refinement candidate's prompt and action_hint are
derived from the device's current state in pure_context_payload.device_states
(off → 켜드릴까요? + light_on; on → 꺼드릴까요? + light_off). This keeps
the refinement consistent with the parent's state-aware prompt.

Today only one refinement template exists (C1_LIGHTING_ASSISTANCE → 거실 / 침실).
Phase 6.1 / 7+ may extend the table or replace static lookup with LLM-driven
refinement; until then, only candidates listed here can refine.
"""

from dataclasses import dataclass
from typing import Optional

from safe_deferral_handler.models import ClarificationChoice


@dataclass
class RefinementTemplate:
    """One refinement turn anchored to a parent candidate_id."""

    refinement_question: str
    refinement_choices: list  # list[ClarificationChoice]


def _state_aware_room_choice(
    candidate_id: str,
    target_device: str,
    room_label: str,
    device_states: Optional[dict],
) -> ClarificationChoice:
    """Build a CLASS_1 lighting choice whose action_hint matches the
    device's current state (off → light_on, on → light_off)."""
    state = str((device_states or {}).get(target_device, "off")).lower()
    if state == "on":
        verb_phrase, action, label_verb = "꺼드릴까요?", "light_off", "끄기"
    else:
        verb_phrase, action, label_verb = "켜드릴까요?", "light_on", "켜기"
    return ClarificationChoice(
        candidate_id=candidate_id,
        prompt=f"{room_label} 조명을 {verb_phrase}",
        candidate_transition_target="CLASS_1",
        action_hint=action,
        target_hint=target_device,
        selection_label=f"{room_label} 조명 {label_verb}",
    )


def get_refinement_template(
    parent_candidate_id: str,
    pure_context_payload: Optional[dict] = None,
):
    """Return the RefinementTemplate for a parent candidate, or None if the
    candidate has no refinement defined (production single-turn path).

    pure_context_payload is consulted (when provided) to render lighting
    refinement candidates with state-aware prompts and action_hints. When
    omitted, refinement candidates default to the off-state ('켜드릴까요?'
    + light_on) for backward compatibility with PR #102 callers."""
    if parent_candidate_id != "C1_LIGHTING_ASSISTANCE":
        return None
    device_states = (pure_context_payload or {}).get("device_states")
    return RefinementTemplate(
        # Question is intentionally generic ('어느 방') — each per-room
        # choice carries the explicit verb in its prompt so the user hears
        # the action they would actually trigger.
        refinement_question="어느 방의 조명을 도와드릴까요?",
        refinement_choices=[
            _state_aware_room_choice(
                "REFINE_LIVING_ROOM", "living_room_light", "거실", device_states,
            ),
            _state_aware_room_choice(
                "REFINE_BEDROOM", "bedroom_light", "침실", device_states,
            ),
        ],
    )


# Backward-compat exposure for tests that introspect the static surface
# without going through get_refinement_template. Kept as a named export
# even though refinement is now built dynamically — value reflects the
# off-state default (no device_states provided).
_REFINEMENT_TEMPLATES: dict[str, RefinementTemplate] = {
    "C1_LIGHTING_ASSISTANCE": get_refinement_template("C1_LIGHTING_ASSISTANCE"),
}
