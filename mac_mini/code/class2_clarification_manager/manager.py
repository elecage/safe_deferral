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
  - CLASS_1 transition still requires Policy Router re-entry + Validator approval.
  - CLASS_0 transition requires emergency confirmation or deterministic evidence.
  - Silence/timeout must never be treated as consent.
  - This manager does not dispatch actuators or approve caregiver confirmation.
"""

import time
import uuid
from typing import Optional

from class2_clarification_manager.models import Class2Result
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

# Canonical Class 2 trigger ID → unresolved_reason
_TRIGGER_TO_REASON: dict[str, str] = {
    "C201": "insufficient_context",
    "C202": "missing_policy_input",
    "C203": "unresolved_context_conflict",
    "C204": "sensor_staleness_detected",
    "C205": "actuation_ack_timeout",
    "C206": "insufficient_context",
    "C207": "timeout_or_no_response",
    "C208": "visitor_context_sensitive_actuation_required",
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

# Default bounded candidate sets per unresolved_reason
_DEFAULT_CANDIDATES: dict[str, list[dict]] = {
    "insufficient_context": [
        {
            "candidate_id": "C1_LIGHTING_ASSISTANCE",
            "prompt": "조명 도움이 필요하신가요?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": "light_on",
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
    "visitor_context_sensitive_actuation_required": [
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


class Class2ClarificationManager:
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

    def start_session(
        self,
        trigger_id: str,
        audit_correlation_id: str,
        candidate_choices: Optional[list] = None,
        attempt_number: int = 1,
        clarification_id: Optional[str] = None,
        presentation_channel: str = "tts",
    ) -> ClarificationSession:
        """Initialise a Class 2 clarification session.

        trigger_id may be C201-C207 (from Policy Router / Validator) or
        'deferral_timeout' (from Safe Deferral Handler escalation).
        candidate_choices may be supplied by the LLM adapter (MM-02);
        if None, falls back to defaults for the resolved unresolved_reason.
        """
        reason = _TRIGGER_TO_REASON.get(trigger_id, "insufficient_context")
        choices = self._build_choices(reason, candidate_choices)
        return ClarificationSession(
            clarification_id=clarification_id or str(uuid.uuid4()),
            audit_correlation_id=audit_correlation_id,
            deferral_reason=reason,
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

    def can_retry(self, session: ClarificationSession) -> bool:
        """True if another clarification attempt is allowed under policy."""
        return session.attempt_number < self._max_attempts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_choices(
        self,
        reason: str,
        override: Optional[list],
    ) -> list:
        raw = override if override is not None else _DEFAULT_CANDIDATES.get(reason, [])
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
        return {
            "clarification_id": session.clarification_id,
            "audit_correlation_id": session.audit_correlation_id,
            "source_layer": "class2_clarification_manager",
            "unresolved_reason": session.deferral_reason,
            "candidate_choices": [c.to_schema_dict() for c in session.candidate_choices],
            "presentation_channel": session.presentation_channel,
            "selection_result": normalised_selection,
            "transition_target": transition_target,
            "timeout_result": timeout_result,
            "llm_boundary": _LLM_BOUNDARY_CONST,
            "timestamp_ms": int(time.time() * 1000),
        }

    def _build_notification(
        self,
        session: ClarificationSession,
        trigger_id: str,
        context_summary: str,
    ) -> dict:
        """Build a class2_notification_payload_schema.json-compliant dict."""
        event_summary = _TRIGGER_SUMMARY.get(trigger_id, "Class 2 clarification/escalation")
        return {
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
            "exception_trigger_id": trigger_id if trigger_id in (
                "C201", "C202", "C203", "C204", "C205", "C206", "C207"
            ) else None,
        }
