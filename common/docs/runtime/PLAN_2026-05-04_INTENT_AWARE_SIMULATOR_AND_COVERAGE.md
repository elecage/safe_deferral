# PLAN — Intent-Aware Simulator + Coverage Matrix v4 (PR #154)

**Date:** 2026-05-04
**Predecessor PR:** #152 (intent_match_rate metric stack)
**Predecessor handoff:** [SESSION_HANDOFF_2026-05-04_END_OF_SESSION_PR148_TO_152_MERGED.md](SESSION_HANDOFF_2026-05-04_END_OF_SESSION_PR148_TO_152_MERGED.md) §3.1
**Methodology doc:** [05_class2_clarification_measurement_methodology.md](../paper/05_class2_clarification_measurement_methodology.md) §6
**Status:** PLAN (no implementation yet — review gate before code)

---

## 1. Problem statement

### 1.1 The simulator is intent-blind

PR #151 introduced `_user_response_script` with two modes:
- `no_response` — caregiver-fallback baseline
- `first_candidate_accept` — single_click immediately after CLASS_2 announcement

PR #152 introduced `intent_match_rate` (semantic fidelity) as the third metric in the pass / match / **intent** stack. The framework now exposes the trial-2 case ("system actuated something correctly, but actuated the wrong thing") to the dashboard and digest.

But the simulator that generates the data feeding `intent_match_rate` does not consult `scenario.user_intent` at all. `first_candidate_accept` always selects index 0 regardless of whether index 0 matches the scenario's declared intent. The 2026-05-04 verification sweep made this concrete: trial 3 of `EXT_A_LLM_DEFER_FIRST_CANDIDATE_ACCEPT` had `pass=✅ match=✅ intent=❌` because the LLM put `light_on living_room_light` first when `user_intent=light_on bedroom_light`. The simulator dutifully selected the first option.

This means the sweep's `intent_match_rate` numbers under existing scripts measure **the LLM's ability to put the user-intended candidate first**, not **the system's ability to reach the user's intent through the dialogue**. They are different questions.

### 1.2 What this gap blocks

- `intent_match_rate` cannot reach 1.0 unless the LLM happens to rank correctly. The dialogue's recovery dimension (the user disambiguates a wrong first proposal via scanning, or via direct-select on a non-first candidate) is invisible.
- The "scanning mode" cells planned in v3 (`EXT_A_LLM_DEFER_SCAN_*`) cannot be implemented honestly without a script that drives the scanning yes/no sequence to a target index.
- `caregiver_help_accept` and `triple_hit_emergency` paths — both architecturally present in the Class 2 clarification flow — are unmeasured.
- The paper's "multi-turn perception scalability" claim rests on the dialogue path being able to recover the user's intent; without intent-aware simulation, the scanning dimension of the experiment matrix is empty.

### 1.3 Why this split (PR #152 vs #154)

PR #152 added the metric (a measurement layer that can be populated by ANY simulator). PR #154 adds the simulator that exercises the metric across all script modes × intent combinations. The split keeps the metric land-and-bake before the simulator changes the input distribution; intent_match_rate per cell from PR #152 stays valid as a baseline against which the new scripts can be compared.

---

## 2. Scope

### 2.1 In scope (this PR)

1. **Schema extension** — add optional `action_hint` / `target_hint` to `clarification_interaction_schema.json` candidate items (see §3.1).
2. **`ClarificationChoice.to_schema_dict()` update** — emit the new optional fields when present.
3. **New script modes** in `runner._match_observation` (see §3.3):
   - `accept_intended_via_direct_select` — scan candidates, find intent-matching, single_click only when it lands at index 0 (limitation documented).
   - `accept_intended_via_scan` — scanning mode with `double_click ... double_click single_click` to reach intent index.
   - `scan_until_yes(yes_at)` — AAC scanning baseline without intent awareness.
   - `scan_all_no` — caregiver fallback path under scanning.
   - `caregiver_help_accept` — explicit single_click on the CAREGIVER_HELP candidate.
   - `triple_hit_emergency` — emergency shortcut testing CLASS_2 → CLASS_0 transition under an active dialogue.
