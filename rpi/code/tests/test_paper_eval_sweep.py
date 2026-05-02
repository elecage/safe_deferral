"""Tests for the paper-eval sweep orchestrator (doc 13 Phase 1).

These tests exercise the orchestrator's matrix-loading, scenario-tag
validation, per-cell run lifecycle, manifest serialisation, and CLI
contract using a fake dashboard client. Real dashboard / network access
is never required.
"""

import json
import pathlib
import textwrap
from unittest.mock import MagicMock

import pytest
import requests

from paper_eval.sweep import (
    Cell,
    DashboardClient,
    MatrixSpec,
    Sweeper,
    SweepResult,
    _validate_cell_scenario_tags,
    load_matrix,
    main,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_REAL_MATRIX = _REPO_ROOT / "integration" / "paper_eval" / "matrix_v1.json"
_REAL_SCENARIOS = _REPO_ROOT / "integration" / "scenarios"


# ==================================================================
# load_matrix — structural validation
# ==================================================================

class TestLoadMatrix:
    """Matrix-loading must catch malformed files before the sweep starts."""

    def test_real_matrix_v1_loads(self):
        """The shipped matrix_v1.json loads cleanly with all 12 cells."""
        spec = load_matrix(_REAL_MATRIX, _REAL_SCENARIOS)
        assert spec.matrix_version == "v1"
        assert spec.package_id == "A"
        assert len(spec.cells) == 12
        # Spot-check the BASELINE cell is comparison_condition=None.
        baseline = next(c for c in spec.cells if c.cell_id == "BASELINE")
        assert baseline.comparison_condition is None

    def test_missing_required_field_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"matrix_version": "v0"}))
        with pytest.raises(ValueError, match="missing required field"):
            load_matrix(bad, _REAL_SCENARIOS)

    def test_unknown_comparison_condition_raises(self, tmp_path):
        m = {
            "matrix_version": "v0", "matrix_description": "",
            "package_id": "A", "trials_per_cell_default": 1,
            "cells": [{
                "cell_id": "BAD",
                "comparison_condition": "bogus_condition",
                "scenarios": [],
                "trials_per_cell": 1,
            }],
        }
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps(m))
        with pytest.raises(ValueError, match="unknown comparison_condition"):
            load_matrix(bad, _REAL_SCENARIOS)

    def test_missing_scenario_raises(self, tmp_path):
        m = {
            "matrix_version": "v0", "matrix_description": "",
            "package_id": "A", "trials_per_cell_default": 1,
            "cells": [{
                "cell_id": "MISS",
                "comparison_condition": None,
                "scenarios": ["definitely_not_a_scenario.json"],
                "trials_per_cell": 1,
            }],
        }
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps(m))
        with pytest.raises(ValueError, match="missing scenario"):
            load_matrix(bad, _REAL_SCENARIOS)

    def test_zero_trials_raises(self, tmp_path):
        m = {
            "matrix_version": "v0", "matrix_description": "",
            "package_id": "A", "trials_per_cell_default": 1,
            "cells": [{
                "cell_id": "ZERO",
                "comparison_condition": None,
                "scenarios": [],
                "trials_per_cell": 0,
            }],
        }
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps(m))
        with pytest.raises(ValueError, match="must be ≥ 1"):
            load_matrix(bad, _REAL_SCENARIOS)


# ==================================================================
# _validate_cell_scenario_tags — P2.6 invariant
# ==================================================================

class TestValidateCellScenarioTags:
    """A cell's scenarios must all carry comparison_conditions[] entries
    matching the cell's condition (P2.6). The BASELINE cell (condition=None)
    is exempt."""

    def test_baseline_cell_passes(self):
        cell = Cell(
            cell_id="BASELINE", description="", comparison_condition=None,
            scenarios=["class1_baseline_scenario_skeleton.json"],
            trials_per_cell=1,
            expected_route_class="CLASS_1", expected_validation="approved",
        )
        assert _validate_cell_scenario_tags(cell, _REAL_SCENARIOS) is None

    def test_correctly_tagged_scenario_passes(self):
        cell = Cell(
            cell_id="C2_D4_SCANNING_INPUT", description="",
            comparison_condition="class2_scanning_input",
            scenarios=["class2_scanning_user_accept_first_scenario_skeleton.json"],
            trials_per_cell=1,
            expected_route_class="CLASS_2", expected_validation="safe_deferral",
        )
        assert _validate_cell_scenario_tags(cell, _REAL_SCENARIOS) is None

    def test_mistagged_scenario_returns_error(self):
        # class1_baseline scenario does NOT carry class2_scanning_input tag.
        cell = Cell(
            cell_id="MISMATCH", description="",
            comparison_condition="class2_scanning_input",
            scenarios=["class1_baseline_scenario_skeleton.json"],
            trials_per_cell=1,
            expected_route_class="CLASS_2", expected_validation="safe_deferral",
        )
        err = _validate_cell_scenario_tags(cell, _REAL_SCENARIOS)
        assert err is not None
        assert "does not tag" in err
        assert "class2_scanning_input" in err

    def test_missing_scenario_file_returns_error(self):
        cell = Cell(
            cell_id="MISSING", description="",
            comparison_condition="class2_scanning_input",
            scenarios=["nonexistent_scenario.json"],
            trials_per_cell=1,
            expected_route_class="CLASS_2", expected_validation="safe_deferral",
        )
        err = _validate_cell_scenario_tags(cell, _REAL_SCENARIOS)
        assert err is not None
        assert "failed to read" in err


