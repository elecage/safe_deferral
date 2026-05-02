"""Verifier for the P2.6 scenario_manifest schema additions and the
comparison_conditions tagging across all scenarios.

P2.6 of the post-doc-12 consistency backfill plan added:
  - `comparison_conditions[]` optional field with enum matching Package A's
    9 conditions (rpi/code/experiment_package/definitions.py)
  - formal definitions for `scan_input_mode_expectation` /
    `multi_turn_refinement_expectation` / `scan_ordering_expectation`
    blocks (introduced ad-hoc by P1.3/P1.4/P1.5)

These tests verify:

  1. Every scenario file in integration/scenarios/ still validates against
     the (extended) manifest schema.
  2. Every Package A condition is tagged by ≥1 scenario (paper-eval
     coverage guarantee).
  3. Tagged conditions match the enum (catches typos).
  4. Scenarios with an *_expectation block validate the block's required
     fields per its formal definition.
"""

import json
import pathlib

import jsonschema
import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SCENARIOS_DIR = _REPO_ROOT / "integration" / "scenarios"
_MANIFEST_SCHEMA_PATH = _SCENARIOS_DIR / "scenario_manifest_schema.json"


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _all_scenario_paths():
    """All scenario manifest JSON files under integration/scenarios/.

    Excludes scenario_manifest_schema.json (the schema itself, not a
    scenario). Previously also excluded sc01_light_on_request.json, but
    that file has been relocated to integration/tests/data/ under the
    canonical sample_policy_router_input_*.json naming so the exclusion
    is no longer needed."""
    excluded = {
        "scenario_manifest_schema.json",
    }
    return [
        p for p in sorted(_SCENARIOS_DIR.glob("*.json"))
        if p.name not in excluded
    ]


@pytest.fixture(scope="module")
def manifest_validator():
    schema = _load_json(_MANIFEST_SCHEMA_PATH)
    return jsonschema.Draft7Validator(schema)


# ==================================================================
# All scenarios still validate
# ==================================================================

class TestAllScenariosValidateAgainstExtendedManifest:
    """The new optional fields must not break ANY existing scenario.
    Scenarios without comparison_conditions / *_expectation pass through
    unchanged; tagged scenarios validate against the formal definitions."""

    @pytest.mark.parametrize(
        "scenario_path",
        _all_scenario_paths(),
        ids=lambda p: p.name,
    )
    def test_scenario_validates(self, scenario_path, manifest_validator):
        scenario = _load_json(scenario_path)
        errors = list(manifest_validator.iter_errors(scenario))
        assert not errors, "; ".join(
            f"{list(e.absolute_path)}: {e.message}" for e in errors
        )


# ==================================================================
# Package A condition coverage
# ==================================================================

# Source of truth: rpi/code/experiment_package/definitions.py
# Hardcoded here to keep the test fast and avoid importing the rpi
# package; if Package A's list ever changes, this must be updated AND
# scenarios re-tagged in the same PR.
_PACKAGE_A_COMPARISON_CONDITIONS = [
    "direct_mapping",
    "rule_only",
    "llm_assisted",
    "class2_static_only",
    "class2_llm_assisted",
    "class2_scan_source_order",
    "class2_scan_deterministic",
    "class2_direct_select_input",
    "class2_scanning_input",
]


def _all_tagged_conditions():
    """Union of comparison_conditions across all scenarios."""
    tagged = set()
    for path in _all_scenario_paths():
        scenario = _load_json(path)
        for c in scenario.get("comparison_conditions", []):
            tagged.add(c)
    return tagged


