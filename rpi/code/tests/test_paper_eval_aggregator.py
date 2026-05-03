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
    _action_target_distributions,
    _aggregate_cell,
    _by_route_class,
    _class2_clarification_correctness,
    _completed_trials,
    _outcome_match_rate,
    _outcome_path_distribution,
    _percentile,
    _scan_history_yes_first_rate,
    _scan_ordering_applied_present_count,
    _trial_final_action_target,
    _trial_outcome_match,
    _trial_outcome_path,
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
        # 10 cells run + 2 multi-turn skip (canonical policy has
        # class2_multi_turn_enabled=False — Sweeper enforces).
        ran = [c for c in matrix.cells if not c.skipped]
        skipped = [c for c in matrix.cells if c.skipped]
        assert len(ran) == 10
        assert len(skipped) == 2
        for c in ran:
            assert c.n_trials == 30
            assert c.pass_rate == 1.0
        for c in skipped:
            assert "MULTI_TURN" in c.cell_id
            assert c.n_trials == 0
        # Class 2 scanning cell still has clarification correctness.
        c2 = matrix.cell_by_id("C2_D4_SCANNING_INPUT")
        assert c2.class2_clarification_correctness == 1.0
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


# ==================================================================
# Trajectory + final action distributions (Problem C — observation_history)
# ==================================================================

class TestTrialOutcomePath:
    """_trial_outcome_path classifies a trial by what trajectory it took,
    derived from observation_history (PR #149 Fix 2). Each completed trial
    must map to exactly one canonical bucket so the per-cell distribution
    is well-defined."""

    def test_timeout_status_is_timeout_path(self):
        assert _trial_outcome_path({"status": "timeout"}) == "timeout"

    def test_empty_history_no_observation(self):
        assert _trial_outcome_path({
            "status": "completed",
            "observation_history": [],
        }) == "no_observation"

    def test_class1_direct_first_route_is_class1_no_class2_block(self):
        assert _trial_outcome_path({
            "status": "completed",
            "observation_history": [
                {"route": {"route_class": "CLASS_1"},
                 "validation": {"validation_status": "approved"}},
            ],
        }) == "class1_direct"

    def test_class0_direct_first_route_is_class0(self):
        assert _trial_outcome_path({
            "status": "completed",
            "observation_history": [
                {"route": {"route_class": "CLASS_0"}},
            ],
        }) == "class0_direct"

    def test_class2_to_class1_when_transition_target_class1(self):
        assert _trial_outcome_path({
            "status": "completed",
            "observation_history": [
                {"route": {"route_class": "CLASS_2"}},
                {"class2": {"transition_target": "CLASS_1"}},
            ],
        }) == "class2_to_class1"

    def test_class2_to_class0_when_transition_target_class0(self):
        assert _trial_outcome_path({
            "status": "completed",
            "observation_history": [
                {"route": {"route_class": "CLASS_2"}},
                {"class2": {"transition_target": "CLASS_0"}},
            ],
        }) == "class2_to_class0"

    def test_class2_safe_deferral_when_transition_target_safe(self):
        assert _trial_outcome_path({
            "status": "completed",
            "observation_history": [
                {"route": {"route_class": "CLASS_2"}},
                {"class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"}},
            ],
        }) == "class2_safe_deferral"

    def test_class2_unresolved_when_class2_route_no_transition(self):
        """A trial that escalated to CLASS_2 but no class2 transition
        snapshot was recorded (e.g. trial budget ran out before the user
        phase completed) goes to a discoverable 'unresolved' bucket so it
        does not silently lump with safe_deferral."""
        assert _trial_outcome_path({
            "status": "completed",
            "observation_history": [
                {"route": {"route_class": "CLASS_2"}},
            ],
        }) == "class2_unresolved"

    def test_legacy_observation_payload_fallback(self):
        """Trials from before PR #149 only have observation_payload (single
        snapshot), no observation_history. _trial_outcome_path must still
        classify them so historical archives can be re-aggregated."""
        assert _trial_outcome_path({
            "status": "completed",
            "observation_history": [],
            "observation_payload": {"route": {"route_class": "CLASS_1"}},
        }) == "class1_direct"