4. **Coverage matrix v4** — `matrix_extensibility_v4_intent_coverage.json` with cells covering each script mode × each `user_intent` (see §3.4).
5. **Aggregator** — light helper to verify cell `expected_route_class` / `expected_validation` is consistent with the scripted intent (see §3.5). No new metric; PR #152's `intent_match_rate` measures the right thing.
6. **Tests** at every layer (see §3.6).
7. **Paper doc §7** — coverage scenario catalog mapping each script mode to the architectural transition it exercises (see §3.7). Existing §7 (Cross-reference index) renumbers to §8.

### 2.2 Out of scope (deferred)

- **Hardware paper-grade verification** — separate work-stream per methodology §3, §5.
- **Multi-turn refinement scripts** — needs `class2_multi_turn_enabled=true` policy flag and refinement candidate handling. Tracked in [PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md §7](PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md). Could be PR #155.
- **Caregiver-phase response scripts** — Telegram inline-keyboard simulator. Cells declaring `caregiver_help_accept` exercise the trigger but not the caregiver-side response. Phase-2 work.
- **Lever A schema extension** (`user_state.inferred_attention` / `recent_events`) — independent backlog item from [PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md](PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md).
- **Trial-isolation bug** (sub-millisecond auto-selection from periodic context re-publish) — backlog item; this PR's scripts may surface but does not fix it.

### 2.3 Why this split (one-PR-vs-many)

All seven items in §2.1 are co-evolving: schema extension is necessary for the new scripts, the new scripts are necessary for the matrix, the matrix is necessary for the verification sweep, and the paper doc §7 is the user-facing index of what the matrix exercises. Splitting them risks landing a schema change that nothing exercises, or a matrix that the simulator can't run. Single PR keeps the logical unit intact.

---

## 3. Detailed design

### 3.1 Schema extension — clarification_interaction_schema.json

**Critical finding from code reading**: `ClarificationChoice.to_schema_dict()` strips `action_hint` and `target_hint` because the wire schema (`clarification_interaction_schema.json`, item-level) lists `additionalProperties: false` and does not include them. The runner reads `clarification_record` from `safe_deferral/clarification/interaction` via `ClarificationStore`. As the wire format stands, the runner cannot match candidates by `action_hint` / `target_hint` — only by `candidate_id` (works for default `OPT_LIVING_ROOM` / `OPT_BEDROOM` paths, fails for LLM-generated `candidate_id` strings).

Resolution — extend the schema to add OPTIONAL `action_hint` and `target_hint` to each `candidate_choices[*]` item. They are guidance only and do not authorize anything; the addition mirrors the in-process model and makes the auditable record complete.

```jsonc
// candidate_choices[*].properties additions (both optional)
"action_hint": {
  "type": ["string", "null"],
  "description": "Suggested CLASS_1 action for this candidate, when applicable. Guidance only — does not authorize actuation. Mirrors low_risk_actions.json action keys."
},
"target_hint": {
  "type": ["string", "null"],
  "description": "Suggested CLASS_1 target device for this candidate, when applicable. Guidance only — must be in low_risk_actions.json's allowed_targets when present."
}
```

`additionalProperties: false` at the item level remains. Both fields are nullable and absent = legacy behaviour.

`ClarificationChoice.to_schema_dict()` updates to emit them when non-None. Existing serialization tests must be updated to reflect the new fields. Existing scenarios continue to validate (additive change).

### 3.2 Where intent matching happens

Intent matching belongs in the **runner** (`rpi/code/experiment_package/runner.py`), not in the Mac mini. The Mac mini has no business knowing the scenario's `user_intent` — that is paper-eval ground truth, not system input (per methodology §6.2 design rule 1). The runner reads the clarification record from MQTT, finds the candidate whose `(action_hint, target_hint)` tuple matches the scenario's `user_intent`, and drives the appropriate button event.

Pseudocode:

