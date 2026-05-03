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
    SweepCancelled,
    SweepProgressEvent,
    Sweeper,
    SweepResult,
    _load_effective_policy,
    _validate_cell_policy_overrides,
    _validate_cell_scenario_tags,
    load_matrix,
    main,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_REAL_MATRIX = _REPO_ROOT / "integration" / "paper_eval" / "matrix_v1.json"
_EXTENSIBILITY_MATRIX = _REPO_ROOT / "integration" / "paper_eval" / "matrix_extensibility.json"
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
        """matrix_v1 has 12 cells but the canonical policy_table.json keeps
        class2_multi_turn_enabled=False, so the 2 MULTI_TURN cells are
        correctly skipped via Sweeper's policy-overrides enforcement.
        The other 10 cells run end-to-end."""
        s, client = fast_sweeper()
        result = s.run()
        assert isinstance(result, SweepResult)
        assert result.matrix_version == "v1"
        assert len(result.cells) == 12
        # 10 cells run; 2 multi-turn cells skipped by policy enforcement.
        skipped = [c for c in result.cells if c.skipped]
        ran = [c for c in result.cells if not c.skipped]
        assert len(ran) == 10
        assert len(skipped) == 2
        assert {c.cell_id for c in skipped} == {
            "C2_MULTI_TURN_REFINEMENT_USER_PICK",
            "C2_MULTI_TURN_REFINEMENT_TIMEOUT",
        }
        # The 10 cells that ran each created one run + 30 trials.
        assert all(not c.incomplete for c in ran)
        assert client.create_package_run.call_count == 10
        assert client.start_trial.call_count == 10 * 30

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


# ==================================================================
# Phase 4 enabler — progress callback + cancel hook
# ==================================================================

class TestProgressCallback:
    """Sweeper emits SweepProgressEvent at lifecycle points so a UI can
    render live state. Both hooks default to no-op (backward compat for
    existing callers)."""

    def test_callback_default_is_noop(self, fast_sweeper):
        # Existing tests don't pass progress_callback — they must keep
        # working without modification (backward compat invariant).
        s, _ = fast_sweeper()
        result = s.run()
        assert len(result.cells) == 12   # unchanged behaviour

    def test_emits_sweep_started_then_completed(self, tmp_path):
        events = []
        client = _fake_client()
        s = Sweeper(
            matrix_path=_REAL_MATRIX, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out", dashboard_url="http://fake",
            node_id="node-001", client=client, poll_interval_s=0.0,
            progress_callback=events.append,
        )
        s.run()
        types = [e.event_type for e in events]
        assert types[0] == "sweep_started"
        assert types[-1] == "sweep_completed"
        # First sweep_started carries total_cells.
        assert events[0].total_cells == 12

    def test_each_cell_emits_started_and_completed(self, tmp_path):
        """All 12 cells emit cell_started; only the 10 that pass policy
        check emit cell_completed (the 2 multi-turn cells emit cell_skipped
        instead). Verified against the canonical policy_table.json which
        has class2_multi_turn_enabled=False."""
        events = []
        client = _fake_client()
        s = Sweeper(
            matrix_path=_REAL_MATRIX, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out", dashboard_url="http://fake",
            node_id="node-001", client=client, poll_interval_s=0.0,
            progress_callback=events.append,
        )
        s.run()
        started = [e for e in events if e.event_type == "cell_started"]
        completed = [e for e in events if e.event_type == "cell_completed"]
        skipped = [e for e in events if e.event_type == "cell_skipped"]
        assert len(started) == 12       # every cell still emits cell_started
        assert len(completed) == 10     # 10 ran end-to-end
        assert len(skipped) == 2        # 2 multi-turn cells policy-skipped
        # cell_index is 0-based and contiguous across started events.
        assert [e.cell_index for e in started] == list(range(12))

    def test_skipped_cell_emits_cell_skipped_with_reason(self, tmp_path):
        # Build a synthetic 1-cell matrix that fails tag validation.
        m = {
            "matrix_version": "v0", "matrix_description": "",
            "package_id": "A", "trials_per_cell_default": 1,
            "cells": [{
                "cell_id": "BAD",
                "comparison_condition": "class2_scanning_input",
                "scenarios": ["class1_baseline_scenario_skeleton.json"],
                "trials_per_cell": 1,
                "expected_route_class": "CLASS_2",
                "expected_validation": "safe_deferral",
            }],
        }
        synth = tmp_path / "m.json"
        synth.write_text(json.dumps(m))
        events = []
        client = _fake_client()
        s = Sweeper(
            matrix_path=synth, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out", dashboard_url="http://fake",
            node_id="node-001", client=client, poll_interval_s=0.0,
            progress_callback=events.append,
        )
        s.run()
        skipped = [e for e in events if e.event_type == "cell_skipped"]
        assert len(skipped) == 1
        assert skipped[0].cell_id == "BAD"
        assert "does not tag" in (skipped[0].skip_reason or "")

    def test_progress_events_carry_completed_count(self, tmp_path):
        events = []
        client = _fake_client()
        s = Sweeper(
            matrix_path=_REAL_MATRIX, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out", dashboard_url="http://fake",
            node_id="node-001", client=client, poll_interval_s=0.0,
            progress_callback=events.append,
        )
        s.run()
        progress = [e for e in events if e.event_type == "cell_progress"]
        # At least one progress event per cell (matrix v1 has 12 cells × 30
        # trials; fake client completes after 1 poll → exactly one progress
        # per cell with completed=requested).
        assert len(progress) >= 12
        last = [e for e in progress if e.completed_trials and e.completed_trials > 0][-1]
        assert last.completed_trials == last.requested_trials

    def test_callback_exception_does_not_break_sweep(self, fast_sweeper):
        def bad_cb(_e):
            raise RuntimeError("ui crashed")
        s, _ = fast_sweeper()
        s._progress_cb = bad_cb
        # Sweep must complete despite callback exceptions (UI bug ≠ data loss).
        result = s.run()
        assert len(result.cells) == 12


