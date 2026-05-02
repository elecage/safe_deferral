# Plan — Post-doc-12 Consistency Backfill

**Date drafted:** 2026-05-02
**Trigger:** Architecture-consistency audit after PRs #104–#111 (doc 12 fully landed) found drift between active architecture docs (00–04), MQTT/payload contract reference, scenario coverage, and the new Class 2 capabilities (scanning, multi-turn refinement, deterministic ordering, interaction-model comparison).
**Goal:** Close the drift in 8 small focused PRs, prioritized P0 → P3. **No new product features in this plan** — only docs, MQTT contracts, scenarios, and verification work.

---

## 1. Audit summary

The Explore-agent audit identified 8 categories of drift / gaps. Distilled:

| # | Area | Drift summary |
|---|------|----|
| A | docs 01–04 | Don't mention scanning, multi-turn refinement, deterministic ordering, the four routing_metadata comparison fields, or the four-dimensional paper-eval composition. Doc 04 (Class 2 deep-dive) only describes direct_select. |
| B | MQTT/payload contract reference | `common/mqtt/topic_payload_contracts.md` doesn't describe the four new `routing_metadata.*` fields or the four new `clarification_interaction_*` fields. No example payloads carrying the new fields. |
| C | Scanning scenarios | Zero scenarios exercise `class2_input_mode='scanning'`. |
| D | Multi-turn scenarios | Zero scenarios exercise `refinement_history` (PR #102's opt-in path). |
| E | Ordering scenarios | Zero scenarios exercise `scan_ordering_applied` (PR #110). |
| F | Manifest tagging | `scenario_manifest_schema.json` has no `comparison_conditions[]` field, so paper-eval cannot mechanically verify which scenario covers which of Package A's 9 conditions. |
| G | Dashboard rendering | PR #99 trial detail UI may not surface `input_mode` / `scan_history` / `scan_ordering_applied` / `refinement_history`. Needs verification. |
| H | Fixture cleanup | Old prompt strings (`"조명 도움이 필요하신가요?"`) still in test fixture comments — cosmetic, can ride along with another PR. |

The full audit (with file paths) is preserved in this session's transcript.

---

## 2. PR roadmap (8 PRs)

### Tier P0 — Authoritative documentation correctness (must-do)

**PR #1 — docs 01–04 backfill for new Class 2 modes**
- Update `01_system_architecture.md`: list scanning / multi-turn / ordering as Class 2 capabilities; reference docs 10–12 for design.
- Update `02_safety_and_authority_boundaries.md`: explicitly state that scanning, refinement, and ordering preserve the same Class 0 / 1 / 2 authority boundaries (no new actuator surface, validator stays final, silence ≠ consent).
- Update `03_payload_and_mqtt_contracts.md`: document the four optional `routing_metadata` fields (`experiment_mode`, `class2_candidate_source_mode`, `class2_scan_ordering_mode`, `class2_input_mode`) and the four new `clarification_interaction` fields (`input_mode`, `scan_history`, `scan_ordering_applied`, `refinement_history`).
- Update `04_class2_clarification.md`: add sections covering scanning interaction model, multi-turn refinement, deterministic ordering, paper-eval comparison composition. Cross-link docs 10, 11, 12.
- No code changes; tests unaffected.

**PR #2 — MQTT/payload contract reference + example payloads**
- Update `common/mqtt/topic_payload_contracts.md` with the 8 new fields (4 in routing_metadata, 4 in clarification_interaction).
- Add 3 example payloads under `common/payloads/examples/`:
  - scanning clarification record (`input_mode='scanning'` + populated `scan_history`)
  - multi-turn refinement record (with `refinement_history`)
  - deterministic-ordering record (with `scan_ordering_applied`)
- Validate examples against the schemas in CI/test.

### Tier P1 — Scenario coverage for paper-eval

**PR #3 — Scanning input scenarios** (P1)
- 2–3 scenarios with `routing_metadata.class2_input_mode='scanning'`.
- Cover: yes-on-first-option, all-no escalation, emergency triple_hit shortcut.
- Validate `scan_history` shape via integration verifier.

**PR #4 — Multi-turn refinement scenarios** (P1)
- 1–2 scenarios with `policy.class2_multi_turn_enabled=true` and a `C1_LIGHTING_ASSISTANCE` parent that triggers refinement.
- Cover: refinement accept, refinement timeout → escalate.

**PR #5 — Deterministic ordering scenarios** (P1)
- 1–2 scenarios that exercise the ordering rules (e.g., C208 doorbell + smoke override).
- Validate `scan_ordering_applied` matched_bucket and applied_overrides.

### Tier P2 — Operational tooling

**PR #6 — Scenario manifest schema: `comparison_conditions[]` field** (P2)
- Add optional `comparison_conditions` array to `scenario_manifest_schema.json`.
- Backfill all 16 scenarios with the conditions they actually exercise.
- Add a verifier (test) that asserts each Package A condition is covered by ≥1 scenario.

**PR #7 — Dashboard audit-field rendering verification** (P2)
- Verify `rpi/code/dashboard/static/index.html` trial detail rows surface `input_mode`, `scan_history`, `scan_ordering_applied`, `refinement_history`.
- If any are missing, add minimal rendering (lazy-loaded section per PR #99 pattern).

### Tier P3 — Polish

**PR #8 — Fixture comment cleanup** (P3)
- Update test fixture comments referencing the old `"조명 도움이 필요하신가요?"` prompt to explain why state-aware prompts now apply.
- No code change. Can be bundled with any other PR; not standalone.

## 3. Sequencing

```
P0 first (PR #1 → PR #2)        ← starts now
  ↓
P1 (PR #3 → #4 → #5, parallel-able if needed)
  ↓
P2 (PR #6 → #7)
  ↓
P3 (PR #8, bundle into a P1/P2 PR if convenient)
```

Each P0 PR creates the reference material the later PRs cite. P1 builds on P0 (scenario writers consult updated docs). P2 builds on P1 (manifest tagging needs the new scenarios to exist). P3 is incidental.

## 4. Out of scope (this plan)

- No new product features. All 8 PRs are docs / scenarios / tooling.
- No changes to authority boundaries, schemas (except the manifest schema in PR #6), or runtime behaviour.
- No paper-eval matrix run. The 4-dimensional comparison_conditions framework is in place after PR #111; the *operational* run (scripted trials, results aggregation) is a separate effort once P0–P2 ship.

## 5. Anti-goals (avoid drift while closing drift)

- Do not touch canonical policy/schema assets unless a documented inconsistency requires it (PR #6 is the one exception — adding an optional manifest field).
- Do not invent new comparison_conditions, modes, or fields. The audit found enough work just describing what already exists.
- Do not refactor `_DEFAULT_CANDIDATES`, `_REFINEMENT_TEMPLATES`, or `_scan_ordering_rules` — these are stable surfaces; consumers read them.
- Do not bundle multiple P0 items into one PR (keeps reviews small and focused).

## 6. Tracking

- Each PR's session handoff goes under `common/docs/runtime/SESSION_HANDOFF_*.md` and is added to `SESSION_HANDOFF.md` index.
- This plan stays as `PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md` for the duration of the backfill. Each PR's handoff references this plan.
- When all 8 PRs land, this plan can move to `common/docs/runtime/archive/` (or similar) — to be decided when we reach that point.

---

## 7. Active starting point

**PR #1 begins immediately after this plan + audit handoff merge.** Branch name: `claude/p0-1-docs-01-04-backfill`.
