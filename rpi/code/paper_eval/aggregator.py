"""Paper-eval cross-run aggregator (doc 13 Phase 2).

Reads a sweep_manifest.json produced by `paper_eval.sweep` and joins each
cell's trials_snapshot into a matrix-shaped `AggregatedMatrix`. One
`CellResult` is emitted per cell (skipped cells become empty CellResults so
downstream digest code can render them as 'no data' rows rather than
guessing).

Boundary: this module is a pure aggregator over the manifest. It does NOT
talk to the dashboard — the manifest must already carry trials_snapshot
(populated by sweep.py since the additive change in this same PR). If a
manifest predates that change and lacks trials_snapshot, the aggregator
emits CellResult with `n_trials=0` and a clear note in `notes`.

Out of scope for Phase 2:
- Statistical inference (CIs, significance) — descriptive stats only.
- Cross-cell normalisation (e.g. comparing baseline-relative deltas) —
  that's a Phase 3 (paper digest) decision.
- Live dashboard fetching — by design, aggregation is offline.
"""

import argparse
import json
import logging
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Optional


log = logging.getLogger("paper_eval.aggregator")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CellResult:
    """One cell's aggregated metrics. Mirrors doc 13 §7 with conservative
    typing — Optional[float] for cell-condition-dependent fields so a row
    that isn't applicable (e.g. scan_history on a non-scanning cell) reads
    as None rather than 0.0 (which would falsely imply '0% yes-first rate').
    """

    cell_id: str
    comparison_condition: Optional[str]
    scenarios: list                            # list[str]
    n_trials: int                              # completed trials only
    pass_rate: Optional[float]                 # None if n_trials == 0
    by_route_class: dict                       # {CLASS_0: int, CLASS_1: int, CLASS_2: int}
    latency_ms_p50: Optional[float]
    latency_ms_p95: Optional[float]
    class2_clarification_correctness: Optional[float]
    scan_history_yes_first_rate: Optional[float]
    scan_history_present_count: int
    scan_ordering_applied_present_count: int
    skipped: bool
    incomplete: bool
    notes: list = field(default_factory=list)  # human-readable diagnostics


@dataclass
class AggregatedMatrix:
    """Output of aggregate(). Carries the per-cell results plus the same
    anchor_commits the sweep recorded so a downstream digest can stamp
    figures with the producing commit set."""

    matrix_version: str
    matrix_path: str
    sweep_started_at_ms: int
    sweep_finished_at_ms: int
    anchor_commits: dict
    cells: list = field(default_factory=list)   # list[CellResult]

    def cell_by_id(self, cell_id: str) -> Optional[CellResult]:
        for c in self.cells:
            if c.cell_id == cell_id:
                return c
        return None

    def to_dict(self) -> dict:
        return {
            "matrix_version": self.matrix_version,
            "matrix_path": self.matrix_path,
            "sweep_started_at_ms": self.sweep_started_at_ms,
            "sweep_finished_at_ms": self.sweep_finished_at_ms,
            "anchor_commits": self.anchor_commits,
            "cells": [
                {
                    "cell_id": c.cell_id,
                    "comparison_condition": c.comparison_condition,
                    "scenarios": c.scenarios,
                    "n_trials": c.n_trials,
                    "pass_rate": c.pass_rate,
                    "by_route_class": c.by_route_class,
                    "latency_ms_p50": c.latency_ms_p50,
                    "latency_ms_p95": c.latency_ms_p95,
                    "class2_clarification_correctness":
                        c.class2_clarification_correctness,
                    "scan_history_yes_first_rate":
                        c.scan_history_yes_first_rate,
                    "scan_history_present_count":
                        c.scan_history_present_count,
                    "scan_ordering_applied_present_count":
                        c.scan_ordering_applied_present_count,
                    "skipped": c.skipped,
                    "incomplete": c.incomplete,
                    "notes": c.notes,
                }
                for c in self.cells
            ],
        }


# ---------------------------------------------------------------------------
# Manifest loading
# ---------------------------------------------------------------------------