class TestCancelHook:
    """cancel_check() is polled between cells AND inside the per-cell poll
    loop. When it returns True, the sweep raises SweepCancelled."""

    def test_cancel_before_first_cell(self, tmp_path):
        client = _fake_client()
        s = Sweeper(
            matrix_path=_REAL_MATRIX, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out", dashboard_url="http://fake",
            node_id="node-001", client=client, poll_interval_s=0.0,
            cancel_check=lambda: True,
        )
        with pytest.raises(SweepCancelled):
            s.run()
        client.create_package_run.assert_not_called()

    def test_cancel_after_one_cell(self, tmp_path):
        client = _fake_client()
        cancel_after = {"n": 0}
        def check():
            cancel_after["n"] += 1
            # Allow first cell to finish (~1 between-cell check), then cancel.
            return cancel_after["n"] > 1
        s = Sweeper(
            matrix_path=_REAL_MATRIX, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out", dashboard_url="http://fake",
            node_id="node-001", client=client, poll_interval_s=0.0,
            cancel_check=check,
        )
        with pytest.raises(SweepCancelled):
            s.run()
        # At least one cell ran before cancellation.
        assert client.create_package_run.call_count >= 1
        assert client.create_package_run.call_count < 12

    def test_no_cancel_check_default_runs_all(self, fast_sweeper):
        s, _ = fast_sweeper()   # cancel_check defaults to no-op
        result = s.run()
        assert len(result.cells) == 12


# ==================================================================
# Item 1 fix — _policy_overrides enforcement
# ==================================================================

class TestValidateCellPolicyOverrides:
    """Sweeper must skip any cell whose declared `_policy_overrides` is
    not satisfied by the currently-loaded canonical policy. Without this
    Phase C 2026-05-03 silently ran 60 trials of supposedly multi-turn
    behaviour against a policy where the multi-turn flag was off; the
    cells fell through to default direct-select and mislabelled their
    results (refinement_history present in 0/60)."""

    def test_no_overrides_returns_none(self):
        cell = Cell(cell_id="X", description="", comparison_condition=None,
                    scenarios=[], trials_per_cell=1,
                    expected_route_class="CLASS_1", expected_validation="approved",
                    policy_overrides=None)
        assert _validate_cell_policy_overrides(cell, {"global_constraints": {}}) is None

    def test_empty_overrides_returns_none(self):
        cell = Cell(cell_id="X", description="", comparison_condition=None,
                    scenarios=[], trials_per_cell=1,
                    expected_route_class="CLASS_1", expected_validation="approved",
                    policy_overrides={})
        assert _validate_cell_policy_overrides(cell, {"global_constraints": {}}) is None

    def test_matching_override_returns_none(self):
        cell = Cell(cell_id="X", description="", comparison_condition=None,
                    scenarios=[], trials_per_cell=1,
                    expected_route_class="CLASS_2", expected_validation="safe_deferral",
                    policy_overrides={"class2_multi_turn_enabled": True})
        policy = {"global_constraints": {"class2_multi_turn_enabled": True}}
        assert _validate_cell_policy_overrides(cell, policy) is None

    def test_mismatched_override_returns_skip_reason(self):
        cell = Cell(cell_id="X", description="", comparison_condition=None,
                    scenarios=[], trials_per_cell=1,
                    expected_route_class="CLASS_2", expected_validation="safe_deferral",
                    policy_overrides={"class2_multi_turn_enabled": True})
        policy = {"global_constraints": {"class2_multi_turn_enabled": False}}
        err = _validate_cell_policy_overrides(cell, policy)
        assert err is not None
        assert "class2_multi_turn_enabled" in err
        assert "required=True" in err
        assert "actual=False" in err

    def test_missing_policy_key_returns_skip(self):
        cell = Cell(cell_id="X", description="", comparison_condition=None,
                    scenarios=[], trials_per_cell=1,
                    expected_route_class="CLASS_2", expected_validation="safe_deferral",
                    policy_overrides={"class2_multi_turn_enabled": True})
        policy = {"global_constraints": {}}   # key absent → actual=None
        err = _validate_cell_policy_overrides(cell, policy)
        assert err is not None
        assert "actual=None" in err

    def test_none_effective_policy_returns_defensive_skip(self):
        """If the orchestrator could not load the policy at all, every
        cell with overrides must skip rather than silently run."""
        cell = Cell(cell_id="X", description="", comparison_condition=None,
                    scenarios=[], trials_per_cell=1,
                    expected_route_class="CLASS_2", expected_validation="safe_deferral",
                    policy_overrides={"class2_multi_turn_enabled": True})
        err = _validate_cell_policy_overrides(cell, None)
        assert err is not None
        assert "no effective policy snapshot" in err

    def test_real_matrix_v1_multi_turn_cells_skip_under_default_policy(self):
        """End-to-end: load real matrix_v1.json + real policy_table.json.
        The two MULTI_TURN cells must be flagged as skip-needed because
        the canonical default has class2_multi_turn_enabled=False."""
        spec = load_matrix(_REAL_MATRIX, _REAL_SCENARIOS)
        repo_root = pathlib.Path(__file__).resolve().parents[3]
        policy = _load_effective_policy(repo_root)
        assert policy is not None
        skip_count = 0
        for cell in spec.cells:
            err = _validate_cell_policy_overrides(cell, policy)
            if err is not None:
                skip_count += 1
                assert "MULTI_TURN" in cell.cell_id, (
                    f"unexpectedly skipped non-multi-turn cell {cell.cell_id}: {err}"
                )
        assert skip_count == 2, f"expected 2 multi-turn cells to skip, got {skip_count}"


