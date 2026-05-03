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
    # Breakdown derived from each trial's observation_history
    # (PR #149's Fix 2 enables this). The strict pass_rate above hides
    # whether a 'fail' trial reached a useful outcome through CLASS_2;
    # these distributions surface the actual trajectory so a paper-honest
    # analysis can answer 'which path did the trial take' and 'what action
    # did the system finally execute' alongside the binary verdict.
    outcome_path_distribution: dict = field(default_factory=dict)  # path -> count
    final_action_distribution: dict = field(default_factory=dict)  # action -> count
    final_target_distribution: dict = field(default_factory=dict)  # target -> count
    # Soft verdict: did each trial reach the action prescribed by the
    # cell's expected_validation, regardless of which route_class got
    # there? A cell where strict pass_rate=0 but outcome_match_rate=1.0
    # is a system that worked as designed through CLASS_2 clarification.
    # None when n_trials == 0 (no trials to score).
    outcome_match_rate: Optional[float] = None
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
                    "outcome_path_distribution": dict(c.outcome_path_distribution),
                    "final_action_distribution": dict(c.final_action_distribution),
                    "final_target_distribution": dict(c.final_target_distribution),
                    "outcome_match_rate": c.outcome_match_rate,
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


def _trial_outcome_path(trial: dict) -> str:
    """Classify what trajectory this trial actually took, derived from
    observation_history (PR #149 Fix 2). The strict pass_/observed_route_class
    pair only tells you 'expected==observed'; this label tells you whether
    the system reached a CLASS_1 actuation directly, escalated to CLASS_2 and
    transitioned back to CLASS_1, escalated and stayed deferred, or never
    produced an observation at all.

    Categories (mutually exclusive, every completed trial maps to exactly
    one):

      timeout                 - trial timed out before any snapshot arrived
      no_observation          - completed but observation_history is empty
                                (defensive — should not happen in healthy runs)
      class0_direct           - CLASS_0 emergency from the first snapshot
      class1_direct           - CLASS_1 from the first snapshot (no CLASS_2
                                escalation in the path)
      class2_to_class1        - escalated to CLASS_2, ended with class2
                                transition_target=CLASS_1 (i.e. recovered to
                                a Class 1 actuation through clarification)
      class2_to_class0        - escalated to CLASS_2, ended with class2
                                transition_target=CLASS_0 (emergency
                                confirmation through clarification)
      class2_safe_deferral    - escalated to CLASS_2 and stayed deferred
                                (transition_target=SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION)
      class2_unresolved       - escalated to CLASS_2 but no terminal class2
                                snapshot recorded (e.g. trial ended on initial
                                routing snapshot before class2 update)

    Operates on observation_history; falls back to observation_payload only
    when history is empty so the function works on legacy trials too.
    """
    if trial.get("status") == "timeout":
        return "timeout"
    history = trial.get("observation_history") or []
    if not history:
        # Legacy fallback: derive from single-snapshot observation_payload.
        op = trial.get("observation_payload")
        history = [op] if isinstance(op, dict) else []
    if not history:
        return "no_observation"
    first = history[0]
    first_route = ((first.get("route") or {}).get("route_class")
                   or first.get("route_class"))
    if first_route == "CLASS_0":
        return "class0_direct"
    # Find the last class2 block in the history (post-transition snapshot).
    last_class2 = None
    for snap in history:
        c2 = snap.get("class2") or {}
        if c2.get("transition_target"):
            last_class2 = c2
    if first_route == "CLASS_1" and last_class2 is None:
        return "class1_direct"
    # If we reached CLASS_2 escalation, classify by transition target.
    if last_class2 is not None:
        target = last_class2.get("transition_target")
        if target == "CLASS_1":
            return "class2_to_class1"
        if target == "CLASS_0":
            return "class2_to_class0"
        if target == "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION":
            return "class2_safe_deferral"
        # Unknown transition_target value — leave a discoverable bucket
        # rather than silently lumping into class2_unresolved.
        return f"class2_unknown:{target}"
    # CLASS_2 in route but no class2 transition snapshot recorded.
    if first_route == "CLASS_2":
        return "class2_unresolved"
    return "unknown"


