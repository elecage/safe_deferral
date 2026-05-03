"""Tests for the paper-eval digest exporter (doc 13 Phase 3).

Exercises load_aggregated, CSV rendering, Markdown rendering with
sub-grid grouping, write_digest filename convention, end-to-end
sweep → aggregate → digest pipeline, and CLI surface. No real dashboard.
"""

import csv
import io
import json
import pathlib
from unittest.mock import MagicMock

import pytest

from paper_eval.aggregator import aggregate
from paper_eval.digest import (
    _CSV_COLUMNS,
    _flatten_cell_for_csv,
    load_aggregated,
    main,
    to_csv,
    to_markdown,
    write_digest,
)
from paper_eval.sweep import DashboardClient, Sweeper


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_REAL_MATRIX = _REPO_ROOT / "integration" / "paper_eval" / "matrix_v1.json"
_REAL_SCENARIOS = _REPO_ROOT / "integration" / "scenarios"


# ==================================================================
# load_aggregated
# ==================================================================

class TestLoadAggregated:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_aggregated(tmp_path / "nope.json")

    def test_missing_cells_field_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"matrix_version": "v1"}))
        with pytest.raises(ValueError, match="no 'cells' field"):
            load_aggregated(bad)

    def test_minimal_loads(self, tmp_path):
        ok = tmp_path / "ok.json"
        ok.write_text(json.dumps({"matrix_version": "v1", "cells": []}))
        data = load_aggregated(ok)
        assert data["cells"] == []


# ==================================================================
# _flatten_cell_for_csv
# ==================================================================

class TestFlattenCellForCsv:
    def test_full_cell_flattens_all_fields(self):
        cell = {
            "cell_id": "C2",
            "comparison_condition": "class2_scanning_input",
            "scenarios": ["a.json", "b.json"],
            "n_trials": 30,
            "pass_rate": 0.9333,
            "by_route_class": {"CLASS_0": 0, "CLASS_1": 0, "CLASS_2": 28, "unknown": 2},
            "latency_ms_p50": 1500.0,
            "latency_ms_p95": 2500.0,
            "class2_clarification_correctness": 0.95,
            "scan_history_yes_first_rate": 0.6667,
            "scan_history_present_count": 30,
            "scan_ordering_applied_present_count": 30,
            "skipped": False,
            "incomplete": False,
            "notes": [],
        }
        out = _flatten_cell_for_csv(cell)
        assert out["cell_id"] == "C2"
        assert out["scenarios"] == "a.json;b.json"
        assert out["pass_rate"] == "0.9333"
        assert out["by_route_class_class2"] == 28
        assert out["by_route_class_unknown"] == 2
        assert out["skipped"] == "false"
        assert out["notes"] == ""

    def test_none_values_render_as_empty_string(self):
        cell = {
            "cell_id": "X",
            "comparison_condition": None,
            "scenarios": [],
            "n_trials": 0,
            "pass_rate": None,
            "by_route_class": {},
            "latency_ms_p50": None,
            "latency_ms_p95": None,
            "class2_clarification_correctness": None,
            "scan_history_yes_first_rate": None,
            "scan_history_present_count": 0,
            "scan_ordering_applied_present_count": 0,
            "skipped": True,
            "incomplete": False,
            "notes": ["skipped: tag missing"],
        }
        out = _flatten_cell_for_csv(cell)
        assert out["pass_rate"] == ""
        assert out["latency_ms_p50"] == ""
        assert out["comparison_condition"] == ""
        assert out["skipped"] == "true"
        assert out["notes"] == "skipped: tag missing"


# ==================================================================
# to_csv — header + row format
# ==================================================================

class TestToCsv:
    def test_header_matches_csv_columns(self):
        out = to_csv({"cells": []})
        first_line = out.splitlines()[0]
        # csv module quotes only when needed; commas in column names would
        # fail this test if any were introduced.
        assert first_line == ",".join(_CSV_COLUMNS)

    def test_one_row_per_cell(self):
        m = {
            "cells": [
                {"cell_id": "A", "n_trials": 1, "pass_rate": 1.0,
                 "by_route_class": {"CLASS_1": 1}},
                {"cell_id": "B", "n_trials": 0, "pass_rate": None,
                 "by_route_class": {}},
            ],
        }
        rows = list(csv.DictReader(io.StringIO(to_csv(m))))
        assert len(rows) == 2
        assert rows[0]["cell_id"] == "A"
        assert rows[0]["pass_rate"] == "1.0000"
        assert rows[1]["pass_rate"] == ""

    def test_empty_matrix_emits_header_only(self):
        out = to_csv({"cells": []})
        # exactly the header line + trailing newline from DictWriter
        assert out.strip().splitlines() == [",".join(_CSV_COLUMNS)]


