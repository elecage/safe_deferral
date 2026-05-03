"""Paper-eval digest exporter (doc 13 Phase 3).

Reads an aggregated_matrix.json (Phase 2 output) and emits paper-ready
CSV + Markdown:
- CSV: one row per cell, all CellResult fields. Paper authors can pivot
  this in their preferred tool.
- Markdown: cells grouped by sub-grid (BASELINE / Class 1 D1 / Class 2
  D2×D3×D4) with anchor_commits in the footer for reproducibility.

Boundary: pure consumer of aggregated_matrix.json. No dashboard / runner
/ aggregator-instance dependency. Output is human-readable text, but no
interpretation: 'static_only is worse than llm_assisted' style claims
belong to the paper author, not the toolchain (doc 13 §10 anti-goals).

Filename convention: digest_<matrix_version>_<timestamp>.{csv,md}
"""

import argparse
import csv
import io
import json
import logging
import pathlib
import sys
import time
from dataclasses import dataclass
from typing import Optional


log = logging.getLogger("paper_eval.digest")


# Order of columns in the CSV. Stable across versions so paper figure code
# can index by column name without breaking when new metrics get added at
# the end. Adding a new field: append to the end, don't reorder.
_CSV_COLUMNS = (
    "cell_id",
    "comparison_condition",
    "scenarios",
    "n_trials",
    "pass_rate",
    "by_route_class_class0",
    "by_route_class_class1",
    "by_route_class_class2",
    "by_route_class_unknown",
    "latency_ms_p50",
    "latency_ms_p95",
    "class2_clarification_correctness",
    "scan_history_yes_first_rate",
    "scan_history_present_count",
    "scan_ordering_applied_present_count",
    "skipped",
    "incomplete",
    # Trajectory / final-action breakdown — derived from each trial's
    # observation_history so a cell where the LLM legitimately deferred
    # and the system reached a useful action through CLASS_2 is no longer
    # collapsed to a binary fail. Counts are over ALL trials (including
    # timeouts), so columns sum to the cell's `requested_trials`.
    "outcome_path_class1_direct",
    "outcome_path_class2_to_class1",
    "outcome_path_class2_to_class0",
    "outcome_path_class2_safe_deferral",
    "outcome_path_class2_unresolved",
    "outcome_path_class0_direct",
    "outcome_path_timeout",
    "outcome_path_no_observation",
    "final_action_light_on",
    "final_action_light_off",
    "final_action_safe_deferral",
    "final_action_none",
    "final_target_living_room_light",
    "final_target_bedroom_light",
    "final_target_none",
    # Soft 'system reached design intent' verdict, complementary to the
    # strict pass_rate. See aggregator._trial_outcome_match for the
    # definition. None when n_trials == 0.
    "outcome_match_rate",
    # Semantic 'system reached the user's declared intent' verdict.
    # None when no trial in the cell carried user_intent_snapshot
    # (legacy scenario without user_intent block).
    "intent_match_rate",
    "intent_match_matched",
    "intent_match_not_matched",
    "intent_match_no_intent",
    "notes",
)


@dataclass
class SubGrid:
    """A logical grouping of cells in the matrix for paper presentation.
    Sub-grid order in the markdown output follows the order of these
    declarations."""

    title: str
    description: str
    cell_id_predicate: callable   # (cell_id) -> bool


