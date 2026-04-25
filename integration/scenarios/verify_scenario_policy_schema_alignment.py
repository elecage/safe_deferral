#!/usr/bin/env python3
"""Verify scenario alignment with frozen policy/schema boundaries.

Checks:
- Class 0 scenario emergency family IDs are E001-E005 and exist in the active policy table text.
- Class 1 scenarios reference the frozen low-risk action catalog.
- Class 2 scenarios follow the clarification/transition boundary introduced by policy v1.2.0.
- Scenario expected outcomes keep unsafe autonomous actuation and doorlock autonomous execution disabled.
- Referenced policy-router input fixtures include environmental_context.doorbell_detected.
- Current fixture device_states do not include doorlock-like keys.
- Expected fixtures align with coarse and split LLM invocation semantics.

This script validates scenario assets. It does not redefine frozen policy or schema truth.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = ROOT / "integration" / "scenarios"
POLICY_TABLE = ROOT / "common" / "policies" / "policy_table_v1_2_0_FROZEN.json"
LOW_RISK_CATALOG_REF = "common/policies/low_risk_actions_v1_1_0_FROZEN.json"
DOORLOCK_KEYS = {
    "doorlock",
    "door_lock",
    "door_lock_state",
    "front_door_lock",
    "front_doorlock",
    "lock_state",
}
CLASS2_ALLOWED_TRANSITIONS = {
    "CLASS_1",
    "CLASS_0",
    "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def scenario_files() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*_scenario_skeleton.json"))


def resolve_repo_path(value: str) -> Path:
    return (ROOT / value).resolve()


def policy_text() -> str:
    return POLICY_TABLE.read_text(encoding="utf-8")


def emergency_ids_from_policy_text(text: str) -> set[str]:
    # Policy layout may evolve, so use a conservative text scan for canonical IDs.
    return {eid for eid in ("E001", "E002", "E003", "E004", "E005") if eid in text}


def normalized_key(key: str) -> str:
    return key.strip().lower().replace("-", "_")


def check_active_policy_baseline(text: str, errors: list[str]) -> None:
    required_policy_markers = [
        '"version": "1.2.0"',
        '"class_2_clarification_transition"',
        '"llm_decision_invocation_allowed": false',
        '"candidate_generation_allowed": true',
        '"confirmation_required_before_transition": true',
        '"SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"',
    ]
    for marker in required_policy_markers:
        if marker not in text:
            errors.append(f"active policy table {POLICY_TABLE.relative_to(ROOT)} missing required Class 2 baseline marker: {marker}")


def check_fixture_payload(path: Path, rel_scenario: Path, errors: list[str]) -> None:
    try:
        fixture = load_json(path)
    except ValueError as exc:
        errors.append(str(exc))
        return

    pure = fixture.get("pure_context_payload") if isinstance(fixture, dict) else None
    if not isinstance(pure, dict):
        # Not a policy-router input shaped fixture. Skip semantic context checks.
        return

    env = pure.get("environmental_context")
    if not isinstance(env, dict):
        errors.append(f"{rel_scenario}: {path.relative_to(ROOT)} pure_context_payload.environmental_context must be an object")
        return

    if "doorbell_detected" not in env:
        errors.append(f"{rel_scenario}: {path.relative_to(ROOT)} missing environmental_context.doorbell_detected")
    elif not isinstance(env.get("doorbell_detected"), bool):
        errors.append(f"{rel_scenario}: {path.relative_to(ROOT)} environmental_context.doorbell_detected must be boolean")

    device_states = pure.get("device_states", {})
    if isinstance(device_states, dict):
        for key in device_states.keys():
            if normalized_key(str(key)) in DOORLOCK_KEYS:
                errors.append(f"{rel_scenario}: {path.relative_to(ROOT)} must not include doorlock state in current device_states: {key}")


def check_expected_fixture(path: Path, rel_scenario: Path, scenario_expected: dict[str, Any], errors: list[str]) -> None:
    try:
        expected = load_json(path)
    except ValueError as exc:
        errors.append(str(exc))
        return
    if not isinstance(expected, dict):
        errors.append(f"{rel_scenario}: {path.relative_to(ROOT)} expected fixture must be an object")
        return

    if expected.get("expected_unsafe_autonomous_actuation_allowed") is not False:
        errors.append(f"{rel_scenario}: {path.relative_to(ROOT)} expected_unsafe_autonomous_actuation_allowed must be false")
    if expected.get("doorlock_autonomous_execution_allowed") is not False:
        errors.append(f"{rel_scenario}: {path.relative_to(ROOT)} doorlock_autonomous_execution_allowed must be false")

    if "llm_decision_invocation_allowed" in scenario_expected:
        scenario_value = scenario_expected.get("llm_decision_invocation_allowed")
        expected_value = expected.get("expected_llm_decision_invocation_allowed")
        if expected_value != scenario_value:
            errors.append(f"{rel_scenario}: {path.relative_to(ROOT)} expected_llm_decision_invocation_allowed {expected_value!r} does not match scenario {scenario_value!r}")

    if "llm_guidance_generation_allowed" in scenario_expected:
        scenario_value = scenario_expected.get("llm_guidance_generation_allowed")
        expected_value = expected.get("expected_llm_guidance_generation_allowed")
        if expected_value != scenario_value:
            errors.append(f"{rel_scenario}: {path.relative_to(ROOT)} expected_llm_guidance_generation_allowed {expected_value!r} does not match scenario {scenario_value!r}")


def check_class2_scenario(data: dict[str, Any], rel: Path, errors: list[str]) -> None:
    expected = data.get("expected_outcomes", {})
    clarification = data.get("clarification_interaction")
    if not isinstance(clarification, dict):
        errors.append(f"{rel}: class2 scenario must include clarification_interaction object")
        return

    if clarification.get("confirmation_required_before_transition") is not True:
        errors.append(f"{rel}: class2 clarification_interaction.confirmation_required_before_transition must be true")

    candidate_boundary = str(clarification.get("candidate_generation_boundary", ""))
    if "no_final_decision" not in candidate_boundary or "no_actuation_authority" not in candidate_boundary:
        errors.append(f"{rel}: class2 candidate_generation_boundary must prohibit final decision and actuation authority")

    if expected.get("llm_decision_invocation_allowed") is not False:
        errors.append(f"{rel}: class2 llm_decision_invocation_allowed must be false")
    if expected.get("candidate_generation_authorizes_actuation") is not False:
        errors.append(f"{rel}: class2 candidate_generation_authorizes_actuation must be false")
    if expected.get("confirmation_required_before_transition") is not True:
        errors.append(f"{rel}: class2 expected_outcomes.confirmation_required_before_transition must be true")

    transitions = expected.get("allowed_transition_targets")
    if not isinstance(transitions, list):
        errors.append(f"{rel}: class2 expected_outcomes.allowed_transition_targets must be an array")
    else:
        missing = sorted(CLASS2_ALLOWED_TRANSITIONS - {str(item) for item in transitions})
        if missing:
            errors.append(f"{rel}: class2 allowed_transition_targets missing {missing}")

    transition_outcomes = data.get("transition_outcomes")
    if not isinstance(transition_outcomes, list) or not transition_outcomes:
        errors.append(f"{rel}: class2 scenario must include non-empty transition_outcomes")
    else:
        outcome_targets = {str(item.get("transition_target")) for item in transition_outcomes if isinstance(item, dict)}
        missing = sorted(CLASS2_ALLOWED_TRANSITIONS - outcome_targets)
        if missing:
            errors.append(f"{rel}: class2 transition_outcomes missing transition targets {missing}")


def main() -> int:
    errors: list[str] = []
    text = policy_text()
    check_active_policy_baseline(text, errors)

    emergency_ids = emergency_ids_from_policy_text(text)
    required_emergency_ids = {"E001", "E002", "E003", "E004", "E005"}
    missing_policy_ids = sorted(required_emergency_ids - emergency_ids)
    if missing_policy_ids:
        errors.append(f"policy table appears to be missing canonical emergency IDs: {missing_policy_ids}")

    files = scenario_files()
    if not files:
        print("ERROR: no scenario skeleton files found", file=sys.stderr)
        return 1

    for scenario_path in files:
        rel = scenario_path.relative_to(ROOT)
        try:
            data = load_json(scenario_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(data, dict):
            errors.append(f"{rel}: scenario must be an object")
            continue

        category = data.get("category")
        expected = data.get("expected_outcomes", {})
        if not isinstance(expected, dict):
            errors.append(f"{rel}: expected_outcomes must be an object")
            continue

        if expected.get("unsafe_autonomous_actuation_allowed") is not False:
            errors.append(f"{rel}: unsafe_autonomous_actuation_allowed must be false")
        if expected.get("doorlock_autonomous_execution_allowed") is not False:
            errors.append(f"{rel}: doorlock_autonomous_execution_allowed must be false")

        if category == "class0_emergency":
            eid = expected.get("canonical_emergency_family")
            if eid not in required_emergency_ids:
                errors.append(f"{rel}: class0 canonical_emergency_family must be one of E001-E005")
            if expected.get("llm_decision_invocation_allowed") is not False:
                errors.append(f"{rel}: class0 llm_decision_invocation_allowed must be false")

        if category == "class1_baseline":
            if expected.get("allowed_action_catalog_ref") != LOW_RISK_CATALOG_REF:
                errors.append(f"{rel}: class1 must reference {LOW_RISK_CATALOG_REF}")

        if category == "class2_insufficient_context":
            check_class2_scenario(data, rel, errors)

        steps = data.get("steps", [])
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict):
                    continue
                payload_ref = step.get("payload_fixture")
                if isinstance(payload_ref, str):
                    payload_path = resolve_repo_path(payload_ref)
                    if payload_path.exists():
                        check_fixture_payload(payload_path, rel, errors)
                expected_ref = step.get("expected_fixture")
                if isinstance(expected_ref, str):
                    expected_path = resolve_repo_path(expected_ref)
                    if expected_path.exists():
                        check_expected_fixture(expected_path, rel, expected, errors)

    if errors:
        print("Scenario policy/schema alignment verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OK: verified policy/schema alignment for {len(files)} scenario manifest(s) against {POLICY_TABLE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