# ==================================================================
# to_markdown — sub-grid grouping
# ==================================================================

class TestToMarkdown:
    def test_three_subgrids_present_in_output(self):
        m = {
            "matrix_version": "v1",
            "cells": [
                {"cell_id": "BASELINE", "comparison_condition": None,
                 "n_trials": 30, "pass_rate": 1.0,
                 "by_route_class": {"CLASS_1": 30},
                 "latency_ms_p50": 50.0, "latency_ms_p95": 100.0,
                 "scan_history_present_count": 0,
                 "scan_ordering_applied_present_count": 0,
                 "notes": []},
                {"cell_id": "C1_D1_RULE_ONLY",
                 "comparison_condition": "rule_only", "n_trials": 30,
                 "pass_rate": 0.9, "by_route_class": {"CLASS_1": 27},
                 "latency_ms_p50": 60.0, "latency_ms_p95": 120.0,
                 "scan_history_present_count": 0,
                 "scan_ordering_applied_present_count": 0,
                 "notes": []},
                {"cell_id": "C2_D2_LLM_ASSISTED",
                 "comparison_condition": "class2_llm_assisted",
                 "n_trials": 30, "pass_rate": 0.95,
                 "by_route_class": {"CLASS_2": 30},
                 "latency_ms_p50": 1500.0, "latency_ms_p95": 2500.0,
                 "class2_clarification_correctness": 1.0,
                 "scan_history_present_count": 0,
                 "scan_ordering_applied_present_count": 0,
                 "notes": []},
            ],
        }
        out = to_markdown(m)
        assert "## Baseline" in out
        assert "## Class 1 — Intent Recovery (D1)" in out
        assert "## Class 2 — Candidate Source × Ordering × Interaction" in out
        assert "BASELINE" in out
        assert "C1_D1_RULE_ONLY" in out
        assert "C2_D2_LLM_ASSISTED" in out

    def test_anchor_commits_in_footer(self):
        m = {
            "matrix_version": "v1",
            "anchor_commits": {
                "matrix_file_sha": "abcd1234",
                "scenarios_dir_sha": "efgh5678",
                "policy_table_sha": "ijkl9012",
            },
            "cells": [],
        }
        out = to_markdown(m)
        assert "## Reproducibility" in out
        assert "abcd1234" in out
        assert "efgh5678" in out
        assert "ijkl9012" in out

    def test_unresolved_anchor_renders_unresolved(self):
        m = {
            "matrix_version": "v1",
            "anchor_commits": {
                "matrix_file_sha": None,
                "scenarios_dir_sha": None,
                "policy_table_sha": None,
            },
            "cells": [],
        }
        out = to_markdown(m)
        assert "unresolved" in out

    def test_unmatched_cell_id_falls_to_other_section(self):
        m = {
            "matrix_version": "v1",
            "cells": [{
                "cell_id": "WEIRD_NAME",
                "comparison_condition": "rule_only",
                "n_trials": 5, "pass_rate": 1.0,
                "by_route_class": {"CLASS_1": 5},
                "latency_ms_p50": 10.0, "latency_ms_p95": 20.0,
                "scan_history_present_count": 0,
                "scan_ordering_applied_present_count": 0,
                "notes": [],
            }],
        }
        out = to_markdown(m)
        assert "## Other cells" in out
        assert "WEIRD_NAME" in out

    def test_none_values_render_as_em_dash(self):
        m = {
            "matrix_version": "v1",
            "cells": [{
                "cell_id": "BASELINE",
                "comparison_condition": None,
                "n_trials": 0,
                "pass_rate": None,
                "by_route_class": {},
                "latency_ms_p50": None,
                "latency_ms_p95": None,
                "scan_history_present_count": 0,
                "scan_ordering_applied_present_count": 0,
                "notes": [],
            }],
        }
        out = to_markdown(m)
        assert "—" in out
        assert "_(default)_" in out

    def test_empty_subgrid_renders_no_cells_message(self):
        # No C1_ or C2_ cells anywhere — sub-grid still rendered with
        # a 'no cells' note rather than dropped silently.
        m = {"matrix_version": "v1", "cells": []}
        out = to_markdown(m)
        assert out.count("_(no cells in this sub-grid)_") >= 3


