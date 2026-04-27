"""Context-Integrity Safe Deferral Handler (MM-05).

Triggered when the Deterministic Validator returns validation_status=safe_deferral
(routing_target=context_integrity_safe_deferral_handler).

Responsibilities:
  1. Build a ClarificationSession with bounded candidate choices.
  2. Accept user selection OR handle timeout/no-response.
  3. Return a DeferralHandlerResult that tells the pipeline what to do next.

Authority rule (02_safety_and_authority_boundaries.md):
  - Silence/timeout must NEVER be treated as consent.
  - Candidate choices are guidance only; selection is confirmation evidence only.
  - CLASS_1 transition still requires Policy Router re-entry + Validator approval.
  - This handler does not dispatch actuators directly.
"""

import time
import uuid
from typing import Optional

from safe_deferral_handler.models import (
    ClarificationChoice,
    ClarificationSession,
    DeferralHandlerResult,
    SessionStatus,
    TransitionTarget,
)
from shared.asset_loader import AssetLoader

_LLM_BOUNDARY_CONST = {
    "candidate_generation_only": True,
    "final_decision_allowed": False,
    "actuation_authority_allowed": False,
    "emergency_trigger_authority_allowed": False,
}

# Default bounded candidate sets per deferral_reason.
# These are used when the LLM adapter has not supplied pre-built choices.
# Prompts are intentionally short and accessible (TTS-friendly).
_DEFAULT_CANDIDATES: dict[str, list[dict]] = {
    "ambiguous_target": [
        {
            "candidate_id": "OPT_LIVING_ROOM",
            "prompt": "거실 조명을 제어할까요?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": None,   # action unknown; caller sets after context lookup
            "target_hint": "living_room_light",
        },
        {
            "candidate_id": "OPT_BEDROOM",
            "prompt": "침실 조명을 제어할까요?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": None,
            "target_hint": "bedroom_light",
        },
        {
            "candidate_id": "OPT_CANCEL",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
    "unresolved_multi_candidate": [
        {
            "candidate_id": "OPT_LIVING_ROOM",
            "prompt": "거실 조명을 제어할까요?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": None,
            "target_hint": "living_room_light",
        },
        {
            "candidate_id": "OPT_BEDROOM",
            "prompt": "침실 조명을 제어할까요?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": None,
            "target_hint": "bedroom_light",
        },
        {
            "candidate_id": "OPT_CANCEL",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
    "insufficient_context": [
        {
            "candidate_id": "OPT_LIGHTING",
            "prompt": "조명을 켜드릴까요?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": "light_on",
            "target_hint": None,
        },
        {
            "candidate_id": "OPT_EMERGENCY",
            "prompt": "긴급상황인가요?",
            "candidate_transition_target": "CLASS_0",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "OPT_CANCEL",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
    "policy_restriction": [
        {
            "candidate_id": "OPT_CAREGIVER",
            "prompt": "보호자에게 연락할까요?",
            "candidate_transition_target": "CAREGIVER_CONFIRMATION",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "OPT_CANCEL",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
}


class SafeDeferralHandler:
    def __init__(self, asset_loader: Optional[AssetLoader] = None):
        loader = asset_loader or AssetLoader()
        policy = loader.load_policy_table()
        gc = policy["global_constraints"]
        self._timeout_ms: int = gc["class2_clarification_timeout_ms"]
        self._max_attempts: int = gc["class2_max_clarification_attempts"]
        self._max_candidates: int = gc["class2_max_candidate_options"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_clarification(
        self,
        deferral_reason: str,
        audit_correlation_id: str,
        candidate_choices: Optional[list] = None,
        presentation_channel: str = "tts",
        attempt_number: int = 1,
        clarification_id: Optional[str] = None,
    ) -> ClarificationSession:
        """Initialise a new clarification session.

        candidate_choices may be pre-supplied by the LLM adapter (MM-02).
        If None, falls back to default bounded choices for the deferral_reason.
        """
        choices = self._build_choices(deferral_reason, candidate_choices)
        return ClarificationSession(
            clarification_id=clarification_id or str(uuid.uuid4()),
            audit_correlation_id=audit_correlation_id,
            deferral_reason=deferral_reason,
            candidate_choices=choices,
            presentation_channel=presentation_channel,
            timeout_ms=self._timeout_ms,
            attempt_number=attempt_number,
        )

    def submit_selection(
        self,
        session: ClarificationSession,
        selected_candidate_id: str,
        selection_source: str,
        selection_timestamp_ms: Optional[int] = None,
    ) -> DeferralHandlerResult:
        """Record a confirmed user selection and return the transition result.

        The caller (MQTT intake / physical node adapter) is responsible for
        providing the actual selection from the bounded input node.
        """
        ts = selection_timestamp_ms or int(time.time() * 1000)

        chosen = next(
            (c for c in session.candidate_choices if c.candidate_id == selected_candidate_id),
            None,
        )
        if chosen is None:
            # Unknown candidate ID — treat as no-response to be safe
            return self._timeout_result(session, ts)

        session.status = SessionStatus.SELECTED
        target = self._resolve_transition(chosen.candidate_transition_target)

        record = self._build_record(
            session=session,
            selection_result={
                "selected_candidate_id": selected_candidate_id,
                "selection_source": selection_source,
                "confirmed": True,
                "selection_timestamp_ms": ts,
            },
            transition_target=target.value,
            timeout_result="not_applicable",
        )

        return DeferralHandlerResult(
            transition_target=target,
            should_escalate_to_class2=(target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION),
            selected_candidate=chosen,
            action_hint=chosen.action_hint,
            target_hint=chosen.target_hint,
            clarification_record=record,
        )

    def handle_timeout(
        self,
        session: ClarificationSession,
        timestamp_ms: Optional[int] = None,
    ) -> DeferralHandlerResult:
        """Handle a timeout or no-response event.

        Silence must never be treated as consent.
        Always escalates to SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION.
        """
        ts = timestamp_ms or int(time.time() * 1000)
        return self._timeout_result(session, ts)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_choices(
        self,
        deferral_reason: str,
        override: Optional[list],
    ) -> list:
        raw = override if override is not None else _DEFAULT_CANDIDATES.get(deferral_reason, [])

        # Enforce max_candidates limit from policy
        raw = raw[: self._max_candidates]

        choices = []
        for item in raw:
            choices.append(
                ClarificationChoice(
                    candidate_id=item["candidate_id"],
                    prompt=item["prompt"],
                    candidate_transition_target=item["candidate_transition_target"],
                    action_hint=item.get("action_hint"),
                    target_hint=item.get("target_hint"),
                )
            )
        return choices

    @staticmethod
    def _resolve_transition(candidate_transition_target: str) -> TransitionTarget:
        mapping = {
            "CLASS_1": TransitionTarget.CLASS_1,
            "CLASS_0": TransitionTarget.CLASS_0,
            "SAFE_DEFERRAL": TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION,
            "CAREGIVER_CONFIRMATION": TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION,
            "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION": TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION,
        }
        return mapping.get(candidate_transition_target, TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION)

    def _timeout_result(self, session: ClarificationSession, ts: int) -> DeferralHandlerResult:
        session.status = SessionStatus.TIMED_OUT
        record = self._build_record(
            session=session,
            selection_result={
                "selection_source": "timeout_or_no_response",
                "confirmed": False,
                "selection_timestamp_ms": ts,
            },
            transition_target=TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION.value,
            timeout_result="safe_deferral_or_caregiver_confirmation",
        )
        return DeferralHandlerResult(
            transition_target=TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION,
            should_escalate_to_class2=True,
            selected_candidate=None,
            action_hint=None,
            target_hint=None,
            clarification_record=record,
        )

    def _build_record(
        self,
        session: ClarificationSession,
        selection_result: dict,
        transition_target: str,
        timeout_result: str,
    ) -> dict:
        """Build a clarification_interaction_schema.json-compliant dict."""
        return {
            "clarification_id": session.clarification_id,
            "audit_correlation_id": session.audit_correlation_id,
            "source_layer": "context_integrity_safe_deferral_handler",
            "unresolved_reason": session.deferral_reason,
            "candidate_choices": [c.to_schema_dict() for c in session.candidate_choices],
            "presentation_channel": session.presentation_channel,
            "selection_result": selection_result,
            "transition_target": transition_target,
            "timeout_result": timeout_result,
            "llm_boundary": _LLM_BOUNDARY_CONST,
            "timestamp_ms": int(time.time() * 1000),
        }
