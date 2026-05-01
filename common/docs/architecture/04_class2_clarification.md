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
- Deterministic Validator re-entry on the confirmed bounded candidate when the
  selected transition is Class 1.

It does not approve execution directly.

## 4. LLM Role In Class 2

The LLM may generate bounded candidate choices and user-facing guidance. The LLM
must not:

- choose a final route by itself,
- authorize execution,
- invent emergency evidence,
- bypass caregiver confirmation,
- bypass validator approval.

### 4.1 Bounded-Variability Constraints

LLM-generated candidate prompts (`prompt` field on each
`ClarificationChoice`) are subject to **bounded-variability constraints**
loaded at startup from
`policy_table.json::global_constraints.class2_conversational_prompt_constraints`.

The LLM-internal candidate set (the value `LocalLlmAdapter.generate_class2_candidates()`
returns to `Class2ClarificationManager`) is governed by
`common/schemas/class2_candidate_set_schema.json`. That schema defines the
in-process payload shape — it is **never published to any MQTT topic**.
The on-the-wire artifact is the clarification record governed by
`common/schemas/clarification_interaction_schema.json` (see §4.3).

The LocalLlmAdapter call is also bounded by a request timeout sourced from
`policy_table.global_constraints.llm_request_timeout_ms` (default 8 s) so
the MQTT message-handler thread cannot block on a slow / hung Ollama. The
manager wraps the call in a daemon thread with a join budget of
`llm_request_timeout_ms / 1000 + 0.5 s`; if the budget elapses, the manager
abandons the in-flight LLM call and uses the static fallback table.
See `10_llm_class2_integration_alignment_plan.md` P0.1 / P0.2 for rationale.
The currently shipped values:

| Constraint | Value | Purpose |
|---|---|---|
| `max_prompt_length_chars` | `80` | Cognitive-load cap so users with attention / cognitive limits are not overwhelmed |
| `prompt_must_be_question` | `true` | Interrogative form makes it explicit that a choice is expected |
| `vocabulary_tier` | `plain_korean` | Restrict to plain spoken Korean — no jargon |
| `must_include_target_action_in_prompt` | `false` | Reserved for future tightening |
| `forbidden_phrasings` | doorlock-related and emergency-dispatch-related tokens | Block phrasings that imply autonomous emergency or doorlock authority |

`max_candidate_count` for the LLM path comes from the existing
`class2_max_candidate_options` field in the same `global_constraints` block
(currently `4`); the manager and the adapter share that single source of
truth so they cannot drift.

`LocalLlmAdapter._normalize_class2_candidate()` enforces every constraint.
Any candidate that violates a constraint is dropped; if all candidates are
rejected the adapter returns a `default_fallback` result and the manager
uses its static `_DEFAULT_CANDIDATES` table (see §4.3 below). Operations
may tighten the constraints by editing `policy_table.json` without
touching code.

### 4.2 Catalog gating

CLASS_1 candidates with `action_hint` / `target_hint` outside
`common/policies/low_risk_actions.json` are dropped by the adapter before
the manager ever sees them. This means the LLM may *suggest* anything the
context warrants, but only candidates whose `action_hint`+`target_hint` are
admissible by the canonical low-risk catalog can ever reach the user. The
catalog is grown by humans through governance, not by the LLM choosing to
expand its own authority.

CLASS_0 candidates from the LLM are always normalized to a fixed safe
template (`candidate_id="C3_EMERGENCY_HELP"`, prompt `"긴급상황인가요?"`)
so the LLM cannot invent emergency rationales. The LLM may decide *whether*
to include an emergency option, never *what* it says.

### 4.3 Provenance audit (`candidate_source`)

The `clarification_interaction_schema.json` includes an optional
`candidate_source` enum field with two values:

- `llm_generated` — the candidate set was produced by
  `LocalLlmAdapter.generate_class2_candidates()` and accepted under all
  bounded-variability constraints.
- `default_fallback` — the static `_DEFAULT_CANDIDATES` table was used,
  either because no LLM generator was registered, or no
  `pure_context_payload` was supplied (timeout-driven escalations like
  C205 do not carry one), or the LLM output was rejected.

Audit reviewers can use this field to distinguish LLM-driven sessions from
fallback ones when reading clarification records. The two paths are
behaviourally equivalent for the user (both produce bounded candidates the
manager can present); the distinction matters only for evaluation and for
debugging LLM regressions.

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
3. the runtime re-enters the Deterministic Validator with the confirmed
   bounded candidate (the selection is not a Policy Router re-routing event;
   it is a confirmed candidate that still must clear the validator),
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
