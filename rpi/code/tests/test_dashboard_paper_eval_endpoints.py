"""Tests for the dashboard /paper_eval/sweeps endpoints (doc 13 Phase 4 MVP).

Covers the HTTP surface that the dashboard UI uses: start sweep,
poll status, cancel, download manifest/aggregated/digest. SweepRunner
is wired with a fake sweeper_factory so tests do not touch real
network or spawn long-lived threads.
"""

import json
import pathlib
import threading

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app
from paper_eval.sweep import SweepProgressEvent, SweepResult
from paper_eval.sweep_runner import SweepRunner


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_REAL_MATRIX = _REPO_ROOT / "integration" / "paper_eval" / "matrix_v1.json"
_REAL_SCENARIOS = _REPO_ROOT / "integration" / "scenarios"


# Reuse the fake sweeper from the runner tests by inlining a minimal one.
class _FakeSweeper:
    def __init__(self, output_dir, progress_callback, cancel_check):
        self.output_dir = output_dir
        self._cb = progress_callback
        self._cancel_check = cancel_check

    def run(self):
        self._cb(SweepProgressEvent(event_type="sweep_started", total_cells=1))
        self._cb(SweepProgressEvent(event_type="cell_started",
                                     cell_id="BASELINE", cell_index=0,
                                     total_cells=1, requested_trials=1))
        self._cb(SweepProgressEvent(event_type="cell_completed",
                                     cell_id="BASELINE", cell_index=0,
                                     total_cells=1, completed_trials=1,
                                     requested_trials=1, incomplete=False))
        self._cb(SweepProgressEvent(event_type="sweep_completed",
                                     total_cells=1, incomplete=False))
        return _FakeResult()

    def write_manifest(self, result):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "sweep_manifest.json"
        path.write_text(json.dumps(result.to_dict(), indent=2),
                        encoding="utf-8")
        return path


class _FakeResult:
    def to_dict(self):
        return {
            "matrix_version": "v1-test",
            "matrix_path": "fake",
            "started_at_ms": 0,
            "finished_at_ms": 0,
            "anchor_commits": {},
            "output_dir": "fake",
            "dashboard_url": "fake",
            "cells": [{
                "cell_id": "BASELINE",
                "comparison_condition": None,
                "run_id": "run-1",
                "requested_trials": 1,
                "completed_trials": 1,
                "incomplete": False,
                "skipped": False,
                "skip_reason": None,
                "metrics_snapshot": None,
                "trials_snapshot": [{
                    "status": "completed", "pass_": True,
                    "expected_route_class": "CLASS_1",
                    "observed_route_class": "CLASS_1",
                    "latency_ms": 50.0,
                }],
                "scenarios": [],
                "expected_route_class": "CLASS_1",
                "expected_validation": "approved",
                "started_at_ms": 0,
                "finished_at_ms": 0,
            }],
        }


@pytest.fixture
def runner_app(tmp_path):
    """Build a dashboard app wired to a SweepRunner whose sweeper_factory
    returns _FakeSweeper. Returns (TestClient, runner) — caller may
    poll runner.get_state() directly to assert internal state."""
    runner = SweepRunner(
        repo_root=_REPO_ROOT,
        scenarios_dir=_REAL_SCENARIOS,
        runs_root=tmp_path / "runs",
        sweeper_factory=lambda **kw: _FakeSweeper(
            kw["output_dir"], kw["progress_callback"], kw["cancel_check"],
        ),
    )
    app = create_app(sweep_runner=runner)
    return TestClient(app), runner


@pytest.fixture
def app_no_runner():
    """Dashboard app with NO sweep_runner — every /paper_eval endpoint
    should respond with 503."""
    return TestClient(create_app(sweep_runner=None))


# ==================================================================
# 503 when sweep_runner is not wired
# ==================================================================

class TestNoRunnerWired:
    def test_get_current_returns_503(self, app_no_runner):
        r = app_no_runner.get("/paper_eval/sweeps/current")
        assert r.status_code == 503

    def test_post_start_returns_503(self, app_no_runner):
        r = app_no_runner.post("/paper_eval/sweeps", json={
            "matrix_path": str(_REAL_MATRIX), "node_id": "x",
        })
        assert r.status_code == 503


# ==================================================================
# Start
# ==================================================================

