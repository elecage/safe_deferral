"""Schema-validation + invariant tests for the doc 12 §14 deterministic
ordering scenarios (P1.5 of the post-doc-12 consistency backfill plan).

Two scenarios were added under integration/scenarios/ to exercise the
deterministic ordering layer (class2_scan_ordering_mode='deterministic'):

  - SCN_CLASS2_DETERMINISTIC_ORDERING_C206_BUCKET
      → trigger-bucket priority, no context overrides matched
  - SCN_CLASS2_DETERMINISTIC_ORDERING_SMOKE_OVERRIDE
      → smoke_detected context override boosts CLASS_0 to front

These tests verify each scenario:
  - validates against scenario_manifest_schema.json,
  - declares the scan_ordering_expectation block consistently,
  - asserts trigger-bucket attribution (matched_bucket) and final_order
    invariants per path,
  - cross-checks the scenario's expected first target against the actual
    rules in policy_table.global_constraints.class2_scan_ordering_rules
    so a policy edit that changes the C206 bucket immediately surfaces
    a scenario-mismatch failure.
"""

import json
import pathlib

import jsonschema
import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SCENARIOS_DIR = _REPO_ROOT / "integration" / "scenarios"
_MANIFEST_SCHEMA_PATH = _SCENARIOS_DIR / "scenario_manifest_schema.json"
_POLICY_PATH = _REPO_ROOT / "common" / "policies" / "policy_table.json"

_ORDERING_SCENARIOS = [
    "class2_deterministic_ordering_c206_bucket_scenario_skeleton.json",
    "class2_deterministic_ordering_smoke_override_scenario_skeleton.json",
]


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def manifest_validator():
    schema = _load_json(_MANIFEST_SCHEMA_PATH)
    return jsonschema.Draft7Validator(schema)


@pytest.fixture(scope="module")
def policy():
    return _load_json(_POLICY_PATH)


# ==================================================================
# Schema validation
# ==================================================================

class TestOrderingScenariosValidateAgainstManifestSchema:
    @pytest.mark.parametrize("filename", _ORDERING_SCENARIOS)
    def test_scenario_validates(self, filename, manifest_validator):
        path = _SCENARIOS_DIR / filename
        assert path.exists(), f"Missing ordering scenario: {path}"
        scenario = _load_json(path)
        errors = list(manifest_validator.iter_errors(scenario))
        assert not errors, "; ".join(
            f"{list(e.absolute_path)}: {e.message}" for e in errors
        )

    @pytest.mark.parametrize("filename", _ORDERING_SCENARIOS)
    def test_scenario_id_matches_pattern(self, filename):
        scenario = _load_json(_SCENARIOS_DIR / filename)
        sid = scenario["scenario_id"]
        assert sid.startswith("SCN_CLASS2_DETERMINISTIC_ORDERING_"), sid


# ==================================================================
# Comparison-condition + scanning prerequisite consistency
# ==================================================================

class TestOrderingScenariosDeclareCondition:
    """Each scenario must declare comparison_condition='class2_scan_deterministic'
    AND scenario_assumes_scanning_input_mode_active=true (because ordering
    is meaningful only under scanning)."""

    @pytest.mark.parametrize("filename", _ORDERING_SCENARIOS)
    def test_declares_deterministic_condition(self, filename):
        scenario = _load_json(_SCENARIOS_DIR / filename)
        e = scenario.get("scan_ordering_expectation", {})
        assert e.get("scenario_comparison_condition") == "class2_scan_deterministic"
        assert e.get("expected_routing_metadata_class2_scan_ordering_mode") == "deterministic"
        assert e.get("scenario_assumes_scanning_input_mode_active") is True

    @pytest.mark.parametrize("filename", _ORDERING_SCENARIOS)
    def test_preconditions_request_deterministic_ordering(self, filename):
        scenario = _load_json(_SCENARIOS_DIR / filename)
        pc = scenario["preconditions"]
        assert pc.get("requires_scanning_input_mode_enabled") is True
        assert pc.get("requires_deterministic_scan_ordering_enabled") is True


