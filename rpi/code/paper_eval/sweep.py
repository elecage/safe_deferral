"""Paper-eval matrix sweep orchestrator (doc 13 Phase 1).

Reads a matrix file (e.g. integration/paper_eval/matrix_v1.json), validates
each cell's scenarios carry the required comparison_conditions[] tag, then
for each cell creates a package_run, fires N trials round-robin across the
cell's scenarios, polls until completion, and writes a manifest with each
cell's run_id + a metrics snapshot.

Boundary: this module ONLY calls the existing dashboard HTTP endpoints
(POST /package_runs, POST /package_runs/{id}/trial, GET /package_runs/{id},
GET /package_runs/{id}/metrics, GET /nodes). No bypass of the runner,
validator, or dispatcher. Reproducibility anchors (matrix_file_sha,
scenarios_dir_sha, policy_table_sha) are filled in by the orchestrator at
sweep start so the resulting digest can be regenerated from the same git
commit set.

Failure modes:
- Cell scenario tag missing → orchestrator refuses to run the cell, prints
  which scenario failed validation, continues to the next cell.
- Run never completes (per-trial timeout exceeded) → orchestrator records
  partial result with `incomplete: true` in the manifest.
- Dashboard unreachable → orchestrator exits with non-zero before any
  matrix progress.

Out of scope for Phase 1:
- Concurrent cells (sequential only).
- Resume / idempotency (operator restarts on failure).
- Statistical inference (Phase 2 aggregator handles descriptive stats only).
- Live progress UI (Phase 4 candidate).
"""

import argparse
import json
import logging
import pathlib
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import requests


log = logging.getLogger("paper_eval.sweep")


# Source of truth: rpi/code/experiment_package/definitions.py PackageId.A.
# Mirrored here so the sweep can reject typos before hitting the dashboard.
_KNOWN_COMPARISON_CONDITIONS = frozenset({
    "direct_mapping", "rule_only", "llm_assisted",
    "class2_static_only", "class2_llm_assisted",
    "class2_scan_source_order", "class2_scan_deterministic",
    "class2_direct_select_input", "class2_scanning_input",
})

_DEFAULT_DASHBOARD_URL = "http://localhost:8000"
_DEFAULT_POLL_INTERVAL_S = 2.0
_DEFAULT_TRIAL_TIMEOUT_S = 600.0


# ---------------------------------------------------------------------------
# Progress events (Phase 4 enabler — emitted by Sweeper.run when a callback
# is supplied; CLI usage ignores them by default)
# ---------------------------------------------------------------------------

@dataclass
class SweepProgressEvent:
    """One observable transition during a sweep. Consumers (dashboard
    SweepRunner, CLI verbose mode) treat these as append-only journal
    entries — never mutate fields after emit. event_type values:
        sweep_started, cell_started, cell_skipped, cell_progress,
        cell_completed, sweep_completed.
    """

    event_type: str
    cell_id: Optional[str] = None
    cell_index: Optional[int] = None         # 0-based; only set on cell_*
    total_cells: Optional[int] = None
    completed_trials: Optional[int] = None
    requested_trials: Optional[int] = None
    skip_reason: Optional[str] = None
    incomplete: Optional[bool] = None
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))


class SweepCancelled(RuntimeError):
    """Raised inside Sweeper.run() when cancel_check() returns True. The
    caller (CLI / SweepRunner) catches and finalises a partial manifest."""
    pass


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Cell:
    """One matrix cell. Mirrors the JSON shape in matrix_v1.json."""

    cell_id: str
    description: str
    comparison_condition: Optional[str]   # None = baseline / policy default
    scenarios: list                        # list[str] — scenario filenames under integration/scenarios/
    trials_per_cell: int
    expected_route_class: str
    expected_validation: str
    policy_overrides: Optional[dict] = None  # _policy_overrides — operator must apply before sweep


@dataclass
class MatrixSpec:
    """Parsed matrix file."""

    matrix_version: str
    matrix_description: str
    package_id: str
    trials_per_cell_default: int
    cells: list   # list[Cell]
    raw_anchor_commits: dict


