# PLAN — Paper-Eval Trial Data Fidelity Fixes (1 + 2)

**Date:** 2026-05-03
**Trigger:** v2 sweep (gemma4:e4b) diagnostic finding — paper_eval trials run by the experiment_package PackageRunner do not capture enough trial-state data to support honest analysis when the LLM legitimately defers and the system escalates to CLASS_2. Operator (user) requested that the dashboard surface the actual outcome path so a human can analyse "what happened" rather than just "did expected==observed".

---

## 1. Background

### 1.1 What we measured during diagnostic

A 5-trial debug sweep of `EXT_A_LLM_ASSISTED` (matrix_extensibility_v2_llm_only_debug5.json) produced this distribution:

| Trial | Status | Pass | Observed Route | Action | Target | Latency |
|---|---|---|---|---|---|---|
| 0 | timeout | ❌ | — | — | — | — |
| 1 | timeout | ❌ | — | — | — | — |
| **2** | **completed** | **✅** | **CLASS_1** | **light_on** | **bedroom_light** | 90 s |
| 3 | completed | ❌ | CLASS_2 | safe_deferral | — | 172 s |
| 4 | timeout | ❌ | — | — | — | — |

Trial 2 demonstrates the v2 paper hypothesis cleanly (gemma4:e4b inferred bedroom-light intent within the actuator catalog and the Class 1 path executed it). Trials 0/1/4 timed out before any observation arrived. Trial 3 escalated to CLASS_2 and is recorded as a fail with no insight into what actually happened in the CLASS_2 path.

### 1.2 Why this is a problem

The dashboard / digest currently distinguishes only `expected_route_class == observed_route_class` (binary pass). For an LLM_ASSISTED cell that legitimately reaches the actuator goal **through the CLASS_2 candidate-set selection** (a different but still valid "perception scalability" path), the dashboard reports a binary failure with no supporting data. This makes it impossible to answer "did the system as a whole produce a correct action for this trial?" — which is the question the operator and a paper reviewer actually need.

The user has been explicit: *"I'm not asking you to manipulate data — I'm asking the dashboard's criteria to make the data understandable."* This plan addresses exactly that.

### 1.3 Three independent problems found

- **Problem A — Trial timeout under-budgeted for LLM escalation.** `_TRIAL_TIMEOUT_S = 30.0` (in `rpi/code/experiment_package/runner.py`) is used for any trial whose `expected_route_class != "CLASS_2"`. With gemma4:e4b's ~89 s LLM call, a Class 1 trial that escalates to CLASS_2 needs the longer `_class2_trial_timeout_s` budget (≈ 338 s under the canonical policy), but the runner does not raise the budget when the *observed* route turns out to be CLASS_2. Result: 60 % timeout in the debug sweep.
- **Problem B — `trial_store` keeps only the single best-match observation.** Mac mini publishes up to three snapshots per CLASS_2-escalated trial (initial routing, class2 update, post-transition outcome). The runner's `_match_observation` returns one snapshot. `trial.observation_payload` is overwritten by that snapshot only. Downstream analysis cannot see the full path — e.g., trial 3's CLASS_2 escalation has no class2 / validation / ack data preserved on disk.
- **Problem C — Digest / dashboard show no breakdown.** Even if A and B are fixed, the digest CSV columns and the dashboard cells are limited to the strict `expected_route_class == observed_route_class` axis. There is no `final_action`, `final_target_device`, `outcome_path`, or "soft pass" (action-matches-intent) view.

This PR addresses **A and B**. Problem C is a follow-up PR (digest + dashboard rendering work; touches different layers).

---

## 2. Scope

### 2.1 In scope (this PR)

