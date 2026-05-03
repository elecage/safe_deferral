# PLAN — Class 2 Clarification Process Measurement

**Date:** 2026-05-03
**Trigger:** User architectural feedback during PR #150 review:

> 내가 원한 건 class 1인데, 다른 모호한 상황으로 인해 class 2가 되면 LLM은 여기서 보류한다로 끝나는 게 아니라 재질문을 통해 점진적 명확화 과정을 거쳐야 해. 그렇다면 그런식으로 명확화를 한다는 모습이 보여야 하는데, 이걸 그냥 보류만 해버리면 LLM의 역할은 제한적일 뿐만 아니라 효용성이 떨어지는 것이라고 보는데, 너의 의견은 어때?

The current EXT_A_LLM_ASSISTED matrix measures only the LLM's *single-shot* recovery rate. When the LLM legitimately defers, the trial ends in `class2_safe_deferral` because the simulated user (the context_node) does not respond to the Class 2 candidate set. **The actual paper contribution — that the LLM defers AND then guides a progressive clarification dialogue toward an actuation outcome — is invisible.**

This plan extends the experiment surface to measure the clarification process itself: scenarios where the LLM defers, the system generates a Class 2 candidate set, and a simulated user responds (single-shot accept, multi-turn refine, scanning).

**Predecessor:** PR #150 (`5009257` Fix 1+2 / `40f3bab` Problem C dashboard breakdown) — `observation_history`, `outcome_path_distribution`, `outcome_match_rate` already in place. The infrastructure to *display* clarification outcomes exists; this plan adds the input that exercises it.

---

## 1. Problem statement

### 1.1 What the current matrix measures

```
LLM Class 1 → safe_deferral (gemma4:e4b chooses defer ~60% on ambiguous input)
   ↓
CLASS_2 escalation (C207)
   ↓
LLM-driven Class 2 candidate set generated (e.g. ["거실 조명을 끄시겠습니까?",
   "침실 조명을 켜시겠습니까?", "보호자 호출"])
   ↓
user_phase 30s wait — context_node has no response logic
   ↓
caregiver phase begins, then trial ends → SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
```

`outcome_path_distribution` for these trials always lands in `class2_safe_deferral`, never in `class2_to_class1`. The clarification process executes (candidate generation runs) but its *recovery effectiveness* is never measured.

### 1.2 What the system can already do (just isn't exercised)

| Mechanism | Implementation | Currently exercised in paper-eval? |
|---|---|---|
| LLM-driven Class 2 candidate generation | `class2_clarification_manager` + `local_llm_adapter.generate_class2_candidates` | Yes (runs every CLASS_2 trial) |
| Static fallback candidate set | `_DEFAULT_CANDIDATES` table | Yes (when `class2_candidate_source_mode=static_only`) |
| Single-turn user selection | `submit_selection(candidate_id)` | Only on `expected_route_class=CLASS_2` cells via `_simulate_class2_button` |
| Multi-turn refinement | `class2_multi_turn_enabled` + `submit_selection_or_refine` | No — only matrix_v1 has the cells, not used in extensibility |
| Scanning input mode | `class2_input_mode=scanning` + `submit_scan_response` | No — same as above |
| Scanning ordering | `class2_scan_ordering_mode` + `class2_scan_ordering_rules` | No |

**The system is well-instrumented; the matrix is what's narrow.**

### 1.3 Why this matters for the paper

The current LLM_ASSISTED outcome ("0% bedroom-light recovery, 60% safe_deferral") supports a one-sided framing in `01_paper_contributions.md §7.4`:

> The LLM is conservative under genuine ambiguity.

The unfair second half of the truth is missing: **the LLM is conservative *and* the system's Class 2 dialogue can recover the deferred intent**. Without exercising the dialogue path, the paper cannot claim its actual contribution — that *perception scalability is a multi-turn property, not a single-inference property*.

---

## 2. Scope

### 2.1 In scope (this PR)