@dataclass
class CellRunResult:
    """One cell's outcome — what the manifest records per cell."""

    cell_id: str
    comparison_condition: Optional[str]
    run_id: Optional[str]                 # None when cell was skipped pre-creation
    requested_trials: int
    completed_trials: int
    incomplete: bool                       # True if any trial timed out / never completed
    skipped: bool                          # True if validation refused the cell
    skip_reason: Optional[str]
    metrics_snapshot: Optional[dict]
    started_at_ms: int
    finished_at_ms: int
    # Phase 2 enabler: raw trial dicts from GET /package_runs/{run_id} captured
    # at sweep finish time. Lets the cross-run aggregator (Phase 2) work fully
    # offline from the sweep manifest — no need to keep the dashboard alive
    # between sweep finish and digest export.
    trials_snapshot: Optional[list] = None
    # Cell-level scenarios + expectations carried into the manifest so the
    # aggregator can reason about them without re-loading the matrix file.
    scenarios: list = field(default_factory=list)
    expected_route_class: Optional[str] = None
    expected_validation: Optional[str] = None


@dataclass
class SweepResult:
    """Output of Sweeper.run() — what gets serialised to sweep_manifest.json."""

    matrix_version: str
    matrix_path: str
    output_dir: str
    dashboard_url: str
    anchor_commits: dict
    started_at_ms: int
    finished_at_ms: int
    cells: list = field(default_factory=list)   # list[CellRunResult]

    def to_dict(self) -> dict:
        return {
            "matrix_version": self.matrix_version,
            "matrix_path": self.matrix_path,
            "output_dir": self.output_dir,
            "dashboard_url": self.dashboard_url,
            "anchor_commits": self.anchor_commits,
            "started_at_ms": self.started_at_ms,
            "finished_at_ms": self.finished_at_ms,
            "cells": [
                {
                    "cell_id": c.cell_id,
                    "comparison_condition": c.comparison_condition,
                    "run_id": c.run_id,
                    "requested_trials": c.requested_trials,
                    "completed_trials": c.completed_trials,
                    "incomplete": c.incomplete,
                    "skipped": c.skipped,
                    "skip_reason": c.skip_reason,
                    "metrics_snapshot": c.metrics_snapshot,
                    "trials_snapshot": c.trials_snapshot,
                    "scenarios": c.scenarios,
                    "expected_route_class": c.expected_route_class,
                    "expected_validation": c.expected_validation,
                    "started_at_ms": c.started_at_ms,
                    "finished_at_ms": c.finished_at_ms,
                }
                for c in self.cells
            ],
        }


# ---------------------------------------------------------------------------
# Matrix loading + validation
# ---------------------------------------------------------------------------

def load_matrix(matrix_path: pathlib.Path,
                scenarios_dir: pathlib.Path) -> MatrixSpec:
    """Load a matrix file, validate its structural shape, and return MatrixSpec.

    Validation done here (cheap, structural):
    - top-level required fields present
    - each cell's comparison_condition is None OR in the known enum
    - each cell's scenarios all exist in scenarios_dir
    - each cell's trials_per_cell is a positive integer

    Validation NOT done here (deferred to runtime):
    - whether each scenario carries the comparison_conditions[] tag matching
      the cell's condition — requires reading scenario files; done by
      Sweeper.validate_cell()
    """
    data = json.loads(matrix_path.read_text(encoding="utf-8"))
    required = (
        "matrix_version", "matrix_description", "package_id",
        "trials_per_cell_default", "cells",
    )
    for k in required:
        if k not in data:
            raise ValueError(f"matrix {matrix_path} missing required field {k!r}")

    cells = []
    for raw in data["cells"]:
        cc = raw.get("comparison_condition")
        if cc is not None and cc not in _KNOWN_COMPARISON_CONDITIONS:
            raise ValueError(
                f"matrix cell {raw.get('cell_id')!r} has unknown "
                f"comparison_condition={cc!r}"
            )
        scenarios = list(raw.get("scenarios", []))
        for s in scenarios:
            if not (scenarios_dir / s).exists():
                raise ValueError(
                    f"matrix cell {raw.get('cell_id')!r} references missing "
                    f"scenario {s!r} in {scenarios_dir}"
                )
        trials = int(raw.get("trials_per_cell", data["trials_per_cell_default"]))
        if trials < 1:
            raise ValueError(
                f"matrix cell {raw.get('cell_id')!r} has trials_per_cell={trials}; "
                "must be ≥ 1"
            )
        cells.append(Cell(
            cell_id=raw["cell_id"],
            description=raw.get("description", ""),
            comparison_condition=cc,
            scenarios=scenarios,
            trials_per_cell=trials,
            expected_route_class=raw.get("expected_route_class", "CLASS_1"),
            expected_validation=raw.get("expected_validation", "approved"),
            policy_overrides=raw.get("_policy_overrides"),
        ))
    return MatrixSpec(
        matrix_version=data["matrix_version"],
        matrix_description=data.get("matrix_description", ""),
        package_id=data.get("package_id", "A"),
        trials_per_cell_default=int(data["trials_per_cell_default"]),
        cells=cells,
        raw_anchor_commits=dict(data.get("anchor_commits", {})),
    )