- **Fix 1 (Problem A):** `runner.py` chooses `trial_timeout` based on the *path* the trial may take, not just the cell's `expected_route_class`. For `comparison_condition == "llm_assisted"` (where the LLM may legitimately escalate), use `_class2_trial_timeout_s` even when expected is CLASS_1. Deterministic cells (`direct_mapping`, `rule_only`) keep the short `_TRIAL_TIMEOUT_S` because their behaviour is deterministic and bounded.
- **Fix 2 (Problem B):** Extend `TrialResult` with an `observation_history: list[dict]` field. The runner records every snapshot whose `audit_correlation_id` matches the trial, in arrival order. `observation_payload` (the existing field) is preserved for backward compatibility — it remains the final / best-match snapshot. Aggregator + dashboard ignore the new field for now (Problem C work uses it).
- **Tests:** unit tests for the new branch in `runner.py` (timeout selection) and the new `observation_history` field on `TrialResult` (ordering, idempotence).

### 2.2 Out of scope (deferred)

- **Problem C (dashboard / digest):** new columns `final_action`, `final_target_device`, `outcome_path`, `outcome_match_intent`. Separate PR — touches `aggregator.py`, `digest.py`, dashboard frontend.
- **Trial isolation issue noticed in logs:** the context_node's periodic re-publish appears to be intercepted by the next trial's CLASS_2 phase as a `single_click` selection (1 ms after `phase-1: waiting 30s for user button press`). This is a real bug but orthogonal — separate investigation PR.
- **Auto-drive policy for LLM_ASSISTED:** whether `_simulate_class2_button` should fire on `expected_route_class == CLASS_1` trials when the LLM escalates is a *semantics* decision that needs paper-side discussion. This PR does not change the auto-drive trigger; it only ensures the trial has enough budget to record what naturally happens.
- **Canonical policy revert:** the `llm_request_timeout_ms` was bumped from 8000 → 120000 *locally* to allow gemma4:e4b to complete its calls during diagnostic. That edit is uncommitted and is reverted at the end of this work-stream — it is not part of this PR.

### 2.3 Why split the fixes this way

Fixes 1 and 2 are infrastructure: they make trial data trustworthy. They do not change measurement semantics or paper claims, so they can land without paper-side discussion. Problem C is presentation work that depends on what data is captured (i.e., it depends on this PR). Splitting keeps each PR small and reviewable.

---

## 3. Detailed design

### 3.1 Fix 1 — adaptive trial timeout

`rpi/code/experiment_package/runner.py` ~line 405:

**Current:**

```python
trial_timeout = (
    self._class2_trial_timeout_s
    if trial.expected_route_class == "CLASS_2"
    else _TRIAL_TIMEOUT_S
)
```

**New:**

```python
# llm_assisted trials may legitimately escalate from CLASS_1 to CLASS_2 when
# the LLM returns safe_deferral. They need the CLASS_2 budget even when the
# matrix expects CLASS_1, otherwise the trial times out before the class2
# update / post-transition snapshot arrives. Deterministic comparison
# conditions (direct_mapping, rule_only) keep the short budget because they
# do not perform an LLM call on the Class 1 path.
needs_class2_budget = (
    trial.expected_route_class == "CLASS_2"
    or (trial.comparison_condition == "llm_assisted")
)
trial_timeout = (
    self._class2_trial_timeout_s if needs_class2_budget else _TRIAL_TIMEOUT_S
)
```

`comparison_condition` is already on `TrialResult` (see manifest). No new field needed.

This change is conservative: it only *raises* the budget for `llm_assisted` trials. It cannot cause any existing trial to fail; the runner returns as soon as the final snapshot arrives.

### 3.2 Fix 2 — observation history

`rpi/code/experiment_package/trial_store.py`:

- Add `observation_history: list[dict]` field to `TrialResult` (defaults to `[]`).
- Add `complete_trial_with_history(trial_id, observation, all_observations, ...)` or extend the existing `complete_trial` to accept the history list.

`runner.py`:

- After `_match_observation` returns, before calling `complete_trial`, query `_obs.find_all_by_correlation_id(correlation_id)` (new method) to retrieve every snapshot.
- Pass that list to the store.

`observation_store.py`:

- Add `find_all_by_correlation_id(cid: str) -> list[dict]` returning every stored snapshot with that `audit_correlation_id`, in arrival order.

The existing `observation_payload` field stays as is — it remains the "best match" / "final" snapshot used by every existing aggregator, digest, dashboard call. The new `observation_history` is purely additive.

### 3.3 Aggregator / digest behaviour (this PR)