def _trial_final_action_target(trial: dict) -> tuple:
    """Return (final_action, final_target_device) for a trial — the action
    the system actually dispatched, derived from observation_history's ACK
    block. Falls back to the class2 candidate's action_hint / target_hint
    when no ACK was published, then to None when nothing was decided.

    Returns ('none', 'none') for trials that timed out or where no
    actionable snapshot was published; the strings are kept literal so they
    appear as histogram buckets alongside light_on / light_off without
    introducing a separate empty bucket.
    """
    if trial.get("status") == "timeout":
        return ("none", "none")
    history = trial.get("observation_history") or []
    if not history:
        op = trial.get("observation_payload")
        history = [op] if isinstance(op, dict) else []
    # Walk newest-first looking for an actionable snapshot.
    for snap in reversed(history):
        ack = snap.get("ack") or {}
        if ack.get("action") and ack.get("target_device"):
            return (ack["action"], ack["target_device"])
        c2 = snap.get("class2") or {}
        # class2 transition records the candidate's action_hint/target_hint
        # before validator/dispatcher run; useful when ACK didn't fire
        # (e.g. validator rejected, or transition_target=SAFE_DEFERRAL).
        if c2.get("action_hint") and c2.get("target_hint"):
            return (c2["action_hint"], c2["target_hint"])
    return ("none", "none")


def _outcome_path_distribution(trials: list) -> dict:
    """Bucket trials by _trial_outcome_path. Every bucket the function can
    emit appears in the result with at least 0; the canonical buckets are
    always present so downstream rendering can show consistent columns."""
    canonical = {
        "class0_direct": 0,
        "class1_direct": 0,
        "class2_to_class1": 0,
        "class2_to_class0": 0,
        "class2_safe_deferral": 0,
        "class2_unresolved": 0,
        "no_observation": 0,
        "timeout": 0,
    }
    out = dict(canonical)
    for t in trials:
        label = _trial_outcome_path(t)
        out[label] = out.get(label, 0) + 1
    return out


_ACTUATOR_ACTIONS: frozenset[str] = frozenset(("light_on", "light_off"))


def _trial_outcome_match(trial: dict) -> bool:
    """Soft 'did the system reach the action this cell's expected_validation
    prescribes' verdict, complementary to the strict expected_route_class
    pass_. Outcome match is True when:

    - the trial's strict pass_ is True (covers every cell type), OR
    - expected_validation == 'approved' AND the trial's final action is a
      catalog actuation (light_on / light_off) — i.e. the system reached
      the dispatch goal even if it took the CLASS_2 clarification path
      instead of the strict CLASS_1-direct path the matrix expected, OR
    - expected_validation == 'safe_deferral' AND the trial's final action
      is none / safe_deferral — i.e. the system correctly avoided
      autonomous actuation regardless of which route the matrix expected.

    Otherwise False. Operators get a 'system worked as designed' rate
    alongside the strict pass_rate without conflating the two; a cell
    where pass_rate=0 but outcome_match_rate=1.0 is a system that
    consistently reached design intent through the CLASS_2 path.
    """
    if trial.get("pass_"):
        return True
    expected_validation = trial.get("expected_validation")
    final_action, _ = _trial_final_action_target(trial)
    if expected_validation == "approved":
        return final_action in _ACTUATOR_ACTIONS
    if expected_validation == "safe_deferral":
        return final_action in ("none", "safe_deferral")
    return False


def _outcome_match_rate(trials: list) -> Optional[float]:
    """Fraction of trials in this list that reach the design-intent action.
    Returns None when the list is empty so the digest renders an em-dash
    rather than 0/0=NaN."""
    if not trials:
        return None
    matched = sum(1 for t in trials if _trial_outcome_match(t))
    return round(matched / len(trials), 4)


def _action_target_distributions(trials: list) -> tuple:
    """Bucket trials by (final_action, final_target_device). Returns the
    two histograms separately so a CSV column for each is straightforward.
    Canonical buckets included with 0 so absent paper-eval actions still
    render as zero-rows rather than disappear from the table."""
    action_canon = {"light_on": 0, "light_off": 0, "safe_deferral": 0, "none": 0}
    target_canon = {
        "living_room_light": 0, "bedroom_light": 0, "none": 0,
    }
    actions = dict(action_canon)
    targets = dict(target_canon)
    for t in trials:
        action, target = _trial_final_action_target(t)
        actions[action] = actions.get(action, 0) + 1
        targets[target] = targets.get(target, 0) + 1
    return actions, targets


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

    # Distributions consider every trial (not just completed) so timeouts
    # are visible — they're part of the cell's actual behaviour and would
    # otherwise disappear from the picture.
    all_trials = list(cell_dict.get("trials_snapshot") or [])
    outcome_paths = _outcome_path_distribution(all_trials)
    final_actions, final_targets = _action_target_distributions(all_trials)
    outcome_match_rate_val = _outcome_match_rate(all_trials)

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
        outcome_path_distribution=outcome_paths,
        final_action_distribution=final_actions,
        final_target_distribution=final_targets,
        outcome_match_rate=outcome_match_rate_val,
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