class TestTrialFinalActionTarget:
    """_trial_final_action_target reads the actually-dispatched action and
    target from the observation history's ack block. Falls back to class2
    transition's action_hint / target_hint when no ACK fired."""

    def test_timeout_returns_none_pair(self):
        assert _trial_final_action_target({"status": "timeout"}) == ("none", "none")

    def test_empty_history_returns_none_pair(self):
        assert _trial_final_action_target({
            "status": "completed", "observation_history": [],
        }) == ("none", "none")

    def test_ack_in_history_wins(self):
        assert _trial_final_action_target({
            "status": "completed",
            "observation_history": [
                {"route": {"route_class": "CLASS_1"},
                 "ack": {"action": "light_on", "target_device": "bedroom_light"}},
            ],
        }) == ("light_on", "bedroom_light")

    def test_class2_transition_action_hint_when_no_ack(self):
        """When the class2 transition recorded action_hint/target_hint but
        no ack was published (e.g. validator rejected, or CLASS_2→
        SAFE_DEFERRAL), the candidate's action_hint is the most informative
        thing we can show as the 'attempted final action'."""
        assert _trial_final_action_target({
            "status": "completed",
            "observation_history": [
                {"route": {"route_class": "CLASS_2"}},
                {"class2": {
                    "transition_target": "CLASS_1",
                    "action_hint": "light_on",
                    "target_hint": "bedroom_light",
                }},
            ],
        }) == ("light_on", "bedroom_light")

    def test_class2_safe_deferral_with_no_action_returns_none_pair(self):
        """A pure SAFE_DEFERRAL Class 2 transition does not carry
        action_hint — the trial executed nothing actionable."""
        assert _trial_final_action_target({
            "status": "completed",
            "observation_history": [
                {"route": {"route_class": "CLASS_2"}},
                {"class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"}},
            ],
        }) == ("none", "none")

    def test_newest_ack_wins_when_multiple(self):
        """Multiple snapshots with ack — the newest one is what the system
        actually did last."""
        assert _trial_final_action_target({
            "status": "completed",
            "observation_history": [
                {"ack": {"action": "light_on", "target_device": "bedroom_light"}},
                {"ack": {"action": "light_off", "target_device": "living_room_light"}},
            ],
        }) == ("light_off", "living_room_light")


class TestTrialOutcomeMatch:
    """The soft 'system reached design intent' verdict per trial. True when
    strict pass is True, or final action satisfies expected_validation."""

    def test_strict_pass_always_matches(self):
        assert _trial_outcome_match({
            "pass_": True, "expected_validation": "approved",
        }) is True
        assert _trial_outcome_match({
            "pass_": True, "expected_validation": "safe_deferral",
        }) is True

    def test_approved_intent_matches_when_actuator_action(self):
        # Strict fail but ack reached light_on → matches.
        assert _trial_outcome_match({
            "pass_": False,
            "expected_validation": "approved",
            "observation_history": [
                {"ack": {"action": "light_on", "target_device": "bedroom_light"}},
            ],
        }) is True
        assert _trial_outcome_match({
            "pass_": False,
            "expected_validation": "approved",
            "observation_history": [
                {"ack": {"action": "light_off", "target_device": "living_room_light"}},
            ],
        }) is True

    def test_approved_intent_does_not_match_when_no_actuation(self):
        assert _trial_outcome_match({
            "pass_": False,
            "expected_validation": "approved",
            "observation_history": [
                {"route": {"route_class": "CLASS_2"}},
                {"class2": {"transition_target":
                             "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"}},
            ],
        }) is False

    def test_safe_deferral_intent_matches_when_no_actuation(self):
        # rule_only / direct_mapping cells whose expected_validation is
        # safe_deferral consider 'system did not actuate' as success.
        assert _trial_outcome_match({
            "pass_": False,
            "expected_validation": "safe_deferral",
            "observation_history": [
                {"route": {"route_class": "CLASS_2"}},
                {"class2": {"transition_target":
                             "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"}},
            ],
        }) is True

    def test_safe_deferral_intent_does_not_match_when_actuator_fired(self):
        # direct_mapping over-acting fails the safety intent.
        assert _trial_outcome_match({
            "pass_": False,
            "expected_validation": "safe_deferral",
            "observation_history": [
                {"route": {"route_class": "CLASS_1"},
                 "ack": {"action": "light_on", "target_device": "living_room_light"}},
            ],
        }) is False

    def test_timeout_does_not_match(self):
        assert _trial_outcome_match({
            "status": "timeout", "pass_": False,
            "expected_validation": "approved",
        }) is False

    def test_outcome_match_rate_none_on_empty_input(self):
        assert _outcome_match_rate([]) is None