No change. Aggregator continues to use `observation_payload` for the metrics it already produces. The new field exists in the manifest JSON but is not yet rendered. (Problem C consumes it.)

---

## 4. Test plan

### 4.1 Unit tests (added in this PR)

- `test_runner_timeout_selection_llm_assisted_uses_class2_budget` — assert that an `llm_assisted` trial with `expected_route_class=CLASS_1` gets the CLASS_2 budget.
- `test_runner_timeout_selection_deterministic_keeps_short_budget` — assert `direct_mapping` / `rule_only` still get `_TRIAL_TIMEOUT_S`.
- `test_trial_result_observation_history_default_empty` — new field defaults to `[]`.
- `test_trial_result_observation_history_preserves_arrival_order` — list ordering matches insertion.
- `test_observation_store_find_all_by_correlation_id_returns_all_snapshots` — store helper returns every snapshot, in order.
- `test_complete_trial_records_full_history_alongside_best_match` — `observation_payload` is the best match; `observation_history` has every snapshot.

### 4.2 Live verification (post-merge)

Re-run `matrix_extensibility_v2_llm_only_debug5.json` and confirm:

- 0 timeouts (Fix 1) — every trial reaches a terminal snapshot within the budget
- For trials whose LLM legitimately defers and escalates to CLASS_2, the manifest's `observation_history` contains the initial routing + class2 update + (when applicable) post-transition outcome snapshots.

### 4.3 Regression suites

`mac_mini` and `rpi` `pytest` suites must remain green. No changes touch the Mac mini codebase, but `aggregator.py` / `digest.py` may need to ignore the new field gracefully.

---

## 5. Files to change

```
rpi/code/experiment_package/runner.py          # Fix 1: timeout branch
rpi/code/experiment_package/trial_store.py     # Fix 2: TrialResult.observation_history
rpi/code/experiment_package/observation_store.py  # Fix 2: find_all_by_correlation_id
rpi/code/tests/test_rpi_components.py           # tests for both fixes
common/docs/runtime/PLAN_2026-05-03_PAPER_EVAL_TRIAL_DATA_FIDELITY_FIXES.md  (this file)
common/docs/runtime/SESSION_HANDOFF_2026-05-03_TRIAL_DATA_FIDELITY_DIAGNOSIS.md  (handoff)
common/docs/runtime/SESSION_HANDOFF.md         # index update
```

No canonical policy / schema / mqtt asset changes.

---

## 6. Operator runbook (after this PR merges)

1. Pull main.
2. Confirm policy still has `llm_request_timeout_ms = 120000` (operator-level; revert to 8000 only after the v2 archive is captured).
3. Restart launcher.
4. Run `matrix_extensibility_v2_llm_only_debug5.json` → expect 0 timeouts and full `observation_history` per trial.
5. Once verified, run `matrix_extensibility_v2_llm_only.json` (n=30, ~90 min).
6. Once that looks healthy, run full `matrix_extensibility_v2.json` for the paper archive (~3 hours including DIRECT/RULE rerun).
7. Restore canonical `llm_request_timeout_ms = 8000` and revert `_TRIAL_TIMEOUT_S` if the fix made it configurable rather than hardcoded.
8. Restore `.env` `OLLAMA_MODEL=llama3.1` after sweep.

---

## 7. Backlog after this PR

| Item | Priority | Notes |
|---|---|---|
| Problem C — dashboard breakdown columns | HIGH | This PR's `observation_history` is the input |
| Trial isolation bug (context node's re-publish gets intercepted as single_click) | HIGH | Separate investigation; affects measurement validity |
| `_TRIAL_TIMEOUT_S` env-var override / config-driven | MEDIUM | Cleanup follow-up — not strictly required if Fix 1 lands |
| Auto-drive policy for `expected_route_class=CLASS_1` LLM trials | MEDIUM | Paper-side semantics decision |
| Lever A (richer pure_context_payload via schema extension) | MEDIUM | Step 5 PR — separate from this fidelity work |
| `llm_request_timeout_ms` canonical revert + per-sweep override mechanism | LOW | Currently operator-driven; codify if used regularly |