# ==================================================================
# write_digest — filename convention + content
# ==================================================================

class TestWriteDigest:
    def test_filenames_follow_convention(self, tmp_path):
        m = {"matrix_version": "v1", "cells": []}
        csv_path, md_path = write_digest(m, tmp_path, timestamp="20260502_103000")
        assert csv_path.name == "digest_v1_20260502_103000.csv"
        assert md_path.name == "digest_v1_20260502_103000.md"
        assert csv_path.exists()
        assert md_path.exists()

    def test_unknown_matrix_version_falls_back(self, tmp_path):
        m = {"cells": []}   # no matrix_version
        csv_path, md_path = write_digest(m, tmp_path, timestamp="ts")
        assert "unknown" in csv_path.name

    def test_content_round_trips(self, tmp_path):
        m = {
            "matrix_version": "v0",
            "cells": [{
                "cell_id": "A", "n_trials": 1, "pass_rate": 1.0,
                "by_route_class": {"CLASS_1": 1},
                "latency_ms_p50": 50.0, "latency_ms_p95": 50.0,
                "scan_history_present_count": 0,
                "scan_ordering_applied_present_count": 0,
                "notes": [],
            }],
        }
        csv_path, md_path = write_digest(m, tmp_path, timestamp="t")
        rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8")))
        assert rows[0]["cell_id"] == "A"
        md = md_path.read_text(encoding="utf-8")
        assert "matrix `v0`" in md
        assert "A" in md


# ==================================================================
# End-to-end: Sweeper → Aggregator → Digest
# ==================================================================

def _fake_client_with_trial_data():
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
            "trial_id": tid, "status": "completed", "pass_": True,
            "expected_route_class": expected_route_class,
            "observed_route_class": expected_route_class,
            "latency_ms": 100.0,
        })
        return {"trial_id": tid, "status": "pending"}
    client.start_trial.side_effect = _start_trial

    def _get_run(run_id):
        return {"run_id": run_id, "trials": started_trials.get(run_id, [])}
    client.get_package_run.side_effect = _get_run
    client.get_package_run_metrics.side_effect = lambda run_id: {
        "run_id": run_id, "total": len(started_trials.get(run_id, []))
    }
    return client


class TestEndToEnd:
    def test_sweep_aggregate_digest_full_pipeline(self, tmp_path):
        client = _fake_client_with_trial_data()
        sweeper = Sweeper(
            matrix_path=_REAL_MATRIX, scenarios_dir=_REAL_SCENARIOS,
            output_dir=tmp_path / "sweep", dashboard_url="http://fake",
            node_id="node-001", client=client, poll_interval_s=0.0,
        )
        sweep_result = sweeper.run()
        sweeper.write_manifest(sweep_result)

        manifest = json.loads((tmp_path / "sweep" / "sweep_manifest.json").read_text())
        agg = aggregate(manifest)
        agg_dict = agg.to_dict()

        csv_path, md_path = write_digest(agg_dict, tmp_path / "digest",
                                         timestamp="t")
        # CSV: 12 cells + header (10 ran with pass_rate=1.0000; the 2
        # MULTI_TURN cells were policy-skipped → empty pass_rate).
        rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8")))
        assert len(rows) == 12
        ran = [r for r in rows if r["skipped"] == "false"]
        skipped = [r for r in rows if r["skipped"] == "true"]
        assert len(ran) == 10
        assert len(skipped) == 2
        assert all(r["pass_rate"] == "1.0000" for r in ran)
        assert all(r["pass_rate"] == "" for r in skipped)
        # Markdown contains all three sub-grids and BASELINE row.
        md = md_path.read_text(encoding="utf-8")
        assert "BASELINE" in md
        assert "## Class 1" in md
        assert "## Class 2" in md
        assert "Reproducibility" in md


# ==================================================================
# CLI smoke
# ==================================================================

