# SESSION_HANDOFF — End of Session: PRs #148-#152 merged, PR #153 planned

**Date:** 2026-05-04
**Predecessor session work:** PRs #148, #149, #150, #151, #152 all merged into `main`.
**Status:** Active work-stream paused. Next session resumes with PR #153 (intent-aware simulator) per the plan in §4 below.

---

## 1. What this session shipped

### 1.1 Five merged PRs forming a coherent measurement framework

| PR | Commit | Theme |
|---|---|---|
| #148 | `91b7e10` | Step 4 Axis A v2 build — Levers B (gemma4:e4b) + C (prompt rule 9), Lever A deferred. Default LLM model llama3.2 → llama3.1. |
| #149 | `5009257` | Trial data fidelity — Fix 1 (`comparison_condition=='llm_assisted'` uses class2 budget) + Fix 2 (`observation_history` accumulation). |
| #150 | `40f3bab` | Problem C dashboard breakdown — `outcome_path_distribution`, `final_action_distribution`, `outcome_match_rate`, latency fix from observation_history span, dashboard column work. |
| #151 | `9ed412f` | Step 6 Class 2 clarification process measurement — `_user_response_script` cell field, runner auto-drive on LLM-defer, v3 matrix `matrix_extensibility_v3_clarification.json`. |
| #152 | `95a0d9a` | Intent-driven measurement — scenario `user_intent` block, `TrialResult.user_intent_snapshot`, three-level `pass_rate` / `outcome_match_rate` / **`intent_match_rate`** metric stack, dashboard `기대 intent ↔ Final action` color-coded comparison. |

### 1.2 Three-level paper-grade metric stack (final form)

| Level | Metric | What it asks | Defined in |
|---|---|---|---|
| 1 | `pass_rate` | Did the system route as the matrix expected? (Routing fidelity) | doc 13 / aggregator since v1 |
| 2 | `outcome_match_rate` | Did the system reach a useful action regardless of route? (Actuation fidelity) | PR #150 |
| 3 | **`intent_match_rate`** | Did the system reach the **user's** action? (Semantic fidelity) | **PR #152** |

Per-cell digest CSV columns and the dashboard tables (Paper-Eval Sweep + 결과분석) all surface the three-level stack with hover titles distinguishing fidelity layer.

### 1.3 Paper documentation now in place

- `common/docs/paper/05_class2_clarification_measurement_methodology.md` — 7 sections covering the conceptual methodology (strict/soft/semantic split, deterministic-script measurement, hardware separation for paper-grade numbers, anti-overclaim guards). Cross-references PRs #149/#150/#151/#152 build plans.

### 1.4 Verification artifact (informational, not paper-grade)

The 2026-05-04 sweep (`16302fac6d59`, n=5 per cell, 2 cells of `matrix_extensibility_v3_clarification.json` against gemma4:e4b on M1) confirmed the three-level metric stack populates correctly:

```
EXT_A_LLM_DEFER_NO_RESPONSE   pass=0.40 match=0.40 intent=0.00
EXT_A_LLM_DEFER_FIRST_CAND_AC pass=0.60 match=1.00 intent=0.80
```

Per-trial trial 3 of FIRST_CANDIDATE_ACCEPT is the headline failure mode the metric stack now exposes:

```
trial 3  pass=✅ match=✅ intent=❌
  expected_intent: light_on → bedroom_light
  final action:    light_on → living_room_light
```

`pass` and `match` both green; `intent` red. This trial — actuation correct in aggregate but wrong specific action — is invisible to the strict + soft pair. PR #152's framework lets a paper reviewer see it directly.

These numbers are NOT paper-grade — paper-grade verification is a separate hardware-and-real-users session per `05_class2_clarification_measurement_methodology.md §3`.

---

## 2. Local environment state at session end

### 2.1 Reverted at session end (this commit)