class TestDistributions:
    """Per-cell distributions over a list of trials. Canonical buckets are
    always present (with 0 when absent) so digest tables can render
    consistent columns across cells."""

    def test_outcome_path_distribution_canonical_keys_present(self):
        d = _outcome_path_distribution([])
        for key in (
            "class0_direct", "class1_direct", "class2_to_class1",
            "class2_to_class0", "class2_safe_deferral",
            "class2_unresolved", "no_observation", "timeout",
        ):
            assert key in d
            assert d[key] == 0

    def test_outcome_path_distribution_counts_correctly(self):
        trials = [
            {"status": "completed", "observation_history": [
                {"route": {"route_class": "CLASS_1"}}]},
            {"status": "completed", "observation_history": [
                {"route": {"route_class": "CLASS_1"}}]},
            {"status": "completed", "observation_history": [
                {"route": {"route_class": "CLASS_2"}},
                {"class2": {"transition_target":
                            "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"}}]},
            {"status": "timeout"},
        ]
        d = _outcome_path_distribution(trials)
        assert d["class1_direct"] == 2
        assert d["class2_safe_deferral"] == 1
        assert d["timeout"] == 1
        # other buckets stay at zero
        assert d["class0_direct"] == 0

    def test_action_target_distributions_canonical_keys_present(self):
        actions, targets = _action_target_distributions([])
        for key in ("light_on", "light_off", "safe_deferral", "none"):
            assert key in actions
            assert actions[key] == 0
        for key in ("living_room_light", "bedroom_light", "none"):
            assert key in targets
            assert targets[key] == 0

    def test_action_target_distributions_counts_acks(self):
        trials = [
            {"status": "completed", "observation_history": [
                {"ack": {"action": "light_on", "target_device": "bedroom_light"}}]},
            {"status": "completed", "observation_history": [
                {"ack": {"action": "light_on", "target_device": "living_room_light"}}]},
            {"status": "timeout"},
        ]
        actions, targets = _action_target_distributions(trials)
        assert actions["light_on"] == 2
        assert actions["none"] == 1
        assert targets["bedroom_light"] == 1
        assert targets["living_room_light"] == 1
        assert targets["none"] == 1


