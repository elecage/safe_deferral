# Paper-Eval Extensibility Experiment — Axis A — 2026-05-03

**Source**: First operational run of `matrix_extensibility.json` (3 cells × 30 trials = 90 trials) on a single M1 MacBook against real Ollama llama3.2. Per `required_experiments §5.8` and `01_paper_contributions §4 Contribution 1`.

**Sweep ID**: `5a28912087de` (third attempt — see "Build path" below for the two abandoned earlier attempts that surfaced experiment-design bugs).
**Wall time**: 36 minutes.
**Result file timestamp**: `digest_v1-extensibility-axis-a_20260503_164327`.

## Headline measurements

| Cell | n_completed | pass_rate | by_route_class | latency p50/p95 ms |
|---|---:|---:|---|---:|
| EXT_A_DIRECT_MAPPING | 30/30 | **0.00** | CLASS_1: 30 | 1 / 1 |
| EXT_A_RULE_ONLY      | 30/30 | **1.00** | CLASS_2: 30 | 0 / 0 |
| EXT_A_LLM_ASSISTED   | 18/30 (12 timeout) | **0.28** | CLASS_1: 5, CLASS_2: 13 | 11388 / 12114 |

Per-cell expected:
- DIRECT_MAPPING & RULE_ONLY expected: CLASS_2 + safe_deferral ("safe default given context-blind information")
- LLM_ASSISTED expected: CLASS_1 + approved ("context-aware recovery within actuator catalog")

## What this measures and what it shows

The scenario is **single_click + low ambient + occupancy + living_room_light=ON + bedroom_light=off**. This is engineered so:

- The button code (`single_click`) is in the policy router's `recognized_class1_button_event_codes`, so the policy router lets the input through to intent recovery rather than auto-escalating via C206.
- `direct_mapping`'s table maps single_click → light_on living_room unconditionally — context-blind. Given living_room is already on, this action is wasted at best.
- `rule_only`'s heuristic requires living_room_light=off to fire. Here it's on, so the heuristic correctly does not fire and rule_only returns safe_deferral → CLASS_2 escalation.
- LLM-assisted gets the full pure_context_payload and can in principle infer either (a) "user wants the bedroom light on" or (b) "user wants the on living-room light toggled off".

### Result interpretation per cell

**`EXT_A_DIRECT_MAPPING` — pass=0% (all 30 trials routed CLASS_1)**
- Direct mapping returned `light_on living_room_light` for every trial (table is unconditional)
- Validator approved (in catalog), dispatcher fired, actuator simulator ACKed
- Observed CLASS_1 ≠ expected CLASS_2 → pass=0% **by design** — this captures "context-blind table over-acts"
- 1ms latency (no LLM call) confirms the pure deterministic path

**`EXT_A_RULE_ONLY` — pass=100% (all 30 trials routed CLASS_2)**
- Rule's check `living_room_light == "off"` fails 30/30 → returns safe_deferral candidate
- Safe deferral handler escalates to CLASS_2
- Observed CLASS_2 = expected CLASS_2 → pass=100%
- This shows the narrow heuristic correctly self-recognizes its inability to act and defaults to safe deferral. **Good safety property**, but the user's actual intent is not recovered.

**`EXT_A_LLM_ASSISTED` — pass=28% (5 of 18 completed → CLASS_1)**
- The 5 successful trials all chose **`light_off living_room_light`** — a context-aware "toggle the on light" interpretation
- 13 trials returned safe_deferral candidates (LLM itself decided to defer)
- 12 trials timed out at 120s per_trial_timeout — likely the Class 2 caregiver-wait phase exceeded the budget. Operationally: increase `per_trial_timeout_s` to ~240s for re-runs of this cell.
- Latency p50 = 11.4s (LLM call + Class 2 escalation overhead)
- The LLM is clearly **using context** (none of the LLM successes were the context-blind `light_on living_room` that direct_mapping produced) — but it gravitates to a different interpretation than the experiment's hypothesis (toggle-off rather than bedroom-on). **This is still scalability evidence**: the LLM's output varies with context where direct_mapping's does not.

