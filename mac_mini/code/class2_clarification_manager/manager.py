"""Class 2 Clarification Manager (MM-06).

Entry points:
  1. Policy Router → CLASS_2  (trigger_id C201-C207)
  2. Validator     → rejected_escalation (exception_trigger_id C201-C207)
  3. Safe Deferral Handler → should_escalate_to_class2=True (timeout)

Responsibilities:
  - Map trigger_id to unresolved_reason.
  - Build bounded candidate choices (default or LLM-supplied).
  - Manage attempt counter; escalate to caregiver on max exceeded.
  - Accept user/caregiver selection or handle timeout.
  - Return Class2Result with transition target and audit records.

Authority rule (02_safety_and_authority_boundaries.md):
  - Candidate selection is confirmation evidence only.
  - CLASS_1 transition still requires Deterministic Validator approval; the
    runtime re-validates the confirmed bounded candidate before any dispatch
    (the Policy Router is not re-invoked).
  - CLASS_0 transition requires emergency confirmation or deterministic evidence.
  - Silence/timeout must never be treated as consent.
  - This manager does not dispatch actuators or approve caregiver confirmation.
"""

import logging
import threading
import time
import uuid
from typing import Optional, Protocol

from class2_clarification_manager.models import Class2Result
from class2_clarification_manager.refinement_templates import (
    get_refinement_template,
)
from class2_clarification_manager.scan_ordering import (
    apply_scan_ordering,
    ScanOrderingResult,
)