```python
def _find_intent_matching_candidate_index(
    clarification_record: dict,
    user_intent: dict,
) -> Optional[int]:
    """Return 0-based index into candidate_choices for the candidate whose
    (action_hint, target_hint) matches user_intent. None if no match.

    The runner uses this index to drive scanning / direct-select correctly.
    Matching is exact on action AND target — partial matches are not honored
    because they would inflate intent_match_rate spuriously."""
    target_action = user_intent.get("action")
    target_device = user_intent.get("target_device")
    if not target_action or not target_device:
        return None
    for i, c in enumerate(clarification_record.get("candidate_choices", [])):
        if c.get("action_hint") == target_action and c.get("target_hint") == target_device:
            return i
    return None
```

### 3.3 Runner script-mode dispatch

Replaces the `script_mode == "first_candidate_accept"` branch in `runner._match_observation`. Refactored into a helper that returns `(event_sequence, drive_after_clarification_record)`:

| Script mode | Drive trigger | Event sequence | Notes |
|---|---|---|---|
| `no_response` | never | — | Existing baseline |
| `first_candidate_accept` | initial CLASS_2 routing snapshot | `["single_click"]` | Existing — kept for v3 baseline |
| `accept_intended_via_direct_select` | clarification_record arrival | `["single_click"]` IFF `_find_intent_matching_candidate_index() == 0` else NO drive | Direct-select can only select index 0 (single_click → first candidate). Documented limitation: when LLM ranks the intended candidate non-first, this script reports `intent=❌` honestly. |
| `accept_intended_via_scan` | clarification_record arrival | `["double_click"] * (idx) + ["single_click"]` paced by `class2_scan_per_option_timeout_ms / 2` | Scanning with `class2_input_mode=scanning` policy override. Each `double_click` = "no" to current option; final `single_click` = "yes". `idx=0` collapses to immediate `single_click`. |
| `scan_until_yes(yes_at: int)` | clarification_record arrival | `["double_click"] * yes_at + ["single_click"]` | Intent-blind scanning — selects whatever lands at `yes_at`. For AAC baseline cells. |
| `scan_all_no` | clarification_record arrival | `["double_click"] * n_candidates` | Drives all `no` responses; session ends in caregiver fallback. |
| `caregiver_help_accept` | clarification_record arrival | depends on `class2_input_mode` — direct: scan candidates for `candidate_transition_target=CAREGIVER_CONFIRMATION`, single_click if at index 0; scanning: navigate to its index | Tests the explicit-caregiver path. |
| `triple_hit_emergency` | initial CLASS_2 routing snapshot | `["triple_hit"]` | Tests CLASS_2 → CLASS_0 transition mid-dialogue. |

The dispatch lives in a new helper `_compute_class2_drive_plan(trial, clarification_record)` returning a typed plan; `_match_observation` just executes it. Trade-off: `triple_hit_emergency` and `first_candidate_accept` still drive on the initial snapshot (no clarification record needed); the others wait for the record so they can read candidate_choices for intent matching. Both gates must be respected.

Scanning event pacing: `class2_scan_per_option_timeout_ms` is the per-option dwell time; the simulator drives one event per dwell window (using `_POLL_INTERVAL_S` between events with floor of `class2_scan_per_option_timeout_ms / 2` as a safe lower bound to land within the announce window). The pacing constant is read from the policy table at script start.

### 3.4 Coverage matrix v4 — `matrix_extensibility_v4_intent_coverage.json`

Two-dimensional sweep: script mode × user_intent. Initial scenario set is the existing extensibility scenarios + 1-2 additional scenarios to give intent diversity:

| Scenario | Declared `user_intent` |
|---|---|
| `extensibility_a_novel_event_code_bedroom_needed_scenario_skeleton.json` | `light_on bedroom_light` (existing) |
| (new) `extensibility_a_novel_event_code_living_room_needed_scenario_skeleton.json` | `light_on living_room_light` |
| (new — optional) `extensibility_a_off_intent_bedroom_scenario_skeleton.json` | `light_off bedroom_light` |
| (new — optional) `extensibility_a_safe_deferral_intent_scenario_skeleton.json` | `action="none"` (intent is "user did not actually want anything actuated") |

Initial cell set (n=5 trials/cell at gemma4:e4b for dev verification):

