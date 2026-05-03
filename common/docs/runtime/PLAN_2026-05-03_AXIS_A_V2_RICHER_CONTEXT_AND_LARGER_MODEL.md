# PLAN — Extensibility Axis A v2: Richer Context + Larger Model + Minor Prompt Refinement

**Date:** 2026-05-03
**Predecessor:** Step 3 archive `2026-05-03_extensibility_axis_a` (PR #146).
**Trigger:** Step 3 sweep showed LLM_ASSISTED at pass_rate=28% (5 of 18 completed CLASS_1, 13 chose `safe_deferral`, 12 timed out under 120s budget). User decided three orthogonal levers should be tried — A (fixture context enrichment), B (gemma4:e4b model swap), C (minor general-purpose prompt hint) — to measure whether richer signal + larger model + slightly more action-oriented prompt change the LLM's recovery rate.

**Why now:** Axis A v1 evidence is paper-honest but weak (28% recovery). v2 measures whether the LLM's deferral was a *capacity* limitation (small model, sparse context) or a *prompt-doctrine* outcome (LLM correctly defers under genuinely ambiguous input). Either way, v1 + v2 side-by-side becomes the paper-grade ablation.

---

## 1. Scope (in this plan)

**Step 4 PR scope reduction (2026-05-03):** Lever A was deferred during Step 4
implementation when the canonical `context_schema.json` was confirmed to NOT
permit `user_state.inferred_attention` or `recent_events`
(`additionalProperties: false`, only `trigger_event`/`environmental_context`/
`device_states` declared). This plan originally claimed those fields were
already canonical — that was incorrect. Per CLAUDE.md ("Canonical policy/schema
assets are not casual edit targets"), the schema change was extracted into a
separate follow-up PR so it can be reviewed independently. Step 4 ships Levers
B + C only; Lever A becomes Step 5 once the schema extension lands.

**In scope (Step 4 PR — Levers B + C):**
- Model swap to gemma4:e4b via env (no canonical change)
- Minor general-purpose prompt hint — `_SYSTEM_HEADER` rule 9
- New v2 matrix `matrix_extensibility_v2.json` reusing v1 scenario/fixture
- Re-run sweep with `per_trial_timeout_s=480` (gemma4:e4b is ~4× larger than
  llama3.2; v1's 120s budget produced 12 timeouts; the v1 README's 240s
  recommendation was sized for llama3.2, so v2 doubles it as headroom)
- Archive as `runs_archive/2026-05-03_extensibility_axis_a_v2/`
- Side-by-side v1 vs v2 README

**Deferred to Step 5 (separate PR):**
- Canonical `context_schema.json` extension to allow optional `user_state`
  (with `inferred_attention` enum) and `recent_events` (array of
  `{event_type, event_code, timestamp_ms}`)
- `prompt_builder` extension to surface those fields in the LLM prompt
- v2 fixture and scenario manifest using the enriched fields
- Re-run of Axis A under Lever A only (or A+B+C combined) for paper

**Out of scope (still):**
- Larger models (gemma4:26b, gemma4:31b) — laptop OOM risk per user
- Axes B and C (still v3 / future, awaits target-device-correctness metric)
- Prompt rewrite of rules 1-8 — only one *additional* general guidance line

## 2. Three lever decisions (recap of conversation)

### 2.1 Lever A — Fixture context enrichment (accepted)

Current Axis A fixture only populates `environmental_context` and `device_states`. Schema permits richer fields the LLM would benefit from:

- `pure_context_payload.user_state.inferred_attention` — e.g. `engaged`, `transitioning`, `idle`
- `pure_context_payload.recent_events` — recent button/sensor events list

These fields are sent to the LLM in `prompt_builder` (currently it includes whatever is in pure_context_payload). Enriching them gives the LLM more signal to disambiguate the single_click + living_on context. **No schema change** — fields are already canonical, just under-used by Axis A v1.

**Honest framing:** v2 fixture = "what a real deployment with active-attention tracking would send." v1 fixture = "what a minimal-context deployment would send." Both are valid sub-scenarios. Paper can cite both as range.

### 2.2 Lever B — Larger model: gemma4:e4b (accepted)

User confirmed `gemma4:e4b` (~9.6 GB, 8B parameters) is OK on this M1 laptop. `gemma4:31b` rejected as too heavy.

Swap mechanism: `OLLAMA_MODEL` env var (already parameterized in #141). Launcher's `.env` template gets the new value before the v2 sweep, restored to llama3.1 default after (llama3.2 is being phased out of the operational default because of Korean-output quality issues; v1 archives that ran on llama3.2 keep their historical reproducibility intact through their archive snapshots).

**Honest framing:** model size is independent of Axes A/B/C — it's an "ablation factor". Paper can present "Axis A under llama3.2 vs gemma4:e4b" as a model-size sensitivity study. Does NOT change the LLM-vs-deterministic comparison structure.

### 2.3 Lever C — Minor general-purpose prompt hint (accepted)

User explicitly limits this to "general-purpose 가이드" — no scenario-specific cherry-picking. Acceptable change:

> **Add to `_SYSTEM_HEADER`**: a single rule that encourages context use without naming specific situations. Suggested wording (Korean to match existing prompt):
>
> "9. device_states와 environmental_context를 명시적으로 활용해 trigger의 의도를 해석하세요. 충분한 신호가 있으면 safe_deferral보다 actuator catalog 안의 행동을 우선 고려합니다."
>
> Translation: "Explicitly use device_states and environmental_context to interpret the trigger's intent. When signals are sufficient, prefer an actuator-catalog action over safe_deferral."

This is **general** (mentions no specific room, button code, or device combination). It encourages the LLM to use available context rather than default to defer.

**Honest framing:** the change applies to ALL trials, ALL cells, ALL future sweeps. Phase C re-run would be needed to confirm no regression in covered-input behaviour. We compare v1 (current prompt) to v2 (current + line 9) on the SAME Axis A scenario as one A/B test, plus rerun matrix_smoke + Phase B to confirm no regression on covered input.

**Anti-cherry-picking guard:** if line 9 changes Axis A llm_assisted from 28% → 60%+ but ALSO changes Phase C pass rates noticeably, we need to discuss whether the prompt is now over-fit. Honest report regardless of direction.

## 3. Files to change (별 PR)

### 3.1 Fixture (Axis A v2)

`integration/tests/data/sample_policy_router_input_extensibility_a_novel_event_code.json` — extend `pure_context_payload` with:

```jsonc
{
  "pure_context_payload": {
    "trigger_event": { /* unchanged: single_click */ },
    "environmental_context": { /* unchanged */ },
    "device_states": { /* unchanged: living_room_light=on, bedroom_light=off */ },
    "user_state": {
      "inferred_attention": "engaged"
    },
    "recent_events": [
      { "event_type": "sensor", "event_code": "occupancy_motion_in_bedroom", "timestamp_ms": <now-30s> }
    ]
  }
}
```

OR the v1 fixture stays untouched and a new `_v2_richer_context.json` fixture is added — TBD, leaning toward NEW fixture file so v1 remains intact for v1-vs-v2 comparison.

**Decision:** new file `sample_policy_router_input_extensibility_a_v2_richer_context.json` so v1 evidence stays intact.

### 3.2 Scenario manifest

Either:
- Reuse the existing scenario manifest with both fixtures listed (steps array adds v2 fixture), OR
- New scenario manifest `extensibility_a_v2_*.json` paired with the new fixture

**Decision:** new scenario file so v1 / v2 manifests are independent and the v2 manifest's description can document the enrichment rationale.

### 3.3 Matrix

New `integration/paper_eval/matrix_extensibility_v2.json` — 3 cells (DIRECT/RULE/LLM) × 30 trials with v2 scenario, per_trial_timeout_s=240.

v1 matrix file (`matrix_extensibility.json`) **unchanged** — preserves reproducibility for the archived v1 run.

### 3.4 Prompt (mac_mini)

`mac_mini/code/local_llm_adapter/prompt_builder.py` — append the line 9 to `_SYSTEM_HEADER`. Single addition.

### 3.5 Tests

- `mac_mini/code/tests/test_local_llm_adapter.py` — verify the new line 9 is in the prompt header (regression guard so future edits don't drop it silently)
- `rpi/code/tests/test_paper_eval_sweep.py` — extend TestExtensibilityMatrix with a `TestExtensibilityMatrixV2` mirror that loads the new matrix and validates the same invariants (per-cell expected, scenario tags)

### 3.6 Schema

**No change.** All v2 fields are already in `context_schema.json`. (Verification step in PR — confirm by validating the new fixture against the canonical schema.)

## 4. Sweep operation procedure

1. `OLLAMA_MODEL=gemma4:e4b` set in `~/smarthome_workspace/.env` (or via launcher restart with new env)
2. `./scripts/local_e2e_launcher.sh` → wait for healthy
3. Create context_node + 2 actuator_simulator (living_room_light, bedroom_light)
4. POST `/paper_eval/sweeps` with `matrix_path=integration/paper_eval/matrix_extensibility_v2.json` + `per_trial_timeout_s=240`
5. Monitor via dashboard → wait for completion
6. Archive to `runs_archive/2026-05-03_extensibility_axis_a_v2/` with paired README that:
   - Lists v1 metrics next to v2 metrics in a single comparison table
   - Notes the model used (gemma4:e4b)
   - Notes the prompt change (line 9)
   - Notes the fixture enrichment

7. **Regression check**: re-run `matrix_smoke.json` + `matrix_phase_b.json` under gemma4:e4b + new prompt. Document side effects in v2 README.

**Estimated wall time:** ~20-40 min for v2 Axis A sweep + ~5-10 min for smoke regression. Total ~50 min.

## 5. Success criteria

The plan succeeds even if outcomes are negative:

- **If v2 LLM pass_rate ≫ v1 (e.g. 60%+ vs 28%):** Lever C and/or A worked. Report which (we'll know because we can run one-at-a-time A/B if needed; for v1 we run all three together first).
- **If v2 LLM pass_rate ≈ v1:** the LLM's deferral was prompt-doctrine, not capacity. Strengthens the framing in `01_paper_contributions §7.4` ("LLM is conservative under genuine ambiguity").
- **If v2 LLM pass_rate < v1:** something regressed (probably C). Investigate before paper claims.
- **Regression on Phase B/smoke:** rolls back lever C (revert prompt), keeps A and B for narrower v2 measurement.

## 6. Anti-goals

- **No retroactive Phase C overwrite.** Phase C archive (PR #140) stays as is. v2 results are an *additional* data point, not a correction.
- **No cherry-picking the scenario.** Same Axis A semantic (single_click + living_on + bedroom_off) — only the *amount of context* and the *model* and *prompt-doctrine line* change.
- **No silent rollback to a stale default.** After v2 sweep, restore `.env` to `OLLAMA_MODEL=llama3.1` (llama3.2 is being retired from the operational default because of Korean-output quality issues; v1 Phase C / smoke / Phase B archives that ran under llama3.2 retain reproducibility through their archive snapshots, not through the live default).

## 7. Phase split

- **This PR:** plan doc + handoff doc only (no code/asset changes). Captures decisions before implementation.
- **Step 4 PR (next):** all code/asset changes from §3 + Step 4 sweep archive.

## 8. Backlog after Step 4

(Carried forward from `PLAN_2026-05-02_PAPER_REFRAME_AND_OPEN_OPS_BACKLOG.md`.)

| 항목 | 우선순위 | 비고 |
|---|---|---|
| Multi-turn recovery sweep | HIGH (paper integrity) | Phase C 2 invalid cells, 정책 임시 활성화 + 재실행 ~30min |
| target-device-correctness metric → Axes B/C | MEDIUM (paper richer) | 코드 확장 필요, 큰 작업 |
| Item 2 fix (cancel partial preservation) | MEDIUM (ops) | ~30min 코드 |
| Temp/top_p sweep | LOW (보조) | 코드 ready (#141 #142), 운영 ~2.5h |
| #1 retry (matrix_v1 timeout=240) | LOWEST | marginal, archive에 이미 351/360 |
| doc 13 update | LOW (cosmetic) | extensibility ship 후 §9 update |