- `~/smarthome_workspace/.env` — `OLLAMA_MODEL=gemma4:e4b` reverted to `OLLAMA_MODEL=llama3.1`. Production default restored.
- `common/policies/policy_table.json` (main repo path, uncommitted) — `llm_request_timeout_ms=120000` reverted to canonical `8000`. Operator-side bump, not committed.
- launcher stopped (`./scripts/local_e2e_launcher.sh --stop`).

### 2.2 Branch state

- `claude/cranky-kilby-11aaff` is fully merged into `main` via PRs #148-#152. The branch tip is `a76a07e` (cherry-picked dabcbff + 67d7fbe pre-merge); after the squash-merge of #152 the meaningful tree is fully in `origin/main`.
- The worktree on this branch can be pruned at next session start. Future work continues on `main`.

### 2.3 Models present on the dev machine

- `llama3.1:latest` — production default
- `llama3.2:latest` — historical; not the default
- `gemma4:e4b` — used for Axis A v2 / v3 sweeps
- `gemma4:26b`, `gemma4:31b` — installed but not used (laptop OOM risk)

---

## 3. Open backlog (carried forward to PR #153 and beyond)

### 3.1 PR #153 (next session — high priority)

**Theme:** Intent-aware simulator + coverage matrix v4. The current `_user_response_script` modes (`no_response`, `first_candidate_accept`) do not consult the scenario's `user_intent`. The simulator picks blindly. To exercise the full Class 2 clarification dialogue under intent-driven response, the runner must read the LLM-generated candidate set, find the candidate whose `action_hint`/`target_hint` match the scenario `user_intent`, and drive the response that selects it.

PLAN doc to write next session: `PLAN_2026-05-XX_INTENT_AWARE_SIMULATOR_AND_COVERAGE.md`. Outline:

1. **New script modes**:
   - `accept_intended_via_direct_select` — read clarification_payload, find matching candidate, dashboard `submit_selection` API call (or single_click only when intent-matching candidate is first)
   - `accept_intended_via_scan` — scanning mode (`class2_input_mode=scanning`), drive `double_click ... double_click single_click` to reach intent-matching index. Mac mini's `scan_input_adapter` already maps single_click→yes / double_click→no for scanning sessions.
   - `scan_until_yes` (parameter `yes_at: int`) — AAC scanning baseline without intent awareness
   - `scan_all_no` — caregiver fallback path under scanning
   - `caregiver_help_accept` — explicit user choice of CAREGIVER_HELP candidate
   - `triple_hit_emergency` — emergency shortcut testing CLASS_2 → CLASS_0 transition

2. **Runner extension**:
   - Wait for `clarification_payload` after initial CLASS_2 routing snapshot (existing `_await_clarification`)
   - Parse candidates list
   - Intent-matching helper computes target candidate index
   - For scanning: drive button-event sequence with `class2_scan_per_option_timeout_ms` / 2 spacing so each `double_click` lands within the announce window
   - For direct_select with intent: only fires when the matching candidate happens to be first; otherwise document the limitation

3. **Coverage matrix v4** (`matrix_extensibility_v4_intent_coverage.json`):
   - Multiple cells exercising: each script mode × each `user_intent` (light_on living, light_on bedroom, light_off living, light_off bedroom, safe_deferral)
   - Each cell's `expected_route_class` / `expected_validation` encodes the design-correct outcome for that script + intent combination
   - `_policy_overrides` for scanning cells: `class2_input_mode=scanning`

4. **Aggregator extension** (light): no new metric needed — PR #152's `intent_match_rate` already measures what coverage cells produce. Possibly add helper to verify cell's `expected_validation` + `expected_route_class` match what the script intends to produce.

5. **Tests**: at every layer.

6. **Paper doc update**: add §7 to `05_class2_clarification_measurement_methodology.md` — coverage-scenario catalog mapping each script mode to the architectural transition it exercises.

7. **Verification sweep**: matrix v4 against gemma4:e4b → produces a development-grade picture of how the Class 2 clarification dialogue performs across all interaction modes. Hardware-grade run is later, separate.

### 3.2 Other backlog items (lower priority, paused)

