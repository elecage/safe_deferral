"""Background sweep runner for the dashboard (doc 13 Phase 4 MVP).

Wraps `paper_eval.sweep.Sweeper` + `paper_eval.aggregator.aggregate` +
`paper_eval.digest.write_digest` in a background thread so the dashboard
can show live progress and serve the resulting artifacts via HTTP.

Single-slot model — only one sweep can run at a time. Subsequent
start_sweep() calls return an error until the current sweep finishes
(or is cancelled). Rationale: matches operational reality (one operator,
one Mac mini stack) and avoids the complexity of multi-tenant
scheduling for a v1 UI.

Boundary: this module is read-only with respect to the dashboard's
HTTP API surface — it calls the same `POST /package_runs`,
`POST /package_runs/{id}/trial`, `GET /package_runs/{id}` endpoints
operators use interactively. No bypass of runner / validator / dispatcher.
"""

import logging
import pathlib
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from paper_eval.aggregator import aggregate
from paper_eval.digest import write_digest
from paper_eval.sweep import (
    DashboardClient,
    SweepCancelled,
    Sweeper,
    SweepProgressEvent,
)


log = logging.getLogger("paper_eval.sweep_runner")


# Lifecycle states that show up in the dashboard.
STATUS_IDLE = "idle"               # no sweep ever started, or last one fully finalised
STATUS_RUNNING = "running"
STATUS_CANCELLING = "cancelling"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"
STATUS_FAILED = "failed"


@dataclass
class CellProgress:
    """Per-cell snapshot the UI renders. Updated in place from progress
    callback events; never replaced wholesale so the UI's incremental
    rendering stays cheap."""

    cell_id: str
    cell_index: int
    requested_trials: int
    status: str = "pending"           # "pending" | "running" | "completed" | "skipped"
    completed_trials: int = 0
    incomplete: bool = False
    skip_reason: Optional[str] = None


@dataclass
class SweepState:
    """Public snapshot of the runner. Returned (as dict) from
    GET /paper_eval/sweeps/current. Mutated under runner._lock."""

    sweep_id: Optional[str] = None
    matrix_path: Optional[str] = None
    status: str = STATUS_IDLE
    started_at_ms: Optional[int] = None
    finished_at_ms: Optional[int] = None
    error: Optional[str] = None
    cells: list = field(default_factory=list)   # list[CellProgress]
    total_cells: Optional[int] = None
    # Output artifact paths populated after sweep + aggregate + digest finish.
    manifest_path: Optional[str] = None
    aggregated_path: Optional[str] = None
    digest_csv_path: Optional[str] = None
    digest_md_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "sweep_id": self.sweep_id,
            "matrix_path": self.matrix_path,
            "status": self.status,
            "started_at_ms": self.started_at_ms,
            "finished_at_ms": self.finished_at_ms,
            "error": self.error,
            "total_cells": self.total_cells,
            "cells": [
                {
                    "cell_id": c.cell_id,
                    "cell_index": c.cell_index,
                    "requested_trials": c.requested_trials,
                    "status": c.status,
                    "completed_trials": c.completed_trials,
                    "incomplete": c.incomplete,
                    "skip_reason": c.skip_reason,
                }
                for c in self.cells
            ],
            "manifest_path": self.manifest_path,
            "aggregated_path": self.aggregated_path,
            "digest_csv_path": self.digest_csv_path,
            "digest_md_path": self.digest_md_path,
        }


