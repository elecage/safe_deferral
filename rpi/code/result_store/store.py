"""Result Store and Analysis Manager (RPI-02).

Stores experiment results, aggregates summaries, computes metrics,
and exports CSV/JSON/Markdown.

Authority boundary:
  - Analysis output is never operational authority.
  - Scenario contracts are not modified during analysis.
  - Result paths are under integration/ or a configured result area.
"""

import csv
import io
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from experiment_manager.models import ExperimentRun, RunState


@dataclass
class RunSummary:
    run_id: str
    experiment_family: str
    trial_count: int
    completed_trials: int
    state: str
    started_at_ms: Optional[int]
    finished_at_ms: Optional[int]
    metrics: dict = field(default_factory=dict)


class ResultStore:
    """In-memory result store with export helpers.

    For production use, back this with a file-system path under integration/.
    """

    def __init__(self, result_dir: Optional[Path] = None) -> None:
        self._dir = result_dir
        self._runs: dict[str, ExperimentRun] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_run(self, run: ExperimentRun) -> None:
        """Register a run in the store."""
        self._runs[run.run_id] = run
        if self._dir:
            self._persist(run)

    def get_run(self, run_id: str) -> Optional[ExperimentRun]:
        return self._runs.get(run_id)

    def list_summaries(self) -> list[RunSummary]:
        return [self._to_summary(r) for r in self._runs.values()]

    def compute_metrics(self, run_id: str) -> dict:
        """Compute paper-facing metrics for a completed run."""
        run = self._runs.get(run_id)
        if run is None:
            return {}

        trials = run.trial_results
        total = len(trials)
        if total == 0:
            return {"total_trials": 0}

        # Route class distribution
        route_counts: dict[str, int] = {}
        for t in trials:
            rc = t.get("route_class", "unknown")
            route_counts[rc] = route_counts.get(rc, 0) + 1

        # Fault outcome distribution
        fault_outcomes: dict[str, int] = {}
        for t in trials:
            fo = t.get("fault_outcome", "none")
            fault_outcomes[fo] = fault_outcomes.get(fo, 0) + 1

        # Latency stats (ms) if present
        latencies = [t["latency_ms"] for t in trials if "latency_ms" in t]
        latency_stats = {}
        if latencies:
            latency_stats = {
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "mean_ms": sum(latencies) / len(latencies),
            }

        return {
            "total_trials": total,
            "route_class_distribution": route_counts,
            "fault_outcome_distribution": fault_outcomes,
            "latency_stats": latency_stats,
        }

    def export_json(self, run_id: str) -> str:
        """Export a run summary + metrics as JSON string."""
        run = self._runs.get(run_id)
        if run is None:
            return json.dumps({"error": f"run {run_id} not found"})
        return json.dumps({
            "summary": run.to_summary_dict(),
            "metrics": self.compute_metrics(run_id),
            "asset_checksums": [
                {"asset_path": c.asset_path, "checksum": c.checksum}
                for c in run.asset_checksums
            ],
        }, indent=2)

    def export_csv(self, run_id: str) -> str:
        """Export trial results as CSV string."""
        run = self._runs.get(run_id)
        if run is None or not run.trial_results:
            return ""
        buf = io.StringIO()
        fields = sorted({k for t in run.trial_results for k in t.keys()})
        writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for trial in run.trial_results:
            writer.writerow(trial)
        return buf.getvalue()

    def export_markdown(self, run_id: str) -> str:
        """Export a paper-friendly Markdown summary."""
        run = self._runs.get(run_id)
        if run is None:
            return f"# Run {run_id}\n\nNot found.\n"
        summary = run.to_summary_dict()
        metrics = self.compute_metrics(run_id)
        lines = [
            f"# Experiment Run: {run_id}",
            "",
            f"**Family:** {summary['experiment_family']}  ",
            f"**State:** {summary['state']}  ",
            f"**Trials recorded:** {summary['trials_recorded']}  ",
            "",
            "## Metrics",
            "",
        ]
        for k, v in metrics.items():
            lines.append(f"- **{k}:** {v}")
        if run.asset_checksums:
            lines += ["", "## Asset Checksums", ""]
            for c in run.asset_checksums:
                lines.append(f"- `{c.asset_path}`: `{c.checksum[:16]}…`")
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_summary(run: ExperimentRun) -> RunSummary:
        return RunSummary(
            run_id=run.run_id,
            experiment_family=run.parameters.experiment_family.value,
            trial_count=run.parameters.trial_count,
            completed_trials=len(run.trial_results),
            state=run.state.value,
            started_at_ms=run.started_at_ms,
            finished_at_ms=run.finished_at_ms,
        )

    def _persist(self, run: ExperimentRun) -> None:
        if self._dir is None:
            return
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / f"{run.run_id}.json"
        path.write_text(self.export_json(run.run_id))
