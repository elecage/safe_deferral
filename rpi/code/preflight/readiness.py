"""Experiment Preflight Readiness Manager (RPI-07).

Evaluates readiness before an experiment run and produces a machine-readable
readiness report with READY / DEGRADED / BLOCKED / UNKNOWN states.

Authority boundary:
  - No automatic policy relaxation when degraded.
  - Blocked state prevents sensitive experiments from running.
  - Readiness reports are observations only — not policy authority.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from shared.asset_loader import RpiAssetLoader


class ReadinessLevel(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"    # some optional checks failed
    BLOCKED = "blocked"      # required checks failed — run must not proceed
    UNKNOWN = "unknown"      # check could not be performed


@dataclass
class ReadinessCheck:
    check_id: str
    description: str
    level: ReadinessLevel
    required: bool            # if True, failure → BLOCKED overall
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "description": self.description,
            "level": self.level.value,
            "required": self.required,
            "detail": self.detail,
        }


@dataclass
class ReadinessReport:
    overall: ReadinessLevel
    generated_at_ms: int
    checks: list[ReadinessCheck] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    authority_note: str = (
        "Preflight readiness report is an experiment-support observation. "
        "It does not relax policy or grant operational authority."
    )

    def to_dict(self) -> dict:
        return {
            "overall": self.overall.value,
            "generated_at_ms": self.generated_at_ms,
            "checks": [c.to_dict() for c in self.checks],
            "blocked_reasons": self.blocked_reasons,
            "authority_note": self.authority_note,
        }


class PreflightManager:
    """Evaluates experiment readiness.

    Checks are registered via add_check().  run_preflight() executes all
    registered checks and returns a ReadinessReport.

    For testing, pass mock check results via add_check() with a fixed level.
    """

    def __init__(self, asset_loader: Optional[RpiAssetLoader] = None) -> None:
        self._loader = asset_loader or RpiAssetLoader()
        self._checks: list[tuple[str, str, bool, callable]] = []
        self._register_default_checks()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_check(
        self,
        check_id: str,
        description: str,
        required: bool,
        check_fn: callable,
    ) -> None:
        """Register a check.  check_fn() returns (ReadinessLevel, detail_str)."""
        self._checks.append((check_id, description, required, check_fn))

    def run_preflight(self) -> ReadinessReport:
        """Execute all registered checks and return a report."""
        now = int(time.time() * 1000)
        check_results: list[ReadinessCheck] = []
        blocked_reasons: list[str] = []
        any_degraded = False

        for check_id, description, required, fn in self._checks:
            try:
                level, detail = fn()
            except Exception as exc:
                level, detail = ReadinessLevel.UNKNOWN, str(exc)

            check_results.append(ReadinessCheck(
                check_id=check_id,
                description=description,
                level=level,
                required=required,
                detail=detail,
            ))
            if level in (ReadinessLevel.BLOCKED, ReadinessLevel.UNKNOWN) and required:
                blocked_reasons.append(f"{check_id}: {detail}")
            elif level == ReadinessLevel.DEGRADED:
                any_degraded = True

        if blocked_reasons:
            overall = ReadinessLevel.BLOCKED
        elif any_degraded:
            overall = ReadinessLevel.DEGRADED
        else:
            overall = ReadinessLevel.READY

        return ReadinessReport(
            overall=overall,
            generated_at_ms=now,
            checks=check_results,
            blocked_reasons=blocked_reasons,
        )

    # ------------------------------------------------------------------
    # Default checks
    # ------------------------------------------------------------------

    def _register_default_checks(self) -> None:
        self.add_check(
            "canonical_assets_present",
            "Canonical policy and schema assets are present",
            required=True,
            check_fn=self._check_canonical_assets,
        )
        self.add_check(
            "scenarios_present",
            "At least one scenario contract is present in integration/scenarios/",
            required=True,
            check_fn=self._check_scenarios_present,
        )

    def _check_canonical_assets(self):
        missing = []
        for rel in [
            "common/policies/policy_table.json",
            "common/policies/low_risk_actions.json",
            "common/schemas/context_schema.json",
        ]:
            if not (self._loader.repo_root / rel).exists():
                missing.append(rel)
        if missing:
            return ReadinessLevel.BLOCKED, f"Missing: {missing}"
        return ReadinessLevel.READY, "all canonical assets present"

    def _check_scenarios_present(self):
        scenarios = self._loader.list_scenarios()
        if not scenarios:
            return ReadinessLevel.BLOCKED, "no scenario contracts found"
        return ReadinessLevel.READY, f"{len(scenarios)} scenario(s) found"
