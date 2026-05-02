# Paper-Eval Matrix Plan

**Status:** Phases 0–4 shipped (PRs #122 / #123 / #125 / #126 / #131). Toolchain complete and dashboard-driven: matrix file → sweep → aggregator → digest → paper-ready CSV + Markdown, with live per-cell progress + artifact downloads available from the operator dashboard.
**Plan baseline:** Follow-up to PRs #112–#121 (post-doc-12 consistency backfill complete + sc01 relocation). The 4-dimensional comparison framework defined by PR #79 / #101 / #110 / #111 has docs / contracts / scenarios / verifier coverage. Now the *operational* layer — actually running trials across the matrix and producing paper-ready digests — is the next gap.

---

## 1. Purpose

Today the dashboard supports creating one `package_run` at a time with one primary `comparison_condition` (per-trial overrides also possible). Per-run metrics include `by_comparison_condition` aggregation. What's missing is:

1. A canonical **matrix definition** — which cells of (Class 1 intent recovery × Class 2 candidate source × Class 2 scanning ordering × Class 2 interaction model) the paper will report on, and how many trials per cell.
2. A **sweep orchestrator** — multi-run automation that reads the matrix, creates the runs, waits for completion, and writes a manifest of run_ids per cell.
3. A **cross-run aggregator** — joins per-cell metrics across runs into a single matrix-shaped result table.
4. A **paper digest exporter** — produces CSV + Markdown for direct inclusion in the paper.

This plan defines all four and breaks them into 4 implementation PRs after this design lands.

## 2. Scope

In scope:
- Matrix v1 JSON definition (`integration/paper_eval/matrix_v1.json`) — concrete cells, scenarios per cell, trial count, expected outcome anchors.
- Sweep orchestrator design (Python CLI + library API).
- Cross-run aggregator design (per-cell metric extraction + matrix join).
- Paper digest format (CSV columns, Markdown table layout).
- Phase split with one PR per phase.

Out of scope:
- Statistical inference layer (significance tests, confidence intervals). v1 ships descriptive stats only; inference belongs to a separate later round once measurement data exists.
- New scenarios beyond what's tagged today (P1.3–P1.5 + P2.6 covered the 9 conditions).
- Live dashboard sweep-monitoring UI. Phase 4 (deferred) candidate.
- New comparison_condition values. The 9 in Package A are exhaustive for the current four dimensions.

## 3. Non-Negotiable Boundaries

- **No new authority surface.** All work runs through the existing `POST /package_runs` and `POST /package_runs/{id}/trial` endpoints. No bypass of the runner, validator, or dispatcher.
- **No canonical-asset modification.** Matrix v1 lives under `integration/paper_eval/`, scenarios under `integration/scenarios/`, schemas/policies untouched.
- **Reproducibility first.** Each sweep run records the matrix file's git commit SHA, the scenario set's commit SHA, and the policy_table commit SHA into the manifest so a paper figure can be regenerated from the same commit set.
- **No paper-ready conclusions.** The aggregator produces *measurements*; interpretation (effect sizes, narratives, claims) is the paper author's job, not the toolchain's.

## 4. Matrix v1 Design

### 4.1 Dimensions

The 4 orthogonal comparison spaces from doc 12 §4.7:

| Dim | Field | Values | Applies to |
|---|---|---|---|
| D1 | `experiment_mode` (PR #79) | direct_mapping / rule_only / llm_assisted | Class 1 trials (intent recovery) |
| D2 | `class2_candidate_source_mode` (PR #101) | static_only / llm_assisted | Class 2 trials (generation) |
| D3 | `class2_scan_ordering_mode` (PR #110) | source_order / deterministic | Class 2 + scanning trials only |
| D4 | `class2_input_mode` (PR #111) | direct_select / scanning | Class 2 trials (interaction model) |

### 4.2 Cell selection

Full Cartesian = 3 × 2 × 2 × 2 = 24 cells, but D1 is meaningful only for Class 1 trials and D2–D4 only for Class 2. Two non-overlapping sub-grids:

- **Class 1 sub-grid** — vary D1 only, D2–D4 not applicable: **3 cells**.
- **Class 2 sub-grid** — vary D2 × D3 × D4: **8 cells**.

Plus a **baseline reference cell** (no overrides, defaults everywhere): **1 cell**.

**Total: 12 cells** for v1.

D3 (`scan_ordering_mode`) is meaningful only when D4 (`input_mode`) is `scanning`. Under `direct_select`, D3's value is not consulted — but matrix v1 still varies D3 across both D4 values to keep the cell-naming uniform; we document that the `direct_select × source_order` and `direct_select × deterministic` cells should produce identical metrics (this is itself a useful invariant check for the runner: if they diverge, the runner is consulting D3 outside scanning mode).

### 4.3 Trials per cell

v1 default: **30 trials per cell**. Rationale:
- Enough for descriptive stats (mean, median, p95) with reasonable noise floor.
- Small enough that the full 12-cell sweep finishes in one operator session: 12 × 30 = 360 trials. With the current shipped policy timing budget (`_class2_trial_timeout_s ≈ 368s` worst-case for Class 2), worst-case wall time is 360 × 6.13 min ≈ 37 hours of sequential trials. Realistic — most trials finish in seconds, not minutes.

The matrix file declares trial count per cell; operators can override globally (`--trials-per-cell N`) or per cell.

### 4.4 Scenarios per cell

Each cell pairs with the scenarios tagged for its dimension values via `comparison_conditions[]` (P2.6). The matrix file lists explicitly per cell; the orchestrator validates that each listed scenario carries the required tag (otherwise paper-eval would silently run the wrong scenarios).

### 4.5 Expected outcome anchors

Each cell declares `expected_route_class` / `expected_validation` / `expected_outcome` for trial completion. These are the same anchors used by today's `start_trial_async` so the verdict (pass/fail) flows through the existing TrialStore semantics.

## 5. Matrix file shape

```jsonc
{
  "matrix_version": "v1",
  "matrix_description": "...",
  "trials_per_cell_default": 30,
  "package_id": "A",
  "cells": [
    {
      "cell_id": "BASELINE",
      "description": "...",
      "comparison_condition": null,
      "scenarios": ["class1_baseline_scenario_skeleton.json"],
      "trials_per_cell": 30,
      "expected_route_class": "CLASS_1",
      "expected_validation": "approved"
    },
    {
      "cell_id": "C1_D1_DIRECT_MAPPING",
      "description": "Class 1 intent recovery via direct mapping",
      "comparison_condition": "direct_mapping",
      "scenarios": ["class1_baseline_scenario_skeleton.json"],
      "trials_per_cell": 30,
      "expected_route_class": "CLASS_1",
      "expected_validation": "approved"
    },
    ...
  ],
  "anchor_commits": {
    "_purpose": "Filled in by the orchestrator at sweep start so the resulting digest is reproducible.",
    "matrix_file_sha": null,
    "scenarios_dir_sha": null,
    "policy_table_sha": null
  }
}
```

The matrix v1 file lives at `integration/paper_eval/matrix_v1.json`. All future matrix versions are immutable: matrix_v2 lives alongside, never overwriting v1.

## 6. Sweep orchestrator (Phase 1) — shipped #123

CLI + library at `rpi/code/paper_eval/sweep.py`. Implementation diverges from the original sketch in two minor ways noted below.

```
python -m paper_eval.sweep \
    --matrix integration/paper_eval/matrix_v1.json \
    --output runs/$(date +%Y%m%d_%H%M%S)/ \
    --node-id <virtual-context-node-id> \
    [--scenarios-dir integration/scenarios] \
    [--dashboard-url http://localhost:8000] \
    [--poll-interval 2.0] \
    [--per-trial-timeout 600.0] \
    [-v]
```

Behavior:
- Parses matrix file; resolves `anchor_commits` from git (matrix file SHA, scenarios dir SHA, policy_table SHA).
- Pre-flight: `GET /health` + `GET /nodes` checked before any cell — fails fast if dashboard unreachable or `--node-id` not registered.
- For each cell, sequentially:
  - Validates cell scenarios carry the required `comparison_conditions[]` tag (P2.6 invariant). Tag-missing → cell skipped + reason recorded; rest of sweep continues.
  - Calls `POST /package_runs` **once per cell** (not per scenario — the dashboard contract treats one run as the cell-scoped unit; trials within fan out round-robin across `cell.scenarios`).
  - Fires `cell.trials_per_cell` trials via `POST /package_runs/{run_id}/trial`.
  - Polls `GET /package_runs/{run_id}` (not `/metrics`) until all trials are non-pending or per-cell deadline (`per_trial_timeout × trials_per_cell` — sequential worst case).
  - Snapshots `metrics_snapshot` (`/metrics`) **and** `trials_snapshot` (raw trial dicts from `/package_runs/{run_id}`) into the manifest. The trials_snapshot enables fully offline Phase 2 aggregation — no live dashboard needed after sweep finishes.
- Writes `output/sweep_manifest.json` with one cell entry containing `{cell_id, run_id, requested_trials, completed_trials, incomplete, skipped, skip_reason, metrics_snapshot, trials_snapshot, scenarios, expected_route_class, expected_validation, started_at_ms, finished_at_ms}` per cell.

Failure modes (each kept observable, never silent):
- Cell scenario tag missing → cell skipped, reason recorded in manifest, sweep continues.
- Run never completes → `incomplete: true` flag set on cell entry.
- Dashboard unreachable / requested node missing → `RuntimeError` before any matrix progress; CLI exit code 1.
- Some cells skipped/incomplete → CLI exit code 2 (success but with caveats); 0 only if all cells aggregated cleanly.

Not yet implemented (deferred to operations-driven needs): `--trials-per-cell N` global override, `--cells CELL_A,CELL_B` subset, concurrent cells, resume.

## 7. Cross-run aggregator (Phase 2) — shipped #125

`rpi/code/paper_eval/aggregator.py`. Reads `sweep_manifest.json` (specifically the `trials_snapshot` field added in Phase 2) and produces:

```python
@dataclass
class CellResult:
    cell_id: str
    comparison_condition: Optional[str]
    scenarios: list[str]
    n_trials: int                                   # completed trials only
    pass_rate: Optional[float]                      # None if n_trials == 0
    by_route_class: dict                            # {CLASS_0, CLASS_1, CLASS_2, unknown}
    latency_ms_p50: Optional[float]
    latency_ms_p95: Optional[float]
    class2_clarification_correctness: Optional[float]   # None unless cell has CLASS_2-expected trials
    scan_history_yes_first_rate: Optional[float]        # None unless trials carry scan_history
    scan_history_present_count: int
    scan_ordering_applied_present_count: int
    skipped: bool
    incomplete: bool
    notes: list                                     # human-readable diagnostics
```

`AggregatedMatrix.cells: list[CellResult]` plus `cell_by_id(cell_id)` lookup. Cell ordering matches the manifest (which matches the matrix file).

Notes vs the original sketch:
- `pass_rate`, `latency_ms_p50/p95`, `class2_clarification_correctness`, `scan_history_yes_first_rate` are `Optional[float]` (not `float`) — `None` when the cell has no applicable trials, distinct from `0.0` which would falsely imply "0% rate".
- `scan_ordering_applied_match_rate` deferred → replaced by `scan_ordering_applied_present_count`. Match-rate (applied vs expected ordering) belongs in Phase 3 once the digest needs it; v1 just measures presence.
- `anchor_commits` is on `AggregatedMatrix`, not on each `CellResult` — it applies to the whole sweep.
- `cell_by_dimensions(d1, d2, d3, d4)` deferred until paper figure code actually needs that lookup shape; `cell_by_id()` covers current digest needs.

CLI: `python -m paper_eval.aggregator --manifest <sweep_manifest.json> --output <aggregated_matrix.json>`. Exit codes mirror sweep (0 / 1 / 2).

## 8. Paper digest exporter (Phase 3) — shipped #126

`rpi/code/paper_eval/digest.py`. Reads `aggregated_matrix.json` and emits two paper-ready files:

- **CSV** — one row per cell, 18-column stable schema (`_CSV_COLUMNS`). Append-only column order so paper figure code that indexes by name keeps working when new metrics get added. `None` → empty string (spreadsheet numeric parsing safe).
- **Markdown** — paper-ready table grouped by sub-grid (Baseline / Class 1 D1 / Class 2 D2×D3×D4). Cells whose `cell_id` doesn't match any sub-grid land in an "Other cells" section (no silent drops). `None` → em-dash (visually distinct from zero). Footer carries `anchor_commits` (matrix_file_sha / scenarios_dir_sha / policy_table_sha) + sweep window timing — same anchors → same input → digest regenerable.

CLI: `python -m paper_eval.digest --aggregated <aggregated_matrix.json> --output-dir <dir> [--timestamp <ts>]`.

Filename convention: `digest_<matrix_version>_<timestamp>.{csv,md}`. matrix_v2 outputs coexist with v1 in the same directory.

## 9. Phase split (4 PRs after this design)

| Phase | PR | Status | Deliverable |
|-------|-----|---|-------------|
| 0 | [#122](https://github.com/elecage/safe_deferral/pull/122) | shipped | Design doc + `integration/paper_eval/matrix_v1.json` + handoff |
| 1 | [#123](https://github.com/elecage/safe_deferral/pull/123) | shipped | `paper_eval/sweep.py` orchestrator CLI + library + 17 tests |
| 2 | [#125](https://github.com/elecage/safe_deferral/pull/125) | shipped | `paper_eval/aggregator.py` cross-run aggregator + 28 tests; sweep additive (`trials_snapshot` + cell metadata in manifest enables fully offline aggregation) |
| 3 | [#126](https://github.com/elecage/safe_deferral/pull/126) | shipped | `paper_eval/digest.py` CSV (18-col stable schema) + Markdown (3 sub-grids + reproducibility footer) + 21 tests |
| 4 | [#131](https://github.com/elecage/safe_deferral/pull/131) | shipped (MVP) | `paper_eval/sweep_runner.py` + 6 dashboard endpoints under `/paper_eval/sweeps/` + ⑤ UI section with live per-cell progress + artifact downloads + 34 tests. Single-slot model; concurrent sweeps + history persistence deferred until usage demands. |

Each implementation PR is self-contained: depends on phase 0 (this design) but not on subsequent phases. Cumulative test count: 100 paper-eval-specific tests (17 sweep + 9 sweep callback + 8 runner + 28 aggregator + 21 digest + 17 endpoint), 0 regressions in mac_mini (711/711).

End-to-end usage:

```bash
# 1. Run sweep
PYTHONPATH=rpi/code python -m paper_eval.sweep \
    --matrix integration/paper_eval/matrix_v1.json \
    --output runs/<ts>/ --node-id <virtual-node-id>

# 2. Aggregate
PYTHONPATH=rpi/code python -m paper_eval.aggregator \
    --manifest runs/<ts>/sweep_manifest.json \
    --output runs/<ts>/aggregated_matrix.json

# 3. Digest
PYTHONPATH=rpi/code python -m paper_eval.digest \
    --aggregated runs/<ts>/aggregated_matrix.json \
    --output-dir runs/<ts>/digest/
# → runs/<ts>/digest/digest_v1_<ts>.{csv,md}
```

## 10. Anti-goals

- No new product features (no new modes, no new comparison_conditions, no new scenarios).
- No interpretation: the toolchain produces measurements, the paper produces conclusions. Don't bake "static_only is worse than llm_assisted" into the digest format.
- No statistical inference in v1. Means / medians / percentiles only. CIs and significance come later if needed.
- No bypass of the dashboard API. Sweep orchestrator uses the same HTTP contract operators use.

## 11. Open questions for the maintainer

1. **Trials per cell** — 30 reasonable, or aim for 100 (cleaner stats, ~3× wall time)? **Open** — answer requires running an actual sweep and observing variance. Tooling supports both (`--trials-per-cell N` global override; per-cell override in matrix file). First-sweep findings should be recorded back here, not in handoff history.
2. **Live dashboard view (Phase 4)** — **Resolved (#131):** shipped as MVP with single-slot model. Concurrent sweeps + history persistence remain deferred — revisit only if operational use surfaces a need (CLI still works for batch / scripted scenarios).
3. **Matrix v2 versioning** — when paper review surfaces "we need cell X", is v2 a sibling file or a delta on v1? **Recommended (not yet exercised):** sibling. v1 stays immutable; v2 lives at `integration/paper_eval/matrix_v2.json`; the digest filename convention (`digest_<matrix_version>_<ts>.{csv,md}`) means both versions' outputs coexist cleanly in the same `runs/<ts>/digest/` directory.

## 12. Source notes

- 4-dimensional comparison framework: doc 10 §3.3 P2.3 + doc 12 §4.7 + §14 + §9 Phase 5 (PRs #79, #101, #110, #111).
- Scenario tagging: P2.6 verifier (`mac_mini/code/tests/test_scenario_manifest_p2_6.py`).
- Existing run + metrics surface: `rpi/code/dashboard/app.py` (`/package_runs`, `/package_runs/{id}/metrics`).
- `by_comparison_condition` aggregation: `rpi/code/experiment_package/trial_store.py::compute_metrics`.
- Phase-split convention: doc 11 / doc 12 (same plan-then-implement pattern).
