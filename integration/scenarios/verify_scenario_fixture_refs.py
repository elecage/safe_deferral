#!/usr/bin/env python3
"""Verify scenario payload_fixture and expected_fixture references.

Checks:
- referenced files exist
- referenced files are inside the repository
- referenced JSON files parse successfully

This script intentionally does not validate semantic policy/schema alignment; use
verify_scenario_policy_schema_alignment.py for boundary checks.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = ROOT / "integration" / "scenarios"
FIXTURE_FIELDS = ("payload_fixture", "expected_fixture")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc


def scenario_files() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*_scenario_skeleton.json"))


def resolve_repo_path(value: str) -> Path:
    return (ROOT / value).resolve()


def is_under_root(path: Path) -> bool:
    try:
        path.relative_to(ROOT)
        return True
    except ValueError:
        return False


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

    if errors:
        print("Scenario fixture reference verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OK: verified {checked_refs} fixture reference(s) across {len(files)} scenario manifest(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
