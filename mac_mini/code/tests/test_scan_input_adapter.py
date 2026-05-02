"""Tests for the scanning input adapter (doc 12 Phase 3).

The adapter is pure — no MQTT, no main-loop coupling — so these tests
exercise the full mapping table without standing up the pipeline. Phase 4
wiring then becomes mechanical.
"""

import pytest

from class2_clarification_manager.scan_input_adapter import (
    DECISION_EMERGENCY,
    DECISION_IGNORE,
    DECISION_SUBMIT,
    interpret_button_event_for_scan,
)


class _FakeChoice:
    def __init__(self, candidate_id, target):
        self.candidate_id = candidate_id
        self.candidate_transition_target = target


class _FakeSession:
    """Minimal stand-in for a scanning ClarificationSession — only the two
    attributes the adapter consults are present."""

    def __init__(self, current_option_index=0, candidate_choices=None):
        self.current_option_index = current_option_index
        self.candidate_choices = candidate_choices or []


# ==================================================================
# single_click → 'yes' to current option
# ==================================================================

class TestSingleClick:
    def test_yes_to_current_option_index(self):
        session = _FakeSession(current_option_index=2)
        d = interpret_button_event_for_scan("single_click", session)
        assert d.kind == DECISION_SUBMIT
        assert d.option_index == 2
        assert d.response == "yes"

    def test_yes_uses_current_index_zero_by_default(self):
        session = _FakeSession()
        d = interpret_button_event_for_scan("single_click", session)
        assert d.option_index == 0
        assert d.response == "yes"


# ==================================================================
# double_click → explicit 'no' to current option
# ==================================================================

class TestDoubleClick:
    def test_no_to_current_option_index(self):
        session = _FakeSession(current_option_index=1)
        d = interpret_button_event_for_scan("double_click", session)
        assert d.kind == DECISION_SUBMIT
        assert d.option_index == 1
        assert d.response == "no"


# ==================================================================
# triple_hit → emergency shortcut (find first CLASS_0 candidate)
# ==================================================================

class TestTripleHit:
    def test_routes_to_first_class0_candidate(self):
        session = _FakeSession(candidate_choices=[
            _FakeChoice("C1_LIGHTING_ASSISTANCE", "CLASS_1"),
            _FakeChoice("C3_EMERGENCY_HELP", "CLASS_0"),
            _FakeChoice("C2_CAREGIVER_HELP", "CAREGIVER_CONFIRMATION"),
        ])
        d = interpret_button_event_for_scan("triple_hit", session)
        assert d.kind == DECISION_EMERGENCY
        assert d.emergency_candidate_id == "C3_EMERGENCY_HELP"

    def test_no_class0_candidate_falls_to_ignore(self):
        """C208/C207 sets have no CLASS_0 option — triple_hit is ignored
        rather than misrouted."""
        session = _FakeSession(candidate_choices=[
            _FakeChoice("C2_CAREGIVER_HELP", "CAREGIVER_CONFIRMATION"),
            _FakeChoice("C4_CANCEL_OR_WAIT", "SAFE_DEFERRAL"),
        ])
        d = interpret_button_event_for_scan("triple_hit", session)
        assert d.kind == DECISION_IGNORE
        assert "triple_hit" in d.reason

    def test_finds_first_class0_when_multiple(self):
        """If by some chance more than one CLASS_0 candidate exists, the
        first wins (deterministic and matches direct-select behaviour)."""
        session = _FakeSession(candidate_choices=[
            _FakeChoice("C3_FIRST", "CLASS_0"),
            _FakeChoice("C3_SECOND", "CLASS_0"),
        ])
        d = interpret_button_event_for_scan("triple_hit", session)
        assert d.emergency_candidate_id == "C3_FIRST"


# ==================================================================
# Other event codes → ignore (do not fall through to normal pipeline)
# ==================================================================

class TestUnrecognisedEventCodes:
    @pytest.mark.parametrize("code", [
        "long_press", "swipe_up", "voice_select", "", "unknown_code",
    ])
    def test_unknown_code_ignored_with_reason(self, code):
        session = _FakeSession()
        d = interpret_button_event_for_scan(code, session)
        assert d.kind == DECISION_IGNORE
        assert d.reason and "unrecognised_event_code" in d.reason


# ==================================================================
# Adapter is pure — does not mutate the session
# ==================================================================

class TestAdapterPurity:
    def test_session_state_unchanged_after_interpret(self):
        session = _FakeSession(
            current_option_index=2,
            candidate_choices=[_FakeChoice("C0", "CLASS_0")],
        )
        before_idx = session.current_option_index
        before_len = len(session.candidate_choices)
        for code in ("single_click", "double_click", "triple_hit",
                     "long_press", ""):
            interpret_button_event_for_scan(code, session)
        assert session.current_option_index == before_idx
        assert len(session.candidate_choices) == before_len
