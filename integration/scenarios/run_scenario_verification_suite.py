#!/usr/bin/env python3
"""Run the scenario verification suite for safe_deferral.

This wrapper runs the static scenario verifiers and, when pytest is available,
the integration scenario tests.

It is intentionally small and standard-library only except for the optional
pytest invocation. The goal is to provide one reproducible local/CI command for
Phase 9 and later final consistency sweeps.

Usage:
    python integration/scenarios/run_scenario_verification_suite.py
    python integration/scenarios/run_scenario_verification_suite.py --skip-pytest
    python integration/scenarios/run_scenario_verification_suite.py --pytest-args -q
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_MARKERS = {"common", "integration", "mac_mini", "rpi", "esp32"}


@dataclass
class CheckResult:
    name: str
    command: list[str]
    returncode: int

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if not candidate.is_dir():
            continue
        names = {p.name for p in candidate.iterdir()}
        if REPO_MARKERS.issubset(names):
            return candidate
    raise RuntimeError("Could not determine repository root from current path")


def run_check(repo_root: Path, name: str, command: list[str]) -> CheckResult:
    print(f"\n==> {name}")
    print("$ " + " ".join(command))
    completed = subprocess.run(command, cwd=repo_root, check=False)
    status = "PASS" if completed.returncode == 0 else "FAIL"
    print(f"==> {name}: {status} ({completed.returncode})")
    return CheckResult(name=name, command=command, returncode=completed.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe_deferral scenario verification suite")
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Run only static scenario verifiers and skip pytest integration tests.",
    )
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        default=[],
        help="Extra arguments passed to pytest after integration/tests/test_integration_scenarios.py.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(Path(__file__))
    py = sys.executable

    checks: list[tuple[str, list[str]]] = [
        (
            "scenario manifest verifier",
            [py, "integration/scenarios/verify_scenario_manifest.py"],
        ),
        (
            "scenario fixture reference verifier",
            [py, "integration/scenarios/verify_scenario_fixture_refs.py"],
        ),
        (
            "scenario topic alignment verifier",
            [py, "integration/scenarios/verify_scenario_topic_alignment.py"],
        ),
        (
            "scenario policy/schema alignment verifier",
            [py, "integration/scenarios/verify_scenario_policy_schema_alignment.py"],
        ),
    ]

    if not args.skip_pytest:
        checks.append(
            (
                "integration pytest scenario tests",
                [py, "-m", "pytest", "integration/tests/test_integration_scenarios.py", *args.pytest_args],
            )
        )

    results = [run_check(repo_root, name, command) for name, command in checks]
    failed = [result for result in results if not result.passed]

    print("\n==> Scenario verification suite summary")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}: {result.name}")

    if failed:
        print("\nScenario verification suite failed.", file=sys.stderr)
        return 1

    print("\nScenario verification suite passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