class TestStartSweep:
    def test_missing_matrix_path_returns_400(self, runner_app):
        client, _ = runner_app
        r = client.post("/paper_eval/sweeps", json={"node_id": "x"})
        assert r.status_code == 400
        assert "matrix_path" in r.json()["detail"]

    def test_missing_node_id_returns_400(self, runner_app):
        client, _ = runner_app
        r = client.post("/paper_eval/sweeps", json={
            "matrix_path": str(_REAL_MATRIX),
        })
        assert r.status_code == 400

    def test_nonexistent_matrix_returns_404(self, runner_app):
        client, _ = runner_app
        r = client.post("/paper_eval/sweeps", json={
            "matrix_path": "/no/such/file.json", "node_id": "x",
        })
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_relative_matrix_resolves_against_repo_root(self, runner_app):
        client, runner = runner_app
        r = client.post("/paper_eval/sweeps", json={
            "matrix_path": "integration/paper_eval/matrix_v1.json",
            "node_id": "node-001",
        })
        assert r.status_code == 200
        runner.join(timeout=5)

    def test_valid_start_returns_running_state(self, runner_app):
        client, runner = runner_app
        r = client.post("/paper_eval/sweeps", json={
            "matrix_path": str(_REAL_MATRIX), "node_id": "node-001",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in ("running", "completed")  # may finish fast
        assert body["sweep_id"] is not None
        runner.join(timeout=5)

    def test_double_start_returns_409(self, runner_app, tmp_path):
        client, runner = runner_app
        # Use a slow sweeper so we can observe RUNNING during the second call.
        block = threading.Event()
        class _BlockingSweeper(_FakeSweeper):
            def run(self):
                block.wait(timeout=2)
                return super().run()
        runner._sweeper_factory = lambda **kw: _BlockingSweeper(
            kw["output_dir"], kw["progress_callback"], kw["cancel_check"],
        )
        r1 = client.post("/paper_eval/sweeps", json={
            "matrix_path": str(_REAL_MATRIX), "node_id": "node-001",
        })
        assert r1.status_code == 200
        r2 = client.post("/paper_eval/sweeps", json={
            "matrix_path": str(_REAL_MATRIX), "node_id": "node-001",
        })
        assert r2.status_code == 409
        assert "already in progress" in r2.json()["detail"]
        block.set()
        runner.join(timeout=2)


# ==================================================================
# Status + cancel
# ==================================================================

class TestStatusAndCancel:
    def test_get_current_idle_before_start(self, runner_app):
        client, _ = runner_app
        r = client.get("/paper_eval/sweeps/current")
        assert r.status_code == 200
        assert r.json()["status"] == "idle"
        assert r.json()["cells"] == []

    def test_get_current_after_completion_has_artifact_paths(self, runner_app):
        client, runner = runner_app
        client.post("/paper_eval/sweeps", json={
            "matrix_path": str(_REAL_MATRIX), "node_id": "node-001",
        })
        runner.join(timeout=5)
        s = client.get("/paper_eval/sweeps/current").json()
        assert s["status"] == "completed"
        assert s["manifest_path"]
        assert s["aggregated_path"]

    def test_cancel_idle_returns_idle(self, runner_app):
        client, _ = runner_app
        r = client.post("/paper_eval/sweeps/current/cancel")
        assert r.status_code == 200
        assert r.json()["status"] == "idle"


# ==================================================================
# Artifact downloads
# ==================================================================

class TestArtifactDownloads:
    def test_manifest_404_before_completion(self, runner_app):
        client, _ = runner_app
        r = client.get("/paper_eval/sweeps/current/manifest")
        assert r.status_code == 404

    def test_manifest_returns_json_after_completion(self, runner_app):
        client, runner = runner_app
        client.post("/paper_eval/sweeps", json={
            "matrix_path": str(_REAL_MATRIX), "node_id": "node-001",
        })
        runner.join(timeout=5)
        r = client.get("/paper_eval/sweeps/current/manifest")
        assert r.status_code == 200
        body = r.json()
        assert body["matrix_version"] == "v1-test"
        assert len(body["cells"]) == 1

    def test_aggregated_returns_json_after_completion(self, runner_app):
        client, runner = runner_app
        client.post("/paper_eval/sweeps", json={
            "matrix_path": str(_REAL_MATRIX), "node_id": "node-001",
        })
        runner.join(timeout=5)
        r = client.get("/paper_eval/sweeps/current/aggregated")
        assert r.status_code == 200
        body = r.json()
        assert "cells" in body
        assert body["cells"][0]["cell_id"] == "BASELINE"
        assert body["cells"][0]["pass_rate"] == 1.0

    def test_digest_csv_returns_text_after_completion(self, runner_app):
        client, runner = runner_app
        client.post("/paper_eval/sweeps", json={
            "matrix_path": str(_REAL_MATRIX), "node_id": "node-001",
        })
        runner.join(timeout=5)
        r = client.get("/paper_eval/sweeps/current/digest.csv")
        assert r.status_code == 200
        # Header line includes the stable column names.
        assert "cell_id" in r.text
        assert "BASELINE" in r.text

    def test_digest_md_returns_text_after_completion(self, runner_app):
        client, runner = runner_app
        client.post("/paper_eval/sweeps", json={
            "matrix_path": str(_REAL_MATRIX), "node_id": "node-001",
        })
        runner.join(timeout=5)
        r = client.get("/paper_eval/sweeps/current/digest.md")
        assert r.status_code == 200
        assert "matrix `v1-test`" in r.text
        assert "BASELINE" in r.text


# ==================================================================
# Boundary: no actuation/publish path was added
# ==================================================================

class TestNoNewAuthoritySurface:
    """Phase 4 MVP must not add any operational-control / actuation /
    publish path under /paper_eval/sweeps. Mirrors the governance UI
    invariant test but scoped to this endpoint family."""

    def test_no_publish_or_actuation_paths(self, runner_app):
        client, _ = runner_app
        paths = [p for p in client.app.openapi().get("paths", {}).keys()
                 if p.startswith("/paper_eval")]
        forbidden = ("actuation", "command", "publish", "doorlock")
        for p in paths:
            for bad in forbidden:
                assert bad not in p, f"{p} contains {bad!r} — boundary regression"
