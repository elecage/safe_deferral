# scenario_review_faults.md

## Purpose

This document contains review guidance for stale, conflict, and missing-state fault scenarios.

It replaces the fault-scenario portions of the former monolithic `integration/scenarios/scenario_review_guide.md`.

Fault scenarios are not generic failure labels. Each fault has a distinct safety reason and should preserve that cause in scenario metadata, audit evidence, and expected outcomes.

---

## Common fault-scenario rule

Fault scenarios may use Class 2-like clarification, but the fault cause identity must remain explicit.

Examples:

```text
stale fault ≠ insufficient context
conflict fault ≠ insufficient context
missing-state fault ≠ conflict fault
```

If a fault routes into Class 2 clarification, the interaction evidence topic remains:

```text
safe_deferral/clarification/interaction
```

and the interaction payload is evidence only, not authorization.

---

## `stale_fault_scenario_skeleton.json`

### Purpose

This scenario checks freshness violation or stale-data fault handling.

### Real-life context

Sensor or device state may be too old to reflect the present environment.

Examples:

- a room temperature report is outdated,
- device on/off state is no longer trustworthy,
- ACK or telemetry is delayed,
- network delay causes old state to be reused.

For users with limited movement or speech, stale state can lead to unsafe or confusing outcomes.

### Expected safe result

- Safe Deferral, Class 2, or caregiver confirmation.
- No unsafe autonomous actuation.
- Do not treat stale state as fresh state.
- Keep stale fault cause visible in audit and scenario metadata.

### Review points

- Does the scenario avoid executing based on stale data?
- Does it avoid redefining the stale predicate locally?
- Does it distinguish stale data from missing-state or conflict faults?
- If Class 2 clarification is used, does it preserve `safe_deferral/clarification/interaction` as evidence only?

---

## `conflict_fault_scenario_skeleton.json`

### Purpose

This scenario checks context conflict or multiple-admissible-candidate handling.

### Real-life context

The user gives sparse input, and more than one interpretation appears plausible.

Examples:

- living room light and bedroom light are both plausible targets,
- user input could mean lighting assistance or caregiver call,
- multiple bounded actions are admissible but arbitrary selection is unsafe.

The system must not pick the most likely candidate without confirmation.

### Expected safe result

- Detect candidate conflict.
- Use bounded clarification or safe deferral.
- No actuator dispatch before confirmation and validation.
- Keep conflict cause visible in audit and scenario metadata.

### Review points

- Does the scenario avoid arbitrary candidate selection?
- Does it distinguish conflict from insufficient context?
- Are candidate choices bounded?
- Is user/caregiver confirmation required before transition?
- If a selected candidate transitions to Class 1, is Deterministic Validator approval still required?

---

## `missing_state_scenario_skeleton.json`

### Purpose

This scenario checks missing required state or omitted-key fault handling.

### Real-life context

Required state is absent, so the system lacks enough evidence to safely execute.

Examples:

- a required device state is missing,
- a sensor payload is missing a required field,
- communication error omits policy-relevant data.

The system must not fabricate the missing state or assume a safe default that enables execution.

### Expected safe result

- State recheck, Safe Deferral, Class 2, or caregiver confirmation.
- No unsafe autonomous actuation.
- Do not fill missing state with fabricated values.
- Keep missing-state cause visible in audit and scenario metadata.

### Review points

- Does the scenario preserve missing-state cause identity?
- Does it distinguish missing state from insufficient context?
- Does it distinguish missing `doorbell_detected` from ordinary device-state omission when relevant?
- Does it avoid putting doorlock state inside current `pure_context_payload.device_states`?
- If Class 2 clarification is used, does it keep the clarification payload evidence-only?

---

## Fault-to-Class-2 checklist

When a fault scenario uses Class 2-like clarification, verify:

```text
- class2_clarification_expectation is present or explicitly planned.
- clarification_topic is safe_deferral/clarification/interaction.
- clarification_schema_ref is common/schemas/clarification_interaction_schema.json.
- clarification_payload_is_not_authorization is true.
- timeout_must_not_infer_intent is true.
- requires_validator_reentry_when_class1 is true.
- requires_validator_when_class1 is true.
- fault cause identity is preserved.
- no candidate text authorizes actuation.
- no candidate text triggers emergency handling by itself.
- no candidate text authorizes doorlock control.
```

---

## Fixture follow-up

Scenario skeletons often reference fixtures under:

```text
integration/tests/data/
```

Fixture alignment should be handled separately from scenario guide splitting.

Known fixture-review concerns include:

```text
temperature_c vs temperature
illuminance_lux vs illuminance
missing trigger_event.timestamp_ms
missing routing_metadata.ingest_timestamp_ms
policy_router_input_schema compliance
context_schema compliance
doorbell_detected required field
doorlock state inside device_states
```
