# SESSION_HANDOFF_2026-04-25_DOORBELL_VISITOR_CONTEXT_UPDATE.md

## Purpose

This handoff records the doorbell / visitor-response context alignment update completed after the policy/schema and documentation alignment passes.

This update was triggered by a design review finding:

> Doorlock-sensitive scenarios cannot be interpreted correctly without knowing whether a recent doorbell or visitor-arrival event occurred.

The system must therefore represent doorbell/visitor context explicitly while preserving the existing safety boundary:

- `doorbell_detected` helps interpret visitor-response intent.
- `doorbell_detected` does **not** authorize autonomous doorlock control.
- Doorlock remains a sensitive actuation domain outside the current Class 1 autonomous low-risk executable path.

Read together with:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_ALIGNMENT_UPDATE.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_DOC_ALIGNMENT_UPDATE.md`
- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`
- `common/docs/required_experiments.md`

---

## 1. Current interpretation

### 1.1 Doorbell context

`doorbell_detected` is now the official visitor-response context signal in the normalized context envelope.

Interpretation:

- `doorbell_detected=true` means a recent doorbell or visitor-arrival event has been detected.
- `doorbell_detected=false` means no such recent visitor-response signal is available.
- This field may affect intent interpretation, explanation, and routing rationale in visitor-response scenarios.
- This field does not authorize autonomous door unlock.

### 1.2 Doorlock-sensitive actuation

Doorlock remains a representative sensitive actuation case.

Current rules:

- Doorlock may exist as an implementation-facing representative interface.
- Doorlock may be used for sensitive-actuation evaluation.
- Doorlock must not be added to the current Class 1 autonomous low-risk action catalog.
- Doorlock must not be emitted as a `candidate_action_schema` autonomous action.
- Doorlock must not be approved as `validator_output_schema.executable_payload`.
- Doorlock-related sensitive outcomes must route to Class 2 escalation or a separately governed manual confirmation path.

### 1.3 Doorlock state boundary

Doorlock state is not currently part of `context_schema.device_states`.

This does **not** mean doorlock is out of scope. It means the current pure-context device-state contract does not carry doorlock state as a normal Class 1 context field.

If experiments need doorlock state, approval state, or ACK state, represent them through one of the following until a future schema revision explicitly adds them:

- experiment annotation,
- mock approval state,
- dashboard-side observation field,
- audit artifact,
- manual confirmation path internal state,
- future schema revision.

Do not insert `doorlock` into `pure_context_payload.device_states` under the current frozen schema.

---

## 2. Files updated

### 2.1 `context_schema_v1_0_0_FROZEN.json`

File:

- `common/schemas/context_schema_v1_0_0_FROZEN.json`

Commit:

- `548fae38708b7f1d7816d1337776b9a96637b29d`

Changes:

- Added `environmental_context.doorbell_detected` as a required boolean field.
- Added `doorbell_detected` to `environmental_context.required`.
- Added `doorbell_detected` to the `sensor` event-code enum under `trigger_event` conditional validation.

Current meaning:

```json
"doorbell_detected": {
  "type": "boolean",
  "description": "True if a recent doorbell or visitor-arrival event has been detected. This is policy-relevant context for visitor-response interpretation and does not authorize autonomous doorlock control."
}
```

Implementation implication:

- All valid context payloads must include `doorbell_detected`.
- Default value for non-visitor scenarios should normally be `false`.
- Visitor-response scenarios may set it to `true`.

---

### 2.2 `policy_table_v1_1_2_FROZEN.json`

File:

- `common/policies/policy_table_v1_1_2_FROZEN.json`

Commit:

- `5bc3322eda499f8e0190e8e3e6fb789e7893d1a5`

Change:

Added `doorbell_context_note`:

```json
"doorbell_context_note": "Doorbell or visitor-arrival detection may be used as policy-relevant context for visitor-response interpretation, but it does not authorize autonomous doorlock control. Doorlock-related sensitive actuation must remain routed to Class 2 escalation or a separately governed manual confirmation path."
```

---

### 2.3 `required_experiments.md`

File:

- `common/docs/required_experiments.md`

Commit:

- `0d129b819d215be34f190f7d7c850b911acbc755`

Changes:

- Added missing frozen/companion asset references:
  - `low_risk_actions_v1_1_0_FROZEN.json`
  - `output_profile_v1_1_0.json`
