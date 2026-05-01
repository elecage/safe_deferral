# Session Handoff — 2026-05-01 CLASS_2 9-Issue Batch Complete

## Status

PR #78 open (ready to merge): 9-issue batch covering CLASS_2 dispatch correctness,
post-transition evidence tracking, and experiment runner automation.

All tests pass: **423 mac_mini + 109 RPi = 532 total**.

---

## What was fixed (9 issues across two commit batches)

### First batch (5 issues)

1. **C1_LIGHTING_ASSISTANCE dispatch never fired**: `target_hint` was `None` →
   `is_class1_ready=False` → CLASS_2→CLASS_1 transition silently skipped dispatch.
   Fixed by adding `"target_hint": "living_room_light"` to `C1_LIGHTING_ASSISTANCE`
   in both `insufficient_context` and `missing_policy_input` candidate tables.
   Also added `"action_hint"` to `OPT_LIVING_ROOM` and `OPT_BEDROOM` in
   `unresolved_context_conflict`.

2. **Post-transition validator evidence not tracked**: `Class2Telemetry` now has
   `post_transition_validator_status` and `post_transition_dispatched`. All CLASS_1
   transition outcomes (approved, not-approved, not-ready) call
   `publish_class2_transition_result()` so the runner can verify evidence.

3. **`_normalize_expected_transition_target()` false failures**: `CAREGIVER_CONFIRMATION`
   was being mapped to `None` (it contains `_OR_` substring check). Fixed by
   introducing `_CANONICAL_TRANSITION_TARGETS` set checked before the `_OR_` test.
   Compound `_OR_` non-canonical values → `None` (open/unset pass).

4. **`04_class2_clarification.md` §6 wrong**: Removed "Policy Router re-entry occurs"
   language; updated to reflect direct bounded-candidate execution path.

5. **Paper docs missing doorbell distinction**: Updated user story docs to clarify
   `doorbell_detected` belongs in `trigger_event` (not `env_context`) when doorbell
   is the trigger.

### Second batch (4 issues)

6. **`_is_pass()` used expected_target not observed_target** (Issue A): The
   `post_transition_validator_status` and `post_transition_escalation_status` guards
   now gate on `observed_target` (from telemetry) not `trial.expected_transition_target`.
   Prevents open/compound expected scenarios from masking a failed post-transition check.

7. **PackageRunner never drove selection step** (Issue B): `_run_trial()` now checks
   `trial.auto_simulate_input`; if set, calls `_wait_for_class2_phase1_ready()` (polls
   until initial CLASS_2 snapshot arrives) then `_simulate_class2_input(event_code)`.
   `"single_click"` → CLASS_1 candidate; `"triple_hit"` → CLASS_0 candidate.
   `_simulate_class2_button()` kept as legacy alias.

8. **CLASS_0 path had no post-transition observation** (Issue C): `Class2Telemetry`
   gets `post_transition_escalation_status` field. `_execute_class2_transition()` CLASS_0
   path now calls `publish_class2_transition_result(post_transition_escalation_status=...)`
   after `send_notification()`, matching the CLASS_1 path for runner verification.

9. **Scenario step text still said "Policy Router re-entry"** (Issue D): Both
   `class2_to_class1` and `class2_to_class0` skeleton JSONs corrected. Added:
   - `requires_policy_router_reentry: false`
   - `auto_simulate_input: "single_click"` / `"triple_hit"`
   - `requires_escalation_evidence_when_class0: true/false`
   The two non-selection CLASS_2 skeletons also received `auto_simulate_input: null`
   and `requires_escalation_evidence_when_class0: false`.

---

## Key data model changes

```python
# telemetry_adapter/models.py — Class2Telemetry
post_transition_validator_status: Optional[str] = None   # was added in first batch
post_transition_dispatched: Optional[bool] = None        # was added in first batch
post_transition_escalation_status: Optional[str] = None  # added in second batch

# trial_store.py — TrialResult
expected_transition_target: Optional[str] = None
requires_validator_when_class1: Optional[bool] = None
requires_escalation_evidence_when_class0: Optional[bool] = None  # second batch
auto_simulate_input: Optional[str] = None                         # second batch
```

---

## Test counts

| Suite | Count |
|---|---|
| mac_mini unit tests | 423 |
| RPi unit tests | 109 |
| **Total** | **532** |

`TestPublishClass2TransitionResultClass0` was inadvertently placed in the RPi test
file (which lacks mac_mini module access). Removed from RPi, added correctly to
`mac_mini/code/tests/test_pipeline_ack_escalation.py`.

---

## Next steps

- Merge PR #78 once reviewed
- Run a live CLASS_2 experiment with `class2_to_class1` scenario to validate
  auto-simulate end-to-end
- Run `class2_to_class0` scenario to validate CLASS_0 escalation evidence path
