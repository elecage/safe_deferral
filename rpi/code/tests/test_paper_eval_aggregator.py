"""Tests for the paper-eval cross-run aggregator (doc 13 Phase 2).

Exercises manifest loading, per-cell aggregation primitives, full-matrix
aggregation against a synthetic manifest, end-to-end via Sweeper +
fake DashboardClient, and the CLI surface. No real dashboard / network.
"""

import json
import pathlib
from unittest.mock import MagicMock

import pytest

from paper_eval.aggregator import (
    AggregatedMatrix,
    CellResult,
    _aggregate_cell,
    _by_route_class,
    _class2_clarification_correctness,
    _completed_trials,
    _percentile,
    _scan_history_yes_first_rate,
    _scan_ordering_applied_present_count,
    aggregate,
    load_sweep_manifest,
    main,
    write_aggregated,
)
from paper_eval.sweep import DashboardClient, Sweeper


# ==================================================================
# load_sweep_manifest — structural validation
# ==================================================================

class TestLoadSweepManifest:
    """Manifest loader rejects garbage but tolerates missing per-field
    additions so older manifests can still be aggregated."""

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_sweep_manifest(tmp_path / "nope.json")

    def test_missing_cells_field_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"matrix_version": "v1"}))
        with pytest.raises(ValueError, match="no 'cells' field"):
            load_sweep_manifest(bad)

    def test_missing_matrix_version_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"cells": []}))
        with pytest.raises(ValueError, match="missing matrix_version"):
            load_sweep_manifest(bad)

    def test_minimal_valid_manifest_loads(self, tmp_path):
        ok = tmp_path / "ok.json"
        ok.write_text(json.dumps({"matrix_version": "v1", "cells": []}))
        data = load_sweep_manifest(ok)
        assert data["matrix_version"] == "v1"
        assert data["cells"] == []


# ==================================================================
# Aggregation primitives
# ==================================================================

class TestPercentile:
    def test_empty_returns_none(self):
        assert _percentile([], 50) is None

    def test_single_value(self):
        assert _percentile([42.0], 50) == 42.0
        assert _percentile([42.0], 95) == 42.0

    def test_ten_values_p50_p95(self):
        # Nearest-rank: p50 of 1..10 → idx=5 → 6; p95 → idx=9 → 10.
        vals = [float(i) for i in range(1, 11)]
        assert _percentile(vals, 50) == 6.0
        assert _percentile(vals, 95) == 10.0


class TestCompletedTrials:
    def test_filters_pending_and_timeout(self):
        trials = [
            {"trial_id": "a", "status": "completed"},
            {"trial_id": "b", "status": "pending"},
            {"trial_id": "c", "status": "timeout"},
            {"trial_id": "d", "status": "completed"},
        ]
        out = _completed_trials(trials)
        assert [t["trial_id"] for t in out] == ["a", "d"]

    def test_handles_none_input(self):
        assert _completed_trials(None) == []


class TestByRouteClass:
    def test_buckets_three_canonical_classes(self):
        trials = [
            {"observed_route_class": "CLASS_0"},
            {"observed_route_class": "CLASS_1"},
            {"observed_route_class": "CLASS_1"},
            {"observed_route_class": "CLASS_2"},
            {"observed_route_class": None},   # → unknown
            {},                                # → unknown
        ]
        out = _by_route_class(trials)
        assert out == {"CLASS_0": 1, "CLASS_1": 2, "CLASS_2": 1, "unknown": 2}

    def test_unknown_string_lands_in_unknown_bucket(self):
        trials = [{"observed_route_class": "CLASS_42"}]
        out = _by_route_class(trials)
        assert out["unknown"] == 1

    def test_empty_trials_returns_zero_counts(self):
        out = _by_route_class([])
        assert out == {"CLASS_0": 0, "CLASS_1": 0, "CLASS_2": 0, "unknown": 0}


class TestScanHistoryYesFirstRate:
    def test_no_scan_history_returns_none(self):
        trials = [
            {"clarification_payload": None},
            {"clarification_payload": {}},
            {"clarification_payload": {"scan_history": []}},
        ]
        rate, count = _scan_history_yes_first_rate(trials)
        assert rate is None
        assert count == 0

    def test_first_response_yes_counts(self):
        trials = [
            {"clarification_payload": {
                "scan_history": [
                    {"option": "light_on", "response": "yes"},
                ],
            }},
            {"clarification_payload": {
                "scan_history": [
                    {"option": "light_on", "response": "no"},
                    {"option": "light_off", "response": "yes"},
                ],
            }},
            {"clarification_payload": {
                "scan_history": [
                    {"option": "light_on", "response": "yes"},
                ],
            }},
        ]
        rate, count = _scan_history_yes_first_rate(trials)
        assert count == 3
        assert rate == round(2 / 3, 4)


