# LLM-Driven Class 2 Integration Alignment Plan

## 1. Purpose

This document captures the **integration alignment review** held on
2026-05-01 after PR #87 (Phase 1+2), PR #88 (Phase 3), and PR #89 (Phase 5)
landed the LLM-driven Class 2 candidate generation feature
(`09_llm_driven_class2_candidate_generation_plan.md`).

The review identified gaps that the Phase 0 design plan did **not** cover
and that surfaced only once the LLM became part of the runtime path:

- Operational timing risks (LLM latency vs Class 2 user-response window
  vs main MQTT message-handler thread blocking).
- Documentation drift (architecture / MQTT / experiment-rules docs still
  describe a static-table-only Class 2 manager).
- Scenario fixture and experiment success-criteria assumptions that
  pre-date LLM-generated candidate text.

This plan organises the findings into three priority tiers, sequences the
work, and is intended to land as a docs-only PR so the maintainer agrees
the priority order before any code is touched.

## 2. Why This Review Was Needed

PR #87+#88+#89 implemented the LLM-driven candidate generation feature and
verified it with synthetic tests. That work was correct in isolation but
took several existing assumptions for granted:

| Assumption | Reality after PR #87+#88+#89 |
|---|---|
| Class 2 candidate generation is fast (microseconds) | LLM call adds 8-10 s typical, up to the 60 s `OllamaClient` timeout |
| `_handle_class2()` returns immediately to free the MQTT message-handler thread | The LLM call now blocks the message-handler thread for the LLM duration |
| Scenario expected fixtures match candidate id literals (e.g. `C1_LIGHTING_ASSISTANCE`) | LLM-generated candidates may use any id (`LLM_C1_LIGHT`, etc.) |
| Architecture docs describe Class 2 as static-table-driven | Class 2 has an LLM upstream now, but most docs still say static |

The asymmetry between the LLM call's worst-case duration (60 s) and the
Class 2 user clarification window (30 s) is the most safety-significant
finding and motivates the P0 tier below.

## 3. Findings — Three Tiers

### 3.1 P0 — Operational safety regressions (must-fix)

#### P0.1 LLM call blocks the MQTT message-handler thread

**Symptom:** `Pipeline.handle_context()` runs on the paho-mqtt callback
thread. When routing yields CLASS_2, `_handle_class2()` synchronously calls
`Class2ClarificationManager.start_session(pure_context_payload=...)`,
which now calls `LocalLlmAdapter.generate_class2_candidates()`, which
calls `OllamaClient.complete()` with a 60-second HTTP timeout. The
message-handler thread is therefore blocked for up to 60 seconds.

**Safety impact:** While blocked, no other MQTT message is processed —
including a Class 0 emergency event that could arrive on
`safe_deferral/emergency/event` or `safe_deferral/context/input` (smoke,
gas, fall, triple-hit). Emergency response can be delayed by up to the
entire LLM timeout. This violates the canonical invariant that Class 0
must be handled deterministically and immediately.

**Fix direction:** The LLM call must run off the message-handler thread.
Concrete options:
- (a) Move LLM candidate generation into the existing background thread
  (`_await_user_then_caregiver`) so `_handle_class2()` returns immediately,
  TTS announces a static fallback first, and LLM candidates replace them
  on next iteration if and when they arrive within budget.
- (b) Spawn a short-lived helper thread inside `start_session` that joins
  with a tight budget (e.g. 2-3 s); fall back to static defaults if the
  budget elapses.

(b) is simpler and keeps the user-facing latency bounded. (a) is more
ambitious but lets us announce *contextual* candidates only when the LLM
can deliver them in time without ever delaying the announcement.

#### P0.2 `OllamaClient` timeout (60 s) > Class 2 user window (30 s)

**Symptom:** Even after P0.1 (LLM off the message-handler thread), an LLM
call that takes 30+ seconds is still wasted work — the user clarification
window starts only after `start_session` returns.

**Fix direction:** Add a policy-defined LLM request timeout, e.g.
`global_constraints.llm_class2_request_timeout_ms` defaulting to 8000.
`LocalLlmAdapter` reads it at startup and passes it into `OllamaClient`
constructor (currently fixed at 60 s in code). Aligns the LLM budget with
the user clarification window so the LLM cannot "burn" most of it.

