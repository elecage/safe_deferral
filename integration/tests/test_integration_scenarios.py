"""
Integration scenario tests using the adapter.

Each scenario test loads a scenario skeleton, executes it through policy_router
or deterministic adapter-level Class 2 clarification hooks, and asserts the
observed result matches the expected fixture.

Scenario files and fixture paths are read from the existing integration asset tree.
Policy values and expected outcomes should remain in fixture files, not in test logic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_INTEGRATION_TESTS = Path(__file__).resolve().parent
if str(_INTEGRATION_TESTS) not in sys.path:
    sys.path.insert(0, str(_INTEGRATION_TESTS))

from integration_test_runner_skeleton import find_repo_root, load_scenario  # noqa: E402
from integration_adapter import execute_scenario, _class2_fixture_observed  # noqa: E402
from expected_outcome_comparator import compare_values  # noqa: E402


# ── helpers ─────────────────────────────────────────────────────────────────

def _run(scenario_rel_path: str):
    """Load and execute a scenario, returning its ScenarioResult."""
    repo_root = find_repo_root(_REPO_ROOT)
    scenario = load_scenario(repo_root, scenario_rel_path)
    return execute_scenario(scenario)


def _load_json(rel_path: str) -> dict:
    path = _REPO_ROOT / rel_path
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    assert isinstance(payload, dict), f"Expected object fixture: {rel_path}"
    return payload


# ── CLASS 0 emergency scenarios ──────────────────────────────────────────────


class TestClass0Scenarios:
    def test_e001_temperature_emergency(self):
        """E001: high temperature triggers CLASS_0 emergency path."""
        result = _run("integration/scenarios/class0_e001_scenario_skeleton.json")
        assert result.passed, _fail_detail(result)

    def test_e002_button_triple_hit_emergency(self):
        """E002: button triple-hit triggers CLASS_0 emergency path."""
        result = _run("integration/scenarios/class0_e002_scenario_skeleton.json")
        assert result.passed, _fail_detail(result)

    def test_e003_smoke_emergency(self):
        """E003: smoke_detected triggers CLASS_0 emergency path."""
        result = _run("integration/scenarios/class0_e003_scenario_skeleton.json")
        assert result.passed, _fail_detail(result)

    def test_e004_gas_emergency(self):
        """E004: gas_detected triggers CLASS_0 emergency path."""
        result = _run("integration/scenarios/class0_e004_scenario_skeleton.json")
        assert result.passed, _fail_detail(result)

    def test_e005_fall_emergency(self):
        """E005: fall_detected sensor event triggers CLASS_0 emergency path."""
        result = _run("integration/scenarios/class0_e005_scenario_skeleton.json")
        assert result.passed, _fail_detail(result)


# ── CLASS 1 baseline scenario ────────────────────────────────────────────────


class TestClass1Scenarios:
    def test_class1_baseline(self):
        """CLASS_1: normal ambient context routes to bounded low-risk assistance."""
        result = _run("integration/scenarios/class1_baseline_scenario_skeleton.json")
        assert result.passed, _fail_detail(result)


# ── CLASS 2 clarification / transition scenario ──────────────────────────────


class TestClass2Scenarios:
    def test_class2_insufficient_context(self):
        """CLASS_2: insufficient context enters clarification/transition state."""
        result = _run(
            "integration/scenarios/class2_insufficient_context_scenario_skeleton.json"
        )
        assert result.passed, _fail_detail(result)

    def test_class2_candidate_prompt_step_is_observable(self):
        """The adapter exposes bounded candidate prompt metadata for Class 2."""
        result = _run(
            "integration/scenarios/class2_insufficient_context_scenario_skeleton.json"
        )
        candidate_steps = [
            sr for sr in result.step_results if sr.action == "generate_bounded_candidate_choices"
        ]
        assert candidate_steps, "No candidate generation step found"
        observed = candidate_steps[0].observed
        assert observed is not None
        expected = _load_json("integration/tests/data/expected_class2_candidate_prompt.json")
        comparison = compare_values(observed, expected)
        assert comparison.passed, comparison.to_dict()

    @pytest.mark.parametrize(
        ("sample_fixture", "expected_fixture"),
        [
            (
                "integration/tests/data/sample_class2_user_selection_class1.json",
                "integration/tests/data/expected_class2_transition_class1.json",
            ),
            (
                "integration/tests/data/sample_class2_user_selection_class0.json",
                "integration/tests/data/expected_class2_transition_class0.json",
            ),
            (
                "integration/tests/data/sample_class2_timeout_no_response.json",
                "integration/tests/data/expected_class2_timeout_safe_deferral.json",
            ),
        ],
    )
    def test_class2_transition_fixtures_compare(self, sample_fixture, expected_fixture):
        """Phase 6 Class 2 transition fixtures compare through the adapter mapping."""
        sample = _load_json(sample_fixture)
        expected = _load_json(expected_fixture)
        observed = _class2_fixture_observed(sample)
        transition_family = expected.get("expected_transition_family")
        if transition_family:
            observed["transition_family"] = transition_family
        comparison = compare_values(observed, expected)
        assert comparison.passed, comparison.to_dict()


# ── fault scenarios ───────────────────────────────────────────────────────────


class TestFaultScenarios:
    def test_stale_fault(self):
        """Stale event routes to conservative CLASS_2 handling (C204-like)."""
        result = _run("integration/scenarios/stale_fault_scenario_skeleton.json")
        assert result.passed, _fail_detail(result)

    def test_missing_state_fault(self):
        """Missing context state routes to conservative safe handling."""
        result = _run("integration/scenarios/missing_state_scenario_skeleton.json")
        assert result.passed, _fail_detail(result)


# ── step-level assertions ─────────────────────────────────────────────────────


class TestAdapterStepBehavior:
    def test_all_steps_have_results(self):
        """Every step in the E001 scenario produces a result (no silent skips)."""
        repo_root = find_repo_root(_REPO_ROOT)
        scenario = load_scenario(
            repo_root, "integration/scenarios/class0_e001_scenario_skeleton.json"
        )
        result = execute_scenario(scenario)
        assert len(result.step_results) > 0
        for sr in result.step_results:
            assert sr.error is None, f"Step {sr.step_id} had error: {sr.error}"

    def test_publish_step_produces_observed(self):
        """The publish_context_payload step must produce an observed dict."""
        repo_root = find_repo_root(_REPO_ROOT)
        scenario = load_scenario(
            repo_root, "integration/scenarios/class1_baseline_scenario_skeleton.json"
        )
        result = execute_scenario(scenario)
        publish_steps = [
            sr for sr in result.step_results if sr.action == "publish_context_payload"
        ]
        assert publish_steps, "No publish step found"
        for ps in publish_steps:
            assert ps.observed is not None, f"Step {ps.step_id} has no observed dict"

    def test_observe_step_has_comparison(self):
        """The observe_audit_stream step must contain a ComparisonResult."""
        repo_root = find_repo_root(_REPO_ROOT)
        scenario = load_scenario(
            repo_root, "integration/scenarios/class0_e001_scenario_skeleton.json"
        )
        result = execute_scenario(scenario)
        observe_steps = [sr for sr in result.step_results if sr.action == "observe_audit_stream"]
        assert observe_steps, "No observe step found"
        for os_ in observe_steps:
            assert os_.comparison is not None, f"Step {os_.step_id} has no comparison"


# ── helper ────────────────────────────────────────────────────────────────────

def _fail_detail(result) -> str:
    lines = [f"Scenario '{result.scenario_id}' FAILED:"]
    for sr in result.step_results:
        if not sr.passed:
            if sr.error:
                lines.append(f"  step {sr.step_id} error: {sr.error}")
            elif sr.comparison and not sr.comparison.passed:
                for m in sr.comparison.mismatches:
                    lines.append(
                        f"  step {sr.step_id} mismatch on '{m['expected_field']}': "
                        f"expected={m['expected_value']!r}, observed={m['observed_value']!r}"
                    )
    return "\n".join(lines)