| cell_id | scenario | script | expected_route | expected_validation | _policy_overrides |
|---|---|---|---|---|---|
| `EXT_A_INTENT_DIRECT_BEDROOM` | bedroom_needed | `accept_intended_via_direct_select` | CLASS_1 OR CLASS_2 | approved OR safe_deferral | (none) |
| `EXT_A_INTENT_SCAN_BEDROOM` | bedroom_needed | `accept_intended_via_scan` | CLASS_1 | approved | `class2_input_mode=scanning` |
| `EXT_A_INTENT_DIRECT_LIVING` | living_room_needed | `accept_intended_via_direct_select` | CLASS_1 | approved | (none) |
| `EXT_A_INTENT_SCAN_LIVING` | living_room_needed | `accept_intended_via_scan` | CLASS_1 | approved | `class2_input_mode=scanning` |
| `EXT_A_SCAN_YES_AT_0` | bedroom_needed | `scan_until_yes(yes_at=0)` | CLASS_1 | approved | `class2_input_mode=scanning` |
| `EXT_A_SCAN_YES_AT_1` | bedroom_needed | `scan_until_yes(yes_at=1)` | CLASS_1 | approved | `class2_input_mode=scanning` |
| `EXT_A_SCAN_ALL_NO` | bedroom_needed | `scan_all_no` | CLASS_2 | safe_deferral | `class2_input_mode=scanning` |
| `EXT_A_CAREGIVER_ACCEPT` | bedroom_needed | `caregiver_help_accept` | CLASS_2 | safe_deferral OR caregiver_required_sensitive_path | (none) |
| `EXT_A_TRIPLE_HIT_MID_DIALOGUE` | bedroom_needed | `triple_hit_emergency` | CLASS_0 | (escalation evidence) | (none) |

`expected_route_class` for direct/scan intent cells is conservative — both `CLASS_1` (intended candidate selected and validated) and `CLASS_2` (LLM put intended candidate non-first, direct-select returned safe-deferral) count as design-correct for the direct cell, because direct-select with non-first intent is a known limitation rather than a system failure. The `intent_match_rate` metric is what differentiates honest performance.

### 3.5 Aggregator helper — script consistency check

Light addition to `aggregator.py`: a function `_validate_cell_script_consistency(cell_dict)` that warns (does not fail) when a cell declares a script + `expected_validation` that the script's design cannot honestly produce. Examples:

- `scan_all_no` + `expected_validation="approved"` — impossible by design (warns).
- `accept_intended_via_scan` + `expected_route_class="CLASS_2"` — possible but unusual (warns).

Warnings surface as `cell._validation_warnings: list[str]` on `CellResult` and render in the digest. No new metric; PR #152's `intent_match_rate` already measures what coverage cells produce.

### 3.6 Tests

| Layer | New test |
|---|---|
| schema | `test_clarification_schema_accepts_action_hint_target_hint` (additive validation) |
| schema | `test_clarification_schema_rejects_unknown_extra_field` (additionalProperties=false still enforced) |
| manager | `test_to_schema_dict_emits_action_hint_when_present` (`mac_mini/code/tests/test_safe_deferral_handler_models.py` or equivalent) |
| sweep | `test_v4_every_cell_declares_user_response_script` |
| sweep | `test_v4_scan_cells_set_class2_input_mode_scanning` |
| sweep | `test_v4_intent_cells_reference_existing_scenarios_with_user_intent` |
| runner | `test_find_intent_matching_candidate_index_*` (match, no-match, missing-fields cases) |
| runner | `test_compute_class2_drive_plan_accept_intended_via_direct_select_at_index_0` |
| runner | `test_compute_class2_drive_plan_accept_intended_via_direct_select_non_first_no_drive` |
| runner | `test_compute_class2_drive_plan_accept_intended_via_scan_pads_double_clicks` |
| runner | `test_compute_class2_drive_plan_scan_until_yes` |
| runner | `test_compute_class2_drive_plan_scan_all_no` |
| runner | `test_compute_class2_drive_plan_caregiver_help_accept_finds_caregiver_candidate` |
| runner | `test_compute_class2_drive_plan_triple_hit_emergency` |
| runner | `test_simulate_class2_button_double_click` (event_code passthrough) |
| aggregator | `test_validate_cell_script_consistency_flags_known_impossible_pairings` |

Total: ~15 new tests across 4 files.

### 3.7 Paper doc §7 — coverage scenario catalog