def load_sweep_manifest(manifest_path: pathlib.Path) -> dict:
    """Parse sweep_manifest.json. Validates only the top-level shape (cells
    list present + matrix_version present). Field-level absence is handled
    leniently by aggregate() so older manifests still produce output rather
    than crash."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"sweep manifest not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "cells" not in data:
        raise ValueError(
            f"manifest {manifest_path} has no 'cells' field — "
            f"is this really a sweep_manifest.json?"
        )
    if "matrix_version" not in data:
        raise ValueError(
            f"manifest {manifest_path} missing matrix_version"
        )
    return data


# ---------------------------------------------------------------------------
# Per-cell aggregation primitives
# ---------------------------------------------------------------------------

def _percentile(values: list, pct: int) -> Optional[float]:
    """Nearest-rank percentile. Returns None on empty input. Matches the
    style used by experiment_package.trial_store._metrics_b so digest
    outputs line up with single-run dashboard metrics."""
    if not values:
        return None
    sorted_vals = sorted(values)
    idx = int(len(sorted_vals) * pct / 100)
    idx = min(idx, len(sorted_vals) - 1)
    return round(float(sorted_vals[idx]), 2)


def _completed_trials(trials_snapshot: Optional[list]) -> list:
    """Filter to trials that finished (status='completed'). 'pending' and
    'timeout' trials don't contribute to descriptive stats — they're noted
    on the cell's `incomplete` flag instead."""
    if not trials_snapshot:
        return []
    return [t for t in trials_snapshot if t.get("status") == "completed"]


def _by_route_class(trials: list) -> dict:
    """Bucket trials by observed_route_class. Returns counts for the three
    canonical classes plus 'unknown' for trials with no observation. Always
    includes all four keys so digest tables can render zero-value rows."""
    out = {"CLASS_0": 0, "CLASS_1": 0, "CLASS_2": 0, "unknown": 0}
    for t in trials:
        rc = t.get("observed_route_class") or "unknown"
        if rc not in out:
            out["unknown"] += 1
        else:
            out[rc] += 1
    return out


def _scan_history_yes_first_rate(trials: list) -> tuple:
    """For trials whose clarification_payload carries a non-empty
    scan_history, compute the fraction whose FIRST entry has response='yes'.
    Returns (rate, present_count). present_count == 0 → rate is None.

    Why 'first option yes-first': it's a useful proxy for whether the
    deterministic ordering is putting the most-likely-correct candidate
    first. Higher rate under deterministic ordering vs source_order is the
    paper-eval signal for D3 effectiveness.
    """
    present = 0
    yes_first = 0
    for t in trials:
        payload = t.get("clarification_payload") or {}
        history = payload.get("scan_history") or []
        if not history:
            continue
        present += 1
        first = history[0]
        if isinstance(first, dict) and first.get("response") == "yes":
            yes_first += 1
    if present == 0:
        return None, 0
    return round(yes_first / present, 4), present


def _scan_ordering_applied_present_count(trials: list) -> int:
    """Count trials whose clarification_payload carries a non-empty
    scan_ordering_applied list (PR #110). v1 just measures presence — a
    deeper 'applied ordering matches expected ordering' check belongs in
    Phase 3 once the digest needs it."""
    n = 0
    for t in trials:
        payload = t.get("clarification_payload") or {}
        applied = payload.get("scan_ordering_applied")
        if applied:
            n += 1
    return n


def _class2_clarification_correctness(trials: list) -> Optional[float]:
    """For trials whose expected_route_class is CLASS_2, compute the
    fraction that ALSO routed to CLASS_2 AND emitted a clarification_payload
    (non-None). Mirrors the spirit of trial_store._metrics_a's
    class2_handoff_correctness but adds the clarification-payload presence
    check — a Class 2 routing without a clarification payload would be a
    regression of the doc 4 contract.

    Returns None if there are no CLASS_2-expected trials in this cell.
    """
    expected_c2 = [t for t in trials if t.get("expected_route_class") == "CLASS_2"]
    if not expected_c2:
        return None
    correct = sum(
        1 for t in expected_c2
        if t.get("observed_route_class") == "CLASS_2"
        and t.get("clarification_payload") is not None
    )
    return round(correct / len(expected_c2), 4)