- **Runner**: extend `_match_observation` to auto-drive a configurable user response when the LLM defers and the trial enters CLASS_2, even on cells whose `expected_route_class=CLASS_1`. The cell declares the response shape; the runner replays it.
- **Cell schema**: add `_user_response_script` field on `Cell` (parsed by `paper_eval.sweep.load_matrix`) carrying one of:
  - `{"mode": "no_response"}` — current default; baseline
  - `{"mode": "first_candidate_accept"}` — simulate `single_click` immediately after the initial CLASS_2 routing snapshot (selects the first candidate)
  - `{"mode": "first_candidate_then_yes", "first_index": 0}` — for scanning cells; sends `{option_index: 0, response: "yes"}` (selects option 0)
  - `{"mode": "scan_until_yes", "yes_at": 1}` — for scanning cells; sends `no` for indices < `yes_at`, `yes` at `yes_at` (multi-step refinement)
- **Matrix**: new `matrix_extensibility_v3_clarification.json` with 4 cells covering the scripts above.
- **Scenarios**: reuse the existing `extensibility_a_novel_event_code_bedroom_needed_scenario_skeleton.json` — same input, different `_user_response_script` per cell. No scenario duplication.
- **Tests**: unit tests for the new auto-drive branches and the cell schema field.
- **PLAN + handoff**: this file plus `SESSION_HANDOFF_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md`.

### 2.2 Out of scope (deferred)