# ==================================================================
# Per-scenario invariants
# ==================================================================

class TestC206BucketScenario:
    """C206 bucket places CLASS_1 first, no overrides matched (smoke/gas/
    doorbell all false in the scenario's input fixture)."""

    @pytest.fixture
    def scenario(self):
        return _load_json(
            _SCENARIOS_DIR
            / "class2_deterministic_ordering_c206_bucket_scenario_skeleton.json"
        )

    def test_terminal_transition_is_class1(self, scenario):
        assert scenario["class2_clarification_expectation"]["expected_transition_target"] == "CLASS_1"

    def test_matched_bucket_is_c206(self, scenario):
        e = scenario["scan_ordering_expectation"]
        assert e["expected_scan_ordering_applied_matched_bucket"] == "C206"

    def test_no_overrides_matched(self, scenario):
        e = scenario["scan_ordering_expectation"]
        assert e["expected_scan_ordering_applied_applied_overrides_count"] == 0

    def test_first_target_is_class1(self, scenario):
        e = scenario["scan_ordering_expectation"]
        assert e["expected_scan_ordering_applied_final_order_first_target"] == "CLASS_1"

    def test_scenario_assertion_matches_policy_c206_bucket(self, scenario, policy):
        """Cross-check: the scenario's expected first target MUST match
        the actual policy's C206 bucket priority list. If someone edits
        the C206 bucket in policy_table, this test surfaces the scenario
        drift immediately rather than letting paper-eval silently report
        the wrong order."""
        rules = policy["global_constraints"]["class2_scan_ordering_rules"]
        c206 = rules["by_trigger_id"]["C206"]
        assert c206[0] == scenario["scan_ordering_expectation"][
            "expected_scan_ordering_applied_final_order_first_target"
        ]
        assert c206[1] == scenario["scan_ordering_expectation"][
            "expected_scan_ordering_applied_final_order_second_target"
        ]


class TestSmokeOverrideScenario:
    """smoke_detected=true context override moves CLASS_0 to front
    regardless of trigger-bucket priority."""

    @pytest.fixture
    def scenario(self):
        return _load_json(
            _SCENARIOS_DIR
            / "class2_deterministic_ordering_smoke_override_scenario_skeleton.json"
        )

    def test_override_count_at_least_one(self, scenario):
        e = scenario["scan_ordering_expectation"]
        assert e["expected_scan_ordering_applied_applied_overrides_count_at_least"] >= 1

    def test_first_override_references_smoke(self, scenario):
        e = scenario["scan_ordering_expectation"]
        assert "smoke_detected" in e["expected_scan_ordering_applied_first_override_references"]

    def test_first_target_is_class0(self, scenario):
        """The whole point of smoke override is CLASS_0 ends up first
        regardless of trigger-bucket default."""
        e = scenario["scan_ordering_expectation"]
        assert e["expected_scan_ordering_applied_final_order_first_target"] == "CLASS_0"

    def test_terminal_transition_is_class0(self, scenario):
        assert scenario["class2_clarification_expectation"]["expected_transition_target"] == "CLASS_0"

    def test_scenario_assertion_matches_policy_smoke_override(self, scenario, policy):
        """Cross-check: the scenario claims smoke_detected boosts CLASS_0.
        Verify the actual policy has that override defined so a policy
        edit (e.g., changing boost_first to a different target) trips
        this test instead of silently letting the scenario be wrong."""
        rules = policy["global_constraints"]["class2_scan_ordering_rules"]
        overrides = rules.get("context_overrides", [])
        smoke_overrides = [
            o for o in overrides
            if o.get("if_field") == "environmental_context.smoke_detected"
            and o.get("if_equals") is True
        ]
        assert len(smoke_overrides) >= 1, "Policy missing smoke_detected override"
        assert smoke_overrides[0]["boost_first"] == scenario["scan_ordering_expectation"][
            "expected_scan_ordering_applied_final_order_first_target"
        ]
