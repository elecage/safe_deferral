"""Tests for SafeDeferralHandler (MM-05)."""

import pytest

from safe_deferral_handler.handler import SafeDeferralHandler
from safe_deferral_handler.models import SessionStatus, TransitionTarget

AUDIT_ID = "test_audit_001"


@pytest.fixture(scope="module")
def handler():
    return SafeDeferralHandler()


# ------------------------------------------------------------------
# Session creation
# ------------------------------------------------------------------

class TestStartClarification:
    @pytest.mark.parametrize("reason", [
        "ambiguous_target",
        "unresolved_multi_candidate",
        "insufficient_context",
        "policy_restriction",
    ])
    def test_session_created_for_known_reason(self, handler, reason):
        session = handler.start_clarification(reason, AUDIT_ID)
        assert session.deferral_reason == reason
        assert session.status == SessionStatus.PENDING
        assert len(session.candidate_choices) >= 1

    def test_candidate_count_within_policy_max(self, handler):
        session = handler.start_clarification("insufficient_context", AUDIT_ID)
        assert len(session.candidate_choices) <= 4   # class2_max_candidate_options

    def test_custom_clarification_id(self, handler):
        session = handler.start_clarification(
            "ambiguous_target", AUDIT_ID, clarification_id="my-clar-id"
        )
        assert session.clarification_id == "my-clar-id"

    def test_audit_id_preserved(self, handler):
        session = handler.start_clarification("ambiguous_target", "my-audit-xyz")
        assert session.audit_correlation_id == "my-audit-xyz"

    def test_custom_candidate_choices_override_defaults(self, handler):
        custom = [
            {
                "candidate_id": "MY_OPT",
                "prompt": "Custom option?",
                "candidate_transition_target": "CLASS_1",
                "action_hint": "light_on",
                "target_hint": "living_room_light",
            }
        ]
        session = handler.start_clarification(
            "ambiguous_target", AUDIT_ID, candidate_choices=custom
        )
        assert len(session.candidate_choices) == 1
        assert session.candidate_choices[0].candidate_id == "MY_OPT"


# ------------------------------------------------------------------
# Default candidates sanity checks
# ------------------------------------------------------------------

