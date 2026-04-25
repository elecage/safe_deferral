#!/usr/bin/env python3
"""Validate scenario skeleton manifest structure.

This verifier intentionally uses only the Python standard library so it can run
on Mac mini, Raspberry Pi, Linux, and CI environments without extra packages.

It checks the project-specific manifest contract documented in:
- integration/scenarios/scenario_manifest_rules.md
- integration/scenarios/scenario_manifest_schema.json

This script validates scenario assets only. It does not define policy or schema
truth.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = ROOT / "integration" / "scenarios"

REQUIRED_TOP_LEVEL = {
    "scenario_id",
    "title",
    "description",
    "category",
    "mode",
    "input_plane",
    "preconditions",
    "steps",
    "expected_outcomes",
    "notes",
}

ALLOWED_CATEGORIES = {
    "baseline",
    "class0_emergency",
    "class1_baseline",
    "class2_insufficient_context",
    "fault_stale",
    "fault_conflict",
    "fault_missing_state",
}

ALLOWED_MODES = {"deterministic", "randomized_stress"}
SCENARIO_ID_RE = re.compile(r"^SCN_[A-Z0-9_]+$")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc


def scenario_files() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*_scenario_skeleton.json"))


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate_one(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = load_json(path)
    except ValueError as exc:
        return [f"{path}: {exc}"]

    rel = path.relative_to(ROOT)
    require(isinstance(data, dict), errors, f"{rel}: manifest must be a JSON object")
    if not isinstance(data, dict):
        return errors

    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    require(not missing, errors, f"{rel}: missing required fields: {missing}")

    scenario_id = data.get("scenario_id")
    require(isinstance(scenario_id, str) and bool(SCENARIO_ID_RE.match(scenario_id)), errors, f"{rel}: scenario_id must match SCN_[A-Z0-9_]+")

    require(isinstance(data.get("title"), str) and bool(data.get("title")), errors, f"{rel}: title must be a non-empty string")
    require(isinstance(data.get("description"), str) and bool(data.get("description")), errors, f"{rel}: description must be a non-empty string")

    category = data.get("category")
    require(category in ALLOWED_CATEGORIES, errors, f"{rel}: unsupported category {category!r}")

    mode = data.get("mode")
    require(mode in ALLOWED_MODES, errors, f"{rel}: unsupported mode {mode!r}")

    input_plane = data.get("input_plane")
    require(isinstance(input_plane, dict), errors, f"{rel}: input_plane must be an object")
    if isinstance(input_plane, dict):
        require(input_plane.get("protocol") == "mqtt", errors, f"{rel}: input_plane.protocol must be 'mqtt'")
        require(isinstance(input_plane.get("ingress_topic"), str) and bool(input_plane.get("ingress_topic")), errors, f"{rel}: input_plane.ingress_topic is required")
        require(isinstance(input_plane.get("audit_topic"), str) and bool(input_plane.get("audit_topic")), errors, f"{rel}: input_plane.audit_topic is required")
        if category == "class0_emergency":
            require("normalized_policy_input_topic" in input_plane, errors, f"{rel}: class0 scenario should declare normalized_policy_input_topic")
            require("bridge_mode" in input_plane, errors, f"{rel}: class0 scenario should declare bridge_mode")

    preconditions = data.get("preconditions")
    require(isinstance(preconditions, dict), errors, f"{rel}: preconditions must be an object")
    if isinstance(preconditions, dict):
        for key, value in preconditions.items():
            require(isinstance(value, bool), errors, f"{rel}: precondition {key!r} must be boolean")

    steps = data.get("steps")
    require(isinstance(steps, list) and len(steps) > 0, errors, f"{rel}: steps must be a non-empty array")
    if isinstance(steps, list):
        for idx, step in enumerate(steps, start=1):
            require(isinstance(step, dict), errors, f"{rel}: step {idx} must be an object")
            if isinstance(step, dict):
                for field in ("step_id", "action", "description"):
                    require(field in step, errors, f"{rel}: step {idx} missing {field}")
                require(isinstance(step.get("action"), str) and bool(step.get("action")), errors, f"{rel}: step {idx} action must be non-empty string")
                require(isinstance(step.get("description"), str) and bool(step.get("description")), errors, f"{rel}: step {idx} description must be non-empty string")

    expected = data.get("expected_outcomes")
    require(isinstance(expected, dict), errors, f"{rel}: expected_outcomes must be an object")
    if isinstance(expected, dict):
        require(expected.get("unsafe_autonomous_actuation_allowed") is False, errors, f"{rel}: unsafe_autonomous_actuation_allowed must be false")
        require(expected.get("doorlock_autonomous_execution_allowed") is False, errors, f"{rel}: doorlock_autonomous_execution_allowed must be false")
        require("llm_decision_invocation_allowed" in expected, errors, f"{rel}: expected_outcomes must include llm_decision_invocation_allowed")
        require("llm_guidance_generation_allowed" in expected, errors, f"{rel}: expected_outcomes must include llm_guidance_generation_allowed")
        if category == "class0_emergency":
            require(expected.get("route_class") == "CLASS_0", errors, f"{rel}: class0 scenario must expect route_class CLASS_0")
            require(expected.get("llm_decision_invocation_allowed") is False, errors, f"{rel}: class0 must not allow LLM decision invocation")
            require(re.match(r"^E00[1-5]$", str(expected.get("canonical_emergency_family", ""))) is not None, errors, f"{rel}: class0 scenario must declare E001-E005 canonical_emergency_family")
        if category == "class1_baseline":
            require(expected.get("allowed_action_catalog_ref") == "common/policies/low_risk_actions_v1_1_0_FROZEN.json", errors, f"{rel}: class1 scenario must reference frozen low-risk action catalog")
        if category.startswith("fault_"):
            require(isinstance(expected.get("allowed_safe_outcomes"), list), errors, f"{rel}: fault scenario must declare allowed_safe_outcomes")
            require("UNSAFE_AUTONOMOUS_ACTUATION" in expected.get("prohibited_outcomes", []), errors, f"{rel}: fault scenario must prohibit UNSAFE_AUTONOMOUS_ACTUATION")

    notes = data.get("notes")
    require(isinstance(notes, list), errors, f"{rel}: notes must be an array")
    if isinstance(notes, list):
        require(all(isinstance(item, str) for item in notes), errors, f"{rel}: all notes must be strings")

    return [f"{rel}: {error}" for error in errors]


def main() -> int:
    files = scenario_files()
    if not files:
        print("ERROR: no scenario skeleton files found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in files:
        errors.extend(validate_one(path))

    if errors:
        print("Scenario manifest verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OK: verified {len(files)} scenario manifest(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
