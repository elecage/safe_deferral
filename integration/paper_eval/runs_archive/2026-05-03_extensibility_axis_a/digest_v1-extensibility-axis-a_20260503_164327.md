# Paper-Eval Digest — matrix `v1-extensibility-axis-a`

_Source manifest: `/Users/dsc-nb14/safe_deferral_claude/.claude/worktrees/blissful-haslett-9b88e2/integration/paper_eval/matrix_extensibility.json`_

## Baseline

Reference cell — no overrides, deployment-default policy.

_(no cells in this sub-grid)_

## Class 1 — Intent Recovery (D1)

Vary `experiment_mode` (direct_mapping / rule_only / llm_assisted). D2–D4 not applicable.

_(no cells in this sub-grid)_

## Class 2 — Candidate Source × Ordering × Interaction (D2 × D3 × D4)

Vary class2_candidate_source_mode / class2_scan_ordering_mode / class2_input_mode. Includes opt-in multi-turn refinement variants.

_(no cells in this sub-grid)_

## Other cells

Cells whose cell_id did not match any defined sub-grid.

| cell_id | condition | n | pass | p50 ms | p95 ms | class2 ✓ | scan-yes-first | notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `EXT_A_DIRECT_MAPPING` | direct_mapping | 30 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | — | — |
| `EXT_A_RULE_ONLY` | rule_only | 30 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | — | — |
| `EXT_A_LLM_ASSISTED` | llm_assisted | 18 | 0.2778 | 11388.0000 | 12114.0000 | — | — | — |

---

## Reproducibility

| anchor | sha |
|---|---|
| `matrix_file_sha` | `c86d2ac14d5f159dca5c8764bf63b80e157b13fb` |
| `scenarios_dir_sha` | `4d51cfb963c863d87b455bce183880f0a559598b` |
| `policy_table_sha` | `a81b204e76e97ec4bb28ac404168233a84004626` |

_Sweep window: started_at_ms=`1777792048374` finished_at_ms=`1777794207318`._

_Digest emitted by `paper_eval.digest`. Measurements only — paper interpretation belongs to the author._