# ==================================================================
# Sweeper — full lifecycle with fake DashboardClient
# ==================================================================

def _fake_client(node_id: str = "node-001",
                 trials_complete_after_polls: int = 1):
    """Build a MagicMock that emulates DashboardClient: dashboard reachable,
    one node, create_package_run + start_trial succeed, get_package_run
    reports trials becoming non-pending after `trials_complete_after_polls`
    polls, get_package_run_metrics returns a placeholder."""
    client = MagicMock(spec=DashboardClient)
    client.health.return_value = {"status": "ok"}
    client.list_nodes.return_value = [{"node_id": node_id}]

    run_counter = {"n": 0}
    started_trials = {}  # run_id → list[trial_id]
    poll_counts = {}     # run_id → int

    def _create_run(package_id, scenario_ids, trial_count, comparison_condition):
        run_counter["n"] += 1
        rid = f"run-{run_counter['n']:04d}"
        started_trials[rid] = []
        poll_counts[rid] = 0
        return {"run_id": rid, "package_id": package_id,
                "scenario_ids": scenario_ids, "trial_count": trial_count,
                "comparison_condition": comparison_condition}
    client.create_package_run.side_effect = _create_run

    def _start_trial(run_id, node_id, scenario_id,
                     expected_route_class, expected_validation,
                     comparison_condition=None):
        tid = f"trial-{run_id}-{len(started_trials[run_id]) + 1:03d}"
        started_trials[run_id].append(tid)
        return {"trial_id": tid, "run_id": run_id,
                "scenario_id": scenario_id,
                "expected_route_class": expected_route_class,
                "expected_validation": expected_validation,
                "status": "pending"}
    client.start_trial.side_effect = _start_trial

    def _get_run(run_id):
        poll_counts[run_id] = poll_counts.get(run_id, 0) + 1
        # All trials report 'pending' until the Nth poll, then 'completed'.
        status = ("completed" if poll_counts[run_id] >= trials_complete_after_polls
                  else "pending")
        trials = [{"trial_id": tid, "status": status, "pass_": True}
                  for tid in started_trials.get(run_id, [])]
        return {"run_id": run_id, "trials": trials}
    client.get_package_run.side_effect = _get_run

    def _get_metrics(run_id):
        return {"run_id": run_id, "total": len(started_trials.get(run_id, [])),
                "by_comparison_condition": {}}
    client.get_package_run_metrics.side_effect = _get_metrics

    return client


@pytest.fixture
def fast_sweeper(tmp_path):
    """Build a Sweeper that talks to a fake client and sweeps with no wall
    delays. Returns (sweeper, fake_client) pair."""
    client = _fake_client()

    def _factory(matrix_path=_REAL_MATRIX, node_id="node-001",
                 per_trial_timeout=5.0):
        s = Sweeper(
            matrix_path=matrix_path,
            scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out",
            dashboard_url="http://fake",
            node_id=node_id,
            client=client,
            poll_interval_s=0.0,           # no wall delay in tests
            per_trial_timeout_s=per_trial_timeout,
        )
        return s, client
    return _factory


class TestSweeperHappyPath:
    """Full real matrix v1 sweep against a fake dashboard."""

    def test_real_matrix_v1_sweep_completes(self, fast_sweeper):
        s, client = fast_sweeper()
        result = s.run()
        assert isinstance(result, SweepResult)
        assert result.matrix_version == "v1"
        assert len(result.cells) == 12
        # All cells should be non-skipped (matrix v1 was tagged in P2.6).
        assert all(not c.skipped for c in result.cells)
        # All cells should be non-incomplete (fake client completes after 1 poll).
        assert all(not c.incomplete for c in result.cells)
        # Each cell created one run + 30 trials (per matrix_v1.json default).
        assert client.create_package_run.call_count == 12
        # 12 cells × 30 trials each = 360 start_trial calls.
        assert client.start_trial.call_count == 12 * 30

    def test_manifest_writes_valid_json(self, fast_sweeper, tmp_path):
        s, _ = fast_sweeper()
        result = s.run()
        manifest_path = s.write_manifest(result)
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["matrix_version"] == "v1"
        assert len(data["cells"]) == 12
        assert "anchor_commits" in data

    def test_manifest_carries_trials_snapshot_for_phase2(self, fast_sweeper):
        """Phase 2 aggregator must be able to compute pass_rate /
        by_route_class / latency stats fully offline. That means each
        non-skipped cell must carry its trials_snapshot in the manifest."""
        s, _ = fast_sweeper()
        result = s.run()
        for cell in result.cells:
            if cell.skipped:
                continue
            assert cell.trials_snapshot is not None
            assert cell.scenarios   # non-empty for matrix v1 cells
            assert cell.expected_route_class
            assert cell.expected_validation


