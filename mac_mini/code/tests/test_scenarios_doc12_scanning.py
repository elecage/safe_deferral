"""Schema-validation + invariant tests for the doc 12 scanning scenarios
(P1.3 of the post-doc-12 consistency backfill plan).

Three scenarios were added under integration/scenarios/ to exercise the
scanning interaction model end-to-end:

  - SCN_CLASS2_SCANNING_USER_ACCEPT_FIRST          — single_click on option 0 → CLASS_1
  - SCN_CLASS2_SCANNING_ALL_REJECTED_CAREGIVER_ESCALATION — every option rejected → caregiver Phase 2
  - SCN_CLASS2_SCANNING_TRIPLE_HIT_EMERGENCY_SHORTCUT     — triple_hit during scan → CLASS_0

These tests verify each scenario:
  - is loadable JSON,
  - validates against integration/scenarios/scenario_manifest_schema.json,
  - declares the comparison_condition that activates scanning mode,
  - declares scan_input_mode_expectation invariants consistent with each path.

This is the FIRST scenario-validation test; future scenario PRs (P1.4, P1.5)
should add similar focused validators for the new fixture families.
"""

import json
import pathlib

import jsonschema
import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SCENARIOS_DIR = _REPO_ROOT / "integration" / "scenarios"
_MANIFEST_SCHEMA_PATH = _SCENARIOS_DIR / "scenario_manifest_schema.json"

_SCANNING_SCENARIOS = [
    "class2_scanning_user_accept_first_scenario_skeleton.json",
    "class2_scanning_all_rejected_caregiver_escalation_scenario_skeleton.json",
    "class2_scanning_triple_hit_emergency_shortcut_scenario_skeleton.json",
]


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def manifest_schema():
    return _load_json(_MANIFEST_SCHEMA_PATH)


@pytest.fixture(scope="module")
def manifest_validator(manifest_schema):
    # The manifest schema declares draft 2020-12 but only uses constructs
    # (additionalProperties, enum, const, $ref, $defs, type-array unions)
    # that are valid under Draft 7. Use Draft7Validator so this test runs
    # on environments where the older jsonschema package is pinned.
    return jsonschema.Draft7Validator(manifest_schema)


# ==================================================================
# Schema validation
# ==================================================================

class TestScanningScenariosValidateAgainstManifestSchema:
    """Each new scanning scenario must validate against
    scenario_manifest_schema.json so the scenario_manager loader and
    dashboard pickers can rely on consistent shape."""

    @pytest.mark.parametrize("filename", _SCANNING_SCENARIOS)
    def test_scenario_validates(self, filename, manifest_validator):
        path = _SCENARIOS_DIR / filename
        assert path.exists(), f"Missing scanning scenario: {path}"
        scenario = _load_json(path)
        errors = list(manifest_validator.iter_errors(scenario))
        assert not errors, "; ".join(
            f"{list(e.absolute_path)}: {e.message}" for e in errors
        )

    @pytest.mark.parametrize("filename", _SCANNING_SCENARIOS)
    def test_scenario_id_matches_pattern(self, filename):
        scenario = _load_json(_SCENARIOS_DIR / filename)
        sid = scenario["scenario_id"]
        assert sid.startswith("SCN_CLASS2_SCANNING_"), sid


# ==================================================================
# Comparison condition wiring
# ==================================================================

class TestScanningScenariosDeclareComparisonCondition:
    """Every scanning scenario must declare the comparison_condition that
    the runner translates into routing_metadata.class2_input_mode='scanning'.
    This ensures paper-eval can mechanically pair scenarios with the right
    runtime configuration."""

    @pytest.mark.parametrize("filename", _SCANNING_SCENARIOS)
    def test_declares_class2_scanning_input_condition(self, filename):
        scenario = _load_json(_SCENARIOS_DIR / filename)
        expectation = scenario.get("scan_input_mode_expectation", {})
        assert expectation.get("scenario_comparison_condition") == "class2_scanning_input"
        assert expectation.get("expected_routing_metadata_class2_input_mode") == "scanning"
        assert expectation.get("expected_clarification_record_input_mode") == "scanning"


# ==================================================================
# Per-scenario terminal-path invariants
# ==================================================================

class TestUserAcceptFirstScenario:
    """User accepts option 0 via single_click → CLASS_1, no caregiver phase."""

    @pytest.fixture
    def scenario(self):
        return _load_json(
            _SCENARIOS_DIR / "class2_scanning_user_accept_first_scenario_skeleton.json"
        )

    def test_terminal_transition_is_class1(self, scenario):
        assert scenario["class2_clarification_expectation"]["expected_transition_target"] == "CLASS_1"

    def test_caregiver_phase_not_invoked(self, scenario):
        assert scenario["scan_input_mode_expectation"]["expected_terminal_invokes_caregiver_phase"] is False

    def test_scan_history_first_entry_is_yes_at_index_0(self, scenario):
        e = scenario["scan_input_mode_expectation"]
        assert e["expected_scan_history_length"] == 1
        assert e["expected_scan_history_first_response"] == "yes"
        assert e["expected_scan_history_first_option_index"] == 0


class TestAllRejectedCaregiverEscalationScenario:
    """User rejects every option (no/silence) → caregiver Phase 2; silence
    ≠ consent invariant explicitly asserted."""

    @pytest.fixture
    def scenario(self):
        return _load_json(
            _SCENARIOS_DIR
            / "class2_scanning_all_rejected_caregiver_escalation_scenario_skeleton.json"
        )

    def test_terminal_transition_is_caregiver_or_safe_deferral(self, scenario):
        assert scenario["class2_clarification_expectation"]["expected_transition_target"] == \
            "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"

    def test_caregiver_phase_invoked(self, scenario):
        assert scenario["scan_input_mode_expectation"]["expected_terminal_invokes_caregiver_phase"] is True

    def test_silence_does_not_imply_consent_explicit(self, scenario):
        assert scenario["scan_input_mode_expectation"]["silence_does_not_imply_consent"] is True

    def test_no_yes_response_in_scan_history(self, scenario):
        assert scenario["scan_input_mode_expectation"]["expected_scan_history_no_yes_response"] is True


class TestTripleHitEmergencyShortcutScenario:
    """triple_hit during scan → immediate CLASS_0, no caregiver phase,
    no further options announced."""

    @pytest.fixture
    def scenario(self):
        return _load_json(
            _SCENARIOS_DIR
            / "class2_scanning_triple_hit_emergency_shortcut_scenario_skeleton.json"
        )

    def test_terminal_transition_is_class0(self, scenario):
        assert scenario["class2_clarification_expectation"]["expected_transition_target"] == "CLASS_0"

    def test_caregiver_phase_not_invoked(self, scenario):
        assert scenario["scan_input_mode_expectation"]["expected_terminal_invokes_caregiver_phase"] is False

    def test_emergency_shortcut_used(self, scenario):
        assert scenario["scan_input_mode_expectation"]["expected_emergency_shortcut_used"] is True

    def test_remaining_options_skipped(self, scenario):
        assert scenario["scan_input_mode_expectation"]["expected_remaining_options_not_announced"] is True