def _aggregate_cell(cell_dict: dict) -> CellResult:
    """Compute a CellResult from one cells[] entry of sweep_manifest.json.

    Notes are appended for two diagnostics future readers will care about:
    - the cell was skipped pre-creation (no trials to aggregate),
    - the cell was incomplete (some trials did not finish before deadline).
    Both translate to flags on the CellResult so a digest can render them
    as caveats in the table footer.
    """
    notes: list = []
    if cell_dict.get("skipped"):
        notes.append(f"skipped: {cell_dict.get('skip_reason') or 'unknown reason'}")
    if cell_dict.get("incomplete"):
        notes.append(
            f"incomplete: {cell_dict.get('completed_trials', 0)}/"
            f"{cell_dict.get('requested_trials', 0)} trials finished"
        )
    if cell_dict.get("trials_snapshot") is None and not cell_dict.get("skipped"):
        notes.append(
            "no trials_snapshot in manifest — sweep predates Phase 2 enabler; "
            "rerun sweep to enrich aggregation"
        )

    completed = _completed_trials(cell_dict.get("trials_snapshot"))
    n = len(completed)
    pass_rate = (
        round(sum(1 for t in completed if t.get("pass_")) / n, 4)
        if n else None
    )
    latencies = [
        t.get("latency_ms") for t in completed if t.get("latency_ms") is not None
    ]
    yes_first_rate, scan_history_count = _scan_history_yes_first_rate(completed)

    return CellResult(
        cell_id=cell_dict.get("cell_id", "<unknown>"),
        comparison_condition=cell_dict.get("comparison_condition"),
        scenarios=list(cell_dict.get("scenarios") or []),
        n_trials=n,
        pass_rate=pass_rate,
        by_route_class=_by_route_class(completed),
        latency_ms_p50=_percentile(latencies, 50),
        latency_ms_p95=_percentile(latencies, 95),
        class2_clarification_correctness=_class2_clarification_correctness(completed),
        scan_history_yes_first_rate=yes_first_rate,
        scan_history_present_count=scan_history_count,
        scan_ordering_applied_present_count=_scan_ordering_applied_present_count(
            completed
        ),
        skipped=bool(cell_dict.get("skipped")),
        incomplete=bool(cell_dict.get("incomplete")),
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Top-level aggregate
# ---------------------------------------------------------------------------

def aggregate(manifest: dict) -> AggregatedMatrix:
    """Build an AggregatedMatrix from a parsed sweep manifest dict.

    Cell ordering matches the manifest (which matches the matrix file).
    """
    cells = [_aggregate_cell(c) for c in manifest.get("cells", [])]
    return AggregatedMatrix(
        matrix_version=manifest.get("matrix_version", "<unknown>"),
        matrix_path=manifest.get("matrix_path", ""),
        sweep_started_at_ms=int(manifest.get("started_at_ms") or 0),
        sweep_finished_at_ms=int(manifest.get("finished_at_ms") or 0),
        anchor_commits=dict(manifest.get("anchor_commits") or {}),
        cells=cells,
    )


def write_aggregated(matrix: AggregatedMatrix, output_path: pathlib.Path) -> pathlib.Path:
    """Write the aggregated matrix as JSON. Returns the path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(matrix.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="paper_eval.aggregator",
        description=(
            "Aggregate a paper-eval sweep into a matrix-shaped result. "
            "Reads sweep_manifest.json (Phase 1 output) and writes "
            "aggregated_matrix.json (Phase 3 digest input)."
        ),
    )
    p.add_argument("--manifest", required=True, type=pathlib.Path,
                   help="Path to sweep_manifest.json from paper_eval.sweep")
    p.add_argument("--output", required=True, type=pathlib.Path,
                   help="Output path for aggregated_matrix.json")
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
    try:
        manifest = load_sweep_manifest(args.manifest.resolve())
    except (FileNotFoundError, ValueError) as exc:
        print(f"aggregator failed: {exc}", file=sys.stderr)
        return 1
    matrix = aggregate(manifest)
    out_path = write_aggregated(matrix, args.output.resolve())
    n = len(matrix.cells)
    n_skipped = sum(1 for c in matrix.cells if c.skipped)
    n_incomplete = sum(1 for c in matrix.cells if c.incomplete)
    print(
        f"aggregated {n} cells ({n_skipped} skipped, {n_incomplete} incomplete)",
        file=sys.stderr,
    )
    print(str(out_path))
    # Treat skipped/incomplete as a non-fatal warning (exit code 2) so an
    # operator running in CI can distinguish "all cells aggregated cleanly"
    # from "matrix has gaps you should know about" without parsing JSON.
    return 0 if n_skipped == 0 and n_incomplete == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
