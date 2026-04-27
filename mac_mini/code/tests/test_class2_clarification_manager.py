"""Tests for Class2ClarificationManager (MM-06)."""

import pytest

from class2_clarification_manager.manager import Class2ClarificationManager
from safe_deferral_handler.models import SessionStatus, TransitionTarget

AUDIT_ID = "test_audit_001"


@pytest.fixture(scope="module")
def manager():
    return Class2ClarificationManager()


# ------------------------------------------------------------------
# Session creation — trigger_id mapping
# ------------------------------------------------------------------

class TestSessionCreation:
    @pytest.mark.parametrize("trigger_id,expected_reason", [
        ("C201", "insufficient_context"),
        ("C202", "missing_policy_input"),
        ("C203", "unresolved_context_conflict"),
        ("C204", "sensor_staleness_detected"),
        ("C205", "actuation_ack_timeout"),
        ("C206", "insufficient_context"),
        ("C207", "timeout_or_no_response"),
        ("deferral_timeout", "timeout_or_no_response"),
    ])
    def test_trigger_id_mapped_to_unresolved_reason(self, manager, trigger_id, expected_reason):
        session = manager.start_session(trigger_id, AUDIT_ID)
        assert session.deferral_reason == expected_reason

    def test_unknown_trigger_id_falls_back_to_insufficient_context(self, manager):
        session = manager.start_session("C999", AUDIT_ID)
        assert session.deferral_reason == "insufficient_context"

    def test_candidate_count_within_policy_max(self, manager):
        for trigger_id in ("C202", "C203", "C204", "C206"):
            session = manager.start_session(trigger_id, AUDIT_ID)
            assert len(session.candidate_choices) <= 4

    def test_attempt_number_stored(self, manager):
        session = manager.start_session("C206", AUDIT_ID, attempt_number=2)
        assert session.attempt_number == 2

    def test_custom_clarification_id(self, manager):
        session = manager.start_session("C206", AUDIT_ID, clarification_id="c2-id-001")
        assert session.clarification_id == "c2-id-001"

    def test_audit_correlation_id_preserved(self, manager):
        session = manager.start_session("C206", "my-audit-abc")
        assert session.audit_correlation_id == "my-audit-abc"

    def test_custom_candidate_choices_override_defaults(self, manager):
        custom = [{"candidate_id": "MY_C1", "prompt": "Test", "candidate_transition_target": "CLASS_1",
                   "action_hint": "light_on", "target_hint": "bedroom_light"}]
        session = manager.start_session("C206", AUDIT_ID, candidate_choices=custom)
        assert len(session.candidate_choices) == 1
        assert session.candidate_choices[0].candidate_id == "MY_C1"


# ------------------------------------------------------------------
# Default candidate shape
# ------------------------------------------------------------------