class TestScanOrderingAppliedPresentCount:
    def test_counts_present_orderings(self):
        trials = [
            {"clarification_payload": {"scan_ordering_applied": ["a", "b"]}},
            {"clarification_payload": {"scan_ordering_applied": []}},  # empty=absent
            {"clarification_payload": {}},
            {"clarification_payload": {"scan_ordering_applied": ["x"]}},
        ]
        assert _scan_ordering_applied_present_count(trials) == 2


class TestClass2ClarificationCorrectness:
    def test_no_class2_expected_returns_none(self):
        trials = [
            {"expected_route_class": "CLASS_1"},
            {"expected_route_class": "CLASS_0"},
        ]
        assert _class2_clarification_correctness(trials) is None

    def test_correct_when_class2_routed_with_payload(self):
        trials = [
            {"expected_route_class": "CLASS_2",
             "observed_route_class": "CLASS_2",
             "clarification_payload": {"foo": "bar"}},
            {"expected_route_class": "CLASS_2",
             "observed_route_class": "CLASS_2",
             "clarification_payload": None},          # missing payload → fail
            {"expected_route_class": "CLASS_2",
             "observed_route_class": "CLASS_1",       # wrong route → fail
             "clarification_payload": {"foo": "bar"}},
            {"expected_route_class": "CLASS_2",
             "observed_route_class": "CLASS_2",
             "clarification_payload": {"baz": "qux"}},
        ]
        # 2 out of 4 expected-CLASS_2 trials qualify.
        assert _class2_clarification_correctness(trials) == 0.5


# ==================================================================
# _aggregate_cell — single-cell end-to-end
# ==================================================================

class TestAggregateCell:
    def test_skipped_cell_emits_zero_metrics_with_note(self):
        cell = {
            "cell_id": "MISMATCHED",
            "comparison_condition": "class2_scanning_input",
            "scenarios": ["foo.json"],
            "skipped": True,
            "skip_reason": "scenario foo.json does not tag ...",
            "trials_snapshot": None,
        }
        result = _aggregate_cell(cell)
        assert result.skipped is True
        assert result.n_trials == 0
        assert result.pass_rate is None
        assert result.latency_ms_p50 is None
        assert any("skipped" in n for n in result.notes)

    def test_incomplete_cell_aggregates_completed_only(self):
        cell = {
            "cell_id": "PARTIAL",
            "comparison_condition": None,
            "scenarios": ["x.json"],
            "skipped": False,
            "incomplete": True,
            "completed_trials": 2,
            "requested_trials": 5,
            "trials_snapshot": [
                {"status": "completed", "pass_": True,
                 "latency_ms": 100.0, "observed_route_class": "CLASS_1"},
                {"status": "completed", "pass_": False,
                 "latency_ms": 200.0, "observed_route_class": "CLASS_1"},
                {"status": "pending"},
                {"status": "pending"},
                {"status": "pending"},
            ],
        }
        result = _aggregate_cell(cell)
        assert result.incomplete is True
        assert result.n_trials == 2
        assert result.pass_rate == 0.5
        assert result.by_route_class["CLASS_1"] == 2
        assert any("incomplete" in n for n in result.notes)

    def test_missing_trials_snapshot_emits_note(self):
        # An older manifest (pre-Phase 2 enabler) won't have trials_snapshot.
        cell = {
            "cell_id": "OLD",
            "comparison_condition": None,
            "scenarios": ["x.json"],
            "skipped": False,
            "incomplete": False,
            "trials_snapshot": None,
        }
        result = _aggregate_cell(cell)
        assert result.n_trials == 0
        assert any("trials_snapshot" in n for n in result.notes)

    def test_full_metrics_class2_scanning_cell(self):
        cell = {
            "cell_id": "C2_SCAN",
            "comparison_condition": "class2_scanning_input",
            "scenarios": ["scan.json"],
            "skipped": False,
            "incomplete": False,
            "trials_snapshot": [
                {
                    "status": "completed", "pass_": True,
                    "expected_route_class": "CLASS_2",
                    "observed_route_class": "CLASS_2",
                    "latency_ms": 1500.0,
                    "clarification_payload": {
                        "scan_history": [
                            {"option": "light_on", "response": "yes"}
                        ],
                        "scan_ordering_applied": ["light_on", "light_off"],
                    },
                },
                {
                    "status": "completed", "pass_": True,
                    "expected_route_class": "CLASS_2",
                    "observed_route_class": "CLASS_2",
                    "latency_ms": 2500.0,
                    "clarification_payload": {
                        "scan_history": [
                            {"option": "light_on", "response": "no"},
                            {"option": "light_off", "response": "yes"},
                        ],
                        "scan_ordering_applied": ["light_on", "light_off"],
                    },
                },
            ],
        }
        result = _aggregate_cell(cell)
        assert result.n_trials == 2
        assert result.pass_rate == 1.0
        assert result.by_route_class == {
            "CLASS_0": 0, "CLASS_1": 0, "CLASS_2": 2, "unknown": 0,
        }
        # Nearest-rank p50 of [1500, 2500] → idx=1 → 2500.
        assert result.latency_ms_p50 == 2500.0
        assert result.latency_ms_p95 == 2500.0
        assert result.class2_clarification_correctness == 1.0
        assert result.scan_history_yes_first_rate == 0.5
        assert result.scan_history_present_count == 2
        assert result.scan_ordering_applied_present_count == 2


