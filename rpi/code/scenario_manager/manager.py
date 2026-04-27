"""Scenario Generation and Execution Manager (RPI-05).

Loads scenario contracts, executes them, and collects expected vs observed.

Authority boundary:
  - No scenario-generated expansion of autonomous Class 1 authority.
  - No treating expected outcomes as validator approval.
  - Active scenario contracts under integration/scenarios/ are never silently modified.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from shared.asset_loader import RpiAssetLoader


class ScenarioRunState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ScenarioResult:
    scenario_id: str
    run_id: str
    state: ScenarioRunState
    expected_outcome: dict
    observed_outcome: dict
    matched: bool
    notes: str = ""
    started_at_ms: Optional[int] = None
    finished_at_ms: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "run_id": self.run_id,
            "state": self.state.value,
            "expected_outcome": self.expected_outcome,
            "observed_outcome": self.observed_outcome,
            "matched": self.matched,
            "notes": self.notes,
            "started_at_ms": self.started_at_ms,
            "finished_at_ms": self.finished_at_ms,
        }

    def to_markdown_row(self) -> str:
        status = "✅" if self.matched else "❌"
        return (
            f"| {self.scenario_id} | "
            f"{self.expected_outcome.get('route_class', '—')} | "
            f"{self.observed_outcome.get('route_class', '—')} | "
            f"{status} |"
        )


class ScenarioManager:
    """Loads and executes scenario contracts.

    execute_scenario() accepts an observer callable that should return the
    actual observed outcome dict.  This keeps the manager decoupled from
    the MQTT/network layer for testing.
    """

    def __init__(self, asset_loader: Optional[RpiAssetLoader] = None) -> None:
        self._loader = asset_loader or RpiAssetLoader()
        self._results: list[ScenarioResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_scenario(self, filename: str) -> dict:
        """Load a scenario contract by filename from integration/scenarios/."""
        return self._loader.load_scenario(filename)

    def list_scenario_files(self) -> list[str]:
        return self._loader.list_scenarios()

    def execute_scenario(
        self,
        scenario: dict,
        observed_outcome: dict,
        run_id: Optional[str] = None,
        notes: str = "",
    ) -> ScenarioResult:
        """Record an execution result for a scenario.

        The caller is responsible for obtaining observed_outcome (e.g. via
        MQTT observation or mock).  This manager compares it against
        scenario['expected_outcomes'] and records the result.
        """
        rid = run_id or str(uuid.uuid4())
        expected = scenario.get("expected_outcomes", {})
        now = int(time.time() * 1000)

        matched = self._compare_outcomes(expected, observed_outcome)
        state = ScenarioRunState.PASSED if matched else ScenarioRunState.FAILED

        result = ScenarioResult(
            scenario_id=scenario.get("scenario_id", "unknown"),
            run_id=rid,
            state=state,
            expected_outcome=expected,
            observed_outcome=observed_outcome,
            matched=matched,
            notes=notes,
            started_at_ms=now,
            finished_at_ms=now,
        )
        self._results.append(result)
        return result

    def get_results(self) -> list[ScenarioResult]:
        return list(self._results)

    def export_json_report(self) -> str:
        return json.dumps(
            [r.to_dict() for r in self._results], indent=2
        )

    def export_markdown_report(self) -> str:
        lines = [
            "# Scenario Execution Report",
            "",
            f"Total: {len(self._results)}  ",
            f"Passed: {sum(1 for r in self._results if r.matched)}  ",
            f"Failed: {sum(1 for r in self._results if not r.matched)}",
            "",
            "| Scenario | Expected Route | Observed Route | Result |",
            "|----------|---------------|----------------|--------|",
        ]
        for r in self._results:
            lines.append(r.to_markdown_row())
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compare_outcomes(expected: dict, observed: dict) -> bool:
        """Check that all keys in expected match observed.

        Keys not present in expected are ignored in observed.
        """
        for key, exp_val in expected.items():
            if key not in observed:
                return False
            if observed[key] != exp_val:
                return False
        return True
