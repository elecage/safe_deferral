"""Schema-validation + invariant tests for the doc 11 multi-turn refinement
scenarios (P1.4 of the post-doc-12 consistency backfill plan).

Two scenarios were added under integration/scenarios/ to exercise the
opt-in multi-turn refinement path (class2_multi_turn_enabled=true):

  - SCN_CLASS2_MULTI_TURN_REFINEMENT_USER_PICKS_ROOM
      → C1_LIGHTING_ASSISTANCE → REFINE_BEDROOM → terminal CLASS_1
  - SCN_CLASS2_MULTI_TURN_REFINEMENT_TURN_TIMEOUT_CAREGIVER_ESCALATION
      → C1_LIGHTING_ASSISTANCE → no refinement response → escalation
        (silence ≠ consent invariant preserved)

These tests verify each scenario:
  - validates against scenario_manifest_schema.json,
  - declares the multi_turn_refinement_expectation block consistently,
  - declares the policy precondition (class2_multi_turn_enabled=true),
  - asserts path-specific terminal invariants and refinement_history shape.
"""

import json
import pathlib

import jsonschema
import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SCENARIOS_DIR = _REPO_ROOT / "integration" / "scenarios"
_MANIFEST_SCHEMA_PATH = _SCENARIOS_DIR / "scenario_manifest_schema.json"

_REFINEMENT_SCENARIOS = [
    "class2_multi_turn_refinement_user_picks_room_scenario_skeleton.json",
    "class2_multi_turn_refinement_turn_timeout_caregiver_escalation_scenario_skeleton.json",
]


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def manifest_validator():
    schema = _load_json(_MANIFEST_SCHEMA_PATH)
    # Manifest declares draft 2020-12 but only uses Draft 7-compatible
    # constructs (matches P1.3 test pattern).
    return jsonschema.Draft7Validator(schema)


# ==================================================================
# Schema validation
# ==================================================================

class TestRefinementScenariosValidateAgainstManifestSchema:
    @pytest.mark.parametrize("filename", _REFINEMENT_SCENARIOS)
    def test_scenario_validates(self, filename, manifest_validator):
        path = _SCENARIOS_DIR / filename
        assert path.exists(), f"Missing refinement scenario: {path}"
        scenario = _load_json(path)
        errors = list(manifest_validator.iter_errors(scenario))
        assert not errors, "; ".join(
            f"{list(e.absolute_path)}: {e.message}" for e in errors
        )

    @pytest.mark.parametrize("filename", _REFINEMENT_SCENARIOS)
    def test_scenario_id_matches_pattern(self, filename):
        scenario = _load_json(_SCENARIOS_DIR / filename)
        sid = scenario["scenario_id"]
        assert sid.startswith("SCN_CLASS2_MULTI_TURN_REFINEMENT_"), sid


# ==================================================================
# Policy precondition consistency
# ==================================================================

class TestRefinementScenariosDeclarePolicyPrecondition:
    """Both scenarios require class2_multi_turn_enabled=true to run.
    The expectation block must declare that, AND preconditions must
    match — otherwise paper-eval might run them in a deployment where
    the flag is off, getting the wrong terminal path."""

    @pytest.mark.parametrize("filename", _REFINEMENT_SCENARIOS)
    def test_declares_required_policy_field(self, filename):
        scenario = _load_json(_SCENARIOS_DIR / filename)
        e = scenario.get("multi_turn_refinement_expectation", {})
        assert e.get("scenario_requires_policy_field") == "class2_multi_turn_enabled"
        assert e.get("scenario_requires_policy_value") is True

    @pytest.mark.parametrize("filename", _REFINEMENT_SCENARIOS)
    def test_preconditions_request_multi_turn_enabled(self, filename):
        scenario = _load_json(_SCENARIOS_DIR / filename)
        pc = scenario["preconditions"]
        assert pc.get("requires_class2_multi_turn_enabled_in_policy") is True


# ==================================================================
# Per-scenario terminal-path invariants
# ==================================================================

class TestUserPicksRoomScenario:
    """Parent C1_LIGHTING_ASSISTANCE → refinement REFINE_BEDROOM →
    terminal CLASS_1. refinement_history captures the single transition."""

    @pytest.fixture
    def scenario(self):
        return _load_json(
            _SCENARIOS_DIR
            / "class2_multi_turn_refinement_user_picks_room_scenario_skeleton.json"
        )

    def test_terminal_transition_is_class1(self, scenario):
        assert scenario["class2_clarification_expectation"]["expected_transition_target"] == "CLASS_1"

    def test_refinement_history_length_is_one(self, scenario):
        e = scenario["multi_turn_refinement_expectation"]
        assert e["expected_refinement_history_length"] == 1

    def test_parent_then_bedroom_transition(self, scenario):
        e = scenario["multi_turn_refinement_expectation"]
        assert e["expected_parent_candidate_id"] == "C1_LIGHTING_ASSISTANCE"
        assert e["expected_refinement_history_first_parent_candidate_id"] == "C1_LIGHTING_ASSISTANCE"
        assert e["expected_refinement_history_first_selected_candidate_id"] == "REFINE_BEDROOM"

    def test_state_aware_terminal_action(self, scenario):
        """Bedroom currently off (per the input fixture's device_states) →
        action_hint='light_on'. If the test ever fails because the input
        fixture's device_states change, the refinement template
        (state-aware) is the source of truth — assert what it would
        produce, not a hardcoded constant."""
        e = scenario["multi_turn_refinement_expectation"]
        assert e["expected_terminal_action_hint"] == "light_on"
        assert e["expected_terminal_target_hint"] == "bedroom_light"


class TestRefinementTurnTimeoutScenario:
    """Parent C1_LIGHTING_ASSISTANCE picked, refinement turn times out
    → caregiver escalation. silence ≠ consent invariant explicit."""

    @pytest.fixture
    def scenario(self):
        return _load_json(
            _SCENARIOS_DIR
            / "class2_multi_turn_refinement_turn_timeout_caregiver_escalation_scenario_skeleton.json"
        )

    def test_terminal_transition_is_safe_deferral_or_caregiver(self, scenario):
        assert scenario["class2_clarification_expectation"]["expected_transition_target"] == \
            "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"

    def test_refinement_turn_timed_out(self, scenario):
        e = scenario["multi_turn_refinement_expectation"]
        assert e["expected_refinement_turn_timed_out"] is True

    def test_caregiver_path_invoked(self, scenario):
        e = scenario["multi_turn_refinement_expectation"]
        assert e["expected_terminal_invokes_caregiver_path"] is True

    def test_silence_does_not_imply_consent_explicit(self, scenario):
        e = scenario["multi_turn_refinement_expectation"]
        assert e["silence_does_not_imply_consent"] is True

    def test_refinement_history_still_recorded_on_timeout(self, scenario):
        """Even on the timeout path, refinement_history captures the
        unanswered turn so audit can tell 'parent picked, refinement
        unanswered' apart from 'never picked anything'."""
        e = scenario["multi_turn_refinement_expectation"]
        assert e["expected_refinement_history_length"] == 1
        assert e["expected_refinement_history_first_parent_candidate_id"] == "C1_LIGHTING_ASSISTANCE"
