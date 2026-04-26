# scenario_review_principles.md

## Purpose

This document contains the general review principles formerly kept in the monolithic `integration/scenarios/scenario_review_guide.md`.

Scenario JSON files are designed for loaders, runners, and comparators, but human reviewers should primarily ask:

- What does this scenario test?
- Why is it needed?
- What result is safe?
- What result is a red flag?
- What does it mean for disabled users, older adults, caregivers, and assistive-service contexts?

This document does not redefine canonical policy truth. Authoritative policy, schema, MQTT, and payload boundaries remain in `common/`.

---

## Current baseline

Scenario review must use the following current baseline.

```text
Active policy baseline:
common/policies/policy_table_v1_2_0_FROZEN.json

Low-risk action catalog:
common/policies/low_risk_actions_v1_1_0_FROZEN.json

Fault injection rules:
common/policies/fault_injection_rules_v1_4_0_FROZEN.json

Pure context schema:
common/schemas/context_schema_v1_0_0_FROZEN.json

Policy-router input schema:
common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json

Validator output schema:
common/schemas/validator_output_schema_v1_1_0_FROZEN.json

Class 2 notification schema:
common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json

Class 2 clarification interaction schema:
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json

Current MQTT topic registry:
common/mqtt/topic_registry_v1_1_0.json

MQTT topic payload contracts:
common/mqtt/topic_payload_contracts_v1_0_0.md

Representative Class 2 clarification interaction example:
common/payloads/examples/clarification_interaction_two_options_pending.json
```

Historical baselines:

```text
common/policies/policy_table_v1_1_2_FROZEN.json
common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json
common/mqtt/topic_registry_v1_0_0.json
```

Historical baselines must not be treated as current authority.

---

## User perspective

The target users include:

- people with severe physical disabilities or reduced motor function,
- users with speech or articulation limitations,
- older adults with reduced strength, vision, reaction speed, or cognition,
- caregivers and activity-support workers.

Therefore, reviewers should not read a scenario only as a technical input event. They should ask what bodily condition, home context, and safety risk the event represents.

---

## Core interpretation rules

- Scenarios are integration/evaluation assets, not canonical truth.
- Scenarios consume frozen policies, frozen schemas, current MQTT topic registry, and interface matrix.
- Scenarios must not redefine thresholds, required keys, trigger predicates, or allowed action scope.
- MQTT topics must stay under the `safe_deferral/...` namespace.
- Legacy `smarthome/...` topics must not be used in new or aligned scenarios.
- Class 0 emergency must not use the LLM as the primary decision path.
- Class 1 autonomous low-risk execution is currently limited to the frozen lighting catalog.
- Class 2 is a clarification / transition state, not terminal failure only.
- Class 2 clarification interaction evidence topic is `safe_deferral/clarification/interaction`.
- Class 2 LLM output may generate bounded candidate guidance, but has no final-decision, actuation-authorization, or emergency-trigger authority.
- Doorlock-sensitive requests must be interpreted as Class 2 clarification/escalation or governed manual confirmation, not autonomous Class 1 execution.
- `doorbell_detected` is required visitor-response context, but is not emergency evidence or autonomous unlock authorization.

---

## General review checklist

### Input and context

- Is this input realistic for the intended user population?
- Is the bounded input assumption too idealized?
- Does the sensor event represent a plausible household situation?
- Does the scenario consider constrained input environments?

### Expected outcome

- Does the scenario block unsafe autonomous actuation under ambiguity or incomplete state?
- Does it prefer safe fallback when needed?
- Does emergency input route immediately to emergency handling?
- Does Class 2 include candidate presentation, confirmation, timeout/no-response, and transition structure?

### Canonical baseline

- Does the scenario avoid redefining thresholds, required keys, or trigger semantics?
- Does it consume frozen policy/schema assets instead of replacing them?
- Does it avoid Class 1 actions outside `low_risk_actions_v1_1_0_FROZEN.json`?
- Does it avoid treating `doorbell_detected` as unlock authorization or emergency trigger?
- Does it avoid treating Class 2 interaction payload as pure context?

### MQTT / interface matrix

- Is the ingress topic in `common/mqtt/topic_registry_v1_1_0.json`?
- Does ordinary context use `safe_deferral/context/input`?
- Does emergency input use `safe_deferral/emergency/event` or an explicit controlled bridge?
- Does Class 2 clarification interaction evidence use `safe_deferral/clarification/interaction`?
- Does Class 2 notification use `safe_deferral/escalation/class2`?
- Does caregiver confirmation use `safe_deferral/caregiver/confirmation`?
- Does audit observation use `safe_deferral/audit/log`?

### Practical evaluation

- Can this scenario connect to a runner, comparator, or closed-loop verifier?
- Can it later connect to latency profiles?
- Are title, description, and notes clear enough for a developer?
- Does the scenario represent a realistic assistive or safety case rather than only a synthetic technical event?
