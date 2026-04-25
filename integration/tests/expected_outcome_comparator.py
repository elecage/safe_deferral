#!/usr/bin/env python3
"""
Expected outcome comparator skeleton for the safe_deferral integration layer.

Purpose:
- load an observed result JSON file,
- load an expected outcome fixture JSON file,
- compare a bounded set of comparable fields,
- print a machine-readable pass/fail summary.

This comparator intentionally does NOT redefine canonical policy or runtime truth.
It only compares integration-side observed results against expected fixture fields.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_MARKERS = {"common", "integration", "mac_mini", "rpi", "esp32"}


class ComparatorError(Exception):
    """Raised when the comparator cannot complete successfully."""


@dataclass
class ComparisonResult:
    passed: bool
    compared_fields: list[str]
    mismatches: list[dict[str, Any]]
    observed_path: str
    expected_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "compared_fields": self.compared_fields,
            "mismatches": self.mismatches,
            "observed_path": self.observed_path,
            "expected_path": self.expected_path,
        }


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        names = {p.name for p in candidate.iterdir()} if candidate.is_dir() else set()
        if REPO_MARKERS.issubset(names):
            return candidate
    raise ComparatorError("Could not determine repository root from the current path.")


def load_json_file(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except FileNotFoundError as exc:
        raise ComparatorError(f"Required JSON file was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ComparatorError(f"Invalid JSON syntax in file: {path} ({exc})") from exc


def resolve_path(repo_root: Path, rel_or_abs: str) -> Path:
    path = Path(rel_or_abs)
    return path if path.is_absolute() else (repo_root / path).resolve()


def _normalise_for_compare(value: Any) -> Any:
    if isinstance(value, list):
        return sorted(value) if all(isinstance(item, str) for item in value) else value
    return value


def compare_values(observed: dict[str, Any], expected: dict[str, Any]) -> ComparisonResult:
    field_mapping = {
        "expected_route_class": "route_class",
        "expected_routing_target": "routing_target",
        "expected_llm_invocation_allowed": "llm_invocation_allowed",
        "expected_llm_decision_invocation_allowed": "llm_decision_invocation_allowed",
        "expected_llm_guidance_generation_allowed": "llm_guidance_generation_allowed",
        "expected_safe_outcome": "safe_outcome",
        "expected_safe_outcome_family": "safe_outcome_family",
        "expected_class2_role": "class2_role",
        "expected_candidate_generation_allowed": "candidate_generation_allowed",
        "expected_candidate_generation_authorizes_actuation": "candidate_generation_authorizes_actuation",
        "expected_confirmation_required_before_transition": "confirmation_required_before_transition",
        "expected_allowed_transition_targets": "allowed_transition_targets",
        "expected_payload_family": "payload_family",
        "expected_candidate_count_max": "candidate_count_max",
        "expected_transition_family": "transition_family",
        "expected_source_route_class": "source_route_class",
        "expected_transition_target": "transition_target",
        "expected_required_confirmation": "required_confirmation",
        "expected_required_confirmation_or_evidence": "required_confirmation_or_evidence",
        "expected_selected_candidate_id": "selected_candidate_id",
        "expected_validator_required_before_dispatch": "validator_required_before_dispatch",
        "expected_single_admissible_action_required": "single_admissible_action_required",
        "expected_timeout_or_no_response": "timeout_or_no_response",
        "expected_confirmation_received": "confirmation_received",
        "expected_no_intent_assumption": "no_intent_assumption",
        "expected_unsafe_autonomous_actuation_allowed": "unsafe_autonomous_actuation_allowed",
        "doorlock_autonomous_execution_allowed": "doorlock_autonomous_execution_allowed",
        "canonical_emergency_family": "canonical_emergency_family",
    }

    compared_fields: list[str] = []
    mismatches: list[dict[str, Any]] = []

    for expected_key, observed_key in field_mapping.items():
        if expected_key not in expected:
            continue
        compared_fields.append(expected_key)
        observed_value = observed.get(observed_key)
        expected_value = expected.get(expected_key)
        if _normalise_for_compare(observed_value) != _normalise_for_compare(expected_value):
            mismatches.append(
                {
                    "expected_field": expected_key,
                    "observed_field": observed_key,
                    "expected_value": expected_value,
                    "observed_value": observed_value,
                }
            )

    return ComparisonResult(
        passed=len(mismatches) == 0,
        compared_fields=compared_fields,
        mismatches=mismatches,
        observed_path="",
        expected_path="",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare an observed integration result JSON against an expected outcome fixture."
    )
    parser.add_argument(
        "--observed",
        required=True,
        help="Repository-relative or absolute path to the observed result JSON file.",
    )
    parser.add_argument(
        "--expected",
        required=True,
        help="Repository-relative or absolute path to the expected outcome fixture JSON file.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the comparison summary JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(Path.cwd())

    observed_path = resolve_path(repo_root, args.observed)
    expected_path = resolve_path(repo_root, args.expected)

    observed = load_json_file(observed_path)
    expected = load_json_file(expected_path)

    if not isinstance(observed, dict):
        raise ComparatorError(f"Observed result must be a JSON object: {observed_path}")
    if not isinstance(expected, dict):
        raise ComparatorError(f"Expected fixture must be a JSON object: {expected_path}")

    result = compare_values(observed, expected)
    result.observed_path = str(observed_path)
    result.expected_path = str(expected_path)

    payload = result.to_dict()
    if args.pretty:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False))

    return 0 if result.passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ComparatorError as exc:
        print(f"[FATAL] {exc}", file=sys.stderr)
        raise SystemExit(1)