- **Real LLM-driven user simulation** — the goal is deterministic, reproducible measurement. The simulated user's behaviour is encoded in the cell, not generated.
- **Per-trial response variation within a cell** — every trial in a cell shares the same script. Variance comes from the LLM's non-determinism (Class 1 candidate + Class 2 candidate set generation), not from the user.
- **Caregiver-phase scripts** — caregiver path is exercised by the existing `no_response` baseline cell. Detailed caregiver dialogue scripts are a future plan.
- **Schema for response_script in canonical assets** — the field stays on the matrix file (which is already an experiment artifact, not a canonical asset). No `policy_router_input_schema` / `context_schema` changes.
- **Dashboard frontend changes** — Problem C (PR #150) already renders `outcome_path_distribution` and `outcome_match_rate`; the new cells will fill those columns naturally without further UI work.

### 2.3 Why this split

The current PR adds *experimental coverage* of an already-implemented mechanism. The system's clarification logic is unchanged — only the matrix surface and the runner's response-simulator branch grow. Splitting "measure existing capability" from "improve the capability" keeps each PR review-sized and the measurement reproducible against a fixed code surface.

---

## 3. Detailed design

### 3.1 Cell schema extension (`paper_eval/sweep.py`)

```python
@dataclass
class Cell:
    ...
    user_response_script: Optional[dict] = None  # _user_response_script in JSON
```

Loader change in `load_matrix`:

```python
user_response_script=raw_cell.get("_user_response_script"),
```

JSON shape on a matrix cell:

```jsonc
{
  "cell_id": "EXT_A_LLM_DEFER_FIRST_CANDIDATE_ACCEPT",
  "_user_response_script": {
    "mode": "first_candidate_accept",
    "rationale": "After LLM defers to CLASS_2, simulate single_click selecting the first generated candidate. Measures: when the LLM-driven candidate set's first option matches user intent, can the system recover to CLASS_1 actuation in one user step?"
  },
  ...
}
```

### 3.2 Runner auto-drive (`experiment_package/runner.py`)

`_match_observation` already auto-drives `single_click` when `expected_route_class=="CLASS_2"` AND `expected_transition_target == "CLASS_1"`. Extend the trigger condition:

```python
# Existing: drive when matrix expects CLASS_2 → CLASS_1.
if accepted_targets == {"CLASS_1"}:
    drive_target = "single_click"
elif accepted_targets == {"CLASS_0"}:
    drive_target = "triple_hit"

# NEW: drive when the cell declares a user_response_script and the trial
# observes CLASS_2 (regardless of expected_route_class). This is the
# 'LLM deferred → user recovers via Class 2 dialogue' path.
script = (trial.user_response_script or {}) if trial else {}
if script.get("mode") == "first_candidate_accept":
    drive_target = "single_click"
```

Trial dict needs to carry `user_response_script` from the cell — extend `start_trial_async` and `TrialResult` accordingly. `single_click` is the right primitive because the existing Mac mini handler `_try_handle_as_user_selection` maps it to "select first candidate".

For `scan_until_yes` and `first_candidate_then_yes`, the simulator publishes `{option_index, response: "yes"|"no"}` payloads on the Class 2 scanning topic — a new helper `_simulate_class2_scan_response` parallel to `_simulate_class2_button`.

### 3.3 Matrix file

`integration/paper_eval/matrix_extensibility_v3_clarification.json` — 4 cells, all `comparison_condition="llm_assisted"`, same scenario, different `_user_response_script`. `expected_route_class` and `expected_validation` are tuned per cell to encode "what would design-correct behaviour look like for THIS user response":

| Cell | Script | Expected | Strict-pass interpretation |
|---|---|---|---|
| `EXT_A_LLM_DEFER_NO_RESPONSE` | `no_response` | `CLASS_2 + safe_deferral` | Baseline — measures caregiver fallback. pass_rate high → safe degradation works. |
| `EXT_A_LLM_DEFER_FIRST_CANDIDATE_ACCEPT` | `first_candidate_accept` (direct_select) | `CLASS_1 + approved` (when LLM generates a CLASS_1-target candidate first) | Measures: LLM defer + 1-step user accept → CLASS_1 recovery rate. |
| `EXT_A_LLM_DEFER_SCANNING_ACCEPT_FIRST` | `first_candidate_then_yes` (scanning) | `CLASS_1 + approved` | AAC scanning at first option. |
| `EXT_A_LLM_DEFER_SCANNING_ACCEPT_SECOND` | `scan_until_yes, yes_at=1` (scanning) | `CLASS_1 + approved` | AAC scanning, user rejects first option, accepts second — measures *progressive* clarification. |

The two scanning cells need `_policy_overrides`:

```json
"_policy_overrides": {
  "llm_request_timeout_ms": 120000,
  "class2_input_mode": "scanning"
}
```

### 3.4 Trial-level outcome interpretation

`outcome_path_distribution` (PR #150) already classifies these — no aggregator change needed:

- `class1_direct` is unchanged
- `class2_to_class1` now appears for `EXT_A_LLM_DEFER_FIRST_CANDIDATE_ACCEPT` trials whose first candidate was a lighting target
- `class2_safe_deferral` now appears only when (a) `no_response` cells, or (b) the script accepted but the candidate didn't transition to CLASS_1

`outcome_match_rate` (PR #150) — `expected_validation=approved` cells score True when final action is light_on/off, regardless of which path got there. This is exactly what the user asked for.

### 3.5 Test plan

- `TestRunnerAutoDriveOnLlmDefer` — auto-drive fires on cell with `user_response_script.mode=first_candidate_accept` even when `expected_route_class=CLASS_1`.
- `TestRunnerAutoDriveScanResponseSequence` — `scan_until_yes` publishes `no, no, yes` in order with intervening waits.
- `TestCellLoadsUserResponseScript` — `Cell.user_response_script` round-trips through `load_matrix`.
- `TestMatrixExtensibilityV3Clarification` — structural invariants (4 cells, all llm_assisted, scripts present).

### 3.6 What the dashboard will show after this lands

A debug sweep across the 4 cells (n=5 each, ≈25 min) should produce a per-cell breakdown like:

| cell_id | pass_rate | match_rate | trajectory |
|---|---|---|---|
| `EXT_A_LLM_DEFER_NO_RESPONSE` | 1.0000 | 1.0000 | class2_safe_deferral=5 |
| `EXT_A_LLM_DEFER_FIRST_CANDIDATE_ACCEPT` | ~0.6 | ~1.0 | class1_direct=2, class2_to_class1=3 |
| `EXT_A_LLM_DEFER_SCANNING_ACCEPT_FIRST` | similar | similar | similar with scanning fields |
| `EXT_A_LLM_DEFER_SCANNING_ACCEPT_SECOND` | varies | varies | shows multi-turn refinement signal |

The interesting signal is **the gap between `pass_rate` and `match_rate`** — for cells whose script accepts a candidate, `pass_rate` may be lower than `match_rate` (because route_class observed is CLASS_2 but actuation reached CLASS_1). That gap is the paper-grade evidence for "LLM defer + clarification dialogue → recovery".

---

## 4. Implementation phases

| Phase | Work | Why this order |
|---|---|---|
| 4.1 | Cell schema (`Cell.user_response_script`) + loader | Smallest contract change; everything below depends on it. |
| 4.2 | Trial schema (`TrialResult.user_response_script`) + start_trial_async pass-through | Mirror cell field onto trial so the runner sees it. |
| 4.3 | Runner auto-drive — `first_candidate_accept` | First script mode; uses existing `_simulate_class2_button` infra. |
| 4.4 | Runner auto-drive — scanning script modes | New `_simulate_class2_scan_response` helper. |
| 4.5 | Matrix `matrix_extensibility_v3_clarification.json` + scenario reuse | One file, four cells. |
| 4.6 | Tests at every layer | After each layer to catch regressions early. |
| 4.7 | Debug sweep verification | Run the new matrix against the live launcher; inspect manifest. |

If 4.4 (scanning) ends up complex (it depends on the scanning topic's MQTT contract), defer to a follow-up PR — `first_candidate_accept` (direct_select mode) alone produces the headline paper-grade evidence and unblocks the §7.4 reframing.

---

## 5. Risk register

| Risk | Mitigation |
|---|---|
| `_simulate_class2_button` already publishes single_click; collides with cells declaring different script | Script field is opt-in; cells without it use existing behaviour. |
| Scanning topic / payload contract drifts vs runner simulator | Tests will fix the contract; the runner publishes through the same `vnm.publish_once` path the existing scanning code uses. |
| New cells make the v2 archive comparison less clean | This matrix is **separate from v2** — `matrix_extensibility_v2.json` stays as the LLM-only paper-grade archive. v3 measures clarification orthogonally. |
| Multi-turn refinement requires `class2_multi_turn_enabled=true` policy bump | Cell `_policy_overrides` declares it; Sweeper enforces the bump (PR #143 mechanism). |
| Tests pin live policy values | Same pattern as PR #149's tests — assert override is *declared*, not that live policy matches. |

---

## 6. Files to change

```
rpi/code/paper_eval/sweep.py                        # Cell.user_response_script + loader
rpi/code/experiment_package/trial_store.py          # TrialResult.user_response_script
rpi/code/experiment_package/runner.py               # auto-drive expansion
rpi/code/tests/test_paper_eval_sweep.py             # cell schema tests
rpi/code/tests/test_rpi_components.py               # runner auto-drive tests
integration/paper_eval/matrix_extensibility_v3_clarification.json  (new)
common/docs/runtime/PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md  (this file)
common/docs/runtime/SESSION_HANDOFF_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md  (handoff)
common/docs/runtime/SESSION_HANDOFF.md              # index update
```

No canonical policy/schema/MQTT contract changes.

---

## 7. Backlog after this PR

| Item | Priority | Notes |
|---|---|---|
| Trial isolation bug (context_node re-publish intercepted) | HIGH | Affects every CLASS_2-escalated trial including v3 cells |
| Multi-turn refinement scenario | MEDIUM | Needs `class2_multi_turn_enabled` flag + cell scripts |
| Real-LLM Class 2 candidate generator quality eval | MEDIUM | Compare LLM-generated candidates vs static fallback signal |
| Caregiver-phase scripts | LOW | Currently exercised by no_response baseline |
| Per-trial script variation (stochastic user model) | LOW | Out of scope for paper-eval determinism |

---

## 8. User-facing reframing

After this PR lands and a sweep produces the matrix, `01_paper_contributions.md §7.4` should read:

> The LLM is conservative under genuine ambiguity. When it defers, the system's Class 2 clarification dialogue recovers the deferred intent through a multi-turn user interaction; the recovery rate measured at [cell] is [X%], and the strict-route pass_rate alone underrepresents the perception scalability contribution by [pass_rate − match_rate] percentage points.

Numbers belong to a future paper-revision PR — this PR produces the data.
