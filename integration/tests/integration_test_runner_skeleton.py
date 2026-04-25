#!/usr/bin/env python3
"""
Minimal integration test runner skeleton for the safe_deferral integration layer.

Purpose:
- load a scenario skeleton JSON file,
- resolve referenced fixture files,
- retain raw step metadata for adapter-level scenario semantics,
- print a machine-readable summary,
- fail fast when required fixture paths are missing or invalid.

This runner intentionally does NOT redefine canonical policy or runtime truth.
It is only a loading/validation skeleton for integration assets.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_MARKERS = {"common", "integration", "mac_mini", "rpi", "esp32"}


class RunnerError(Exception):
    """Raised when the integration runner cannot complete successfully."""


@dataclass
class LoadedFixture:
    path: Path
    payload: Any


@dataclass
class LoadedScenario:
    path: Path
    payload: dict[str, Any]


@dataclass
class StepResolution:
    step_id: Any
    action: str
    payload_fixture: LoadedFixture | None
    expected_fixture: LoadedFixture | None
    raw_step: dict[str, Any]


@dataclass
class RunnerSummary:
    scenario_id: str
    scenario_path: str
    step_count: int
    resolved_payload_fixtures: list[str]
    resolved_expected_fixtures: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_path": self.scenario_path,
            "step_count": self.step_count,
            "resolved_payload_fixtures": self.resolved_payload_fixtures,
            "resolved_expected_fixtures": self.resolved_expected_fixtures,
        }


def find_repo_root(start: Path) -> Path:
    """Find the repository root by looking for known top-level directories."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        names = {p.name for p in candidate.iterdir()} if candidate.is_dir() else set()
        if REPO_MARKERS.issubset(names):
            return candidate
    raise RunnerError("Could not determine repository root from the current path.")


def load_json_file(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except FileNotFoundError as exc:
        raise RunnerError(f"Required JSON file was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RunnerError(f"Invalid JSON syntax in file: {path} ({exc})") from exc


def load_scenario(repo_root: Path, scenario_rel_path: str) -> LoadedScenario:
    scenario_path = (repo_root / scenario_rel_path).resolve()
    payload = load_json_file(scenario_path)
    if not isinstance(payload, dict):
        raise RunnerError(f"Scenario must be a JSON object: {scenario_path}")
    if "scenario_id" not in payload:
        raise RunnerError(f"Scenario is missing required key 'scenario_id': {scenario_path}")
    if "steps" not in payload or not isinstance(payload["steps"], list):
        raise RunnerError(f"Scenario must contain a list 'steps': {scenario_path}")
    return LoadedScenario(path=scenario_path, payload=payload)


def load_fixture(repo_root: Path, fixture_rel_path: str) -> LoadedFixture:
    fixture_path = (repo_root / fixture_rel_path).resolve()
    payload = load_json_file(fixture_path)
    return LoadedFixture(path=fixture_path, payload=payload)


def resolve_steps(repo_root: Path, scenario: LoadedScenario) -> list[StepResolution]:
    resolved: list[StepResolution] = []
    for step in scenario.payload.get("steps", []):
        if not isinstance(step, dict):
            raise RunnerError(f"Each scenario step must be a JSON object: {scenario.path}")

        payload_fixture = None
        expected_fixture = None

        payload_rel = step.get("payload_fixture")
        if payload_rel is not None:
            if not isinstance(payload_rel, str) or not payload_rel.strip():
                raise RunnerError(
                    f"Invalid payload_fixture in scenario step {step.get('step_id')}: {scenario.path}"
                )
            payload_fixture = load_fixture(repo_root, payload_rel)

        expected_rel = step.get("expected_fixture")
        if expected_rel is not None:
            if not isinstance(expected_rel, str) or not expected_rel.strip():
                raise RunnerError(
                    f"Invalid expected_fixture in scenario step {step.get('step_id')}: {scenario.path}"
                )
            expected_fixture = load_fixture(repo_root, expected_rel)

        resolved.append(
            StepResolution(
                step_id=step.get("step_id"),
                action=str(step.get("action", "UNKNOWN")),
                payload_fixture=payload_fixture,
                expected_fixture=expected_fixture,
                raw_step=step,
            )
        )
    return resolved


def build_summary(scenario: LoadedScenario, steps: list[StepResolution]) -> RunnerSummary:
    payloads = [str(s.payload_fixture.path) for s in steps if s.payload_fixture is not None]
    expecteds = [str(s.expected_fixture.path) for s in steps if s.expected_fixture is not None]
    return RunnerSummary(
        scenario_id=str(scenario.payload["scenario_id"]),
        scenario_path=str(scenario.path),
        step_count=len(steps),
        resolved_payload_fixtures=payloads,
        resolved_expected_fixtures=expecteds,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load an integration scenario skeleton and resolve referenced fixture files."
    )
    parser.add_argument(
        "--scenario",
        default="integration/scenarios/baseline_scenario_skeleton.json",
        help="Repository-relative path to the scenario JSON file.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the summary JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(Path.cwd())
    scenario = load_scenario(repo_root, args.scenario)
    steps = resolve_steps(repo_root, scenario)
    summary = build_summary(scenario, steps)

    if args.pretty:
        print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(summary.to_dict(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunnerError as exc:
        print(f"[FATAL] {exc}", file=sys.stderr)
        raise SystemExit(1)
