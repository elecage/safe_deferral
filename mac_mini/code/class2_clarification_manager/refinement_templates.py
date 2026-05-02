"""Static refinement templates for the Class 2 multi-turn path (doc 11 Phase 6.0).

Each entry maps a parent candidate_id to ONE refinement turn that may follow
the user's initial selection. Adding entries is a deliberate review step:
the candidate set must respect the same authority boundaries as
_DEFAULT_CANDIDATES (no new low-risk actions, no escalation to CLASS_0,
no doorlock authority).

The table is intentionally tiny in this round. Phase 6.1 / 7+ may extend it
or replace static lookup with LLM-driven refinement; until then, only
candidates listed here can refine.
"""

from dataclasses import dataclass

from safe_deferral_handler.models import ClarificationChoice


@dataclass
class RefinementTemplate:
    """One refinement turn anchored to a parent candidate_id."""

    refinement_question: str
    refinement_choices: list  # list[ClarificationChoice]


_REFINEMENT_TEMPLATES: dict[str, RefinementTemplate] = {
    # When the user picks the generic "lighting assistance" option, ask
    # which room. Both choices stay inside the canonical low-risk catalog
    # (light_on / living_room_light / bedroom_light).
    "C1_LIGHTING_ASSISTANCE": RefinementTemplate(
        refinement_question="어느 방의 조명을 켜드릴까요?",
        refinement_choices=[
            ClarificationChoice(
                candidate_id="REFINE_LIVING_ROOM",
                prompt="거실",
                candidate_transition_target="CLASS_1",
                action_hint="light_on",
                target_hint="living_room_light",
            ),
            ClarificationChoice(
                candidate_id="REFINE_BEDROOM",
                prompt="침실",
                candidate_transition_target="CLASS_1",
                action_hint="light_on",
                target_hint="bedroom_light",
            ),
        ],
    ),
}


def get_refinement_template(parent_candidate_id: str):
    """Return the RefinementTemplate for a parent candidate, or None if
    the candidate has no refinement defined (production single-turn path)."""
    return _REFINEMENT_TEMPLATES.get(parent_candidate_id)