class TestCLI:
    def test_help_returns_zero(self):
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            with pytest.raises(SystemExit) as exc:
                main(["--help"])
        assert exc.value.code == 0

    def test_missing_aggregated_returns_one(self, tmp_path):
        rc = main([
            "--aggregated", str(tmp_path / "nope.json"),
            "--output-dir", str(tmp_path / "out"),
        ])
        assert rc == 1

    def test_clean_run_writes_both_files(self, tmp_path):
        agg = {"matrix_version": "v0", "cells": []}
        agg_path = tmp_path / "agg.json"
        agg_path.write_text(json.dumps(agg))
        out_dir = tmp_path / "out"
        rc = main([
            "--aggregated", str(agg_path),
            "--output-dir", str(out_dir),
            "--timestamp", "test_ts",
        ])
        assert rc == 0
        assert (out_dir / "digest_v0_test_ts.csv").exists()
        assert (out_dir / "digest_v0_test_ts.md").exists()


# ====================================================================
# Distribution columns (Problem C — derived from observation_history)
# ====================================================================

class TestDigestDistributionColumns:
    """The CSV columns and Markdown trajectory/final-action cells surface
    the per-cell breakdown from the aggregator's
    outcome_path_distribution / final_action_distribution / final_target_distribution.
    Without these, an LLM_ASSISTED cell where the LLM legitimately
    deferred and the system reached a useful action through CLASS_2
    would be invisible — the strict pass_rate alone collapses the
    information."""

    def _matrix_with_distributions(self):
        return {
            "matrix_version": "v0",
            "matrix_path": "x.json",
            "anchor_commits": {},
            "sweep_started_at_ms": 0,
            "sweep_finished_at_ms": 0,
            "cells": [
                {
                    "cell_id": "EXT_A_LLM_ASSISTED",
                    "comparison_condition": "llm_assisted",
                    "scenarios": ["s.json"],
                    "n_trials": 5,
                    "pass_rate": 0.6,
                    "by_route_class": {
                        "CLASS_0": 0, "CLASS_1": 3, "CLASS_2": 2, "unknown": 0,
                    },
                    "latency_ms_p50": 90000.0,
                    "latency_ms_p95": 100000.0,
                    "class2_clarification_correctness": None,
                    "scan_history_yes_first_rate": None,
                    "scan_history_present_count": 0,
                    "scan_ordering_applied_present_count": 0,
                    "skipped": False,
                    "incomplete": False,
                    "outcome_path_distribution": {
                        "class1_direct": 3,
                        "class2_safe_deferral": 2,
                        "class2_to_class1": 0,
                        "class2_to_class0": 0,
                        "class2_unresolved": 0,
                        "class0_direct": 0,
                        "no_observation": 0,
                        "timeout": 0,
                    },
                    "final_action_distribution": {
                        "light_on": 3, "light_off": 0,
                        "safe_deferral": 0, "none": 2,
                    },
                    "final_target_distribution": {
                        "living_room_light": 1, "bedroom_light": 2, "none": 2,
                    },
                    "notes": [],
                },
            ],
        }

    def test_csv_carries_distribution_columns(self):
        out = to_csv(self._matrix_with_distributions())
        rows = list(csv.DictReader(io.StringIO(out)))
        row = rows[0]
        assert row["outcome_path_class1_direct"] == "3"
        assert row["outcome_path_class2_safe_deferral"] == "2"
        assert row["outcome_path_timeout"] == "0"
        assert row["final_action_light_on"] == "3"
        assert row["final_action_none"] == "2"
        assert row["final_target_bedroom_light"] == "2"
        assert row["final_target_living_room_light"] == "1"

    def test_csv_distribution_columns_sum_to_n_trials_for_paths(self):
        """Sanity invariant: the trajectory bucket counts must sum to
        n_trials. The path distribution covers every trial including
        timeouts."""
        out = to_csv(self._matrix_with_distributions())
        rows = list(csv.DictReader(io.StringIO(out)))
        row = rows[0]
        path_keys = [
            "outcome_path_class1_direct",
            "outcome_path_class2_to_class1",
            "outcome_path_class2_to_class0",
            "outcome_path_class2_safe_deferral",
            "outcome_path_class2_unresolved",
            "outcome_path_class0_direct",
            "outcome_path_timeout",
            "outcome_path_no_observation",
        ]
        total = sum(int(row[k]) for k in path_keys)
        assert total == int(row["n_trials"])

    def test_csv_columns_are_append_only_compatible(self):
        """The original column ordering must be preserved (append-only
        invariant from the file's docstring) so paper figure code that
        indexes by column name keeps working."""
        original_prefix = (
            "cell_id,comparison_condition,scenarios,n_trials,pass_rate,"
            "by_route_class_class0,by_route_class_class1,"
            "by_route_class_class2,by_route_class_unknown,"
            "latency_ms_p50,latency_ms_p95,"
            "class2_clarification_correctness,"
            "scan_history_yes_first_rate,scan_history_present_count,"
            "scan_ordering_applied_present_count,skipped,incomplete,"
        )
        out = to_csv(self._matrix_with_distributions())
        first_line = out.splitlines()[0]
        assert first_line.startswith(original_prefix)
        assert first_line.endswith(",notes")

    def test_markdown_trajectory_column_renders_distribution(self):
        out = to_markdown(self._matrix_with_distributions())
        # Trajectory shows the non-zero buckets only.
        assert "class1_direct=3" in out
        assert "class2_safe_deferral=2" in out
        # Final action column shows what was actually executed.
        assert "light_on=3" in out
        assert "none=2" in out
        # Strict pass_rate is still present for binary verdict.
        assert "0.6000" in out

    def test_markdown_omits_zero_buckets_in_distribution_cells(self):
        """Trajectory / final-action cells must omit zero-count buckets so
        they don't get unreadably wide on cells that only exercise one or
        two paths."""
        out = to_markdown(self._matrix_with_distributions())
        # 0-count buckets must NOT appear (would make the cell noisy).
        assert "class2_to_class0=0" not in out
        assert "no_observation=0" not in out