- Added `doorbell_detected` as visitor-response context signal.
- Clarified that `doorbell_detected` is not doorlock authorization.
- Removed/avoided wording that would imply doorlock state belongs inside `device_states`.
- Clarified that notify / caregiver call / unlock intent are intended interpretation labels or Class 2/manual-confirmation routing labels, not autonomous candidate actions.
- Added doorbell-context-aware doorlock-sensitive validation items.
- Added `exception_trigger_id` to recommended Class 2 payload completeness fields.

---

### 2.4 `policy_router.models`

File:

- `mac_mini/code/policy_router/models.py`

Commit:

- `acaf48aef81f5e24bc896258feb86a0742345faa`

Change:

Added `doorbell_detected` to the Pydantic `EnvironmentalContext` model.

Current field:

```python
doorbell_detected: bool = Field(
    ...,
    description=(
        "방문자/도어벨 상황 해석을 위한 context signal. "
        "doorlock 자동 개방 권한을 의미하지 않는다."
    ),
)
```

Implementation implication:

- Mac mini runtime input model now matches the updated context schema.
- Missing `doorbell_detected` will be invalid at the strict model layer unless an adapter fills it before model construction.

---

### 2.5 `integration_adapter.py`

File:

- `integration/tests/integration_adapter.py`

Commit:

- `f26885086a3d93751b7bfc2d635b47a8f9fb95e9`

Change:

Added lenient fixture normalization for missing `doorbell_detected`:

```python
doorbell_detected=bool(ec_raw.get("doorbell_detected", False)),
```

Meaning:

- Existing fixtures that do not include `doorbell_detected` will default to `false`.
- Visitor-response fixtures should explicitly set `doorbell_detected=true` where needed.
- This adapter fallback does not authorize doorlock control.

---

### 2.6 `50_configure_fault_profiles_rpi.sh`

File:

- `rpi/scripts/configure/50_configure_fault_profiles_rpi.sh`

Commit:

- `99ee4cd51c579eea1cdbe3e3b30ea843f782a8c8`

Change:

Added validation that `fault_injection_rules_v1_4_0_FROZEN.json` dynamic references match the expected policy/schema JSONPath contract.

Verified contract:

```text
freshness_limit == $.global_constraints.freshness_threshold_ms
required_environmental_keys == $.properties.environmental_context.required
required_device_keys == $.properties.device_states.required
```

Why this matters:

- `doorbell_detected` is now part of `environmental_context.required`.
- Missing-context fault generation should dynamically follow the context schema required list.
- This prevents recurrence of earlier dynamic reference JSONPath drift.

---

### 2.7 Doorlock architecture document

File:

- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`

Commit:

- `78f0a5a6c0b27d5a609190a92ffe43836764f131`

Changes:

- Added `doorbell_detected` as official visitor-response context signal.
- Clarified that `doorbell_detected=true` does not authorize autonomous doorlock control.
- Clarified that doorlock state is not currently part of `context_schema.device_states`.
- Clarified that doorlock state, approval state, and ACK state should be represented outside current pure-context `device_states` unless a future schema revision adds them.
- Clarified that caregiver-approved doorlock dispatch belongs to a separately governed manual confirmation path outside the Class 1 validator executable payload.
- Added doorbell-context-aware interpretation as an experiment implication.

---

### 2.8 Prompt documents

Files:

- `common/docs/architecture/12_prompts_core_system.md`
- `common/docs/architecture/12_prompts_nodes_and_evaluation.md`

Commits:

- `1a5d55d61f90ee607f7327d6a53ca4b7eaecde92`
- `4dc9e1d6c006a2ebe82be0f6ea480c20c62f90f5`

Changes:

`12_prompts_core_system.md`:

- Updated repository separation:
  - `mac_mini/` = safety-critical operational edge hub.
  - `rpi/` = experiment dashboard, simulation, fault injection, orchestration, replay, and closed-loop evaluation support.
- Updated Prompt 7 so virtual sensor nodes publish `doorbell_detected` as `environmental_context.doorbell_detected`.
- Stated that `doorbell_detected` must not be interpreted as autonomous doorlock authorization.

`12_prompts_nodes_and_evaluation.md`:

- Added `doorbell_detected` to environmental sensing and visitor-response evaluation prompts.
- Updated visitor-response scenario guidance to use `environmental_context.doorbell_detected`.
- Updated dashboard prompt to make Raspberry Pi 5 the experiment dashboard host.
- Updated test-app prompt to distinguish developer/debug support from the RPi-hosted dashboard.
- Updated orchestration prompt to make Raspberry Pi 5 the natural host for scenario execution, simulation, replay, fault injection, progress publication, and result artifact generation.
- Repeated that `doorbell_detected` must not authorize autonomous doorlock control.

---

## 3. Implementation instructions for Claude Code or future coding agents

### 3.1 Context payloads

Every context payload must include:

```json
"doorbell_detected": false
```

inside:

```json
"pure_context_payload": {
  "environmental_context": {
    ...
  }
}
```

Use `true` only for visitor-response scenarios with a recent doorbell or visitor-arrival event.

### 3.2 Scenario fixtures

When generating fixtures under future implementation areas such as:

- `integration/scenarios/`
- `integration/tests/data/`
- `rpi/**/fixtures`
- `rpi/**/simulation`
- `mac_mini/**/tests`

include `environmental_context.doorbell_detected` in every valid context fixture.

Default for non-visitor scenarios:

```json
"doorbell_detected": false
```

Visitor-response examples:

```json
"doorbell_detected": true
```

### 3.3 Do not put doorlock state in current `device_states`

Current valid `device_states` are:

- `living_room_light`
- `bedroom_light`
- `living_room_blind`
- `tv_main`

Do not add:

```json
"doorlock": "locked"
```

or similar fields to `pure_context_payload.device_states` unless a future schema revision explicitly adds them.

### 3.4 Doorlock execution boundary

Do not generate:

- `door_unlock` as a Class 1 candidate action,
- `front_door_lock` as a Class 1 target device,
- doorlock fields in `validator_output_schema.executable_payload`,
- unrestricted dashboard/test-app door unlock controls,
- direct door unlock dispatch that bypasses caregiver approval and audit.

Doorlock-sensitive execution, if implemented, must use:

- Class 2 escalation,
- separately governed manual confirmation path,
- explicit caregiver approval,
- ACK verification,
- local audit logging.

---

## 4. Current status of fixture review

### Checked

The visible contents of these locations were checked:

- `integration/tests/data/`
- `integration/scenarios/`

Observed state at review time:

- `integration/tests/data/` contained only `README.md`.
- `integration/scenarios/` contained only `.gitkeep`.

No concrete JSON fixture files were found there to update.

### Mitigation applied

`integration/tests/integration_adapter.py` now defaults missing `doorbell_detected` to `false`, reducing breakage risk for legacy or future loose fixtures.

### Deferred to implementation phase

The following are implementation areas and should be handled by Claude Code or future coding agents:

- `mac_mini/**/tests`
- `rpi/**/fixtures`
- `rpi/**/simulation`
- dashboard/app implementation

These areas must follow the instructions in Section 3.

---

## 5. Remaining recommended work

### 5.1 Runtime/test implementation

Future implementation should add or update tests for:

- missing `doorbell_detected` rejected by strict schema/model,
- adapter normalization fills missing `doorbell_detected=false`,
- visitor-response scenario with `doorbell_detected=true`,
- visitor-response scenario with `doorbell_detected=false`,
- doorlock state rejected if inserted into `device_states`,
- doorlock unlock rejected as Class 1 candidate/executable payload,
- sensitive doorlock path escalates or uses governed manual confirmation.

### 5.2 Scenario packs

Future scenario generation should include at least:

1. Non-visitor baseline:
   - `doorbell_detected=false`
   - no doorlock-sensitive interpretation
2. Visitor-response, notify-only:
   - `doorbell_detected=true`
   - intended interpretation label: notify/call caregiver
3. Visitor-response, possible unlock intent:
   - `doorbell_detected=true`
   - expected outcome: Class 2 escalation or manual confirmation path, not autonomous unlock
4. Suspicious unlock request:
   - `doorbell_detected=false`
   - expected outcome: conservative escalation or safe blocking
5. Missing doorbell context fault:
   - omit `doorbell_detected`
   - expected outcome: missing-context handling / Class 2 in strict paths

### 5.3 Handoff consolidation

This addendum should be referenced during future master handoff consolidation.

The master `SESSION_HANDOFF.md` may still contain older wording and should not override this addendum for:

- `doorbell_detected`,
- visitor-response interpretation,
- doorlock state boundary,
- RPi dashboard placement,
- sensitive actuation routing.

---

## 6. Non-negotiable summary

1. `doorbell_detected` is required context.
2. `doorbell_detected` belongs in `environmental_context`.
3. `doorbell_detected` is not doorlock authorization.
4. Doorlock state is not in current `device_states`.
5. Doorlock is implementation-facing and experiment-facing, but not current Class 1 autonomous low-risk execution.
6. Doorlock-sensitive actions must route to Class 2 escalation or a separately governed manual confirmation path.
7. RPi hosts experiment dashboard/orchestration; Mac mini remains the safety-critical operational edge hub.