| Item | Source | Notes |
|---|---|---|
| Trial isolation bug | observed during PRs #148-#152 sweeps | context_node periodic re-publish appears to be intercepted as a CLASS_2 `single_click` selection (the sub-millisecond auto-selection seen in earlier handoffs). Affects measurement cleanliness. Not blocking PR #153 but should be tracked. |
| Step 5 — Lever A schema extension | PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md | Add `user_state.inferred_attention` + `recent_events` to canonical `context_schema.json` and propagate. Independent of PR #153 — could be a parallel work-stream. |
| Multi-turn refinement scenario | PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md §7 | Needs `class2_multi_turn_enabled=true` policy flag + cell scripts. Doc 11 Phase 6.0 implementation already exists. |
| Per-trial drill-down view | PLAN_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md §7 | Surface `observation_history` timeline per trial in 결과분석 tab. |
| Caregiver-phase response scripts | PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md §7 | Telegram inline-keyboard simulator. Not exercised by current matrices. |
| Hardware paper-grade verification | `05_class2_clarification_measurement_methodology.md §3, §5` | Mac mini + RPi 5 + ESP32 + real users. The numbers that go in the paper. Separate session. |
| Multi-turn recovery sweep | PLAN_2026-05-02_PAPER_REFRAME_AND_OPEN_OPS_BACKLOG.md | Phase C 2 invalid cells re-execution with multi-turn flag. ~30 min ops. |
| target-device-correctness metric → Axes B/C | same | Larger axes work after intent_match_rate is established (which is now true). |

---

## 4. Operator runbook for resuming work

Next session should start by:

1. **Pull `main`** — confirm `git log -1` is at or after PR #152's squash commit (`95a0d9a`).
2. **Inspect this handoff doc** as the entry point. The recent PLAN docs are:
   - `PLAN_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md` (PR #152 baseline — completed)
   - `PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md` (PR #151 baseline — completed)
   - `PLAN_2026-05-03_PAPER_EVAL_TRIAL_DATA_FIDELITY_FIXES.md` (PR #149 baseline — completed)
   - `PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md` (PR #148 baseline — Lever A still deferred)
3. **Decide next PR direction** — recommended: PR #153 intent-aware simulator (per §3.1 above).
4. **Write `PLAN_2026-05-XX_INTENT_AWARE_SIMULATOR_AND_COVERAGE.md`** as the build plan, modelled on the PR #152 plan structure.
5. **Implement** in the canonical phase order (cell schema → trial schema → runner auto-drive → matrix → tests → verification sweep).
6. **For verification sweeps**: temporarily bump `policy_table.global_constraints.llm_request_timeout_ms` to 120000 + set `OLLAMA_MODEL=gemma4:e4b` in `~/smarthome_workspace/.env`. Restore at session end (this session's pattern).
7. **Hardware verification** is a separate work-stream, deliberately not tied to any PR's merge gate.

---

## 5. Files touched in THIS session-end commit

```
common/docs/runtime/SESSION_HANDOFF_2026-05-04_END_OF_SESSION_PR148_TO_152_MERGED.md  (new — this file)
common/docs/runtime/SESSION_HANDOFF.md                                                  (index update)
```

That is all — environment reverts (.env, policy_table.json) are operator-side and not committed.

---

## 6. Cross-reference summary

| Topic | Document |
|---|---|
| Three-level metric stack methodology | `common/docs/paper/05_class2_clarification_measurement_methodology.md` (§2.1, §6) |
| Hardware vs development environment separation | same doc, §3, §5 |
| Three PRs of build plans (#149/#150/#151/#152) | `common/docs/runtime/PLAN_2026-05-0[3-4]_*.md` |
| Step 4 (PR #148) baseline | `common/docs/runtime/PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md` and `SESSION_HANDOFF_2026-05-03_STEP4_AXIS_A_V2_BUILD_LEVERS_B_C.md` |
| Backlog summary | this doc §3 |
| Operator resume runbook | this doc §4 |