# ==================================================================
# aggregate() — full manifest
# ==================================================================

class TestAggregate:
    def test_synthetic_manifest_round_trip(self, tmp_path):
        manifest = {
            "matrix_version": "v1-test",
            "matrix_path": "/tmp/matrix.json",
            "started_at_ms": 1000,
            "finished_at_ms": 9000,
            "anchor_commits": {"matrix_file_sha": "abc"},
            "cells": [
                {
                    "cell_id": "BASELINE",
                    "comparison_condition": None,
                    "scenarios": ["baseline.json"],
                    "skipped": False, "incomplete": False,
                    "trials_snapshot": [
                        {"status": "completed", "pass_": True,
                         "expected_route_class": "CLASS_1",
                         "observed_route_class": "CLASS_1",
                         "latency_ms": 50.0},
                    ],
                },
                {
                    "cell_id": "C1_RULE_ONLY",
                    "comparison_condition": "rule_only",
                    "scenarios": ["x.json"],
                    "skipped": True,
                    "skip_reason": "missing tag",
                    "trials_snapshot": None,
                },
            ],
        }
        out = aggregate(manifest)
        assert isinstance(out, AggregatedMatrix)
        assert out.matrix_version == "v1-test"
        assert out.anchor_commits == {"matrix_file_sha": "abc"}
        assert len(out.cells) == 2
        baseline = out.cell_by_id("BASELINE")
        assert baseline.n_trials == 1
        assert baseline.pass_rate == 1.0
        ro = out.cell_by_id("C1_RULE_ONLY")
        assert ro.skipped is True
        assert ro.n_trials == 0

    def test_write_aggregated_round_trip(self, tmp_path):
        manifest = {
            "matrix_version": "v0",
            "cells": [
                {"cell_id": "X", "comparison_condition": None,
                 "scenarios": [], "skipped": False, "incomplete": False,
                 "trials_snapshot": [
                     {"status": "completed", "pass_": True,
                      "observed_route_class": "CLASS_1",
                      "latency_ms": 10.0},
                 ]},
            ],
        }
        out = aggregate(manifest)
        path = tmp_path / "aggregated.json"
        write_aggregated(out, path)
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["matrix_version"] == "v0"
        assert loaded["cells"][0]["cell_id"] == "X"
        assert loaded["cells"][0]["pass_rate"] == 1.0


# ==================================================================
# End-to-end: Sweeper → manifest → aggregator
# ==================================================================

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_REAL_MATRIX = _REPO_ROOT / "integration" / "paper_eval" / "matrix_v1.json"
_REAL_SCENARIOS = _REPO_ROOT / "integration" / "scenarios"