log = logging.getLogger(__name__)
from safe_deferral_handler.models import (
    ClarificationChoice,
    ClarificationSession,
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

# Canonical Class 2 trigger IDs accepted by class2_notification_payload_schema's
# exception_trigger_id enum. Anything else (e.g. "deferral_timeout",
# "EMERGENCY_BUTTON") must be omitted from the payload entirely — leaving the
# field as None fails schema validation because the schema declares type=string.
_CANONICAL_C2_TRIGGER_IDS: frozenset[str] = frozenset(
    ("C201", "C202", "C203", "C204", "C205", "C206", "C207", "C208")
)

# Canonical Class 2 trigger ID → unresolved_reason
_TRIGGER_TO_REASON: dict[str, str] = {
    "C201": "insufficient_context",
    "C202": "missing_policy_input",
    "C203": "unresolved_context_conflict",
    "C204": "sensor_staleness_detected",
    "C205": "actuation_ack_timeout",
    "C206": "insufficient_context",
    "C207": "timeout_or_no_response",
    "C208": "caregiver_required_sensitive_path",
    # internal label used when MM-05 escalates
    "deferral_timeout": "timeout_or_no_response",
}

# Event summary strings for notification payload
_TRIGGER_SUMMARY: dict[str, str] = {
    "C201": "안전 유예 타임아웃으로 Class 2 진입",
    "C202": "필수 정책 입력 누락으로 Class 2 진입",
    "C203": "컨텍스트 충돌 미해결로 Class 2 진입",
    "C204": "센서 데이터 신선도 위반으로 Class 2 진입",
    "C205": "액추에이터 ACK 타임아웃으로 Class 2 진입",
    "C206": "의도 해석 불충분으로 Class 2 진입",
    "C207": "사용자 선택 타임아웃 또는 무응답으로 Class 2 진입",
    "C208": "방문자 감지 — 도어락 민감 경로로 Class 2 진입",
    "deferral_timeout": "안전 유예 핸들러 타임아웃으로 Class 2 진입",
}

# Lighting candidates that should be rendered with state-aware prompts
# (doc 12 step 2-B). Maps candidate_id → (target_device, korean_room_label).
# Anything in this map is overridden by _state_aware_lighting_candidate so
# the user hears '거실 조명을 켜드릴까요?' / '꺼드릴까요?' depending on
# the device's current state in pure_context_payload.device_states.
_LIGHTING_CANDIDATE_TARGETS: dict[str, tuple] = {
    "C1_LIGHTING_ASSISTANCE": ("living_room_light", "거실"),
    "OPT_LIVING_ROOM": ("living_room_light", "거실"),
    "OPT_BEDROOM": ("bedroom_light", "침실"),
}

# Reasons whose default set is built around assuming a lighting action.
# For these, C4_CANCEL_OR_WAIT's prompt is replaced with the more honest
# '다른 동작이 필요하신가요?' so the user has an explicit safety net for
# 'system assumed the wrong action'. The candidate_id and transition
# target are unchanged (still SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION) —
# escalation behaviour identical to the old 'cancel and wait' path.
_LIGHTING_REASONS: set = {
    "insufficient_context",
    "missing_policy_input",
    "unresolved_context_conflict",
}


def _state_aware_lighting_candidate(item: dict, device_states: dict) -> dict:
    """Override a lighting candidate's prompt + action_hint based on the
    device's current state. Off → '켜드릴까요?' + light_on; On → '꺼드릴까요?'
    + light_off. Returns a new dict (does not mutate the input)."""
    target_info = _LIGHTING_CANDIDATE_TARGETS.get(item["candidate_id"])
    if target_info is None:
        return item
    device, room_label = target_info
    state = str((device_states or {}).get(device, "off")).lower()
    if state == "on":
        verb_phrase, action = "꺼드릴까요?", "light_off"
    else:
        verb_phrase, action = "켜드릴까요?", "light_on"
    return {
        **item,
        "prompt": f"{room_label} 조명을 {verb_phrase}",
        "action_hint": action,
        "target_hint": device,
    }


def _build_default_candidates(reason: str,
                              pure_context_payload: Optional[dict] = None) -> list:
    """Apply state-aware overrides on top of the static _DEFAULT_CANDIDATES
    table for the given reason (doc 12 step 2-B).

    - Lighting candidates listed in _LIGHTING_CANDIDATE_TARGETS get prompts
      and action_hints rewritten to reflect the device's current state.
    - For lighting reasons, the C4_CANCEL_OR_WAIT candidate's prompt is
      replaced with '다른 동작이 필요하신가요?' so the user has an explicit
      'system assumed wrong action' safety net (transition unchanged —
      still escalates via SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION).
    - Non-lighting reasons (sensor_staleness_detected, actuation_ack_timeout,
      timeout_or_no_response, caregiver_required_sensitive_path) pass
      through untouched."""
    raw = _DEFAULT_CANDIDATES.get(reason, [])
    device_states = (
        (pure_context_payload or {}).get("device_states")
        if pure_context_payload else None
    )
    is_lighting_reason = reason in _LIGHTING_REASONS
    out = []
    for item in raw:
        if item.get("candidate_id") in _LIGHTING_CANDIDATE_TARGETS:
            out.append(_state_aware_lighting_candidate(item, device_states or {}))
        elif is_lighting_reason and item.get("candidate_id") == "C4_CANCEL_OR_WAIT":
            out.append({**item, "prompt": "다른 동작이 필요하신가요?"})
        else:
            out.append(item)
    return out


# Default bounded candidate sets per unresolved_reason
_DEFAULT_CANDIDATES: dict[str, list[dict]] = {
    "insufficient_context": [
        {
            "candidate_id": "C1_LIGHTING_ASSISTANCE",
            "prompt": "조명 도움이 필요하신가요?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": "light_on",
            # Default to the canonical low-risk catalog living-room target so
            # is_class1_ready=True and the validator/dispatcher path can run.
            # Specific living-room vs bedroom disambiguation is handled by the
            # OPT_LIVING_ROOM/OPT_BEDROOM candidates in unresolved_context_conflict.
            "target_hint": "living_room_light",
        },
        {
            "candidate_id": "C3_EMERGENCY_HELP",
            "prompt": "긴급상황인가요?",
            "candidate_transition_target": "CLASS_0",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C2_CAREGIVER_HELP",
            "prompt": "보호자에게 연락할까요?",
            "candidate_transition_target": "CAREGIVER_CONFIRMATION",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C4_CANCEL_OR_WAIT",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
    "missing_policy_input": [
        {
            "candidate_id": "C1_LIGHTING_ASSISTANCE",
            "prompt": "조명 도움이 필요하신가요?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": "light_on",
            "target_hint": "living_room_light",
        },
        {
            "candidate_id": "C3_EMERGENCY_HELP",
            "prompt": "긴급상황인가요?",
            "candidate_transition_target": "CLASS_0",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C2_CAREGIVER_HELP",
            "prompt": "보호자에게 연락할까요?",
            "candidate_transition_target": "CAREGIVER_CONFIRMATION",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C4_CANCEL_OR_WAIT",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
    "unresolved_context_conflict": [
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
            "candidate_id": "C2_CAREGIVER_HELP",
            "prompt": "보호자에게 연락할까요?",
            "candidate_transition_target": "CAREGIVER_CONFIRMATION",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C4_CANCEL_OR_WAIT",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
    "sensor_staleness_detected": [
        {
            "candidate_id": "C2_CAREGIVER_HELP",
            "prompt": "보호자에게 연락할까요?",
            "candidate_transition_target": "CAREGIVER_CONFIRMATION",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C4_CANCEL_OR_WAIT",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
    "actuation_ack_timeout": [
        {
            "candidate_id": "OPT_RETRY",
            "prompt": "다시 시도할까요?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C2_CAREGIVER_HELP",
            "prompt": "보호자에게 연락할까요?",
            "candidate_transition_target": "CAREGIVER_CONFIRMATION",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C4_CANCEL_OR_WAIT",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
    "timeout_or_no_response": [
        {
            "candidate_id": "C2_CAREGIVER_HELP",
            "prompt": "보호자에게 연락할까요?",
            "candidate_transition_target": "CAREGIVER_CONFIRMATION",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C4_CANCEL_OR_WAIT",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
    # C208: visitor/doorbell detected — doorlock-sensitive path.
    # Caregiver confirmation is the first option; lighting assistance is
    # intentionally excluded because doorlock is outside the Class 1 catalog.
    "caregiver_required_sensitive_path": [
        {
            "candidate_id": "C2_CAREGIVER_HELP",
            "prompt": "보호자에게 방문자 확인을 요청할까요?",
            "candidate_transition_target": "CAREGIVER_CONFIRMATION",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C3_EMERGENCY_HELP",
            "prompt": "긴급상황인가요?",
            "candidate_transition_target": "CLASS_0",
            "action_hint": None,
            "target_hint": None,
        },
        {
            "candidate_id": "C4_CANCEL_OR_WAIT",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": None,
            "target_hint": None,
        },
    ],
}


class Class2CandidateGenerator(Protocol):
    """Minimal interface a Class 2 candidate generator (e.g. LocalLlmAdapter)
    must implement so the manager can call it without importing the LLM
    adapter directly. Returns a Class2CandidateResult-like object with
    candidates list, candidate_source, and rejection_reason."""
    def generate_class2_candidates(
        self,
        pure_context_payload: dict,
        unresolved_reason: str,
        max_candidates: int,
        audit_correlation_id: str = "",
    ): ...


class Class2ClarificationManager:
    def __init__(
        self,
        asset_loader: Optional[AssetLoader] = None,
        llm_candidate_generator: Optional["Class2CandidateGenerator"] = None,
    ) -> None:
        loader = asset_loader or AssetLoader()
        policy = loader.load_policy_table()
        gc = policy["global_constraints"]
        self._timeout_ms: int = gc["class2_clarification_timeout_ms"]
        self._max_attempts: int = gc["class2_max_clarification_attempts"]
        self._max_candidates: int = gc["class2_max_candidate_options"]
        # Optional LLM-driven candidate generator
        # (09_llm_driven_class2_candidate_generation_plan.md Phase 2). When
        # present, start_session() asks it for contextual candidates first
        # and falls back to _DEFAULT_CANDIDATES on any failure.
        self._llm_generator = llm_candidate_generator
        # P0.1 of 10_llm_class2_integration_alignment_plan.md: cap how long
        # start_session is willing to wait on the LLM. Aligned with the
        # OllamaClient HTTP timeout (llm_request_timeout_ms) plus a small
        # slack for HTTP teardown. The LLM call runs on a daemon thread
        # that we join with this budget; if the budget elapses, we abandon
        # the in-flight request and use the static _DEFAULT_CANDIDATES
        # table. The MQTT message-handler thread is therefore blocked for
        # at most this budget, capping emergency-response latency.
        _llm_timeout_s = int(gc.get("llm_request_timeout_ms", 8000)) / 1000.0
        self._llm_call_budget_s: float = _llm_timeout_s + 0.5
        # Doc 11 Phase 6.0 — opt-in multi-turn refinement. When False
        # (default), submit_selection_or_refine is identical to
        # submit_selection. Setting True in policy unlocks the second
        # turn for candidates listed in refinement_templates.
        self._multi_turn_enabled: bool = bool(
            gc.get("class2_multi_turn_enabled", False)
        )
        self._refinement_turn_timeout_ms: int = int(
            gc.get("class2_refinement_turn_timeout_ms", self._timeout_ms)
        )
        # Doc 12 Phase 1 — opt-in scanning input mode. The default
        # 'direct_select' preserves the existing one-utterance/one-pick
        # interaction; 'scanning' presents one option at a time and accepts
        # yes/no per turn (AAC scanning pattern). Per-option budget is
        # exposed so scanning callers can drive their per-option timeout
        # consistently with the policy.
        self._input_mode_default: str = str(
            gc.get("class2_input_mode", "direct_select")
        )
        self._scan_per_option_timeout_ms: int = int(
            gc.get("class2_scan_per_option_timeout_ms", 8000)
        )
        self._scan_user_phase_extension: float = float(
            gc.get("class2_scan_user_phase_extension", 1.5)
        )
        # Doc 12 §14 Phase 1.5 — deterministic scanning ordering. Default
        # 'source_order' keeps candidate order as produced by the source
        # layer; 'deterministic' applies _scan_ordering_rules below.
        # Honored only when input_mode='scanning' (direct_select shows all
        # options at once so order is cosmetic).
        self._scan_ordering_mode_default: str = str(
            gc.get("class2_scan_ordering_mode", "source_order")
        )
        self._scan_ordering_rules: dict = (
            gc.get("class2_scan_ordering_rules") or {}
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_session(
        self,
        trigger_id: str,
        audit_correlation_id: str,
        candidate_choices: Optional[list] = None,
        attempt_number: int = 1,
        clarification_id: Optional[str] = None,
        presentation_channel: str = "tts",
        pure_context_payload: Optional[dict] = None,
        candidate_source_mode: Optional[str] = None,
        input_mode: Optional[str] = None,
        scan_ordering_mode: Optional[str] = None,
    ) -> ClarificationSession:
        """Initialise a Class 2 clarification session.

        trigger_id may be C201-C208 (from Policy Router / Validator) or
        'deferral_timeout' (from Safe Deferral Handler escalation).

        Candidate source priority:
          1. Explicit candidate_choices argument (caller-supplied override).
          2. When candidate_source_mode == "static_only" (Package A LLM-vs-static
             comparison; doc 10 §3.3 P2.3), the LLM call is skipped entirely
             and candidate_source is recorded as "static_only_forced" so the
             clarification record can distinguish "explicitly forced" from
             "LLM failed and we fell back".
          3. LLM-generated candidates when an llm_candidate_generator is
             registered AND pure_context_payload is provided AND
             candidate_source_mode != "static_only".
          4. Static _DEFAULT_CANDIDATES table for the resolved unresolved_reason.

        candidate_source is recorded on the session so the clarification
        record (built in submit_selection / handle_timeout) can audit which
        path produced the candidate set.
        """
        reason = _TRIGGER_TO_REASON.get(trigger_id, "insufficient_context")
        candidate_source = "default_fallback"
        choices_input = candidate_choices
        force_static = candidate_source_mode == "static_only"
        if force_static:
            candidate_source = "static_only_forced"
        if (
            choices_input is None
            and not force_static
            and self._llm_generator is not None
            and pure_context_payload is not None
        ):
            llm_result = self._call_llm_with_budget(
                pure_context_payload, reason, audit_correlation_id,
            )
            if (
                llm_result is not None
                and getattr(llm_result, "candidate_source", None) == "llm_generated"
                and getattr(llm_result, "candidates", None)
            ):
                choices_input = llm_result.candidates
                candidate_source = "llm_generated"
        choices = self._build_choices(reason, choices_input, pure_context_payload)
        # Doc 12 §14 Phase 1.5 — apply deterministic ordering if scanning
        # mode is active AND ordering policy is 'deterministic'. The
        # original source order is preserved when the policy keeps the
        # default 'source_order'. Direct-select sessions skip ranking
        # because their order is cosmetic (all options shown at once).
        effective_input_mode_for_ordering = (
            input_mode or self._input_mode_default
        )
        effective_scan_ordering_mode = (
            scan_ordering_mode or self._scan_ordering_mode_default
        )
        scan_ordering_result: Optional[ScanOrderingResult] = None
        if (
            effective_input_mode_for_ordering == "scanning"
            and effective_scan_ordering_mode == "deterministic"
        ):
            scan_ordering_result = apply_scan_ordering(
                candidates=choices,
                pure_context_payload=pure_context_payload,
                trigger_id=trigger_id,
                rules=self._scan_ordering_rules,
            )
            choices = scan_ordering_result.ordered_candidates
        session = ClarificationSession(
            clarification_id=clarification_id or str(uuid.uuid4()),
            audit_correlation_id=audit_correlation_id,
            deferral_reason=reason,
            candidate_choices=choices,
            presentation_channel=presentation_channel,
            timeout_ms=self._timeout_ms,
            attempt_number=attempt_number,
        )
        # Stash candidate_source on the session so the clarification record
        # built in submit_selection / handle_timeout can include it.
        # ClarificationSession is a dataclass without this field; use a
        # dynamic attribute to avoid changing the shared model.
        session.candidate_source = candidate_source  # type: ignore[attr-defined]
        # Stash pure_context_payload too so submit_selection_or_refine can
        # produce state-aware refinement candidates (doc 12 step 2-B +
        # PR #102 multi-turn).
        session.pure_context_payload = pure_context_payload  # type: ignore[attr-defined]
        # Stash ordering audit so _build_record can surface
        # scan_ordering_applied. Only set when ranking actually ran
        # (input_mode='scanning' AND scan_ordering_mode='deterministic').
        if scan_ordering_result is not None:
            session.scan_ordering_audit = scan_ordering_result.to_audit_dict()  # type: ignore[attr-defined]
        # Doc 12 Phase 1 — record interaction mode and (when scanning)
        # initialise per-option pointer + history. Default mode comes from
        # policy; explicit input_mode argument overrides it (used by trial
        # runner / scenario fixtures). Direct-select sessions carry input_mode
        # too so the audit record can attribute interaction mode uniformly.
        effective_input_mode = input_mode or self._input_mode_default
        session.input_mode = effective_input_mode  # type: ignore[attr-defined]
        if effective_input_mode == "scanning":
            session.current_option_index = 0  # type: ignore[attr-defined]
            session.scan_history = []  # type: ignore[attr-defined]
            # Per-option timeout overrides the session's user-phase timeout
            # for scanning callers. The original timeout_ms is preserved so
            # legacy direct-select callers aren't surprised; scanning callers
            # should consult session.scan_per_option_timeout_ms instead.
            session.scan_per_option_timeout_ms = self._scan_per_option_timeout_ms  # type: ignore[attr-defined]
        return session

    def submit_selection(
        self,
        session: ClarificationSession,
        selected_candidate_id: str,
        selection_source: str,
        selection_timestamp_ms: Optional[int] = None,
        trigger_id: str = "C206",
        context_summary: str = "",
    ) -> Class2Result:
        """Record a confirmed selection and return the Class 2 result."""
        ts = selection_timestamp_ms or int(time.time() * 1000)

        chosen = next(
            (c for c in session.candidate_choices if c.candidate_id == selected_candidate_id),
            None,
        )
        if chosen is None:
            return self._timeout_result(session, ts, trigger_id, context_summary)

        session.status = SessionStatus.SELECTED
        target = self._resolve_transition(chosen.candidate_transition_target)
        notify = target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION

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

        notification = (
            self._build_notification(session, trigger_id, context_summary)
            if notify else None
        )

        return Class2Result(
            transition_target=target,
            should_notify_caregiver=notify,
            action_hint=chosen.action_hint,
            target_hint=chosen.target_hint,
            clarification_record=record,
            notification_payload=notification,
        )

    def submit_selection_or_refine(
        self,
        session: ClarificationSession,
        selected_candidate_id: str,
        selection_source: str,
        selection_timestamp_ms: Optional[int] = None,
        trigger_id: str = "C206",
        context_summary: str = "",
    ):
        """Multi-turn opt-in entry point (doc 11 Phase 6.0).

        When `class2_multi_turn_enabled` is False, this is identical to
        `submit_selection` and returns a terminal `Class2Result`.

        When True AND the chosen candidate has a refinement template AND
        this session has no parent (i.e. is itself the initial turn),
        returns a NEW `ClarificationSession` representing the refinement
        turn. The caller (Mac mini main loop) is responsible for
        announcing the refinement question and collecting the next user
        selection. Resolving the refinement session via `submit_selection`
        produces a terminal `Class2Result` whose `clarification_record`
        carries a `refinement_history` entry.

        Otherwise (no template, or this IS already a refinement turn,
        or feature flag off), delegates to `submit_selection`.
        """
        if not self._multi_turn_enabled:
            return self.submit_selection(
                session, selected_candidate_id, selection_source,
                selection_timestamp_ms, trigger_id, context_summary,
            )

        # Refinement turns themselves never refine further (max one turn).
        if getattr(session, "is_refinement_turn", False):
            return self.submit_selection(
                session, selected_candidate_id, selection_source,
                selection_timestamp_ms, trigger_id, context_summary,
            )

        chosen = next(
            (c for c in session.candidate_choices if c.candidate_id == selected_candidate_id),
            None,
        )
        if chosen is None:
            # Unknown candidate id → terminal timeout, identical to submit_selection.
            return self.submit_selection(
                session, selected_candidate_id, selection_source,
                selection_timestamp_ms, trigger_id, context_summary,
            )

        template = get_refinement_template(
            chosen.candidate_id,
            pure_context_payload=getattr(session, "pure_context_payload", None),
        )
        if template is None:
            # No refinement defined for this candidate → terminal as before.
            return self.submit_selection(
                session, selected_candidate_id, selection_source,
                selection_timestamp_ms, trigger_id, context_summary,
            )

        ts = selection_timestamp_ms or int(time.time() * 1000)
        # Build a refinement session. It re-uses ClarificationSession with
        # a refinement-specific timeout and dynamic attributes carrying
        # the parent context for audit.
        refinement = ClarificationSession(
            clarification_id=str(uuid.uuid4()),
            audit_correlation_id=session.audit_correlation_id,
            deferral_reason=session.deferral_reason,
            candidate_choices=template.refinement_choices,
            presentation_channel=session.presentation_channel,
            timeout_ms=self._refinement_turn_timeout_ms,
            attempt_number=session.attempt_number,
        )
        refinement.is_refinement_turn = True  # type: ignore[attr-defined]
        refinement.parent_clarification_id = session.clarification_id  # type: ignore[attr-defined]
        refinement.parent_candidate_id = chosen.candidate_id  # type: ignore[attr-defined]
        refinement.refinement_question = template.refinement_question  # type: ignore[attr-defined]
        refinement.parent_selection_source = selection_source  # type: ignore[attr-defined]
        refinement.parent_selection_timestamp_ms = ts  # type: ignore[attr-defined]
        # Preserve the parent's candidate_source so the terminal record
        # accurately reflects how the parent's candidates were generated.
        refinement.candidate_source = getattr(  # type: ignore[attr-defined]
            session, "candidate_source", "default_fallback"
        )
        return refinement

    def handle_timeout(
        self,
        session: ClarificationSession,
        timestamp_ms: Optional[int] = None,
        trigger_id: str = "C207",
        context_summary: str = "",
    ) -> Class2Result:
        """Handle a timeout or no-response.

        Silence must never be treated as consent.
        Always escalates to SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION.
        """
        ts = timestamp_ms or int(time.time() * 1000)
        return self._timeout_result(session, ts, trigger_id, context_summary)

    # ------------------------------------------------------------------
    # Scanning (doc 12 Phase 1)
    # ------------------------------------------------------------------

    def submit_scan_response(
        self,
        session: ClarificationSession,
        option_index: int,
        response: str,
        input_source: str,
        elapsed_ms: int = 0,
        timestamp_ms: Optional[int] = None,
        trigger_id: str = "C206",
        context_summary: str = "",
    ):
        """Resolve one scanning turn (doc 12 §6).

        Returns:
          - Class2Result (terminal) if response='yes' (accept current option),
            or if response='no'/'silence' on the FINAL option (escalate to
            caregiver — silence ≠ consent invariant).
          - The same session (advanced) if response='no'/'silence' on a
            non-final option. current_option_index is incremented and
            scan_history records the turn.

        Stale or out-of-order responses (option_index != current_option_index)
        are appended to scan_history with response='dropped' and the session
        is returned unchanged. This prevents a slow button-press race from
        accidentally accepting a previous option.
        """
        if getattr(session, "input_mode", "direct_select") != "scanning":
            raise ValueError(
                "submit_scan_response called on non-scanning session "
                f"(input_mode={getattr(session, 'input_mode', None)!r})"
            )
        if response not in ("yes", "no", "silence"):
            raise ValueError(f"invalid scan response: {response!r}")

        ts = timestamp_ms or int(time.time() * 1000)
        current_index = getattr(session, "current_option_index", 0)
        history = getattr(session, "scan_history", [])

        # Stale-input drop. Record it for audit but do not advance.
        if option_index != current_index:
            history.append({
                "option_index": int(option_index),
                "candidate_id": (
                    session.candidate_choices[option_index].candidate_id
                    if 0 <= option_index < len(session.candidate_choices)
                    else "<out_of_range>"
                ),
                "response": "dropped",
                "elapsed_ms": int(elapsed_ms),
                "input_source": input_source,
            })
            session.scan_history = history  # type: ignore[attr-defined]
            return session

        candidate = session.candidate_choices[current_index]
        history.append({
            "option_index": int(current_index),
            "candidate_id": candidate.candidate_id,
            "response": response,
            "elapsed_ms": int(elapsed_ms),
            "input_source": input_source,
        })
        session.scan_history = history  # type: ignore[attr-defined]

        if response == "yes":
            # Terminal acceptance of the current option. Reuse the existing
            # submit_selection terminal pipeline so transition resolution,
            # caregiver-notification logic, and audit-record assembly stay
            # in one place. The scan_history we just appended is picked up
            # automatically by _build_record because it reads from the
            # session attribute.
            return self.submit_selection(
                session,
                selected_candidate_id=candidate.candidate_id,
                selection_source=input_source,
                selection_timestamp_ms=ts,
                trigger_id=trigger_id,
                context_summary=context_summary,
            )

        # response in ('no', 'silence') — advance or escalate.
        if current_index + 1 < len(session.candidate_choices):
            session.current_option_index = current_index + 1  # type: ignore[attr-defined]
            return session

        # Final option rejected (or silenced). Silence ≠ consent — escalate
        # to caregiver via the existing timeout pipeline so the audit record
        # carries scan_history alongside the standard escalation fields.
        return self._timeout_result(session, ts, trigger_id, context_summary)

    def handle_scan_silence(
        self,
        session: ClarificationSession,
        elapsed_ms: int = 0,
        timestamp_ms: Optional[int] = None,
        trigger_id: str = "C206",
        context_summary: str = "",
    ):
        """Per-option timeout convenience (doc 12 §6).

        Equivalent to submit_scan_response(option_index=current, response='silence',
        input_source='timeout'). Returned object follows the same union
        contract as submit_scan_response.
        """
        if getattr(session, "input_mode", "direct_select") != "scanning":
            raise ValueError(
                "handle_scan_silence called on non-scanning session "
                f"(input_mode={getattr(session, 'input_mode', None)!r})"
            )
        return self.submit_scan_response(
            session,
            option_index=getattr(session, "current_option_index", 0),
            response="silence",
            input_source="timeout",
            elapsed_ms=elapsed_ms,
            timestamp_ms=timestamp_ms,
            trigger_id=trigger_id,
            context_summary=context_summary,
        )

    def can_retry(self, session: ClarificationSession) -> bool:
        """True if another clarification attempt is allowed under policy."""
        return session.attempt_number < self._max_attempts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_llm_with_budget(
        self,
        pure_context_payload: dict,
        unresolved_reason: str,
        audit_correlation_id: str,
    ):
        """Run the LLM candidate generator on a daemon thread and join with
        ``self._llm_call_budget_s``. Returns the result if it arrived in
        time, ``None`` otherwise.

        Why a thread: ``self._llm_generator.generate_class2_candidates()``
        ultimately makes an HTTP POST to Ollama. Even with the OllamaClient
        request timeout policy-bound (P0.2), running it directly on the
        MQTT message-handler thread blocks every other inbound message —
        including a Class 0 emergency event — for the full LLM duration.
        Running it on a daemon thread and bounding the join lets us
        guarantee start_session returns within ``self._llm_call_budget_s``
        regardless of LLM behaviour. If the budget elapses we abandon the
        in-flight request (the daemon thread keeps running until Ollama
        responds or its own HTTP timeout fires) and fall back to
        _DEFAULT_CANDIDATES, preserving the safety invariant that the
        static table is always sufficient.
        """
        if self._llm_generator is None:
            return None

        result_holder: list = []

        def _runner() -> None:
            try:
                result_holder.append(self._llm_generator.generate_class2_candidates(
                    pure_context_payload=pure_context_payload,
                    unresolved_reason=unresolved_reason,
                    max_candidates=self._max_candidates,
                    audit_correlation_id=audit_correlation_id,
                ))
            except Exception as exc:  # noqa: BLE001 — silent fallback contract
                log.warning("Class 2 LLM call raised: %s — using static fallback", exc)

        worker = threading.Thread(
            target=_runner,
            daemon=True,
            name=f"class2-llm-{audit_correlation_id[:8]}" if audit_correlation_id else "class2-llm",
        )
        worker.start()
        worker.join(timeout=self._llm_call_budget_s)
        if worker.is_alive():
            log.warning(
                "Class 2 LLM call exceeded budget %.2fs (audit=%s) — abandoning, "
                "using static _DEFAULT_CANDIDATES",
                self._llm_call_budget_s, audit_correlation_id,
            )
            return None
        return result_holder[0] if result_holder else None

    def _build_choices(
        self,
        reason: str,
        override: Optional[list],
        pure_context_payload: Optional[dict] = None,
    ) -> list:
        # Default candidates flow through _build_default_candidates so
        # state-aware lighting prompts (doc 12 step 2-B) are applied.
        # An explicit override (caller-supplied list or LLM output) is
        # used as-is — the LLM is responsible for its own state awareness.
        raw = (
            override if override is not None
            else _build_default_candidates(reason, pure_context_payload)
        )
        raw = raw[: self._max_candidates]
        return [
            ClarificationChoice(
                candidate_id=item["candidate_id"],
                prompt=item["prompt"],
                candidate_transition_target=item["candidate_transition_target"],
                action_hint=item.get("action_hint"),
                target_hint=item.get("target_hint"),
            )
            for item in raw
        ]

    @staticmethod
    def _resolve_transition(candidate_transition_target: str) -> TransitionTarget:
        mapping = {
            "CLASS_1": TransitionTarget.CLASS_1,
            "CLASS_0": TransitionTarget.CLASS_0,
            "SAFE_DEFERRAL": TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION,
            "CAREGIVER_CONFIRMATION": TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION,
            "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION": TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION,
        }
        return mapping.get(
            candidate_transition_target,
            TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION,
        )

    def _timeout_result(
        self,
        session: ClarificationSession,
        ts: int,
        trigger_id: str,
        context_summary: str,
    ) -> Class2Result:
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
        notification = self._build_notification(session, trigger_id, context_summary)
        return Class2Result(
            transition_target=TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION,
            should_notify_caregiver=True,
            action_hint=None,
            target_hint=None,
            clarification_record=record,
            notification_payload=notification,
        )

    # Maps runtime selection_source values to the enum allowed by
    # clarification_interaction_schema.json selection_result.selection_source.
    _SELECTION_SOURCE_MAP: dict[str, str] = {
        "user_mqtt_button": "bounded_input_node",
        "user_mqtt_button_late": "bounded_input_node",
        "caregiver_telegram_inline_keyboard": "caregiver_confirmation",
    }

    def _build_record(
        self,
        session: ClarificationSession,
        selection_result: dict,
        transition_target: str,
        timeout_result: str,
    ) -> dict:
        # Normalise selection_source to the schema enum before storing.
        normalised_selection = dict(selection_result)
        raw_source = normalised_selection.get("selection_source", "none")
        normalised_selection["selection_source"] = self._SELECTION_SOURCE_MAP.get(
            raw_source, raw_source
        )
        # candidate_source is set by start_session(); default to fallback for
        # legacy callers that bypass it.
        candidate_source = getattr(session, "candidate_source", "default_fallback")
        record = {
            "clarification_id": session.clarification_id,
            "audit_correlation_id": session.audit_correlation_id,
            "source_layer": "class2_clarification_manager",
            "unresolved_reason": session.deferral_reason,
            "candidate_source": candidate_source,
            "candidate_choices": [c.to_schema_dict() for c in session.candidate_choices],
            "presentation_channel": session.presentation_channel,
            "selection_result": normalised_selection,
            "transition_target": transition_target,
            "timeout_result": timeout_result,
            "llm_boundary": _LLM_BOUNDARY_CONST,
            "timestamp_ms": int(time.time() * 1000),
        }
        # Doc 12 Phase 1 — surface scanning interaction mode and per-option
        # decision history when present. Direct-select sessions still record
        # input_mode='direct_select' for audit attribution; scanning sessions
        # additionally include scan_history (may be empty if the very first
        # option was accepted before any 'no'/'silence'/'dropped' was logged).
        input_mode = getattr(session, "input_mode", None)
        if input_mode is not None:
            record["input_mode"] = input_mode
        scan_history = getattr(session, "scan_history", None)
        if scan_history is not None:
            # Defensive copy so post-build mutation doesn't change the record.
            record["scan_history"] = [dict(entry) for entry in scan_history]
        # Doc 12 §14.5 — surface ordering audit when deterministic ranking ran.
        scan_ordering_audit = getattr(session, "scan_ordering_audit", None)
        if scan_ordering_audit is not None:
            # Defensive copy so post-build mutation doesn't change the record.
            record["scan_ordering_applied"] = {
                "rule_source": scan_ordering_audit["rule_source"],
                "matched_bucket": scan_ordering_audit["matched_bucket"],
                "applied_overrides": list(scan_ordering_audit["applied_overrides"]),
                "final_order": list(scan_ordering_audit["final_order"]),
            }
        # Doc 11 Phase 6.0 — when this session is a refinement turn, embed
        # one entry summarising the parent → refinement transition. The
        # selected_candidate_id field is the value the user picked (or
        # "TIMEOUT" when the turn timed out — selection_result already
        # carries that distinction via timeout_result).
        if getattr(session, "is_refinement_turn", False):
            record["refinement_history"] = [{
                "turn_index": 1,
                "parent_candidate_id": getattr(session, "parent_candidate_id", ""),
                "refinement_question": getattr(session, "refinement_question", ""),
                "selected_candidate_id": normalised_selection.get(
                    "selected_candidate_id", "TIMEOUT"
                ),
                "selection_source": normalised_selection.get("selection_source", ""),
                "selection_timestamp_ms": normalised_selection.get(
                    "selection_timestamp_ms", record["timestamp_ms"]
                ),
            }]
        return record

    def _build_notification(
        self,
        session: ClarificationSession,
        trigger_id: str,
        context_summary: str,
    ) -> dict:
        """Build a class2_notification_payload_schema.json-compliant dict.

        exception_trigger_id is included only when trigger_id is in the canonical
        enum; otherwise the field is omitted entirely so jsonschema validation
        does not reject the payload (the field is type=string in the schema).
        """
        event_summary = _TRIGGER_SUMMARY.get(trigger_id, "Class 2 clarification/escalation")
        payload = {
            "event_summary": event_summary,
            "context_summary": context_summary or "현재 환경 및 기기 상태 요약 없음",
            "unresolved_reason": session.deferral_reason,
            "manual_confirmation_path": (
                "보호자는 Telegram 또는 대시보드를 통해 상황을 검토하고 "
                "수동 확인, 거부, 또는 개입 경로를 선택할 수 있습니다."
            ),
            "audit_correlation_id": session.audit_correlation_id,
            "timestamp_ms": int(time.time() * 1000),
            "notification_channel": "telegram",
            "source_layer": "class2_clarification_manager",
        }
        if trigger_id in _CANONICAL_C2_TRIGGER_IDS:
            payload["exception_trigger_id"] = trigger_id
        return payload
