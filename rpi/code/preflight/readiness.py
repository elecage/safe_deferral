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
from typing import Optional, TYPE_CHECKING

from shared.asset_loader import RpiAssetLoader

if TYPE_CHECKING:
    from node_presence.registry import NodePresenceRegistry


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

    Node presence checks (physical ESP32, STM32) are DEGRADED, not BLOCKED:
      - Physical nodes absent → experiments run in virtual-only mode (paper-valid
        for software pipeline metrics; label clearly in results).
      - STM32 absent → GPIO end-to-end latency unavailable; software MQTT
        latency is still valid per required_experiments.md §6.5 ("바람직하다").
    """

    def __init__(
        self,
        asset_loader: Optional[RpiAssetLoader] = None,
        node_presence_registry: Optional["NodePresenceRegistry"] = None,
    ) -> None:
        self._loader = asset_loader or RpiAssetLoader()
        self._presence = node_presence_registry
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
        self.add_check(
            "physical_nodes_present",
            "At least one physical ESP32 node is online (DEGRADED if absent — virtual-only mode)",
            required=False,
            check_fn=self._check_physical_nodes,
        )
        self.add_check(
            "stm32_present",
            "STM32 timing node connected via USB-serial (DEGRADED if absent — software latency only)",
            required=False,
            check_fn=self._check_stm32,
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

    def _check_physical_nodes(self):
        if self._presence is None:
            return (
                ReadinessLevel.UNKNOWN,
                "NodePresenceRegistry not injected — cannot check physical nodes",
            )
        physical = self._presence.find_by_source("physical")
        if not physical:
            return (
                ReadinessLevel.DEGRADED,
                "No physical ESP32 nodes online — running in virtual-only mode. "
                "Software pipeline latency metrics remain valid; "
                "label results as virtual-only.",
            )
        node_ids = [n.node_id for n in physical]
        return ReadinessLevel.READY, f"{len(physical)} physical node(s) online: {node_ids}"

    def _check_stm32(self):
        """Check for STM32 timing node via USB-serial device.

        STM32 provides GPIO interrupt-based end-to-end latency measurement.
        Absent → software MQTT latency only (valid per required_experiments.md §6.5).
        """
        import glob
        usb_paths = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
        if not usb_paths:
            return (
                ReadinessLevel.DEGRADED,
                "No USB-serial device found (/dev/ttyUSB*, /dev/ttyACM*). "
                "STM32 GPIO end-to-end latency unavailable; "
                "software MQTT latency (ingest→dispatch) is still paper-valid — "
                "label as 'software pipeline latency'.",
            )
        return ReadinessLevel.READY, f"USB-serial device(s) found: {usb_paths}"