Add §7 to [05_class2_clarification_measurement_methodology.md](../paper/05_class2_clarification_measurement_methodology.md), renumbering existing §7 (Cross-reference index) to §8. New §7 outline:

```
## 7. Coverage scenario catalog

### 7.1 Why this catalog matters
Each script mode in matrix v4 maps to a specific architectural mechanism. The
catalog makes the mapping explicit so reviewers can verify that the matrix
covers the dialogue's design space.

### 7.2 Catalog
| Script mode | Architectural transition exercised | Dialogue mechanism | Expected metric pattern |
|---|---|---|---|
| no_response | CLASS_2 → safe_deferral → caregiver phase | timeout fallback | pass≈match ≈ low; intent=N/A |
| first_candidate_accept | CLASS_2 → CLASS_1 (LLM-ranked first) | direct-select index 0 | intent==pass when LLM ranks intended first |
| accept_intended_via_direct_select | CLASS_2 → CLASS_1 only when intent at index 0 | direct-select index 0 with intent guard | exposes LLM ranking dependency |
| accept_intended_via_scan | CLASS_2 → CLASS_1 at intent index | scanning yes/no navigation | intent recoverable independent of LLM ranking |
| scan_until_yes(yes_at) | CLASS_2 → CLASS_1 at index `yes_at` (intent-blind) | scanning baseline | sweeps yes_at to characterize candidate ordering |
| scan_all_no | CLASS_2 → safe_deferral / caregiver | scanning timeout | matches no_response under scanning |
| caregiver_help_accept | CLASS_2 → caregiver phase via explicit selection | direct-select on CAREGIVER candidate | distinct from no_response (active selection vs timeout) |
| triple_hit_emergency | CLASS_2 → CLASS_0 mid-dialogue | emergency shortcut | tests dialogue-time emergency authority |

### 7.3 What this catalog does not cover (deferred)
- Multi-turn refinement (PR #155 candidate)
- Caregiver-phase Telegram response scripts
- Real-user dialogue variability (hardware run per §3, §5)
```

---

## 4. Implementation phases

Phase order (cleanest commit boundaries):

1. Schema + ClarificationChoice serialization + tests.
2. Runner intent-matching helper + script-mode dispatch helper + tests (no integration with `_match_observation` yet — pure functions).
3. Runner `_match_observation` integration (calls the new helpers) + `_simulate_class2_button` event_code passthrough + tests.
4. Coverage matrix v4 + new scenario fixtures + sweep tests.
5. Aggregator script-consistency helper + digest column + tests.
6. Paper doc §7 + handoff doc + PLAN doc updates.
7. Verification sweep against gemma4:e4b (operator-side; not a code commit).

Each phase is independently revertable.

---

## 5. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Schema extension breaks an existing consumer that reads `clarification_record` | Low — additive optional fields | Test `additionalProperties=false` still enforced for unknown keys; check rpi/code consumers (`clarification_store.py`, dashboard) for assumptions about candidate item shape |
| Scanning event pacing race — double_click events get coalesced or missed inside the dwell window | Medium | Pace at `class2_scan_per_option_timeout_ms / 2`; instrument drive events with timestamps so post-hoc analysis can detect pacing failures |
| LLM puts the intended candidate in a slot the scanning sweep doesn't reach (e.g., LLM emits 2 candidates, intent at index 3) | Medium | `_find_intent_matching_candidate_index` returns None → script logs and degrades to no-drive (safe-defer / caregiver path), trial reports `intent=❌` honestly |
| `triple_hit_emergency` mid-dialogue might not trigger the expected CLASS_2 → CLASS_0 transition if no CLASS_0 candidate is in the session | Low | scan_input_adapter already emits DECISION_IGNORE in that case; matrix cell uses scenario whose default candidates include `C3_EMERGENCY_HELP` |
| Dev sweep shows `intent_match_rate` regression in scan cells vs direct cells (unexpected) | Medium | Treat as discovery, not bug — report in handoff, do not change scripts to "fix" the number |
| Coverage matrix v4 verification sweep takes longer than expected (9 cells × 5 trials × LLM latency) | Medium | Per-trial timeout 480s; cell budget ≈ 40min; full sweep budget ≈ 6h. Operator runs overnight if needed. |