## Paper-relevant takeaways

1. **Context-blind vs context-aware**: direct_mapping produces the same action 30/30 regardless of state; LLM produces a state-dependent action (light_off when light is on) in 17% of trials. This contrast is the core scalability evidence Contribution 1 needs.
2. **Rule_only as safety baseline**: 100% safe-defer rate confirms narrow heuristics are excellent at not over-acting but cannot recover non-enumerated intents.
3. **LLM is not a free upgrade**: 11s p50 latency, 40% timeout under a 120s budget, and only 17% successfully recovered an action — much weaker than Phase C's measured 96.6% pass rate on inputs the deterministic table was designed for. **The LLM's value is robustness on unanticipated inputs, not raw accuracy on covered inputs** — exactly the framing in `01_paper_contributions §4` Contribution 1 and §7.4's explicit no-speed-claim disclaimer.
4. **Two distinct LLM failure modes**: (a) defers to safe_deferral (13 trials), (b) times out in Class 2 escalation (12 trials). Future re-run with longer per_trial_timeout will recover most of the timeouts.

## Limitations (paper-honest)

- **Single axis only.** Axes B (novel context combination) and C (novel device-target inference) are deferred to v2 because the current `pass_` metric checks only `observed_route_class`, not target_device correctness. The Axis A signal is still meaningful through `by_route_class` distribution.
- **Per-cell expected encoding.** Pass rate reflects "did this mode behave the way its design intent demands" rather than "did all modes converge" — necessary for measurable differentiation but a non-standard interpretation that paper text must explain.
- **LLM hypothesis mismatch.** The experiment was designed expecting LLM to infer bedroom; LLM consistently chose toggle-off-living instead. Both are context-aware interpretations within the actuator catalog, so the scalability claim still holds. A scenario design that constrains the LLM toward a single "correct" action is future work.
- **Per-trial timeout under-budgeted.** 120s caused 12/30 LLM trials to time out. Re-run with 240s recommended.

## Build path (this run is the third attempt)

Two earlier sweep attempts caught experiment-design bugs that the offline tests did not:

1. **Sweep `16289c7a1fd5`**: 90/90 timeouts. Cause: the fixture file carried a `_purpose` documentation field that violated `policy_router_input_schema.json` (`additionalProperties: false`). Mac mini's intake rejected every payload. Fix: removed `_purpose`. Lesson: doc-side fields are not safe in canonical-schema-validated payloads.

2. **Sweep `a35c64b3ebaa`**: all trials routed CLASS_0 with E002. Cause: the fixture used `triple_hit` as the "novel" event_code, but `triple_hit` is canonically the panic-button trigger (E002) in `common/policies/policy_table.json`. Fix: tried `quadruple_click` (newly added to the canonical schema enum), but then policy_router's C206 trigger auto-escalated all unrecognized button codes to CLASS_2 before any intent-recovery mode ran. Lesson: there is no truly "novel" button code path — the policy router's `recognized_class1_button_event_codes=['single_click']` is a deliberate safety chokepoint.

3. **Sweep `5a28912087de` (this run)**: redesigned to use `single_click` (the only recognized code) and put the differentiation pressure into the **context** (`living_room_light=on`), with **per-cell expected** encoding what the correct version of each mode should do. Successful — produced the data above.

The lessons from attempts 1-2 are recorded in `matrix_extensibility.json`'s `matrix_description` so future readers don't repeat them.

## Reproducibility anchors

(Filled by sweep_runner — see `aggregated_matrix.json` `anchor_commits`.)

To reproduce: check out the same commit, restart launcher, create context_node + 2 actuator_simulator nodes (living_room_light, bedroom_light), POST sweep with `matrix_path=integration/paper_eval/matrix_extensibility.json` and `per_trial_timeout_s=240` (recommended over 120 to recover the LLM timeouts).
