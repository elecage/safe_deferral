# Class 2 Clarification

## 1. Purpose

This document defines the active Class 2 clarification and transition
architecture.

## 2. Class 2 Meaning

Class 2 is not a terminal failure by default. It is a controlled state for
ambiguous, insufficient, sensitive, stale, conflicting, or transition-oriented
conditions.

Class 2 may end in:

- transition to Class 1 after valid low-risk clarification and validator approval,
- transition to Class 0 after valid emergency evidence,
- safe deferral,
- caregiver escalation,
- caregiver-mediated manual confirmation where a sensitive path is explicitly governed.

## 3. Clarification Manager Role

The Class 2 Clarification Manager coordinates:

- entry into clarification,
- bounded candidate presentation,
- user or caregiver selection evidence,
- timeout/no-response handling,
- transition target recording,
- audit evidence,
- Policy Router re-entry when appropriate.

It does not approve execution directly.

## 4. LLM Role In Class 2

The LLM may generate bounded candidate choices and user-facing guidance. The LLM
must not:

- choose a final route by itself,
- authorize execution,
- invent emergency evidence,
- bypass caregiver confirmation,
- bypass validator approval.

## 5. Clarification Interaction Payload

Clarification interaction state is not pure context and not actuation authority.

Use:

```text
schema: common/schemas/clarification_interaction_schema.json
topic: safe_deferral/clarification/interaction
payload_family: clarification_interaction_payload
```

This topic is **publish-only evidence**. The runtime publishes interaction
snapshots here for audit and experiment observation. It does not subscribe to
this topic to receive CLASS_2 selections — user selections arrive via
`safe_deferral/context/input` (button press) and caregiver selections arrive
via the Telegram callback path.

This payload may record:

- candidate choices,
- presentation channel,
- selected choice,
- timeout/no-response result,
- transition target,
- final safe outcome.

## 6. Transition To Class 1

A Class 2 case may transition to Class 1 only when:

1. clarification provides bounded low-risk intent evidence,
2. the target action remains inside `low_risk_actions.json`,
3. Policy Router re-entry occurs,
4. Deterministic Validator approves the exact admissible action,
5. dispatch remains limited to the approved low-risk action.

Clarification selection is not validator approval.

## 7. Transition To Class 0

A Class 2 case may transition to Class 0 only when valid emergency evidence is
available, such as policy-aligned emergency sensor input, emergency input, or
explicit confirmation accepted by the current policy path.

LLM text alone must not trigger Class 0.

## 8. Timeout Or No Response

Timeout, no response, or ambiguous response must not be treated as consent.

The safe outcomes are:

- safe deferral,
- caregiver notification,
- caregiver confirmation request,
- user-facing explanation,
- audit record.

## 9. Sensitive Paths

Doorlock-sensitive requests remain outside autonomous Class 1 execution. Class 2
may clarify user intent, but unlock-related outcomes must route to caregiver
escalation or another separately governed manual confirmation path.

## 10. Scenario Alignment

Class 2 scenario contracts should include explicit expectations for:

- clarification topic,
- clarification schema reference,
- candidate choices,
- transition target,
- timeout/no-response behavior,
- final safe outcome,
- audit expectation.

## 11. Source Notes

This active summary consolidates the stable material from:

- `common/docs/archive/architecture_legacy/19_class2_clarification_architecture_alignment.md`
- `common/docs/archive/architecture_legacy/20_scenario_data_flow_matrix.md`
- `common/docs/archive/architecture_legacy/12_prompts_core_system.md`
- `common/docs/archive/architecture_legacy/12_prompts_mqtt_payload_governance.md`
- `integration/scenarios/`
