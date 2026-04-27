"""Experiment Manager (RPI-01).

Manages paper-oriented experiment batch runs.

Authority boundary:
  - No policy decision authority.
  - No direct actuator dispatch.
  - No silent modification of canonical assets.
  - Asset checksums are recorded for reproducibility, not used to alter policy.
"""

import hashlib
import json
import platform
import time
import uuid
from pathlib import Path
from typing import Optional

from experiment_manager.models import (
    AssetChecksum,
    ExperimentFamily,
    ExperimentRun,
    RunParameters,
    RunState,
)
from shared.asset_loader import RpiAssetLoader

_CANONICAL_ASSETS = [
    "common/policies/policy_table.json",
    "common/policies/low_risk_actions.json",
    "common/policies/fault_injection_rules.json",
    "common/schemas/context_schema.json",
    "common/schemas/candidate_action_schema.json",
    "common/schemas/validator_output_schema.json",
    "common/schemas/class2_notification_payload_schema.json",
]


class ExperimentManager:
    """Manages experiment batch runs.

    Usage:
        mgr = ExperimentManager()
        run = mgr.create_run(RunParameters(...))
        mgr.start_run(run)
        mgr.record_trial(run, {"scenario_id": "SCN_CLASS1_BASELINE", "outcome": "CLASS_1"})
        mgr.complete_run(run)
    """

    def __init__(self, asset_loader: Optional[RpiAssetLoader] = None) -> None:
        self._loader = asset_loader or RpiAssetLoader()
        self._runs: dict[str, ExperimentRun] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_run(
        self,
        parameters: RunParameters,
        run_id: Optional[str] = None,
    ) -> ExperimentRun:
        """Create a new experiment run in PENDING state."""
        rid = run_id or str(uuid.uuid4())
        run = ExperimentRun(
            run_id=rid,
            parameters=parameters,
            state=RunState.PENDING,
            started_at_ms=None,
            finished_at_ms=None,
            host_info=self._collect_host_info(),
        )
        self._runs[rid] = run
        return run

    def start_run(self, run: ExperimentRun) -> None:
        """Transition run to RUNNING; record asset checksums."""
        run.state = RunState.RUNNING
        run.started_at_ms = int(time.time() * 1000)
        run.asset_checksums = self._checksum_assets()

    def pause_run(self, run: ExperimentRun) -> None:
        if run.state == RunState.RUNNING:
            run.state = RunState.PAUSED

    def resume_run(self, run: ExperimentRun) -> None:
        if run.state == RunState.PAUSED:
            run.state = RunState.RUNNING

    def complete_run(self, run: ExperimentRun) -> None:
        run.state = RunState.COMPLETED
        run.finished_at_ms = int(time.time() * 1000)

    def fail_run(self, run: ExperimentRun, error: str) -> None:
        run.state = RunState.FAILED
        run.finished_at_ms = int(time.time() * 1000)
        run.error_message = error

    def abort_run(self, run: ExperimentRun) -> None:
        run.state = RunState.ABORTED
        run.finished_at_ms = int(time.time() * 1000)

    def record_trial(self, run: ExperimentRun, trial_result: dict) -> None:
        """Append a trial result dict to the run."""
        run.trial_results.append({
            **trial_result,
            "trial_index": len(run.trial_results),
            "recorded_at_ms": int(time.time() * 1000),
        })

    def get_run(self, run_id: str) -> Optional[ExperimentRun]:
        return self._runs.get(run_id)

    def list_runs(self) -> list[ExperimentRun]:
        return list(self._runs.values())

    def list_runs_by_family(self, family: ExperimentFamily) -> list[ExperimentRun]:
        return [r for r in self._runs.values()
                if r.parameters.experiment_family == family]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _checksum_assets(self) -> list[AssetChecksum]:
        checksums = []
        for rel in _CANONICAL_ASSETS:
            full = self._loader.repo_root / rel
            try:
                data = full.read_bytes()
                h = hashlib.sha256(data).hexdigest()
                checksums.append(AssetChecksum(asset_path=rel, checksum=h))
            except FileNotFoundError:
                checksums.append(AssetChecksum(asset_path=rel, checksum="FILE_NOT_FOUND"))
        return checksums

    @staticmethod
    def _collect_host_info() -> dict:
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "node": platform.node(),
        }