class TestPackageAConditionCoverage:
    """Each of Package A's 9 comparison_conditions must be tagged by at
    least one scenario. If the runner is asked to execute a trial under
    a condition with no scenario coverage, the trial would still run but
    paper-eval cannot describe its purpose."""

    @pytest.mark.parametrize("condition", _PACKAGE_A_COMPARISON_CONDITIONS)
    def test_condition_has_at_least_one_scenario(self, condition):
        tagged = _all_tagged_conditions()
        assert condition in tagged, (
            f"No scenario tags comparison_condition='{condition}'. "
            f"Either add a scenario or update Package A's definition."
        )

    def test_no_typos_in_tagged_conditions(self):
        """All tagged conditions must be in the Package A enum (catches
        future scenario typos before paper-eval silently runs the wrong
        condition)."""
        tagged = _all_tagged_conditions()
        unknown = tagged - set(_PACKAGE_A_COMPARISON_CONDITIONS)
        assert not unknown, (
            f"Scenarios reference unknown comparison_conditions: {unknown}. "
            f"Either fix the typo or add the value to Package A's definition."
        )

    def test_known_class2_dimensions_have_paired_coverage(self):
        """Sanity: the scanning interaction model and deterministic
        ordering each have ≥1 scenario AND we explicitly distinguish
        the two scanning conditions (scanning vs direct-select) from
        the ordering ones."""
        tagged = _all_tagged_conditions()
        assert "class2_scanning_input" in tagged
        assert "class2_direct_select_input" in tagged
        assert "class2_scan_source_order" in tagged or \
            "class2_scan_deterministic" in tagged


# ==================================================================
# Per-scenario tagging consistency
# ==================================================================

class TestPerScenarioTaggingConsistency:
    """Scenarios that declare scan_input_mode_expectation must also tag
    class2_scanning_input in comparison_conditions (paper-eval pairing
    must be unambiguous)."""

    def test_scan_input_mode_expectation_implies_scanning_tag(self):
        for path in _all_scenario_paths():
            scenario = _load_json(path)
            if "scan_input_mode_expectation" in scenario:
                tags = scenario.get("comparison_conditions", [])
                assert "class2_scanning_input" in tags, (
                    f"{path.name}: declares scan_input_mode_expectation "
                    f"but does NOT tag 'class2_scanning_input'"
                )

    def test_scan_ordering_expectation_implies_deterministic_tag(self):
        for path in _all_scenario_paths():
            scenario = _load_json(path)
            if "scan_ordering_expectation" in scenario:
                tags = scenario.get("comparison_conditions", [])
                assert "class2_scan_deterministic" in tags, (
                    f"{path.name}: declares scan_ordering_expectation "
                    f"but does NOT tag 'class2_scan_deterministic'"
                )
                # Ordering meaningful only under scanning — also asserted.
                assert "class2_scanning_input" in tags, (
                    f"{path.name}: scan_ordering_expectation is meaningful "
                    f"only under scanning; tag class2_scanning_input too"
                )

    def test_multi_turn_refinement_expectation_present_when_block_used(self):
        """Scenarios with multi_turn_refinement_expectation must declare
        the policy precondition consistency (already enforced by the
        block schema's const value, but we also assert here for clarity)."""
        for path in _all_scenario_paths():
            scenario = _load_json(path)
            if "multi_turn_refinement_expectation" in scenario:
                e = scenario["multi_turn_refinement_expectation"]
                assert e.get("scenario_requires_policy_field") == "class2_multi_turn_enabled"


# ==================================================================
# Manifest schema self-checks (the new definitions exist + work)
# ==================================================================

class TestManifestSchemaHasNewDefinitions:
    """The manifest schema declares the 4 new fields (comparison_conditions
    + 3 expectation blocks) so future scenario authors can rely on them."""

    @pytest.fixture
    def manifest(self):
        return _load_json(_MANIFEST_SCHEMA_PATH)

    @pytest.mark.parametrize("field_name", [
        "comparison_conditions",
        "scan_input_mode_expectation",
        "multi_turn_refinement_expectation",
        "scan_ordering_expectation",
    ])
    def test_field_defined_at_top_level(self, manifest, field_name):
        assert field_name in manifest["properties"], (
            f"P2.6 added '{field_name}' to scenario_manifest_schema.json — "
            f"it must remain in the top-level properties so scenarios can "
            f"declare it."
        )

    def test_comparison_conditions_enum_matches_package_a(self, manifest):
        enum = manifest["properties"]["comparison_conditions"]["items"]["enum"]
        assert sorted(enum) == sorted(_PACKAGE_A_COMPARISON_CONDITIONS), (
            "comparison_conditions enum in manifest schema diverged from "
            "Package A's definition. Update both together."
        )