class TestDigestOutcomeMatchColumn:
    """outcome_match_rate is a soft 'system reached design intent' verdict
    complementary to the strict pass_rate. Both must surface in the CSV
    and the Markdown table so a reviewer can compare them at a glance."""

    def _matrix_with_outcome_match(self, pass_rate, match_rate):
        return {
            "matrix_version": "v0",
            "matrix_path": "x.json",
            "anchor_commits": {},
            "sweep_started_at_ms": 0,
            "sweep_finished_at_ms": 0,
            "cells": [
                {
                    "cell_id": "C", "comparison_condition": "llm_assisted",
                    "scenarios": [], "n_trials": 5,
                    "pass_rate": pass_rate,
                    "outcome_match_rate": match_rate,
                    "by_route_class": {"CLASS_0": 0, "CLASS_1": 3,
                                       "CLASS_2": 2, "unknown": 0},
                    "latency_ms_p50": None, "latency_ms_p95": None,
                    "class2_clarification_correctness": None,
                    "scan_history_yes_first_rate": None,
                    "scan_history_present_count": 0,
                    "scan_ordering_applied_present_count": 0,
                    "skipped": False, "incomplete": False,
                    "outcome_path_distribution": {},
                    "final_action_distribution": {},
                    "final_target_distribution": {},
                    "notes": [],
                },
            ],
        }

    def test_csv_includes_outcome_match_rate_column(self):
        out = to_csv(self._matrix_with_outcome_match(0.4, 0.8))
        rows = list(csv.DictReader(io.StringIO(out)))
        assert rows[0]["outcome_match_rate"] == "0.8000"
        assert rows[0]["pass_rate"] == "0.4000"

    def test_csv_outcome_match_rate_empty_when_none(self):
        out = to_csv(self._matrix_with_outcome_match(None, None))
        rows = list(csv.DictReader(io.StringIO(out)))
        assert rows[0]["outcome_match_rate"] == ""

    def test_markdown_renders_outcome_match_column(self):
        """The Markdown table must show pass and match side by side so
        a reviewer can spot the case where strict pass=0 but the system
        consistently reached design intent through CLASS_2."""
        out = to_markdown(self._matrix_with_outcome_match(0.0, 1.0))
        # Header carries both columns.
        assert "| pass | match |" in out
        # Both values render with 4-digit precision.
        assert "0.0000" in out
        assert "1.0000" in out

    def test_markdown_outcome_match_em_dash_when_none(self):
        out = to_markdown(self._matrix_with_outcome_match(None, None))
        # The pass/match cells render as em-dash, not 'None' or ''.
        assert "| — | — |" in out