---

## 6. Files to change

```
common/schemas/clarification_interaction_schema.json                  (extend candidate_choices items)
mac_mini/code/safe_deferral_handler/models.py                          (ClarificationChoice.to_schema_dict)
mac_mini/code/tests/test_safe_deferral_handler_models.py               (or wherever the choice serialization is tested)

# Runner
rpi/code/experiment_package/runner.py                                  (helpers + _match_observation refactor + event_code passthrough)
rpi/code/tests/test_rpi_components.py                                  (extend existing user_response_script test class)

# Matrix + scenarios
integration/paper_eval/matrix_extensibility_v4_intent_coverage.json    (new)
integration/scenarios/extensibility_a_novel_event_code_living_room_needed_scenario_skeleton.json   (new)
# Optional: extensibility_a_off_intent_bedroom_scenario_skeleton.json + extensibility_a_safe_deferral_intent_scenario_skeleton.json
rpi/code/tests/test_paper_eval_sweep.py                                (v4 cell-shape tests)

# Aggregator
rpi/code/paper_eval/aggregator.py                                      (script-consistency helper + warnings field)
rpi/code/paper_eval/digest.py                                          (warnings column)
rpi/code/tests/test_paper_eval_aggregator.py                           (consistency check tests)

# Paper docs
common/docs/paper/05_class2_clarification_measurement_methodology.md   (add §7, renumber existing §7 → §8)

# Plan + handoff
common/docs/runtime/PLAN_2026-05-04_INTENT_AWARE_SIMULATOR_AND_COVERAGE.md   (this file)
common/docs/runtime/SESSION_HANDOFF.md                                 (index update at PR-merge time)
```

Approximate line count: 250-400 LOC additions across runner / aggregator / tests, plus the matrix JSON and scenario fixtures.

---

## 7. Backlog after this PR

Carried forward (in order of likely next-PR priority):

1. **Multi-turn refinement scripts** — needs `class2_multi_turn_enabled=true` policy flag handling in the runner. Refinement candidates use a different prompt structure (state-aware via `refinement_templates.py`). PR #155 candidate.
2. **Trial isolation bug** (sub-millisecond auto-selection from periodic context re-publish) — discovered in PR #148-#152 sweeps; not blocking but should be fixed before paper-grade hardware sweeps.
3. **Per-trial drill-down view** in dashboard — surface `observation_history` + drive-event timeline per trial for forensic analysis. From [PLAN_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md §7](PLAN_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md).
4. **Caregiver-phase Telegram response scripts** — extends the simulator into the post-CLASS_2 phase.
5. **Lever A schema extension** (`user_state.inferred_attention` / `recent_events`) — independent axis A v3 work.
6. **Hardware paper-grade verification** — separate work-stream per methodology §3, §5.

---

## 8. Cross-reference

| Document | Section | Relation |
|---|---|---|
| [05_class2_clarification_measurement_methodology.md](../paper/05_class2_clarification_measurement_methodology.md) | §6, new §7 | Methodology; new §7 is the coverage catalog this PR adds |
| [PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md](PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md) | §7 | Source of `_user_response_script` baseline (no_response / first_candidate_accept) |
| [PLAN_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md](PLAN_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md) | §3.1 | Source of `scenario.user_intent` shape; this PR consumes it |
| [SESSION_HANDOFF_2026-05-04_END_OF_SESSION_PR148_TO_152_MERGED.md](SESSION_HANDOFF_2026-05-04_END_OF_SESSION_PR148_TO_152_MERGED.md) | §3.1 | Predecessor handoff that scoped this PR |
| [02_safety_and_authority_boundaries.md](../architecture/02_safety_and_authority_boundaries.md) | Class 2 transition rules | Schema extension preserves boundary — `action_hint`/`target_hint` are guidance only |
| [04_class2_clarification.md](../architecture/04_class2_clarification.md) | scanning input model | Source of `class2_input_mode=scanning` semantics this PR exercises |
| [common/schemas/clarification_interaction_schema.json](../../schemas/clarification_interaction_schema.json) | candidate_choices item | Extended in this PR |