class TestAggregateCellWithDistributions:
    """_aggregate_cell now records outcome_path / final_action / final_target
    distributions on the CellResult. Distributions are computed over ALL
    trials (incl. timeouts) so the histogram sums to the cell's
    requested_trials — invariant the digest CSV depends on."""

    def test_cell_result_carries_distributions(self):
        cell_dict = {
            "cell_id": "X",
            "comparison_condition": "llm_assisted",
            "scenarios": ["s.json"],
            "trials_snapshot": [
                {"status": "completed", "pass_": True,
                 "observed_route_class": "CLASS_1",
                 "observation_history": [
                     {"route": {"route_class": "CLASS_1"},
                      "validation": {"validation_status": "approved"},
                      "ack": {"action": "light_on", "target_device": "bedroom_light"}},
                 ]},
                {"status": "completed", "pass_": False,
                 "observed_route_class": "CLASS_2",
                 "observation_history": [
                     {"route": {"route_class": "CLASS_2"}},
                     {"class2": {"transition_target":
                                  "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"}},
                 ]},
                {"status": "timeout", "pass_": False},
            ],
        }
        result = _aggregate_cell(cell_dict)
        # Strict pass_rate unchanged (1 of 2 completed trials passed).
        assert result.pass_rate == 0.5
        # Distributions cover every trial (3 total).
        assert result.outcome_path_distribution["class1_direct"] == 1
        assert result.outcome_path_distribution["class2_safe_deferral"] == 1
        assert result.outcome_path_distribution["timeout"] == 1
        path_total = sum(result.outcome_path_distribution.values())
        assert path_total == 3
        assert result.final_action_distribution["light_on"] == 1
        assert result.final_action_distribution["none"] == 2
        assert result.final_target_distribution["bedroom_light"] == 1
        assert result.final_target_distribution["none"] == 2

    def test_cell_result_carries_outcome_match_rate(self):
        """outcome_match_rate is the soft 'system reached design intent'
        verdict — True when strict pass, OR (expected approved AND final
        action is light_on/off), OR (expected safe_deferral AND no
        actuation)."""
        cell_dict = {
            "cell_id": "X",
            "comparison_condition": "llm_assisted",
            "scenarios": [],
            "trials_snapshot": [
                # strict pass — counts toward outcome_match
                {"status": "completed", "pass_": True,
                 "expected_validation": "approved",
                 "observation_history": [
                     {"ack": {"action": "light_on", "target_device": "bedroom_light"}},
                 ]},
                # strict fail (CLASS_2 route observed) but reached actuation
                # via class2_to_class1 transition — counts toward outcome_match
                {"status": "completed", "pass_": False,
                 "expected_validation": "approved",
                 "observation_history": [
                     {"route": {"route_class": "CLASS_2"}},
                     {"class2": {"transition_target": "CLASS_1"},
                      "ack": {"action": "light_on", "target_device": "living_room_light"}},
                 ]},
                # strict fail and no actuation — does NOT count
                {"status": "completed", "pass_": False,
                 "expected_validation": "approved",
                 "observation_history": [
                     {"route": {"route_class": "CLASS_2"}},
                     {"class2": {"transition_target":
                                  "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"}},
                 ]},
                # timeout — does NOT count
                {"status": "timeout", "pass_": False,
                 "expected_validation": "approved"},
            ],
        }
        result = _aggregate_cell(cell_dict)
        # 1 strict pass + 1 reached-actuation-via-class2 → 2 / 4 = 0.5
        assert result.outcome_match_rate == 0.5
        # Strict pass_rate disagrees: only 1 / 3 completed = 0.3333
        assert result.pass_rate == round(1 / 3, 4)

    def test_cell_result_outcome_match_safe_deferral_intent(self):
        """For a cell whose expected_validation is safe_deferral
        (e.g. EXT_A_DIRECT_MAPPING, EXT_A_RULE_ONLY where the safety-correct
        behaviour is to NOT actuate), outcome_match counts trials where
        the system did not produce a catalog action."""
        cell_dict = {
            "cell_id": "X",
            "comparison_condition": "rule_only",
            "scenarios": [],
            "trials_snapshot": [
                # strict pass: routed CLASS_2 + safe_deferral
                {"status": "completed", "pass_": True,
                 "expected_validation": "safe_deferral",
                 "observation_history": [
                     {"route": {"route_class": "CLASS_2"}},
                     {"class2": {"transition_target":
                                  "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"}},
                 ]},
                # strict fail (routed CLASS_1, table over-acted) — no
                # safe_deferral observed → outcome_match=False
                {"status": "completed", "pass_": False,
                 "expected_validation": "safe_deferral",
                 "observation_history": [
                     {"route": {"route_class": "CLASS_1"},
                      "ack": {"action": "light_on", "target_device": "living_room_light"}},
                 ]},
            ],
        }
        result = _aggregate_cell(cell_dict)
        assert result.outcome_match_rate == 0.5

    def test_cell_result_outcome_match_serialises(self):
        cell_dict = {
            "cell_id": "X",
            "comparison_condition": "llm_assisted",
            "scenarios": [],
            "trials_snapshot": [
                {"status": "completed", "pass_": True,
                 "expected_validation": "approved",
                 "observation_history": [
                     {"ack": {"action": "light_on", "target_device": "bedroom_light"}},
                 ]},
            ],
        }
        cells = [_aggregate_cell(cell_dict)]
        agg = AggregatedMatrix(
            matrix_version="v1", matrix_path="",
            sweep_started_at_ms=0, sweep_finished_at_ms=0,
            anchor_commits={}, cells=cells,
        )
        assert agg.to_dict()["cells"][0]["outcome_match_rate"] == 1.0

    def test_cell_result_distributions_serialise(self):
        """Distributions must round-trip through to_dict so the
        aggregated_matrix.json carries them for the digest."""
        cell_dict = {
            "cell_id": "X",
            "comparison_condition": "rule_only",
            "scenarios": [],
            "trials_snapshot": [
                {"status": "completed", "pass_": True,
                 "observation_history": [
                     {"route": {"route_class": "CLASS_2"}},
                     {"class2": {"transition_target":
                                  "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"}},
                 ]},
            ],
        }
        cells = [_aggregate_cell(cell_dict)]
        agg = AggregatedMatrix(
            matrix_version="v1", matrix_path="",
            sweep_started_at_ms=0, sweep_finished_at_ms=0,
            anchor_commits={}, cells=cells,
        )
        serialised = agg.to_dict()
        cell_out = serialised["cells"][0]
        assert "outcome_path_distribution" in cell_out
        assert cell_out["outcome_path_distribution"]["class2_safe_deferral"] == 1
        assert "final_action_distribution" in cell_out
        assert "final_target_distribution" in cell_out