class TestDefaultCandidates:
    def test_insufficient_context_has_class0_option(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        targets = {c.candidate_transition_target for c in session.candidate_choices}
        assert "CLASS_0" in targets

    def test_insufficient_context_has_class1_option(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        targets = {c.candidate_transition_target for c in session.candidate_choices}
        assert "CLASS_1" in targets

    def test_sensor_staleness_no_class1_option(self, manager):
        """Stale sensors should not offer a direct low-risk action path."""
        session = manager.start_session("C204", AUDIT_ID)
        targets = {c.candidate_transition_target for c in session.candidate_choices}
        assert "CLASS_1" not in targets

    def test_timeout_reason_no_class0_option(self, manager):
        """Repeated timeout → don't offer emergency path by default."""
        session = manager.start_session("C207", AUDIT_ID)
        targets = {c.candidate_transition_target for c in session.candidate_choices}
        assert "CLASS_0" not in targets

    def test_all_choices_require_confirmation(self, manager):
        for trigger_id in ("C202", "C203", "C206"):
            session = manager.start_session(trigger_id, AUDIT_ID)
            for c in session.candidate_choices:
                assert c.to_schema_dict()["requires_confirmation"] is True


# ------------------------------------------------------------------
# Selection → CLASS_1
# ------------------------------------------------------------------

class TestSelectionClass1:
    def test_class1_candidate_gives_class1_transition(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c1 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_1")
        result = manager.submit_selection(session, c1.candidate_id, "bounded_input_node", trigger_id="C206")
        assert result.transition_target == TransitionTarget.CLASS_1
        assert result.should_notify_caregiver is False
        assert result.notification_payload is None

    def test_class1_with_target_hint_is_ready(self, manager):
        custom = [{"candidate_id": "C1", "prompt": "거실?", "candidate_transition_target": "CLASS_1",
                   "action_hint": "light_on", "target_hint": "living_room_light"}]
        session = manager.start_session("C206", AUDIT_ID, candidate_choices=custom)
        result = manager.submit_selection(session, "C1", "bounded_input_node", trigger_id="C206")
        assert result.is_class1_ready is True
        assert result.action_hint == "light_on"
        assert result.target_hint == "living_room_light"

    def test_session_status_selected(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c1 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_1")
        manager.submit_selection(session, c1.candidate_id, "bounded_input_node", trigger_id="C206")
        assert session.status == SessionStatus.SELECTED


# ------------------------------------------------------------------
# Selection → CLASS_0
# ------------------------------------------------------------------

class TestSelectionClass0:
    def test_emergency_candidate_gives_class0_transition(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c0 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_0")
        result = manager.submit_selection(session, c0.candidate_id, "bounded_input_node", trigger_id="C206")
        assert result.transition_target == TransitionTarget.CLASS_0
        assert result.should_notify_caregiver is False

    def test_class0_llm_boundary_in_record(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c0 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_0")
        result = manager.submit_selection(session, c0.candidate_id, "bounded_input_node", trigger_id="C206")
        lb = result.clarification_record["llm_boundary"]
        assert lb["emergency_trigger_authority_allowed"] is False


# ------------------------------------------------------------------
# Selection → caregiver / safe deferral
# ------------------------------------------------------------------

class TestSelectionEscalation:
    def test_caregiver_candidate_escalates(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        cg = next(c for c in session.candidate_choices if c.candidate_transition_target == "CAREGIVER_CONFIRMATION")
        result = manager.submit_selection(session, cg.candidate_id, "bounded_input_node",
                                          trigger_id="C206", context_summary="거실 조명 요청")
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_notify_caregiver is True
        assert result.notification_payload is not None

    def test_cancel_candidate_escalates(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        cancel = next(c for c in session.candidate_choices if c.candidate_transition_target == "SAFE_DEFERRAL")
        result = manager.submit_selection(session, cancel.candidate_id, "bounded_input_node",
                                          trigger_id="C206")
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_notify_caregiver is True

    def test_unknown_candidate_id_treated_as_timeout(self, manager):
        """Unknown selection must never be treated as consent."""
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.submit_selection(session, "DOES_NOT_EXIST", "bounded_input_node", trigger_id="C206")
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_notify_caregiver is True


# ------------------------------------------------------------------
# Timeout / no-response
# ------------------------------------------------------------------

class TestTimeout:
    def test_timeout_escalates_to_caregiver(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C207")
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_notify_caregiver is True
        assert result.action_hint is None
        assert result.target_hint is None

    def test_timeout_never_assumes_intent(self, manager):
        session = manager.start_session("C202", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C207")
        assert result.transition_target != TransitionTarget.CLASS_1
        assert result.transition_target != TransitionTarget.CLASS_0

    def test_timeout_session_status_timed_out(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        manager.handle_timeout(session)
        assert session.status == SessionStatus.TIMED_OUT

    def test_timeout_preserves_candidate_choices_in_record(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        n = len(session.candidate_choices)
        result = manager.handle_timeout(session)
        assert len(result.clarification_record["candidate_choices"]) == n


# ------------------------------------------------------------------
# Retry logic
# ------------------------------------------------------------------

class TestRetry:
    def test_can_retry_within_max_attempts(self, manager):
        session = manager.start_session("C206", AUDIT_ID, attempt_number=1)
        assert manager.can_retry(session) is True

    def test_cannot_retry_at_max_attempts(self, manager):
        session = manager.start_session("C206", AUDIT_ID, attempt_number=2)
        assert manager.can_retry(session) is False

    def test_cannot_retry_beyond_max_attempts(self, manager):
        session = manager.start_session("C206", AUDIT_ID, attempt_number=3)
        assert manager.can_retry(session) is False

    def test_retry_session_increments_attempt(self, manager):
        session1 = manager.start_session("C206", AUDIT_ID, attempt_number=1)
        # Caller creates a new session with incremented attempt
        session2 = manager.start_session("C206", AUDIT_ID, attempt_number=session1.attempt_number + 1)
        assert session2.attempt_number == 2


# ------------------------------------------------------------------
# Notification payload
# ------------------------------------------------------------------

class TestNotificationPayload:
    def test_notification_has_required_fields(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C206", context_summary="온도 22도, 거실 조명 꺼짐")
        n = result.notification_payload
        assert n is not None
        for field in ("event_summary", "context_summary", "unresolved_reason", "manual_confirmation_path"):
            assert field in n, f"missing field: {field}"

    def test_notification_context_summary_passed_through(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session, context_summary="거실 조명 꺼짐, 점유 감지됨")
        assert "거실" in result.notification_payload["context_summary"]

    def test_notification_exception_trigger_id_c201_to_c207(self, manager):
        for trigger_id in ("C201", "C202", "C203", "C204", "C205", "C206", "C207"):
            session = manager.start_session(trigger_id, AUDIT_ID)
            result = manager.handle_timeout(session, trigger_id=trigger_id)
            assert result.notification_payload["exception_trigger_id"] == trigger_id

    def test_notification_not_emitted_on_class1_selection(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c1 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_1")
        result = manager.submit_selection(session, c1.candidate_id, "bounded_input_node", trigger_id="C206")
        assert result.notification_payload is None


# ------------------------------------------------------------------
# Clarification record schema shape
# ------------------------------------------------------------------

class TestClarificationRecord:
    def test_record_required_fields_present(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session)
        record = result.clarification_record
        for field in ("clarification_id", "unresolved_reason", "candidate_choices",
                      "transition_target", "llm_boundary"):
            assert field in record

    def test_record_source_layer_is_manager(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session)
        assert result.clarification_record["source_layer"] == "class2_clarification_manager"

    def test_record_llm_boundary_correct(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session)
        lb = result.clarification_record["llm_boundary"]
        assert lb["candidate_generation_only"] is True
        assert lb["final_decision_allowed"] is False
        assert lb["actuation_authority_allowed"] is False
        assert lb["emergency_trigger_authority_allowed"] is False