def _fake_client_with_trial_data():
    """Like _fake_client in test_paper_eval_sweep but every trial reports
    completed status + observed_route_class + latency_ms so the aggregator
    has real data to chew on."""
    client = MagicMock(spec=DashboardClient)
    client.health.return_value = {"status": "ok"}
    client.list_nodes.return_value = [{"node_id": "node-001"}]

    run_counter = {"n": 0}
    started_trials = {}

    def _create_run(package_id, scenario_ids, trial_count, comparison_condition):
        run_counter["n"] += 1
        rid = f"run-{run_counter['n']:04d}"
        started_trials[rid] = []
        return {"run_id": rid}
    client.create_package_run.side_effect = _create_run

    def _start_trial(run_id, node_id, scenario_id,
                     expected_route_class, expected_validation,
                     comparison_condition=None):
        tid = f"trial-{run_id}-{len(started_trials[run_id]) + 1:03d}"
        started_trials[run_id].append({
            "trial_id": tid,
            "status": "completed",
            "pass_": True,
            "expected_route_class": expected_route_class,
            "observed_route_class": expected_route_class,
            "latency_ms": 100.0,
            "clarification_payload": (
                {"scan_history": [{"option": "x", "response": "yes"}]}
                if expected_route_class == "CLASS_2" else None
            ),
        })
        return {"trial_id": tid, "status": "pending"}
    client.start_trial.side_effect = _start_trial

    def _get_run(run_id):
        return {"run_id": run_id, "trials": started_trials.get(run_id, [])}
    client.get_package_run.side_effect = _get_run

    def _get_metrics(run_id):
        return {"run_id": run_id, "total": len(started_trials.get(run_id, []))}
    client.get_package_run_metrics.side_effect = _get_metrics

    return client


class TestEndToEnd:
    """Sweeper writes a manifest with trials_snapshot, aggregator reads it
    back into an AggregatedMatrix with the expected per-cell stats."""

    def test_sweep_then_aggregate_real_matrix(self, tmp_path):
        client = _fake_client_with_trial_data()
        sweeper = Sweeper(
            matrix_path=_REAL_MATRIX, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "out", dashboard_url="http://fake",
            node_id="node-001", client=client, poll_interval_s=0.0,
        )
        sweep_result = sweeper.run()
        manifest_path = sweeper.write_manifest(sweep_result)

        # Now aggregate.
        manifest = load_sweep_manifest(manifest_path)
        matrix = aggregate(manifest)

        assert matrix.matrix_version == "v1"
        assert len(matrix.cells) == 12
        # Every cell's trials_snapshot was populated by sweep, so n_trials
        # should equal requested (30) for non-skipped cells.
        for cell in matrix.cells:
            assert cell.skipped is False
            assert cell.n_trials == 30
            assert cell.pass_rate == 1.0
        # Class 2 cells should have non-None clarification correctness.
        c2 = matrix.cell_by_id("C2_D4_SCANNING_INPUT")
        assert c2.class2_clarification_correctness == 1.0
        # Scanning-tagged cells should report scan_history presence.
        assert c2.scan_history_present_count == 30


# ==================================================================
# CLI smoke
# ==================================================================

class TestCLI:
    def test_help_returns_zero(self):
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            with pytest.raises(SystemExit) as exc:
                main(["--help"])
        assert exc.value.code == 0

    def test_missing_manifest_returns_one(self, tmp_path):
        rc = main([
            "--manifest", str(tmp_path / "nope.json"),
            "--output", str(tmp_path / "out.json"),
        ])
        assert rc == 1

    def test_clean_aggregation_returns_zero(self, tmp_path):
        manifest = {
            "matrix_version": "v0",
            "cells": [
                {"cell_id": "X", "comparison_condition": None,
                 "scenarios": [], "skipped": False, "incomplete": False,
                 "trials_snapshot": [
                     {"status": "completed", "pass_": True,
                      "observed_route_class": "CLASS_1",
                      "latency_ms": 10.0},
                 ]},
            ],
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest))
        out_path = tmp_path / "out.json"
        rc = main([
            "--manifest", str(manifest_path),
            "--output", str(out_path),
        ])
        assert rc == 0
        assert out_path.exists()

    def test_skipped_cell_returns_two(self, tmp_path):
        manifest = {
            "matrix_version": "v0",
            "cells": [
                {"cell_id": "S", "comparison_condition": "rule_only",
                 "scenarios": [], "skipped": True,
                 "skip_reason": "tag missing",
                 "trials_snapshot": None},
            ],
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest))
        rc = main([
            "--manifest", str(manifest_path),
            "--output", str(tmp_path / "out.json"),
        ])
        assert rc == 2
