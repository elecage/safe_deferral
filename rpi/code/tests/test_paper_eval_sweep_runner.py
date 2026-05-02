"""Tests for the background SweepRunner (doc 13 Phase 4 MVP).

Exercises the runner state machine, single-slot enforcement, cancel
signal propagation, progress event mapping into SweepState.cells, and
end-to-end sweep → aggregate → digest finalisation. Real network never
touched — Sweeper is replaced by a fake via sweeper_factory.
"""

import pathlib
import threading
import time
from unittest.mock import MagicMock

import pytest

from paper_eval.sweep import (
    DashboardClient,
    SweepCancelled,
    SweepProgressEvent,
    SweepResult,
    Sweeper,
)
from paper_eval.sweep_runner import (
    STATUS_CANCELLED,
    STATUS_CANCELLING,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_IDLE,
    STATUS_RUNNING,
    SweepRunner,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_REAL_MATRIX = _REPO_ROOT / "integration" / "paper_eval" / "matrix_v1.json"
_REAL_SCENARIOS = _REPO_ROOT / "integration" / "scenarios"


# ==================================================================
# Fake sweeper helpers
# ==================================================================

class _FakeSweeper:
    """Stand-in for paper_eval.sweep.Sweeper that:
    1. Captures the progress_callback + cancel_check the runner installed.
    2. Synthesises a controllable lifecycle (events + result) so the
       runner-side state machine can be exercised without real HTTP.
    3. Writes a real manifest file to disk so aggregator + digest can
       complete (they're called inline by the runner worker).
    """

    def __init__(self, output_dir: pathlib.Path,
                 progress_callback, cancel_check,
                 cells_meta=None,
                 raise_after_emits=None):
        self.output_dir = output_dir
        self._cb = progress_callback
        self._cancel_check = cancel_check
        # Default to a tiny matrix shape (2 cells × 1 trial each).
        self.cells_meta = cells_meta or [
            {"cell_id": "BASELINE", "trials": 1},
            {"cell_id": "C1_RULE_ONLY", "trials": 1},
        ]
        self.raise_after_emits = raise_after_emits   # int → raise SweepCancelled
        self._emit_count = 0
        self.write_manifest_called = False

    def _maybe_raise(self):
        self._emit_count += 1
        if (self.raise_after_emits is not None
                and self._emit_count >= self.raise_after_emits):
            raise SweepCancelled("test-cancel")

    def run(self) -> SweepResult:
        total = len(self.cells_meta)
        self._cb(SweepProgressEvent(event_type="sweep_started", total_cells=total))
        cells = []
        for i, meta in enumerate(self.cells_meta):
            if self._cancel_check():
                raise SweepCancelled("test-cancel")
            self._cb(SweepProgressEvent(
                event_type="cell_started", cell_id=meta["cell_id"],
                cell_index=i, total_cells=total,
                requested_trials=meta["trials"],
            ))
            self._maybe_raise()
            self._cb(SweepProgressEvent(
                event_type="cell_progress", cell_id=meta["cell_id"],
                cell_index=i, total_cells=total,
                completed_trials=meta["trials"],
                requested_trials=meta["trials"],
            ))
            self._cb(SweepProgressEvent(
                event_type="cell_completed", cell_id=meta["cell_id"],
                cell_index=i, total_cells=total,
                completed_trials=meta["trials"],
                requested_trials=meta["trials"],
                incomplete=False,
            ))
            # Build a complete CellRunResult-shaped dict (matches
            # SweepResult.to_dict() shape so aggregator/digest run cleanly).
            cells.append({
                "cell_id": meta["cell_id"],
                "comparison_condition": None,
                "run_id": f"run-{i}",
                "requested_trials": meta["trials"],
                "completed_trials": meta["trials"],
                "incomplete": False,
                "skipped": False,
                "skip_reason": None,
                "metrics_snapshot": None,
                "trials_snapshot": [
                    {"status": "completed", "pass_": True,
                     "expected_route_class": "CLASS_1",
                     "observed_route_class": "CLASS_1",
                     "latency_ms": 50.0}
                    for _ in range(meta["trials"])
                ],
                "scenarios": [],
                "expected_route_class": "CLASS_1",
                "expected_validation": "approved",
                "started_at_ms": 0,
                "finished_at_ms": 0,
            })
        self._cb(SweepProgressEvent(event_type="sweep_completed",
                                     total_cells=total, incomplete=False))
        # Build a SweepResult-shaped object — to_dict() is what the runner
        # passes to aggregate(), so we shortcut by returning a tiny shim.
        return _FakeSweepResult(cells)

    def write_manifest(self, result):
        self.write_manifest_called = True
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "sweep_manifest.json"
        import json
        path.write_text(json.dumps(result.to_dict(), indent=2),
                        encoding="utf-8")
        return path


class _FakeSweepResult:
    def __init__(self, cells):
        self._cells = cells

    def to_dict(self):
        return {
            "matrix_version": "v1-test",
            "matrix_path": "fake",
            "started_at_ms": 0,
            "finished_at_ms": 0,
            "anchor_commits": {},
            "cells": self._cells,
            "output_dir": "fake",
            "dashboard_url": "fake",
        }


def _make_runner(tmp_path, sweeper_factory_override=None):
    factory = sweeper_factory_override or (
        lambda matrix_path, output_dir, node_id, per_trial_timeout_s,
               poll_interval_s, progress_callback, cancel_check:
            _FakeSweeper(output_dir, progress_callback, cancel_check)
    )
    return SweepRunner(
        repo_root=_REPO_ROOT,
        scenarios_dir=_REAL_SCENARIOS,
        runs_root=tmp_path / "runs",
        sweeper_factory=factory,
    )


# ==================================================================
# Initial state
# ==================================================================

class TestInitialState:
    def test_idle_status_with_no_cells(self, tmp_path):
        r = _make_runner(tmp_path)
        s = r.get_state()
        assert s["status"] == STATUS_IDLE
        assert s["sweep_id"] is None
        assert s["cells"] == []


# ==================================================================
# Single-slot enforcement
# ==================================================================

class TestSingleSlot:
    def test_second_start_raises_while_running(self, tmp_path):
        # Use a sweeper that blocks on an event so we can observe RUNNING.
        block = threading.Event()
        class _BlockingSweeper(_FakeSweeper):
            def run(self):
                block.wait(timeout=2)
                return super().run()
        r = _make_runner(tmp_path,
            sweeper_factory_override=lambda **kw: _BlockingSweeper(
                kw["output_dir"], kw["progress_callback"], kw["cancel_check"],
            ))
        r.start(matrix_path=_REAL_MATRIX, node_id="node-001")
        # Now status is RUNNING — second start must reject.
        with pytest.raises(RuntimeError, match="already in progress"):
            r.start(matrix_path=_REAL_MATRIX, node_id="node-001")
        block.set()
        r.join(timeout=2)


# ==================================================================
# Happy path: end-to-end sweep → aggregate → digest finalisation
# ==================================================================

class TestHappyPath:
    def test_completed_status_with_artifact_paths(self, tmp_path):
        r = _make_runner(tmp_path)
        r.start(matrix_path=_REAL_MATRIX, node_id="node-001")
        r.join(timeout=5)
        s = r.get_state()
        assert s["status"] == STATUS_COMPLETED
        assert s["manifest_path"]
        assert s["aggregated_path"]
        assert s["digest_csv_path"]
        assert s["digest_md_path"]
        # Files actually exist
        for key in ("manifest_path", "aggregated_path",
                    "digest_csv_path", "digest_md_path"):
            assert pathlib.Path(s[key]).exists(), f"{key} missing"

    def test_progress_events_become_cells(self, tmp_path):
        r = _make_runner(tmp_path)
        r.start(matrix_path=_REAL_MATRIX, node_id="node-001")
        r.join(timeout=5)
        s = r.get_state()
        assert len(s["cells"]) == 2
        assert s["cells"][0]["cell_id"] == "BASELINE"
        assert s["cells"][0]["status"] == "completed"
        assert s["cells"][0]["completed_trials"] == 1


# ==================================================================
# Cancel
# ==================================================================

class TestCancel:
    def test_cancel_during_run_marks_cancelled(self, tmp_path):
        # Sweeper that raises SweepCancelled mid-way.
        r = _make_runner(tmp_path,
            sweeper_factory_override=lambda **kw: _FakeSweeper(
                kw["output_dir"], kw["progress_callback"], kw["cancel_check"],
                raise_after_emits=1,   # raise after first cell_started
            ))
        r.start(matrix_path=_REAL_MATRIX, node_id="node-001")
        r.join(timeout=5)
        s = r.get_state()
        assert s["status"] == STATUS_CANCELLED
        assert s["finished_at_ms"] is not None

    def test_cancel_signal_sets_status(self, tmp_path):
        block = threading.Event()
        class _BlockingSweeper(_FakeSweeper):
            def run(self):
                block.wait(timeout=2)
                # Honour cancel signal immediately on resume.
                if self._cancel_check():
                    raise SweepCancelled("post-block-cancel")
                return super().run()
        r = _make_runner(tmp_path,
            sweeper_factory_override=lambda **kw: _BlockingSweeper(
                kw["output_dir"], kw["progress_callback"], kw["cancel_check"],
            ))
        r.start(matrix_path=_REAL_MATRIX, node_id="node-001")
        # Cancel while sweeper is blocked.
        cancel_state = r.cancel()
        assert cancel_state["status"] == STATUS_CANCELLING
        block.set()
        r.join(timeout=2)
        assert r.get_state()["status"] == STATUS_CANCELLED

    def test_cancel_idle_is_noop(self, tmp_path):
        r = _make_runner(tmp_path)
        # No sweep ever started — cancel is a no-op (returns idle state).
        s = r.cancel()
        assert s["status"] == STATUS_IDLE


# ==================================================================
# Failure
# ==================================================================

class TestFailure:
    def test_unhandled_sweeper_exception_marks_failed(self, tmp_path):
        class _BrokenSweeper(_FakeSweeper):
            def run(self):
                raise RuntimeError("boom")
        r = _make_runner(tmp_path,
            sweeper_factory_override=lambda **kw: _BrokenSweeper(
                kw["output_dir"], kw["progress_callback"], kw["cancel_check"],
            ))
        r.start(matrix_path=_REAL_MATRIX, node_id="node-001")
        r.join(timeout=2)
        s = r.get_state()
        assert s["status"] == STATUS_FAILED
        assert "boom" in (s["error"] or "")
        assert "RuntimeError" in (s["error"] or "")
