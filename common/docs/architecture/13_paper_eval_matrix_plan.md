# Paper-Eval Matrix Plan

**Status:** Phase 0 design (this PR). Implementation phases land separately after maintainer alignment.
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

## 6. Sweep orchestrator (Phase 1)

CLI + library:

```
python -m paper_eval.sweep \
    --matrix integration/paper_eval/matrix_v1.json \
    --output integration/paper_eval/runs/$(date +%Y%m%d_%H%M%S)/ \
    [--trials-per-cell N] \
    [--cells CELL_A,CELL_B] \
    [--dashboard-url http://localhost:8000]
```

Behavior:
- Parses matrix file; resolves anchor_commits from git.
- For each cell:
  - Validates cell scenarios carry the required `comparison_conditions[]` tag (cross-check via existing P2.6 verifier logic).
  - Calls `POST /package_runs` once per scenario per cell.
  - Polls `GET /package_runs/{id}/metrics` until completion (or abort timeout).
  - Records `{cell_id, run_id, scenario_id, completed_at_ms, metrics_snapshot}` into the output dir.
- Writes `output/sweep_manifest.json` listing every run produced.

Failure modes (each kept observable, never silent):
- Cell scenario tag missing → orchestrator refuses to run the cell, prints which scenario failed validation.
- Run never completes → orchestrator records partial result + `incomplete: true`.
- Dashboard unreachable → orchestrator exits with non-zero before any matrix progress.

## 7. Cross-run aggregator (Phase 2)

Reads `sweep_manifest.json` + each run's exported metrics, joins on `cell_id`, produces:

```python
@dataclass
class CellResult:
    cell_id: str
    comparison_condition: Optional[str]
    scenarios: list[str]
    n_trials: int
    pass_rate: float
    by_route_class: dict[str, int]
    latency_ms_p50: float
    latency_ms_p95: float
    class2_clarification_correctness: Optional[float]   # if Class 2 cells
    scan_history_yes_first_rate: Optional[float]        # if scanning cells
    scan_ordering_applied_match_rate: Optional[float]   # if deterministic-ordering cells
    anchor_commits: dict
```

`AggregatedMatrix.cells: list[CellResult]` is the result; matrix-shape access via `.cell_by_dimensions(d1, d2, d3, d4)` for paper figure assembly.

## 8. Paper digest exporter (Phase 3)

Two outputs:

- **CSV** — one row per cell, columns = all `CellResult` fields (paper authors can pivot in their preferred tool).
- **Markdown** — paper-ready table grouped by sub-grid (Class 1 D1 / Class 2 D2×D3×D4 / baseline). Includes anchor_commits in the table footer for reproducibility.

Filename convention: `output/digest_v1_$(matrix_version)_$(timestamp).{csv,md}`.

## 9. Phase split (5 PRs after this design)

| Phase | PR | Deliverable |
|-------|-----|-------------|
| 0 | this PR | Design doc + matrix_v1.json + handoff |
| 1 | next | `paper_eval/sweep.py` orchestrator CLI + library + tests |
| 2 | after | `paper_eval/aggregator.py` cross-run aggregator + tests |
| 3 | after | `paper_eval/digest.py` CSV + Markdown exporter + tests |
| 4 | optional | Dashboard sweep-progress UI (deferred until Phases 1–3 prove the toolchain) |

Each implementation PR is self-contained: it depends on phase 0 (this design) but not on subsequent phases. Phases 1, 2, 3 can land in any order if needed.

## 10. Anti-goals

- No new product features (no new modes, no new comparison_conditions, no new scenarios).
- No interpretation: the toolchain produces measurements, the paper produces conclusions. Don't bake "static_only is worse than llm_assisted" into the digest format.
- No statistical inference in v1. Means / medians / percentiles only. CIs and significance come later if needed.
- No bypass of the dashboard API. Sweep orchestrator uses the same HTTP contract operators use.

## 11. Open questions for the maintainer

1. **Trials per cell** — 30 reasonable, or aim for 100 (cleaner stats, ~3× wall time)? Defer until first sweep tells us actual variance.
2. **Live dashboard view (Phase 4)** — worth building, or operator-CLI is enough for paper-eval? Defer until Phases 1–3 are in use.
3. **Matrix v2 versioning** — when paper review surfaces "we need cell X", is v2 a sibling file or a delta on v1? Recommend sibling so v1 stays reproducible.

## 12. Source notes

- 4-dimensional comparison framework: doc 10 §3.3 P2.3 + doc 12 §4.7 + §14 + §9 Phase 5 (PRs #79, #101, #110, #111).
- Scenario tagging: P2.6 verifier (`mac_mini/code/tests/test_scenario_manifest_p2_6.py`).
- Existing run + metrics surface: `rpi/code/dashboard/app.py` (`/package_runs`, `/package_runs/{id}/metrics`).
- `by_comparison_condition` aggregation: `rpi/code/experiment_package/trial_store.py::compute_metrics`.
- Phase-split convention: doc 11 / doc 12 (same plan-then-implement pattern).