class TestDefaultCandidates:
    def test_ambiguous_target_has_two_device_choices(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        device_ids = {c.candidate_id for c in session.candidate_choices}
        assert "OPT_LIVING_ROOM" in device_ids
        assert "OPT_BEDROOM" in device_ids

    def test_ambiguous_target_class1_choices_have_target_hint(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        class1_choices = [
            c for c in session.candidate_choices
            if c.candidate_transition_target == "CLASS_1"
        ]
        for c in class1_choices:
            assert c.target_hint is not None

    def test_insufficient_context_has_emergency_option(self, handler):
        session = handler.start_clarification("insufficient_context", AUDIT_ID)
        targets = {c.candidate_transition_target for c in session.candidate_choices}
        assert "CLASS_0" in targets

    def test_policy_restriction_no_direct_class1(self, handler):
        session = handler.start_clarification("policy_restriction", AUDIT_ID)
        targets = {c.candidate_transition_target for c in session.candidate_choices}
        assert "CLASS_1" not in targets

    def test_all_choices_require_confirmation(self, handler):
        for reason in ("ambiguous_target", "insufficient_context", "policy_restriction"):
            session = handler.start_clarification(reason, AUDIT_ID)
            for c in session.candidate_choices:
                assert c.to_schema_dict()["requires_confirmation"] is True


# ------------------------------------------------------------------
# User selection — CLASS_1 path
# ------------------------------------------------------------------

class TestSelectionClass1:
    def test_class1_candidate_gives_class1_transition(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        class1_choice = next(
            c for c in session.candidate_choices
            if c.candidate_transition_target == "CLASS_1"
        )
        result = handler.submit_selection(
            session, class1_choice.candidate_id, "bounded_input_node"
        )
        assert result.transition_target == TransitionTarget.CLASS_1
        assert result.should_escalate_to_class2 is False
        assert result.selected_candidate is not None

    def test_class1_result_carries_target_hint(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        living_room = next(
            c for c in session.candidate_choices
            if c.candidate_id == "OPT_LIVING_ROOM"
        )
        result = handler.submit_selection(
            session, living_room.candidate_id, "bounded_input_node"
        )
        assert result.target_hint == "living_room_light"

    def test_is_class1_ready_true_when_action_and_target_set(self, handler):
        custom = [{
            "candidate_id": "C1",
            "prompt": "거실 조명 켤까요?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": "light_on",
            "target_hint": "living_room_light",
        }]
        session = handler.start_clarification(
            "ambiguous_target", AUDIT_ID, candidate_choices=custom
        )
        result = handler.submit_selection(session, "C1", "bounded_input_node")
        assert result.is_class1_ready is True

    def test_session_status_set_to_selected(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        choice_id = session.candidate_choices[0].candidate_id
        handler.submit_selection(session, choice_id, "bounded_input_node")
        assert session.status == SessionStatus.SELECTED


# ------------------------------------------------------------------
# User selection — CLASS_0 path
# ------------------------------------------------------------------

class TestSelectionClass0:
    def test_emergency_candidate_gives_class0_transition(self, handler):
        session = handler.start_clarification("insufficient_context", AUDIT_ID)
        emergency = next(
            c for c in session.candidate_choices
            if c.candidate_transition_target == "CLASS_0"
        )
        result = handler.submit_selection(
            session, emergency.candidate_id, "bounded_input_node"
        )
        assert result.transition_target == TransitionTarget.CLASS_0
        assert result.should_escalate_to_class2 is False


# ------------------------------------------------------------------
# User selection — safe deferral / cancel path
# ------------------------------------------------------------------

class TestSelectionSafeDeferral:
    def test_cancel_candidate_escalates(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        cancel = next(
            c for c in session.candidate_choices
            if c.candidate_id == "OPT_CANCEL"
        )
        result = handler.submit_selection(
            session, cancel.candidate_id, "bounded_input_node"
        )
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_escalate_to_class2 is True

    def test_unknown_candidate_id_treated_as_timeout(self, handler):
        """Unknown selection ID must never be treated as consent."""
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        result = handler.submit_selection(session, "UNKNOWN_ID", "bounded_input_node")
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_escalate_to_class2 is True


# ------------------------------------------------------------------
# Timeout / no-response
# ------------------------------------------------------------------

class TestTimeout:
    def test_timeout_escalates_to_caregiver(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        result = handler.handle_timeout(session)
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_escalate_to_class2 is True
        assert result.selected_candidate is None
        assert result.action_hint is None
        assert result.target_hint is None

    def test_timeout_never_assumes_intent(self, handler):
        """Key safety invariant: silence != consent."""
        session = handler.start_clarification("insufficient_context", AUDIT_ID)
        result = handler.handle_timeout(session)
        assert result.transition_target != TransitionTarget.CLASS_1
        assert result.transition_target != TransitionTarget.CLASS_0

    def test_timeout_session_status_timed_out(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        handler.handle_timeout(session)
        assert session.status == SessionStatus.TIMED_OUT


# ------------------------------------------------------------------
# Clarification record (schema shape)
# ------------------------------------------------------------------

class TestClarificationRecord:
    def test_record_has_required_schema_fields(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        choice_id = session.candidate_choices[0].candidate_id
        result = handler.submit_selection(session, choice_id, "bounded_input_node")
        record = result.clarification_record

        for field in ("clarification_id", "unresolved_reason", "candidate_choices",
                      "transition_target", "llm_boundary"):
            assert field in record, f"missing field: {field}"

    def test_llm_boundary_constants_correct(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        result = handler.handle_timeout(session)
        lb = result.clarification_record["llm_boundary"]
        assert lb["candidate_generation_only"] is True
        assert lb["final_decision_allowed"] is False
        assert lb["actuation_authority_allowed"] is False
        assert lb["emergency_trigger_authority_allowed"] is False

    def test_timeout_record_preserves_candidate_choices(self, handler):
        """Timeout artifacts must retain the choices that were pending — for auditability."""
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        n_choices = len(session.candidate_choices)
        result = handler.handle_timeout(session)
        assert len(result.clarification_record["candidate_choices"]) == n_choices

    def test_selection_record_transition_target_matches_result(self, handler):
        session = handler.start_clarification("insufficient_context", AUDIT_ID)
        emergency = next(
            c for c in session.candidate_choices
            if c.candidate_transition_target == "CLASS_0"
        )
        result = handler.submit_selection(
            session, emergency.candidate_id, "bounded_input_node"
        )
        assert result.clarification_record["transition_target"] == "CLASS_0"
        assert result.clarification_record["timeout_result"] == "not_applicable"

    def test_timeout_record_timeout_result_field(self, handler):
        session = handler.start_clarification("ambiguous_target", AUDIT_ID)
        result = handler.handle_timeout(session)
        assert result.clarification_record["timeout_result"] == "safe_deferral_or_caregiver_confirmation"