class SweepRunner:
    """Single-slot background runner. Designed to be instantiated once
    by the dashboard at startup and reused across requests.

    Thread safety: state mutations are guarded by self._lock so the HTTP
    handler reading get_state() never sees a torn dict. The worker
    thread writes; the HTTP handler only reads.
    """

    def __init__(
        self,
        repo_root: pathlib.Path,
        scenarios_dir: pathlib.Path,
        runs_root: pathlib.Path,
        dashboard_url: str = "http://localhost:8000",
        sweeper_factory=None,
    ):
        self._repo_root = repo_root
        self._scenarios_dir = scenarios_dir
        self._runs_root = runs_root
        self._dashboard_url = dashboard_url
        # Injectable for tests — production builds a real Sweeper around a
        # real DashboardClient. Tests substitute a fake.
        self._sweeper_factory = sweeper_factory or self._default_sweeper_factory

        self._lock = threading.Lock()
        self._state = SweepState()
        self._cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_state(self) -> dict:
        with self._lock:
            return self._state.to_dict()

    def start(
        self,
        matrix_path: pathlib.Path,
        node_id: str,
        per_trial_timeout_s: float = 600.0,
        poll_interval_s: float = 2.0,
    ) -> dict:
        """Spawn the sweep worker. Returns the new state on success.
        Raises RuntimeError if a sweep is already running."""
        with self._lock:
            if self._state.status in (STATUS_RUNNING, STATUS_CANCELLING):
                raise RuntimeError(
                    f"sweep already in progress (status={self._state.status})"
                )
            sweep_id = uuid.uuid4().hex[:12]
            output_dir = self._runs_root / sweep_id
            self._state = SweepState(
                sweep_id=sweep_id,
                matrix_path=str(matrix_path),
                status=STATUS_RUNNING,
                started_at_ms=int(time.time() * 1000),
            )
            self._cancel_event.clear()
        # Spawn outside the lock so handler returns immediately.
        self._thread = threading.Thread(
            target=self._run_worker,
            args=(matrix_path, node_id, output_dir,
                  per_trial_timeout_s, poll_interval_s),
            name=f"sweep-runner-{sweep_id}",
            daemon=True,
        )
        self._thread.start()
        return self.get_state()

    def cancel(self) -> dict:
        """Signal the worker to stop at the next safe point. Returns the
        post-signal state. No-op if no sweep is running."""
        with self._lock:
            if self._state.status != STATUS_RUNNING:
                return self._state.to_dict()
            self._state.status = STATUS_CANCELLING
        self._cancel_event.set()
        return self.get_state()

    def join(self, timeout: Optional[float] = None) -> None:
        """Test helper — wait for the worker thread to finish.
        Mirrors threading.Thread.join's parameter name (`timeout`)."""
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    # ------------------------------------------------------------------
    # Worker
    # ------------------------------------------------------------------

    def _default_sweeper_factory(self, matrix_path, output_dir, node_id,
                                 per_trial_timeout_s, poll_interval_s,
                                 progress_callback, cancel_check):
        return Sweeper(
            matrix_path=matrix_path,
            scenarios_dir=self._scenarios_dir,
            output_dir=output_dir,
            dashboard_url=self._dashboard_url,
            node_id=node_id,
            repo_root=self._repo_root,
            client=DashboardClient(self._dashboard_url),
            poll_interval_s=poll_interval_s,
            per_trial_timeout_s=per_trial_timeout_s,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )

    def _run_worker(self, matrix_path, node_id, output_dir,
                    per_trial_timeout_s, poll_interval_s):
        """Run sweep → aggregate → digest. All exceptions captured into
        state.error so the UI can show them."""
        sweeper = self._sweeper_factory(
            matrix_path=matrix_path,
            output_dir=output_dir,
            node_id=node_id,
            per_trial_timeout_s=per_trial_timeout_s,
            poll_interval_s=poll_interval_s,
            progress_callback=self._on_event,
            cancel_check=self._cancel_event.is_set,
        )
        try:
            result = sweeper.run()
            manifest_path = sweeper.write_manifest(result)
            with self._lock:
                self._state.manifest_path = str(manifest_path)
            # Aggregate + digest. Both are pure functions over the manifest;
            # any exception short-circuits to status=failed.
            agg = aggregate(result.to_dict())
            agg_path = output_dir / "aggregated_matrix.json"
            agg_path.write_text(
                __import__("json").dumps(agg.to_dict(), indent=2,
                                          ensure_ascii=False),
                encoding="utf-8",
            )
            digest_dir = output_dir / "digest"
            csv_path, md_path = write_digest(agg.to_dict(), digest_dir)
            with self._lock:
                self._state.aggregated_path = str(agg_path)
                self._state.digest_csv_path = str(csv_path)
                self._state.digest_md_path = str(md_path)
                self._state.finished_at_ms = int(time.time() * 1000)
                self._state.status = STATUS_COMPLETED
        except SweepCancelled:
            log.info("sweep %s cancelled", self._state.sweep_id)
            with self._lock:
                self._state.status = STATUS_CANCELLED
                self._state.finished_at_ms = int(time.time() * 1000)
        except Exception as exc:
            log.exception("sweep %s failed", self._state.sweep_id)
            with self._lock:
                self._state.status = STATUS_FAILED
                self._state.error = f"{type(exc).__name__}: {exc}"
                self._state.finished_at_ms = int(time.time() * 1000)

    # ------------------------------------------------------------------
    # Progress event handling
    # ------------------------------------------------------------------

    def _on_event(self, event: SweepProgressEvent) -> None:
        """Translate Sweeper progress events into SweepState mutations.
        Called from the worker thread; serialised by self._lock so the
        HTTP get_state reader never observes a torn cell list."""
        with self._lock:
            if event.event_type == "sweep_started":
                self._state.total_cells = event.total_cells
                # Pre-allocate cell slots so the UI can render the table
                # immediately (status=pending) before any cell starts.
                # cell_id will be populated by the first cell_started event.
                self._state.cells = []
            elif event.event_type == "cell_started":
                # If pre-allocated slot exists for this cell_index, update
                # it; otherwise append. This keeps cell ordering stable.
                cp = self._find_or_create_cell(event)
                cp.status = "running"
                cp.requested_trials = event.requested_trials or 0
            elif event.event_type == "cell_skipped":
                cp = self._find_or_create_cell(event)
                cp.status = "skipped"
                cp.skip_reason = event.skip_reason
            elif event.event_type == "cell_progress":
                cp = self._find_or_create_cell(event)
                if event.completed_trials is not None:
                    cp.completed_trials = event.completed_trials
                if event.requested_trials is not None:
                    cp.requested_trials = event.requested_trials
            elif event.event_type == "cell_completed":
                cp = self._find_or_create_cell(event)
                cp.status = "completed"
                if event.completed_trials is not None:
                    cp.completed_trials = event.completed_trials
                if event.incomplete is not None:
                    cp.incomplete = event.incomplete
            # sweep_completed handled by the worker (sets status=completed
            # after digest writes).

    def _find_or_create_cell(self, event: SweepProgressEvent) -> CellProgress:
        for c in self._state.cells:
            if c.cell_id == event.cell_id:
                return c
        cp = CellProgress(
            cell_id=event.cell_id or "<?>",
            cell_index=event.cell_index if event.cell_index is not None else len(self._state.cells),
            requested_trials=event.requested_trials or 0,
        )
        self._state.cells.append(cp)
        return cp