#### P0.3 Runner auto-drive delay does not budget for LLM latency

**Symptom:** `_CLASS2_SELECTION_DRIVE_DELAY_S = 0.5`. The PackageRunner
publishes the scenario's context payload, waits 0.5 s, then sends a
synthetic `single_click` (or `triple_hit`) to drive the user selection.
With the LLM in the loop, the manager may still be calling Ollama at
that 0.5 s mark — so the synthetic button arrives *before* the manager
has registered a session in `_pending_user_class2`. The button is then
either dropped or delivered to a stale session.

**Fix direction:** Either (a) bump `_CLASS2_SELECTION_DRIVE_DELAY_S` to
something safely above the policy-defined LLM budget (e.g. 12 s), or
(b) replace the fixed delay with a deterministic wait-for-class2-session
signal. (b) requires a small audit/observation surface (e.g. wait until
the initial CLASS_2 dashboard observation arrives, then drive). (b) is
cleaner and the runner already polls observations anyway — the existing
"initial CLASS_2 routing snapshot" detection in `_match_observation`
naturally tells us the manager has reached `start_session` end.

### 3.2 P1 — Documentation alignment (mechanical)

#### P1.1 Active architecture docs

| Doc | Update |
|---|---|
| `00_architecture_index.md` §3 Canonical Schemas | List `class2_candidate_set_schema.json` (added by PR #87). |
| `01_system_architecture.md` Class 2 data flow | Mention LLM upstream of the manager and the silent fallback path. |
| `03_payload_and_mqtt_contracts.md` §5/§7 | Note that the RPi side now subscribes to `safe_deferral/clarification/interaction` (PR #89) and `safe_deferral/escalation/class2` (PR #82) for evaluation capture; clarify these are evaluation-side reads, not authority. |
| `04_class2_clarification.md` | Already has §4.1-§4.3 from PR #88; cross-reference new schema and the policy block explicitly. |
| `07_scenarios_and_evaluation.md` | Add an "LLM variability in candidate text" section: scenario expectations must allow LLM-generated `candidate_id` and `prompt` strings to vary; only `candidate_transition_target`, `action_hint`, and `target_hint` are stable contract surfaces. |

#### P1.2 MQTT registry / matrix

| Doc | Update |
|---|---|
| `common/mqtt/topic_registry.json` | Add RPi subscribers to `safe_deferral/clarification/interaction` and `safe_deferral/escalation/class2`; describe purpose as evaluation capture. |
| `common/mqtt/publisher_subscriber_matrix.md` | Same. |
| `common/mqtt/topic_payload_contracts.md` | Reference `class2_candidate_set_schema.json` as adapter-internal evidence (not on any operational topic). |

#### P1.3 Asset manifest and required experiments

| Doc | Update |
|---|---|
| `common/asset_manifest.json` | Add `class2_candidate_set_schema.json`. |
| `common/docs/required_experiments.md` §8 (Package D) | Add `class2_llm_quality` sub-block metrics (`llm_generated_rate`, `default_fallback_rate`, `llm_user_pickup_rate`, `default_fallback_user_pickup_rate`); explicitly note that the original Phase 5 metric proposal (`llm_candidate_admissibility_rate`, `prompt_length_violation_rate`, `llm_candidate_relevance_rate`) was discarded because PR #87's pre-validation makes them all 100% / 0% by construction. |

### 3.3 P2 — Scenario fixtures and experiment success criteria

#### P2.1 Expected-fixture variability allowance

`integration/tests/data/expected_class2_*.json` files mention specific
`expected_first_candidate_id` values like `C1_LIGHTING_ASSISTANCE`. Under
LLM mode the candidate id may be different. Two options:

- (a) Relax expected-fixture matching: accept any candidate id whose
  `candidate_transition_target` and `action_hint`/`target_hint` match the
  expected first-candidate semantics.
- (b) Add a separate `expected_class2_*_llm_mode.json` shadow fixture
  family so static-mode trials and LLM-mode trials evaluate against
  different expectations.

(a) is simpler but couples the verifier to looser assertions. (b) is
explicit but doubles the fixture surface. Recommendation: (a) with the
loosening codified in `integration/scenarios/scenario_manifest_rules.md`
and a comment in each affected expected fixture pointing at the rule.

#### P2.2 Trial timeout decomposition

`_TRIAL_TIMEOUT_CLASS2_S = 360.0` is currently a single number meant to
cover Phase 1 (user, 30 s) + Phase 2 (caregiver, 300 s) + telemetry. With
LLM in the loop the implicit budget breakdown is fragile. Decompose into
named constants:

```
_LLM_BUDGET_S          # policy llm_class2_request_timeout_ms / 1000 + slack
_USER_PHASE_TIMEOUT_S  # policy class2_clarification_timeout_ms / 1000
_CAREGIVER_PHASE_TIMEOUT_S  # CAREGIVER_RESPONSE_TIMEOUT_S
_TRIAL_TIMEOUT_CLASS2_S = _LLM_BUDGET_S + _USER_PHASE_TIMEOUT_S + _CAREGIVER_PHASE_TIMEOUT_S + slack
```

This way, when policy timing changes, the trial timeout adjusts
automatically and the dashboard can show per-phase consumption.

#### P2.3 Class 2 LLM-vs-static comparison condition

Package A already has `comparison_condition` for Class 1 intent recovery
(`direct_mapping`, `rule_only`, `llm_assisted`). Class 2 candidate
generation deserves a parallel concept so the paper / evaluation can
measure the LLM contribution independently:

- `class2_candidate_source_mode = static_only` — manager skips LLM call,
  always uses `_DEFAULT_CANDIDATES`.
- `class2_candidate_source_mode = llm_assisted` — current default.

Implementation would mirror PR #79's `experiment_mode` plumbing
(`routing_metadata.experiment_mode` extended, manager honours it).

This is the largest item in P2 and should be the last to land — the
metrics from PR #89 already let us see LLM vs static effects; an explicit
mode flag is needed only when we want to *force* a comparison.

## 4. Recommended Sequencing

| PR | Tier | Items | Rationale |
|---|---|---|---|
| **A** (this doc) | — | This alignment plan | Land first; freeze the priority agreement before any code touches |
| **B** | P0 | P0.1 + P0.2 + P0.3 together | They are coupled; fixing only one leaves the others harmful |
| **C** | P1 | All P1 items in one docs-only PR | No code; mechanical |
| **D** | P2.1 | Expected-fixture variability allowance | Required before any real LLM-mode trial run |
| **E** | P2.2 | Trial timeout decomposition | Should follow B (uses the new policy timeout) |
| **F** | P2.3 | Class 2 LLM-vs-static comparison condition | Optional / future paper-evaluation feature |

PR B (P0) is the only true safety regression fix. PR C (P1) is housekeeping
and can land in parallel with B. PRs D-F are evaluation-side improvements
that mostly matter when real LLM trials begin.

## 5. Out of Scope

- Multi-turn clarification (Phase 6 of `09_*`) remains deferred.
- LLM model selection / Ollama configuration tuning. Operations concern;
  not a code/policy concern in this codebase.
- Telegram caregiver path latency. Caregiver phase is already a long
  budget (300 s); LLM has no effect on Telegram round-trip.

## 6. Open Decisions for the Maintainer

1. **P0.1 fix shape — option (a) or (b)?**
   (a) "static first, LLM may upgrade later" or
   (b) "wait briefly for LLM with tight budget, otherwise static".
   (b) is simpler and lets us land P0 in one shot. (a) is the better
   long-term experience but takes another iteration. Recommend (b) now.

2. **P0.2 — where does the LLM request timeout live?**
   Suggest `global_constraints.llm_class2_request_timeout_ms = 8000` so
   it sits next to other Class 2 timing constants. Adapter still keeps a
   60 s code-level fallback for safety on very old policy versions.

3. **P2.1 fixture strategy (a vs b)?**
   Recommend (a) (loosened matching with a manifest-rules note); cheaper.

4. **P2.3 priority — implement now or defer?**
   Recommend defer until first paper-evaluation cycle. Premature plumbing
   without a measured need.

## 7. Source Notes

This document captures the 2026-05-01 integration alignment review between
the maintainer and the AI assistant. Phases referenced:

- `09_llm_driven_class2_candidate_generation_plan.md` (PR #86)
- PR #87 (Phases 1+2), PR #88 (Phase 3), PR #89 (Phase 5)