_SUB_GRIDS = (
    SubGrid(
        title="Baseline",
        description="Reference cell — no overrides, deployment-default policy.",
        cell_id_predicate=lambda cid: cid == "BASELINE",
    ),
    SubGrid(
        title="Class 1 — Intent Recovery (D1)",
        description=(
            "Vary `experiment_mode` (direct_mapping / rule_only / "
            "llm_assisted). D2–D4 not applicable."
        ),
        cell_id_predicate=lambda cid: cid.startswith("C1_"),
    ),
    SubGrid(
        title="Class 2 — Candidate Source × Ordering × Interaction (D2 × D3 × D4)",
        description=(
            "Vary class2_candidate_source_mode / class2_scan_ordering_mode "
            "/ class2_input_mode. Includes opt-in multi-turn refinement variants."
        ),
        cell_id_predicate=lambda cid: cid.startswith("C2_"),
    ),
)


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_aggregated(path: pathlib.Path) -> dict:
    """Parse aggregated_matrix.json. Validates only that 'cells' is present
    so older formats can degrade gracefully."""
    if not path.exists():
        raise FileNotFoundError(f"aggregated matrix not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if "cells" not in data:
        raise ValueError(
            f"{path} has no 'cells' field — is this an aggregated matrix?"
        )
    return data


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def _format_optional_number(v) -> str:
    """CSV-friendly None handling. None → '' so the column reads as empty
    in spreadsheets (rather than literal 'None' which would corrupt
    downstream numeric parsing)."""
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _flatten_cell_for_csv(cell: dict) -> dict:
    """Flatten nested by_route_class dict + serialise list fields so each
    CellResult fits in one CSV row."""
    by_rc = cell.get("by_route_class") or {}
    paths = cell.get("outcome_path_distribution") or {}
    actions = cell.get("final_action_distribution") or {}
    targets = cell.get("final_target_distribution") or {}
    return {
        "cell_id": cell.get("cell_id", ""),
        "comparison_condition": cell.get("comparison_condition") or "",
        "scenarios": ";".join(cell.get("scenarios") or []),
        "n_trials": cell.get("n_trials", 0),
        "pass_rate": _format_optional_number(cell.get("pass_rate")),
        "by_route_class_class0": by_rc.get("CLASS_0", 0),
        "by_route_class_class1": by_rc.get("CLASS_1", 0),
        "by_route_class_class2": by_rc.get("CLASS_2", 0),
        "by_route_class_unknown": by_rc.get("unknown", 0),
        "latency_ms_p50": _format_optional_number(cell.get("latency_ms_p50")),
        "latency_ms_p95": _format_optional_number(cell.get("latency_ms_p95")),
        "class2_clarification_correctness": _format_optional_number(
            cell.get("class2_clarification_correctness")
        ),
        "scan_history_yes_first_rate": _format_optional_number(
            cell.get("scan_history_yes_first_rate")
        ),
        "scan_history_present_count": cell.get("scan_history_present_count", 0),
        "scan_ordering_applied_present_count": cell.get(
            "scan_ordering_applied_present_count", 0
        ),
        "skipped": "true" if cell.get("skipped") else "false",
        "incomplete": "true" if cell.get("incomplete") else "false",
        "outcome_path_class1_direct": paths.get("class1_direct", 0),
        "outcome_path_class2_to_class1": paths.get("class2_to_class1", 0),
        "outcome_path_class2_to_class0": paths.get("class2_to_class0", 0),
        "outcome_path_class2_safe_deferral": paths.get("class2_safe_deferral", 0),
        "outcome_path_class2_unresolved": paths.get("class2_unresolved", 0),
        "outcome_path_class0_direct": paths.get("class0_direct", 0),
        "outcome_path_timeout": paths.get("timeout", 0),
        "outcome_path_no_observation": paths.get("no_observation", 0),
        "final_action_light_on": actions.get("light_on", 0),
        "final_action_light_off": actions.get("light_off", 0),
        "final_action_safe_deferral": actions.get("safe_deferral", 0),
        "final_action_none": actions.get("none", 0),
        "final_target_living_room_light": targets.get("living_room_light", 0),
        "final_target_bedroom_light": targets.get("bedroom_light", 0),
        "final_target_none": targets.get("none", 0),
        "outcome_match_rate": _format_optional_number(
            cell.get("outcome_match_rate")
        ),
        "intent_match_rate": _format_optional_number(
            cell.get("intent_match_rate")
        ),
        "intent_match_matched": (
            (cell.get("intent_match_distribution") or {}).get("matched", 0)
        ),
        "intent_match_not_matched": (
            (cell.get("intent_match_distribution") or {}).get("not_matched", 0)
        ),
        "intent_match_no_intent": (
            (cell.get("intent_match_distribution") or {}).get("no_intent", 0)
        ),
        "notes": " | ".join(cell.get("notes") or []),
    }


def to_csv(matrix: dict) -> str:
    """Render the aggregated matrix as a CSV string with one row per cell.
    Column order is _CSV_COLUMNS (stable across versions — append-only)."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(_CSV_COLUMNS))
    writer.writeheader()
    for cell in matrix.get("cells", []):
        writer.writerow(_flatten_cell_for_csv(cell))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def _md_format_optional(v, suffix: str = "") -> str:
    """Markdown-cell formatter. None → em-dash so missing values are
    visually distinct from zero values in printed tables."""
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.4f}{suffix}"
    return f"{v}{suffix}"


def _md_format_distribution(dist: dict, keys: tuple) -> str:
    """Render a small histogram as a compact 'k1=n1, k2=n2' string. Keys
    with zero counts are omitted to keep the cell short. Returns '—' when
    every count is zero so the column reads as 'no signal' rather than '0'."""
    if not dist:
        return "—"
    parts = []
    for k in keys:
        v = dist.get(k, 0)
        if v:
            parts.append(f"{k}={v}")
    if not parts:
        return "—"
    return ", ".join(parts)


def _md_table_for_cells(cells: list) -> list:
    """Render a list of cells as a Markdown table. Returns the table as a
    list of lines so the caller can interleave headers / footers cleanly.

    Columns chosen for paper-table density. The strict pass_rate is kept,
    but the trajectory + final-action columns let a reader see WHERE
    'failed' trials ended up (e.g. CLASS_2 escalated to CLASS_1 via
    clarification, vs deferred to caregiver, vs timed out). The full
    per-route-class breakdown still lives in the CSV.
    """
    if not cells:
        return ["_(no cells in this sub-grid)_", ""]
    lines = [
        "| cell_id | condition | n | pass | match | intent | p50 ms | p95 ms | trajectory | final action | notes |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    _path_keys = (
        "class1_direct", "class2_to_class1", "class2_to_class0",
        "class2_safe_deferral", "class2_unresolved",
        "class0_direct", "timeout", "no_observation",
    )
    _action_keys = ("light_on", "light_off", "safe_deferral", "none")
    for c in cells:
        notes = "; ".join(c.get("notes") or []) or "—"
        trajectory = _md_format_distribution(
            c.get("outcome_path_distribution") or {}, _path_keys,
        )
        final_action = _md_format_distribution(
            c.get("final_action_distribution") or {}, _action_keys,
        )
        lines.append(
            "| `{cid}` | {cond} | {n} | {pr} | {om} | {im} | {p50} | {p95} | {traj} | {fa} | {notes} |".format(
                cid=c.get("cell_id", ""),
                cond=c.get("comparison_condition") or "_(default)_",
                n=c.get("n_trials", 0),
                pr=_md_format_optional(c.get("pass_rate")),
                om=_md_format_optional(c.get("outcome_match_rate")),
                im=_md_format_optional(c.get("intent_match_rate")),
                p50=_md_format_optional(c.get("latency_ms_p50")),
                p95=_md_format_optional(c.get("latency_ms_p95")),
                traj=trajectory,
                fa=final_action,
                notes=notes,
            )
        )
    lines.append("")
    return lines


def to_markdown(matrix: dict) -> str:
    """Render the aggregated matrix as a paper-ready Markdown report.
    Cells grouped by sub-grid (Baseline / Class 1 D1 / Class 2 D2×D3×D4).
    Footer carries anchor_commits + sweep timing for reproducibility."""
    lines = [
        f"# Paper-Eval Digest — matrix `{matrix.get('matrix_version', '?')}`",
        "",
        f"_Source manifest: `{matrix.get('matrix_path', '?')}`_",
        "",
    ]
    cells = matrix.get("cells", [])
    placed_ids = set()
    for sub in _SUB_GRIDS:
        sub_cells = [c for c in cells if sub.cell_id_predicate(c.get("cell_id", ""))]
        for sc in sub_cells:
            placed_ids.add(sc.get("cell_id"))
        lines.append(f"## {sub.title}")
        lines.append("")
        lines.append(sub.description)
        lines.append("")
        lines.extend(_md_table_for_cells(sub_cells))

    # Anything not placed by a sub-grid still gets shown so a malformed
    # cell_id doesn't silently drop from the digest.
    leftover = [c for c in cells if c.get("cell_id") not in placed_ids]
    if leftover:
        lines.append("## Other cells")
        lines.append("")
        lines.append("Cells whose cell_id did not match any defined sub-grid.")
        lines.append("")
        lines.extend(_md_table_for_cells(leftover))

    # Footer: anchor commits + sweep timing. This is the reproducibility
    # contract — same anchor_commits → same input set → digest can be
    # regenerated identically.
    lines.append("---")
    lines.append("")
    lines.append("## Reproducibility")
    lines.append("")
    anchors = matrix.get("anchor_commits") or {}
    if anchors:
        lines.append("| anchor | sha |")
        lines.append("|---|---|")
        for k in ("matrix_file_sha", "scenarios_dir_sha", "policy_table_sha"):
            v = anchors.get(k)
            lines.append(f"| `{k}` | `{v or 'unresolved'}` |")
        lines.append("")
    started = matrix.get("sweep_started_at_ms")
    finished = matrix.get("sweep_finished_at_ms")
    if started or finished:
        lines.append(
            f"_Sweep window: started_at_ms=`{started}` finished_at_ms=`{finished}`._"
        )
        lines.append("")
    lines.append(
        "_Digest emitted by `paper_eval.digest`. Measurements only — paper "
        "interpretation belongs to the author._"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S", time.localtime())


def write_digest(matrix: dict, output_dir: pathlib.Path,
                 timestamp: Optional[str] = None) -> tuple:
    """Write CSV + Markdown to output_dir. Filenames follow
    digest_<matrix_version>_<timestamp>.{csv,md}. Returns (csv_path, md_path).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = timestamp or _timestamp()
    version = matrix.get("matrix_version", "unknown")
    csv_path = output_dir / f"digest_{version}_{ts}.csv"
    md_path = output_dir / f"digest_{version}_{ts}.md"
    csv_path.write_text(to_csv(matrix), encoding="utf-8")
    md_path.write_text(to_markdown(matrix), encoding="utf-8")
    return csv_path, md_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="paper_eval.digest",
        description=(
            "Render a paper-eval aggregated matrix as paper-ready "
            "CSV + Markdown. Reads aggregated_matrix.json (Phase 2 output)."
        ),
    )
    p.add_argument("--aggregated", required=True, type=pathlib.Path,
                   help="Path to aggregated_matrix.json from paper_eval.aggregator")
    p.add_argument("--output-dir", required=True, type=pathlib.Path,
                   help="Directory for digest_<version>_<ts>.{csv,md}")
    p.add_argument("--timestamp", default=None,
                   help="Override timestamp suffix (default: now in YYYYMMDD_HHMMSS)")
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
        matrix = load_aggregated(args.aggregated.resolve())
    except (FileNotFoundError, ValueError) as exc:
        print(f"digest failed: {exc}", file=sys.stderr)
        return 1
    csv_path, md_path = write_digest(matrix, args.output_dir.resolve(),
                                     timestamp=args.timestamp)
    print(f"wrote {csv_path}", file=sys.stderr)
    print(f"wrote {md_path}", file=sys.stderr)
    print(str(csv_path))
    print(str(md_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
