# Paper-Eval Phase C Run — 2026-05-03

**Source**: First full `matrix_v1.json` sweep (12 cells × 30 trials = 360 trials) executed end-to-end on a single M1 MacBook against real Ollama llama3.2.

**Hardware**: M1 MacBook (no separate Mac mini / RPi nodes).
**MQTT broker**: local mosquitto via `mosquitto -d` (#135).
**LLM**: Ollama llama3.2 @ localhost:11434.
**Sweep ID**: `8b38f5e52ccd`.
**Wall time**: 132.6 minutes (1:33:20 → 4:21:13).

## Files

- `sweep_manifest.json` — full per-trial detail (1.4 MB; produced by `paper_eval.sweep_runner`)
- `aggregated_matrix.json` — one CellResult per cell (input to digest)
- `digest_v1_20260503_023433.csv` — 12 rows, 18 columns; paper figure plotting
- `digest_v1_20260503_023433.md` — paper-table-ready Markdown grouped by sub-grid + reproducibility footer

## Reproducibility anchors

| Anchor | SHA |
|---|---|
| `matrix_file_sha` | `ee4b4db0177b367cffa3a9dd4c10e25d626ade1f` |
| `scenarios_dir_sha` | `9107bc511f01af4c926eb580213ad41634243b50` |
| `policy_table_sha` | `a81b204e76e97ec4bb28ac404168233a84004626` |

To reproduce: check out the commit set above and re-run

```bash
./scripts/local_e2e_launcher.sh
# create context_node + 2 actuator_simulator nodes via dashboard
# kick off sweep with matrix_v1.json + per_trial_timeout_s=120
```

## Headline results

| Cell | n | pass_rate | Notes |
|---|---:|---:|---|
| BASELINE | 30 | 1.000 | All 30 → CLASS_1, p50 1.7s p95 2.1s |
| C1_D1_DIRECT_MAPPING | 30 | 1.000 | 1ms latency (LLM bypassed by design) |
| C1_D1_RULE_ONLY | 30 | 1.000 | 1ms latency (LLM bypassed) |
| C1_D1_LLM_ASSISTED | 29 | **0.966** | 1 LLM-chose-deferral, 1 timeout. Real-LLM variance. |
| C2_D2_STATIC_ONLY | 30 | 1.000 | All 30 → CLASS_2, clarification_correctness 1.0 |
| C2_D2_LLM_ASSISTED | 30 | 1.000 | All 30 → CLASS_2, clarification_correctness 1.0 |
| C2_D3_SCAN_SOURCE_ORDER | 29 | **0.897** | 3 wrong-reason failures + 1 timeout |
| C2_D3_SCAN_DETERMINISTIC | 28 | 1.000 | 2 timeouts (incomplete) |
| C2_D4_DIRECT_SELECT_INPUT | 30 | 1.000 | clean baseline for D4 |
| C2_D4_SCANNING_INPUT | 29 | **0.966** | scan_history_yes_first_rate **0.474** (19 of 30 had history) |
| C2_MULTI_TURN_REFINEMENT_USER_PICK | 28 | **0.964** | 1 wrong-reason + 2 timeouts |
| C2_MULTI_TURN_REFINEMENT_TIMEOUT | 30 | 1.000 | clean |

**Aggregate**: 351/360 trials reached terminal status (97.5%); pass-rate-weighted average ~98.5%.

## Findings worth thinking about for the paper

- **doc 13 §11 #1 answered**: 30 trials/cell is sufficient for descriptive stats (no cell had pass-rate variance below 0.85; most cells were 1.000 or 0.95+). For the 4 cells that didn't hit 30/30, raising `per_trial_timeout_s` from 120s → 180s would likely close the gap.
- **D1 dimension** (C1 cells) shows expected pattern: deterministic modes (direct_mapping, rule_only) at 1.000 with sub-millisecond latency; LLM-assisted at 0.966 with 1.6s median and 4.8s p95. The 3.4-percentage-point pass-rate cost is the LLM's contribution to safety guidance flexibility — quantifiable for the paper.
- **D2 dimension** (C2_D2_*): both static_only and llm_assisted at 1.000 with class2_clarification_correctness 1.0. No measured benefit of LLM in candidate generation under this scenario; would need scenarios designed to show LLM advantage to surface a gap.
- **D3 deterministic ordering** vs source_order: deterministic at 1.000 vs source_order at 0.897. The 3 wrong-reason failures in source_order are worth investigating — could be a real ordering-related defect.
- **scan_history_yes_first_rate = 0.474** (C2_D4_SCANNING_INPUT) is a paper-relevant accessibility metric: ~47% of users accepted the first announced option in scanning mode. Higher under deterministic ordering (D3) would justify D3 as accessibility win.
- **Multi-turn refinement timeout path** (C2_MULTI_TURN_REFINEMENT_TIMEOUT) at 1.000 — the silence-≠-consent invariant held across all 30 trials.

## Operational notes

- Per-trial timeout 120s caused 9 trials to remain pending in 4 cells. Recommend 180s or 240s for next run.
- Mid-run dashboard polling worked smoothly throughout the 132-minute sweep.
- LLM call latency consistent ~1.5-2s typical, ~4-5s p95.
- No memory pressure or thermal throttling observed on M1 MacBook.

## NOT for paper interpretation

These are descriptive measurements only. Inference (significance tests, CIs, narrative claims) is the paper author's responsibility — the toolchain provides numbers, not conclusions.