def resolve_anchor_commits(repo_root: pathlib.Path,
                           matrix_path: pathlib.Path) -> dict:
    """Look up the git SHA for the matrix file, scenarios dir, and
    policy_table.json so the manifest is reproducible. Returns a dict with
    None values for any path that fails resolution (e.g. not under git)."""

    def _sha(path: pathlib.Path) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", f"HEAD:{path}"],
                cwd=repo_root, capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    return {
        "matrix_file_sha": _sha(matrix_path.relative_to(repo_root)),
        "scenarios_dir_sha": _sha(pathlib.Path("integration/scenarios")),
        "policy_table_sha": _sha(pathlib.Path("common/policies/policy_table.json")),
    }


# ---------------------------------------------------------------------------
# Dashboard HTTP client
# ---------------------------------------------------------------------------

class DashboardClient:
    """Thin requests-based wrapper around the dashboard's HTTP API.

    Only the endpoints the sweep needs are exposed. Each method raises
    requests.RequestException on transport errors (caller decides how to
    handle); 4xx/5xx HTTP responses raise via raise_for_status() so callers
    can catch HTTPError.
    """

    def __init__(self, base_url: str, timeout_s: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def health(self) -> dict:
        r = requests.get(self._url("/health"), timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def list_nodes(self) -> list:
        r = requests.get(self._url("/nodes"), timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def create_package_run(self, package_id: str, scenario_ids: list,
                           trial_count: int,
                           comparison_condition: Optional[str]) -> dict:
        body = {
            "package_id": package_id,
            "scenario_ids": scenario_ids,
            "trial_count": trial_count,
        }
        if comparison_condition is not None:
            body["comparison_condition"] = comparison_condition
        r = requests.post(self._url("/package_runs"), json=body,
                          timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def start_trial(self, run_id: str, node_id: str, scenario_id: str,
                    expected_route_class: str, expected_validation: str,
                    comparison_condition: Optional[str] = None) -> dict:
        body = {
            "node_id": node_id,
            "scenario_id": scenario_id,
            "expected_route_class": expected_route_class,
            "expected_validation": expected_validation,
        }
        if comparison_condition is not None:
            body["comparison_condition"] = comparison_condition
        r = requests.post(self._url(f"/package_runs/{run_id}/trial"),
                          json=body, timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def get_package_run(self, run_id: str) -> dict:
        r = requests.get(self._url(f"/package_runs/{run_id}"),
                         timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def get_package_run_metrics(self, run_id: str) -> dict:
        r = requests.get(self._url(f"/package_runs/{run_id}/metrics"),
                         timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------------------
# Sweeper
# ---------------------------------------------------------------------------

def _now_ms() -> int:
    return int(time.time() * 1000)


def _validate_cell_scenario_tags(cell: Cell,
                                 scenarios_dir: pathlib.Path) -> Optional[str]:
    """Return a human-readable error string if any of the cell's scenarios
    fails to declare the cell's comparison_condition in its
    comparison_conditions[] tag (P2.6). Returns None if all scenarios OK
    OR if the cell has no condition (BASELINE)."""
    if cell.comparison_condition is None:
        return None
    for filename in cell.scenarios:
        path = scenarios_dir / filename
        try:
            scenario = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return f"failed to read scenario {filename}: {exc}"
        tags = scenario.get("comparison_conditions") or []
        if cell.comparison_condition not in tags:
            return (
                f"scenario {filename} does not tag comparison_condition="
                f"{cell.comparison_condition!r} in its comparison_conditions[]; "
                f"actual tags: {tags!r}"
            )
    return None


def _validate_cell_policy_overrides(cell: Cell,
                                    effective_policy: Optional[dict]) -> Optional[str]:
    """Return a human-readable error string if the cell declares
    `_policy_overrides` (e.g. {class2_multi_turn_enabled: true}) that the
    currently-loaded canonical policy_table.json does not satisfy.

    Why this matters: matrix_v1's MULTI_TURN cells require the multi-turn
    flag to be on at deployment time. Without this check the orchestrator
    silently runs them via the default direct-select path and the digest
    looks like a valid multi-turn measurement when it is not (Phase C
    2026-05-03 archive shows refinement_history present in 0/360 trials —
    proof that the previous unguarded behaviour mislabelled cells).

    Returns None when (a) the cell has no overrides, (b) the orchestrator
    has no effective_policy to check against (defensive — never silently
    runs in that case; caller should construct effective_policy = {} to
    mean 'enforce against empty defaults' or pass None to mean 'no
    enforcement available').
    """
    overrides = cell.policy_overrides or {}
    if not overrides:
        return None
    if effective_policy is None:
        # Defensive: no policy snapshot means we can't verify. Skip with
        # a clear reason rather than risk corrupting paper-eval data.
        return (
            "policy_overrides declared but no effective policy snapshot "
            "available — orchestrator cannot verify cell can run safely"
        )
    gc = effective_policy.get("global_constraints", {}) or {}
    mismatches = []
    for key, required in overrides.items():
        actual = gc.get(key)
        if actual != required:
            mismatches.append(
                f"{key}: required={required!r} actual={actual!r}"
            )
    if mismatches:
        return (
            "policy mismatch — cell requires overrides not present in "
            f"current common/policies/policy_table.json: {'; '.join(mismatches)}. "
            "Flip the policy flag(s) at deployment and re-run."
        )
    return None


def _load_effective_policy(repo_root: pathlib.Path) -> Optional[dict]:
    """Load common/policies/policy_table.json from the repo root. Returns
    None on failure so the orchestrator can fall back to a defensive skip
    rather than crashing."""
    policy_path = repo_root / "common" / "policies" / "policy_table.json"
    try:
        return json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.warning("Could not load %s: %s", policy_path, exc)
        return None


class Sweeper:
    """Orchestrate a paper-eval matrix sweep against a running dashboard.

    Usage:
        s = Sweeper(matrix_path, scenarios_dir, output_dir,
                    dashboard_url, node_id)
        result = s.run()   # SweepResult
        s.write_manifest(result)

    Or via CLI:
        python -m paper_eval.sweep \\
            --matrix integration/paper_eval/matrix_v1.json \\
            --output runs/$(date +%Y%m%d_%H%M%S)/ \\
            --node-id <virtual-node-id> \\
            --dashboard-url http://localhost:8000
    """

    def __init__(
        self,
        matrix_path: pathlib.Path,
        scenarios_dir: pathlib.Path,
        output_dir: pathlib.Path,
        dashboard_url: str,
        node_id: str,
        repo_root: Optional[pathlib.Path] = None,
        client: Optional[DashboardClient] = None,
        poll_interval_s: float = _DEFAULT_POLL_INTERVAL_S,
        per_trial_timeout_s: float = _DEFAULT_TRIAL_TIMEOUT_S,
        progress_callback: Optional[Callable] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ):
        self.matrix_path = matrix_path
        self.scenarios_dir = scenarios_dir
        self.output_dir = output_dir
        self.dashboard_url = dashboard_url
        self.node_id = node_id
        self.repo_root = repo_root or matrix_path.resolve().parents[2]
        self.client = client or DashboardClient(dashboard_url)
        self.poll_interval_s = poll_interval_s
        self.per_trial_timeout_s = per_trial_timeout_s
        # Phase 4 hooks (additive; both default no-op).
        # progress_callback: receives SweepProgressEvent at lifecycle points
        # so a UI can render live progress without polling individual runs.
        # cancel_check: called between cells AND inside the per-cell poll
        # loop; raises SweepCancelled when it returns True so the runner
        # can finalise a partial manifest.
        self._progress_cb = progress_callback or (lambda _e: None)
        self._cancel_check = cancel_check or (lambda: False)

    def _emit(self, **kw) -> None:
        try:
            self._progress_cb(SweepProgressEvent(**kw))
        except Exception:
            log.exception("progress callback raised; continuing sweep")

    def _check_cancelled(self) -> None:
        if self._cancel_check():
            raise SweepCancelled("sweep cancelled by caller")

    # ------------------------------------------------------------------
    # Top-level sweep
    # ------------------------------------------------------------------

    def run(self) -> SweepResult:
        """Run the full matrix. Returns SweepResult with one CellRunResult
        per cell. Caller should write_manifest(result) afterwards."""
        spec = load_matrix(self.matrix_path, self.scenarios_dir)
        # Refuse to start if dashboard is unreachable — fail fast before
        # half-running the matrix.
        try:
            self.client.health()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Dashboard unreachable at {self.dashboard_url}: {exc}"
            )
        # Verify the requested node exists. If absent, fail fast — the
        # operator has not set up the virtual node the matrix needs.
        nodes = self.client.list_nodes()
        if not any(n.get("node_id") == self.node_id for n in nodes):
            available = [n.get("node_id") for n in nodes]
            raise RuntimeError(
                f"node_id={self.node_id!r} not found on dashboard; "
                f"available nodes: {available}"
            )

        anchors = resolve_anchor_commits(self.repo_root, self.matrix_path)
        # Snapshot the effective policy ONCE per sweep so each cell's
        # _policy_overrides can be checked against it. Phase C 2026-05-03
        # ran 60 trials (2 cells × 30) of supposedly multi-turn behaviour
        # against a policy where class2_multi_turn_enabled=false; the cells
        # silently fell through to the default direct-select path and
        # mislabelled their results. _validate_cell_policy_overrides closes
        # that loophole by skipping any mismatched cell with a clear reason.
        effective_policy = _load_effective_policy(self.repo_root)
        result = SweepResult(
            matrix_version=spec.matrix_version,
            matrix_path=str(self.matrix_path),
            output_dir=str(self.output_dir),
            dashboard_url=self.dashboard_url,
            anchor_commits=anchors,
            started_at_ms=_now_ms(),
            finished_at_ms=0,
        )
        total = len(spec.cells)
        self._emit(event_type="sweep_started", total_cells=total)
        for idx, cell in enumerate(spec.cells):
            self._check_cancelled()
            cell_result = self._run_cell(spec, cell, cell_index=idx,
                                         total_cells=total,
                                         effective_policy=effective_policy)
            result.cells.append(cell_result)
        result.finished_at_ms = _now_ms()
        self._emit(
            event_type="sweep_completed",
            total_cells=total,
            incomplete=any(c.incomplete for c in result.cells),
        )
        return result

    # ------------------------------------------------------------------
    # Per-cell run
    # ------------------------------------------------------------------

    def _run_cell(self, spec: MatrixSpec, cell: Cell,
                  cell_index: Optional[int] = None,
                  total_cells: Optional[int] = None,
                  effective_policy: Optional[dict] = None) -> CellRunResult:
        """Validate, create run, fire trials, poll to completion."""
        started = _now_ms()
        self._emit(
            event_type="cell_started",
            cell_id=cell.cell_id,
            cell_index=cell_index,
            total_cells=total_cells,
            requested_trials=cell.trials_per_cell,
        )
        # Pre-validation 1/2: cell's _policy_overrides must already match the
        # currently-deployed policy (orchestrator does NOT mutate policy itself
        # — that would be a new authority surface). Mismatch → skip with
        # explicit reason. Closes the data-integrity hole that mislabelled
        # Phase C's two MULTI_TURN cells (refinement_history present in 0/60
        # trials despite the cells being labelled multi-turn).
        policy_err = _validate_cell_policy_overrides(cell, effective_policy)
        if policy_err is not None:
            log.warning("Skipping cell %s: %s", cell.cell_id, policy_err)
            self._emit(
                event_type="cell_skipped",
                cell_id=cell.cell_id,
                cell_index=cell_index,
                total_cells=total_cells,
                skip_reason=policy_err,
            )
            return CellRunResult(
                cell_id=cell.cell_id,
                comparison_condition=cell.comparison_condition,
                run_id=None,
                requested_trials=cell.trials_per_cell,
                completed_trials=0,
                incomplete=False,
                skipped=True,
                skip_reason=policy_err,
                metrics_snapshot=None,
                trials_snapshot=None,
                scenarios=list(cell.scenarios),
                expected_route_class=cell.expected_route_class,
                expected_validation=cell.expected_validation,
                started_at_ms=started,
                finished_at_ms=_now_ms(),
            )
        # Pre-validation 2/2: scenario tagging (P2.6 invariant)
        tag_err = _validate_cell_scenario_tags(cell, self.scenarios_dir)
        if tag_err is not None:
            log.warning("Skipping cell %s: %s", cell.cell_id, tag_err)
            self._emit(
                event_type="cell_skipped",
                cell_id=cell.cell_id,
                cell_index=cell_index,
                total_cells=total_cells,
                skip_reason=tag_err,
            )
            return CellRunResult(
                cell_id=cell.cell_id,
                comparison_condition=cell.comparison_condition,
                run_id=None,
                requested_trials=cell.trials_per_cell,
                completed_trials=0,
                incomplete=False,
                skipped=True,
                skip_reason=tag_err,
                metrics_snapshot=None,
                trials_snapshot=None,
                scenarios=list(cell.scenarios),
                expected_route_class=cell.expected_route_class,
                expected_validation=cell.expected_validation,
                started_at_ms=started,
                finished_at_ms=_now_ms(),
            )

        # Create the package run (one run per cell; trials within fan out
        # round-robin across the cell's scenarios).
        run = self.client.create_package_run(
            package_id=spec.package_id,
            scenario_ids=cell.scenarios,
            trial_count=cell.trials_per_cell,
            comparison_condition=cell.comparison_condition,
        )
        run_id = run["run_id"]
        log.info("Cell %s: created run %s (%d trials, condition=%s)",
                 cell.cell_id, run_id, cell.trials_per_cell,
                 cell.comparison_condition)

        # Fire trials SEQUENTIALLY (round-robin across scenarios). Earlier
        # versions fired all trials up front and then polled for completion;
        # that broke the policy router's freshness check (default 3s
        # threshold) because back-pressured trials sat in the MQTT queue
        # while Mac mini processed the first one (LLM call ~2-6s), and by
        # the time a backlogged trial reached the router its trigger
        # timestamp was stale → spurious CLASS_2 routing with C204
        # `sensor_staleness_detected`. The doc 13 §6 design intent was
        # already "sequential cells, sequential trials within cell"; this
        # change brings the implementation in line with it.
        trial_ids = []
        completed = 0
        for i in range(cell.trials_per_cell):
            self._check_cancelled()
            scenario_id = cell.scenarios[i % len(cell.scenarios)]
            try:
                t = self.client.start_trial(
                    run_id=run_id,
                    node_id=self.node_id,
                    scenario_id=scenario_id,
                    expected_route_class=cell.expected_route_class,
                    expected_validation=cell.expected_validation,
                    comparison_condition=cell.comparison_condition,
                )
                trial_id = t["trial_id"]
                trial_ids.append(trial_id)
            except requests.RequestException as exc:
                log.warning(
                    "Cell %s: failed to start trial #%d: %s",
                    cell.cell_id, i + 1, exc,
                )
                continue

            # Wait for THIS trial to reach a non-pending status before
            # firing the next one. Per-trial deadline guards against a
            # stuck trial blocking the rest of the cell forever.
            trial_deadline = time.monotonic() + self.per_trial_timeout_s
            while time.monotonic() < trial_deadline:
                self._check_cancelled()
                try:
                    run_state = self.client.get_package_run(run_id)
                except requests.RequestException as exc:
                    log.warning("Cell %s: polling failed: %s; retrying",
                                cell.cell_id, exc)
                    time.sleep(self.poll_interval_s)
                    continue
                trials = run_state.get("trials", [])
                this = next((tt for tt in trials
                             if tt.get("trial_id") == trial_id), None)
                if this and this.get("status") not in (None, "pending"):
                    break
                time.sleep(self.poll_interval_s)

            # Recompute completed count + emit progress every trial.
            try:
                run_state = self.client.get_package_run(run_id)
                trials = run_state.get("trials", [])
                completed = sum(
                    1 for tt in trials
                    if tt.get("status") not in (None, "pending")
                )
            except requests.RequestException:
                pass
            self._emit(
                event_type="cell_progress",
                cell_id=cell.cell_id,
                cell_index=cell_index,
                total_cells=total_cells,
                completed_trials=completed,
                requested_trials=cell.trials_per_cell,
            )

        incomplete = completed < len(trial_ids)
        if incomplete:
            log.warning(
                "Cell %s: only %d/%d trials reached terminal status",
                cell.cell_id, completed, len(trial_ids),
            )

        # Snapshot metrics
        metrics_snapshot = None
        try:
            metrics_snapshot = self.client.get_package_run_metrics(run_id)
        except requests.RequestException as exc:
            log.warning("Cell %s: metrics fetch failed: %s",
                        cell.cell_id, exc)

        # Snapshot raw trials so the Phase 2 aggregator can work fully offline
        # from this manifest (no live dashboard required after sweep finishes).
        trials_snapshot = None
        try:
            run_state = self.client.get_package_run(run_id)
            trials_snapshot = run_state.get("trials")
        except requests.RequestException as exc:
            log.warning("Cell %s: trials snapshot fetch failed: %s",
                        cell.cell_id, exc)

        cell_result = CellRunResult(
            cell_id=cell.cell_id,
            comparison_condition=cell.comparison_condition,
            run_id=run_id,
            requested_trials=cell.trials_per_cell,
            completed_trials=completed,
            incomplete=incomplete,
            skipped=False,
            skip_reason=None,
            metrics_snapshot=metrics_snapshot,
            trials_snapshot=trials_snapshot,
            scenarios=list(cell.scenarios),
            expected_route_class=cell.expected_route_class,
            expected_validation=cell.expected_validation,
            started_at_ms=started,
            finished_at_ms=_now_ms(),
        )
        self._emit(
            event_type="cell_completed",
            cell_id=cell.cell_id,
            cell_index=cell_index,
            total_cells=total_cells,
            completed_trials=completed,
            requested_trials=cell.trials_per_cell,
            incomplete=incomplete,
        )
        return cell_result

    # ------------------------------------------------------------------
    # Manifest writing
    # ------------------------------------------------------------------

    def write_manifest(self, result: SweepResult) -> pathlib.Path:
        """Write sweep_manifest.json under output_dir. Returns the path."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.output_dir / "sweep_manifest.json"
        manifest_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return manifest_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="paper_eval.sweep",
        description="Run a paper-eval matrix sweep against the dashboard.",
    )
    p.add_argument("--matrix", required=True, type=pathlib.Path,
                   help="Path to matrix file (e.g. integration/paper_eval/matrix_v1.json)")
    p.add_argument("--output", required=True, type=pathlib.Path,
                   help="Output directory for sweep_manifest.json")
    p.add_argument("--node-id", required=True,
                   help="Virtual node_id to run trials against (operator-managed)")
    p.add_argument("--scenarios-dir", default="integration/scenarios",
                   type=pathlib.Path,
                   help="Scenarios directory (default: integration/scenarios)")
    p.add_argument("--dashboard-url", default=_DEFAULT_DASHBOARD_URL,
                   help=f"Dashboard URL (default: {_DEFAULT_DASHBOARD_URL})")
    p.add_argument("--poll-interval", type=float,
                   default=_DEFAULT_POLL_INTERVAL_S,
                   help=f"Poll interval in seconds (default: {_DEFAULT_POLL_INTERVAL_S})")
    p.add_argument("--per-trial-timeout", type=float,
                   default=_DEFAULT_TRIAL_TIMEOUT_S,
                   help=f"Per-trial timeout in seconds (default: {_DEFAULT_TRIAL_TIMEOUT_S})")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Enable INFO logging")
    return p


def main(argv: Optional[list] = None) -> int:
    parser = _build_argparser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    sweeper = Sweeper(
        matrix_path=args.matrix.resolve(),
        scenarios_dir=args.scenarios_dir.resolve(),
        output_dir=args.output.resolve(),
        dashboard_url=args.dashboard_url,
        node_id=args.node_id,
        poll_interval_s=args.poll_interval,
        per_trial_timeout_s=args.per_trial_timeout,
    )
    try:
        result = sweeper.run()
    except RuntimeError as exc:
        print(f"sweep failed: {exc}", file=sys.stderr)
        return 1
    manifest_path = sweeper.write_manifest(result)
    n_cells = len(result.cells)
    n_skipped = sum(1 for c in result.cells if c.skipped)
    n_incomplete = sum(1 for c in result.cells if c.incomplete)
    print(
        f"sweep finished: {n_cells} cells, "
        f"{n_skipped} skipped, {n_incomplete} incomplete",
        file=sys.stderr,
    )
    print(str(manifest_path))
    return 0 if n_skipped == 0 and n_incomplete == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