class TestSweeperFailureModes:
    """Boundary failure scenarios: dashboard unreachable, missing node,
    mistagged cell, run never completing."""

    def test_dashboard_unreachable_raises_before_progress(self, tmp_path):
        client = MagicMock(spec=DashboardClient)
        client.health.side_effect = requests.RequestException("connection refused")
        s = Sweeper(
            matrix_path=_REAL_MATRIX, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out", dashboard_url="http://fake",
            node_id="x", client=client, poll_interval_s=0.0,
        )
        with pytest.raises(RuntimeError, match="Dashboard unreachable"):
            s.run()
        # Critical: no run was created before the failure.
        client.create_package_run.assert_not_called()

    def test_missing_node_raises_before_progress(self, tmp_path):
        client = _fake_client(node_id="node-existing")
        s = Sweeper(
            matrix_path=_REAL_MATRIX, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out", dashboard_url="http://fake",
            node_id="node-missing", client=client, poll_interval_s=0.0,
        )
        with pytest.raises(RuntimeError, match="not found on dashboard"):
            s.run()
        client.create_package_run.assert_not_called()

    def test_mistagged_cell_skipped_with_reason(self, fast_sweeper, tmp_path):
        # Build a synthetic matrix with a bad cell + a good cell.
        m = {
            "matrix_version": "v0-test", "matrix_description": "",
            "package_id": "A", "trials_per_cell_default": 2,
            "cells": [
                {
                    "cell_id": "GOOD",
                    "comparison_condition": "class2_scanning_input",
                    "scenarios": ["class2_scanning_user_accept_first_scenario_skeleton.json"],
                    "trials_per_cell": 2,
                    "expected_route_class": "CLASS_2",
                    "expected_validation": "safe_deferral",
                },
                {
                    "cell_id": "MISMATCHED",
                    "comparison_condition": "class2_scanning_input",
                    # Class 1 baseline scenario doesn't carry class2_scanning_input
                    "scenarios": ["class1_baseline_scenario_skeleton.json"],
                    "trials_per_cell": 2,
                    "expected_route_class": "CLASS_2",
                    "expected_validation": "safe_deferral",
                },
            ],
        }
        synth_path = tmp_path / "matrix.json"
        synth_path.write_text(json.dumps(m))
        s, client = fast_sweeper(matrix_path=synth_path)
        result = s.run()
        good = next(c for c in result.cells if c.cell_id == "GOOD")
        bad = next(c for c in result.cells if c.cell_id == "MISMATCHED")
        assert not good.skipped and good.run_id is not None
        assert bad.skipped and bad.run_id is None
        assert "does not tag" in bad.skip_reason
        # Only the good cell created a run.
        assert client.create_package_run.call_count == 1

    def test_run_never_completes_marks_incomplete(self, tmp_path):
        # Fake client where get_package_run NEVER returns non-pending.
        client = _fake_client(trials_complete_after_polls=10**9)
        # Build a tiny 1-cell matrix to keep runtime short.
        m = {
            "matrix_version": "v0-test", "matrix_description": "",
            "package_id": "A", "trials_per_cell_default": 1,
            "cells": [{
                "cell_id": "STUCK",
                "comparison_condition": None,
                "scenarios": ["class1_baseline_scenario_skeleton.json"],
                "trials_per_cell": 1,
                "expected_route_class": "CLASS_1",
                "expected_validation": "approved",
            }],
        }
        synth_path = tmp_path / "matrix.json"
        synth_path.write_text(json.dumps(m))
        s = Sweeper(
            matrix_path=synth_path, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out", dashboard_url="http://fake",
            node_id="node-001", client=client, poll_interval_s=0.0,
            per_trial_timeout_s=0.1,   # 0.1s × 1 trial = 0.1s deadline
        )
        result = s.run()
        cell = result.cells[0]
        assert cell.incomplete is True
        assert cell.completed_trials < cell.requested_trials


# ==================================================================
# CLI smoke check
# ==================================================================

class TestCLI:
    """Argparser builds; main() exits with the documented codes."""

    def test_help_runs_without_error(self, capsys):
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            with pytest.raises(SystemExit) as exc:
                main(["--help"])
        assert exc.value.code == 0

    def test_dashboard_unreachable_returns_nonzero(self, tmp_path,
                                                    monkeypatch):
        # Point at a port nothing listens on; main() should fail fast and
        # return 1 (not raise). --scenarios-dir is passed explicitly because
        # the CLI default is the relative path 'integration/scenarios' which
        # only resolves when invoked from the repo root.
        rc = main([
            "--matrix", str(_REAL_MATRIX),
            "--output", str(tmp_path / "out"),
            "--node-id", "doesnt-matter",
            "--scenarios-dir", str(_REAL_SCENARIOS),
            "--dashboard-url", "http://127.0.0.1:1",  # closed port
            "--poll-interval", "0",
            "--per-trial-timeout", "1",
        ])
        assert rc == 1