class TestLoadEffectivePolicy:
    def test_loads_canonical_policy_table(self):
        repo_root = pathlib.Path(__file__).resolve().parents[3]
        p = _load_effective_policy(repo_root)
        assert p is not None
        # Sanity: canonical default for the multi-turn flag is False
        # (intentional safety posture).
        gc = p.get("global_constraints", {})
        assert gc.get("class2_multi_turn_enabled") is False

    def test_missing_repo_returns_none(self, tmp_path):
        # tmp_path has no common/policies/policy_table.json
        assert _load_effective_policy(tmp_path) is None


# ==================================================================
# Step 2 — Extensibility experiment matrix structural tests
# ==================================================================

class TestExtensibilityMatrix:
    """matrix_extensibility.json defines the v1 Axis A experiment for
    Contribution 1 (perception scalability). Structural invariants here
    catch drift between the matrix file, its scenario, and the Sweeper's
    pre-flight checks."""

    def test_matrix_loads_with_three_cells(self):
        spec = load_matrix(_EXTENSIBILITY_MATRIX, _REAL_SCENARIOS)
        assert spec.matrix_version == "v1-extensibility-axis-a"
        assert len(spec.cells) == 3
        # Three modes, same scenario file across all three cells.
        assert {c.comparison_condition for c in spec.cells} == {
            "direct_mapping", "rule_only", "llm_assisted",
        }
        scenarios = {tuple(c.scenarios) for c in spec.cells}
        assert len(scenarios) == 1, "all 3 cells should use the same scenario file"

    def test_each_cell_passes_scenario_tag_check(self):
        """The shared scenario must declare all three comparison_conditions
        so the P2.6 invariant holds for every cell that runs against it."""
        spec = load_matrix(_EXTENSIBILITY_MATRIX, _REAL_SCENARIOS)
        for cell in spec.cells:
            err = _validate_cell_scenario_tags(cell, _REAL_SCENARIOS)
            assert err is None, (
                f"cell {cell.cell_id} failed P2.6 tag check: {err}"
            )

    def test_each_cell_passes_policy_overrides_check(self):
        """Extensibility cells must not declare policy_overrides — this
        experiment doesn't require any flag flips."""
        spec = load_matrix(_EXTENSIBILITY_MATRIX, _REAL_SCENARIOS)
        repo_root = pathlib.Path(__file__).resolve().parents[3]
        policy = _load_effective_policy(repo_root)
        for cell in spec.cells:
            err = _validate_cell_policy_overrides(cell, policy)
            assert err is None, (
                f"cell {cell.cell_id} failed policy check: {err}"
            )

    def test_per_cell_expected_encodes_mode_specific_correct_behaviour(self):
        """Per-cell expected encodes 'what the correct version of THIS mode
        should do given this novel input'. Deterministic modes are expected
        to safe-defer (their context-blind output cannot be relied on);
        llm_assisted is expected to recover the right intent. This shape
        is what makes pass_rate informative across modes — uniform
        expected would hide the differentiation we're trying to measure."""
        spec = load_matrix(_EXTENSIBILITY_MATRIX, _REAL_SCENARIOS)
        by_id = {c.cell_id: c for c in spec.cells}
        # Deterministic modes: expected to safe-defer
        for cell_id in ("EXT_A_DIRECT_MAPPING", "EXT_A_RULE_ONLY"):
            assert by_id[cell_id].expected_route_class == "CLASS_2"
            assert by_id[cell_id].expected_validation == "safe_deferral"
        # LLM mode: expected to recover and successfully route a Class 1 action
        assert by_id["EXT_A_LLM_ASSISTED"].expected_route_class == "CLASS_1"
        assert by_id["EXT_A_LLM_ASSISTED"].expected_validation == "approved"
