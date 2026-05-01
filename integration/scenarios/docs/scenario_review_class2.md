# scenario_review_class2.md

## Purpose

This document contains review guidance for Class 2 clarification / transition scenarios.

It replaces the Class 2 portions of the former monolithic `integration/scenarios/scenario_review_guide.md` and aligns them with:

```text
safe_deferral/clarification/interaction
common/schemas/clarification_interaction_schema.json
common/payloads/examples/clarification_interaction_two_options_pending.json
```

---

## Core interpretation

Current interpretation:

```text
Class 2 = clarification / transition state
```

Class 2 is not terminal failure only and not caregiver escalation only.

Allowed high-level flow:

```text
ambiguous or insufficient input
→ bounded candidate choices
→ TTS/display/caregiver prompt
→ user/caregiver selection, timeout/no-response, or deterministic evidence
→ Deterministic Validator re-entry with confirmed bounded candidate (Class 1 only)
  | emergency announcement and caregiver notification (Class 0)
  | safe deferral / caregiver confirmation (timeout, no-response, or ambiguous)
→ CLASS_1 / CLASS_0 / SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
```

---

## Dedicated interaction topic

When Class 2 clarification interaction artifacts are published over MQTT, use:

```text
safe_deferral/clarification/interaction
```

Contract:

```text
payload_family: clarification_interaction_payload
schema: common/schemas/clarification_interaction_schema.json
example_payload: common/payloads/examples/clarification_interaction_two_options_pending.json
authority_level: class2_interaction_evidence_not_authority
```

This topic may carry:

- candidate choices,
- presentation channel,
- user/caregiver selection result,
- timeout/no-response result,
- transition target,
- final safe outcome evidence.

It must not be interpreted as:

- validator approval,
- actuation command,
- emergency trigger authority,
- doorlock authorization.

---

## `class2_insufficient_context_scenario_skeleton.json`

### Purpose

This scenario checks the representative Class 2 insufficient-context clarification / transition path.

### Real-life context

The user clearly needs help, but current information is not enough to infer a safe action.

Examples:

- a user presses a button but the target device is unclear,
- lighting assistance, caregiver call, and emergency help are all plausible,
- environmental and device state are too sparse to infer intent safely,
- the user cannot provide a rich spoken explanation.

The system must not act on a guess. It should present bounded candidates and wait for confirmation or evidence.

### Expected safe result

- Enter `CLASS_2` clarification state.
- Generate bounded candidate choices where appropriate.
- Do not execute before user/caregiver confirmation.
- Record clarification evidence through `safe_deferral/clarification/interaction` when published.
- Transition only after the runtime re-validates the confirmed bounded candidate (Class 1) or after explicit emergency confirmation/evidence (Class 0); the Policy Router is not re-invoked.
- Possible outcomes: `CLASS_1`, `CLASS_0`, `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION`.

---

## Required `class2_clarification_expectation`

Class 2 transition scenarios should include a block like this:

```json
"class2_clarification_expectation": {
  "enabled": true,
  "clarification_topic": "safe_deferral/clarification/interaction",
  "clarification_schema_ref": "common/schemas/clarification_interaction_schema.json",
  "example_payload_ref": "common/payloads/examples/clarification_interaction_two_options_pending.json",
  "expected_transition_target": "CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
  "requires_validator_reentry_when_class1": true,
  "requires_validator_when_class1": true,
  "timeout_must_not_infer_intent": true,
  "clarification_payload_is_not_authorization": true,
  "forbidden_interpretations": [
    "validator_approval",
    "actuation_command",
    "emergency_trigger_authority",
    "doorlock_authorization"
  ]
}
```

This block is scenario expectation evidence only. It does not authorize execution.

---

## Review checklist

Class 2-related scenarios must answer yes to the following:

```text
- Class 2 is not represented as terminal failure only.
- clarification_interaction is present where Class 2 interaction is modeled.
- class2_clarification_expectation is present for Class 2 transition tests.
- clarification_topic is safe_deferral/clarification/interaction.
- clarification_schema_ref is common/schemas/clarification_interaction_schema.json.
- example_payload_ref is common/payloads/examples/clarification_interaction_two_options_pending.json.
- candidate choices are bounded and at most 4.
- candidate generation boundary forbids final decision and actuation authority.
- confirmation_required_before_transition is true.
- requires_validator_reentry_when_class1 is true.
- requires_validator_when_class1 is true.
- timeout_must_not_infer_intent is true.
- clarification_payload_is_not_authorization is true.
- forbidden_interpretations include validator_approval, actuation_command, emergency_trigger_authority, and doorlock_authorization.
- Class 1 transition requires low-risk catalog membership and Deterministic Validator approval.
- Class 0 transition requires explicit emergency confirmation or deterministic E001~E005 evidence.
- Timeout/no-response routes to Safe Deferral or Caregiver Confirmation.
- Candidate, selection, timeout, and transition evidence are audit-visible.
```

---

## Minimum additional Class 2 scenarios

The following skeletons should be added to cover the current architecture:

```text
class2_to_class1_low_risk_confirmation_scenario_skeleton.json
class2_to_class0_emergency_confirmation_scenario_skeleton.json
class2_timeout_no_response_safe_deferral_scenario_skeleton.json
class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json
```

### Class 2 → Class 1

Purpose:

```text
User/caregiver selects a low-risk lighting candidate.
Runtime re-enters the Deterministic Validator with the confirmed bounded candidate.
Deterministic Validator approves exactly one low-risk lighting action.
```

Must verify:

```text
candidate text alone does not authorize actuation
selection re-enters the Deterministic Validator with the bounded candidate (no Policy Router re-routing)
Class 1 requires validator approval
low-risk catalog is not expanded
```

### Class 2 → Class 0

Purpose:

```text
User/caregiver confirms emergency help, or deterministic E001~E005 evidence arrives during clarification.
Runtime announces the emergency and dispatches a caregiver notification directly; transition to Class 0 occurs without Policy Router re-routing.
```

Must verify:

```text
LLM candidate text alone is not emergency trigger
Class 0 transition requires emergency confirmation or deterministic evidence
```

### Class 2 timeout/no-response

Purpose:

```text
Class 2 candidate presentation times out or receives no response.
The system must not infer user intent.
Safe Deferral or Caregiver Confirmation is required.
```

Must verify:

```text
timeout/no-response does not infer user intent
no autonomous actuation
timeout result is audit-visible
```

### Class 2 caregiver confirmation / doorlock-sensitive

Purpose:

```text
Doorlock-sensitive or visitor-response-sensitive request enters Class 2/caregiver confirmation.
No autonomous Class 1 unlock is allowed.
Manual confirmation path, ACK, and audit are required.
```

Must verify:

```text
doorbell_detected is not unlock authorization
doorlock is not Class 1 low-risk action
caregiver confirmation is not validator approval
ACK and audit are required for governed manual path
```
