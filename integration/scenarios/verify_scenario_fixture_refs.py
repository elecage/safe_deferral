#!/usr/bin/env python3
"""Verify scenario payload_fixture and expected_fixture references.

Checks:
- referenced files exist
- referenced files are inside the repository
- referenced JSON files parse successfully
- Phase 6 Class 2 clarification/transition fixtures preserve safety boundaries

This script intentionally does not redefine canonical policy/schema truth; use
verify_scenario_policy_schema_alignment.py for broader boundary checks.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = ROOT / "integration" / "scenarios"
FIXTURE_FIELDS = ("payload_fixture", "expected_fixture")
CLASS2_SCHEMA_REF = "common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json"
CLASS2_EXPECTED_FIXTURES = {
    "expected_routing_class2.json",
    "expected_class2_candidate_prompt.json",
    "expected_class2_transition_class1.json",
    "expected_class2_transition_class0.json",
    "expected_class2_timeout_safe_deferral.json",
}
CLASS2_SAMPLE_FIXTURES = {
    "sample_class2_user_selection_class1.json",
    "sample_class2_user_selection_class0.json",
    "sample_class2_timeout_no_response.json",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc


def scenario_files() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*_scenario_skeleton.json"))


def fixture_files() -> list[Path]:
    return sorted((ROOT / "integration" / "tests" / "data").glob("*.json"))


def resolve_repo_path(value: str) -> Path:
    return (ROOT / value).resolve()


def is_under_root(path: Path) -> bool:
    try:
        path.relative_to(ROOT)
        return True
    except ValueError:
        return False


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate_class2_expected_fixture(path: Path, data: Any, errors: list[str]) -> None:
    rel = path.relative_to(ROOT)
    require(isinstance(data, dict), errors, f"{rel}: Class 2 expected fixture must be object")
    if not isinstance(data, dict):
        return

    if path.name == "expected_routing_class2.json":
        require(data.get("expected_class2_role") == "clarification_transition_state", errors, f"{rel}: must represent initial clarification_transition_state")
        require(data.get("expected_candidate_generation_allowed") is True, errors, f"{rel}: expected_candidate_generation_allowed must be true")
        require(data.get("expected_confirmation_required_before_transition") is True, errors, f"{rel}: confirmation before transition must be required")
        targets = set(data.get("expected_allowed_transition_targets", []))
        for target in ("CLASS_1", "CLASS_0", "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"):
            require(target in targets, errors, f"{rel}: missing expected transition target {target}")

    if path.name == "expected_class2_candidate_prompt.json":
        require(data.get("schema_ref") == CLASS2_SCHEMA_REF, errors, f"{rel}: schema_ref must be {CLASS2_SCHEMA_REF}")
        require(data.get("expected_candidate_count_max") == 4, errors, f"{rel}: expected_candidate_count_max must be 4")
        candidates = data.get("expected_candidate_choices")
        require(isinstance(candidates, list) and 1 <= len(candidates) <= 4, errors, f"{rel}: expected_candidate_choices must contain 1-4 candidates")
        if isinstance(candidates, list):
            targets = {candidate.get("candidate_transition_target") for candidate in candidates if isinstance(candidate, dict)}
            for target in ("CLASS_1", "CLASS_0"):
                require(target in targets, errors, f"{rel}: expected_candidate_choices missing {target}")

    for key in (
        "expected_llm_decision_invocation_allowed",
        "expected_candidate_generation_authorizes_actuation",
        "expected_unsafe_autonomous_actuation_allowed",
    ):
        if key in data:
            require(data.get(key) is False, errors, f"{rel}: {key} must be false")
    if "doorlock_autonomous_execution_allowed" in data:
        require(data.get("doorlock_autonomous_execution_allowed") is False, errors, f"{rel}: doorlock_autonomous_execution_allowed must be false")

    boundary = data.get("expected_llm_boundary")
    if isinstance(boundary, dict):
        require(boundary.get("candidate_generation_only") is True, errors, f"{rel}: candidate_generation_only must be true")
        require(boundary.get("final_decision_allowed") is False, errors, f"{rel}: final_decision_allowed must be false")
        require(boundary.get("actuation_authority_allowed") is False, errors, f"{rel}: actuation_authority_allowed must be false")
        require(boundary.get("emergency_trigger_authority_allowed") is False, errors, f"{rel}: emergency_trigger_authority_allowed must be false")


def validate_class2_sample_fixture(path: Path, data: Any, errors: list[str]) -> None:
    rel = path.relative_to(ROOT)
    require(isinstance(data, dict), errors, f"{rel}: Class 2 sample fixture must be object")
    if not isinstance(data, dict):
        return

    require(data.get("schema_ref") == CLASS2_SCHEMA_REF, errors, f"{rel}: schema_ref must be {CLASS2_SCHEMA_REF}")
    require(data.get("source_layer") == "class2_clarification_manager", errors, f"{rel}: source_layer must be class2_clarification_manager")
    require(isinstance(data.get("clarification_id"), str) and bool(data.get("clarification_id")), errors, f"{rel}: clarification_id is required")
    candidates = data.get("candidate_choices")
    require(isinstance(candidates, list) and 1 <= len(candidates) <= 4, errors, f"{rel}: candidate_choices must contain 1-4 candidates")
    if isinstance(candidates, list):
        for idx, candidate in enumerate(candidates, start=1):
            require(isinstance(candidate, dict), errors, f"{rel}: candidate {idx} must be object")
            if isinstance(candidate, dict):
                require(candidate.get("requires_confirmation") is True, errors, f"{rel}: candidate {idx} requires_confirmation must be true")

    selection = data.get("selection_result")
    require(isinstance(selection, dict), errors, f"{rel}: selection_result must be object")
    if isinstance(selection, dict):
        source = selection.get("selection_source")
        if path.name == "sample_class2_timeout_no_response.json":
            require(source == "timeout_or_no_response", errors, f"{rel}: timeout sample selection_source must be timeout_or_no_response")
            require(selection.get("confirmed") is False, errors, f"{rel}: timeout sample confirmed must be false")
            require(data.get("transition_target") == "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION", errors, f"{rel}: timeout sample transition target must be SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION")
        else:
            require(selection.get("confirmed") is True, errors, f"{rel}: selection confirmed must be true")

    boundary = data.get("llm_boundary")
    require(isinstance(boundary, dict), errors, f"{rel}: llm_boundary must be object")
    if isinstance(boundary, dict):
        require(boundary.get("candidate_generation_only") is True, errors, f"{rel}: candidate_generation_only must be true")
        require(boundary.get("final_decision_allowed") is False, errors, f"{rel}: final_decision_allowed must be false")
        require(boundary.get("actuation_authority_allowed") is False, errors, f"{rel}: actuation_authority_allowed must be false")
        require(boundary.get("emergency_trigger_authority_allowed") is False, errors, f"{rel}: emergency_trigger_authority_allowed must be false")


def main() -> int:
    errors: list[str] = []
    checked_refs = 0
    files = scenario_files()

    if not files:
        print("ERROR: no scenario skeleton files found", file=sys.stderr)
        return 1

    for scenario_path in files:
        rel_scenario = scenario_path.relative_to(ROOT)
        try:
            data = load_json(scenario_path)
        except ValueError as exc:
            errors.append(f"{rel_scenario}: {exc}")
            continue

        steps = data.get("steps", [])
        if not isinstance(steps, list):
            errors.append(f"{rel_scenario}: steps must be a list")
            continue

        for idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                errors.append(f"{rel_scenario}: step {idx} must be an object")
                continue
            for field in FIXTURE_FIELDS:
                value = step.get(field)
                if value is None:
                    continue
                checked_refs += 1
                if not isinstance(value, str) or not value:
                    errors.append(f"{rel_scenario}: step {idx} {field} must be a non-empty string")
                    continue
                target = resolve_repo_path(value)
                if not is_under_root(target):
                    errors.append(f"{rel_scenario}: step {idx} {field} escapes repository root: {value}")
                    continue
                if not target.exists():
                    errors.append(f"{rel_scenario}: step {idx} {field} does not exist: {value}")
                    continue
                if target.suffix == ".json":
                    try:
                        load_json(target)
                    except ValueError as exc:
                        errors.append(f"{rel_scenario}: step {idx} {field} {value} {exc}")

    for fixture_path in fixture_files():
        try:
            fixture = load_json(fixture_path)
        except ValueError as exc:
            errors.append(f"{fixture_path.relative_to(ROOT)}: {exc}")
            continue
        if fixture_path.name in CLASS2_EXPECTED_FIXTURES:
            validate_class2_expected_fixture(fixture_path, fixture, errors)
        if fixture_path.name in CLASS2_SAMPLE_FIXTURES:
            validate_class2_sample_fixture(fixture_path, fixture, errors)

    if errors:
        print("Scenario fixture reference verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OK: verified {checked_refs} fixture reference(s) across {len(files)} scenario manifest(s), including Class 2 fixture semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
