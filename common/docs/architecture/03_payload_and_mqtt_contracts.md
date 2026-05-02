# Payload And MQTT Contracts

## 1. Purpose

This document summarizes the active payload and MQTT contract architecture.

## 2. Canonical References

Policy assets:

- `common/policies/policy_table.json`
- `common/policies/low_risk_actions.json`
- `common/policies/fault_injection_rules.json`
- `common/policies/output_profile.json`

Schema assets:

- `common/schemas/policy_router_input_schema.json`
- `common/schemas/context_schema.json`
- `common/schemas/candidate_action_schema.json`
- `common/schemas/validator_output_schema.json`
- `common/schemas/class2_notification_payload_schema.json`
- `common/schemas/clarification_interaction_schema.json`

MQTT and payload references:

- `common/mqtt/topic_registry.json`
- `common/mqtt/publisher_subscriber_matrix.md`
- `common/mqtt/topic_payload_contracts.md`
- `common/payloads/README.md`

## 3. Payload Authority Levels

| Level | Meaning | Examples |
| --- | --- | --- |
| Schema-governed | JSON schema defines structural validity | context, candidate action, validator output, Class 2 notification, clarification interaction |
| Policy-governed | Policy/rules define behavioral admissibility | policy-router input, low-risk catalog, fault rules |
| Runtime or governance artifact | Evidence, observation, report, draft, or experiment output | audit events, dashboard observations, governance reports, result exports |

Runtime and governance artifacts must not redefine policy truth.

## 4. Core Payload Families

| Payload family | Primary contract |
| --- | --- |
| `policy_router_input` | `common/schemas/policy_router_input_schema.json` |
| `pure_context_payload` | `common/schemas/context_schema.json` |
| `candidate_action` | `common/schemas/candidate_action_schema.json` |
| `validator_output` | `common/schemas/validator_output_schema.json` |
| `class_2_notification_payload` | `common/schemas/class2_notification_payload_schema.json` |
| `clarification_interaction_payload` | `common/schemas/clarification_interaction_schema.json` |
| `fault_injection_payload` | `common/policies/fault_injection_rules.json` plus scenario/fault tooling |
| `actuation_command_payload` | Topic contract and dispatcher implementation, after validator/manual approval |
| `actuation_ack_payload` | Closed-loop evidence, not pure context |
| `audit_event_payload` | Audit/runtime contract, not policy authority |
| `dashboard_observation_payload` | Visibility artifact, not validator input |

## 5. MQTT Topic Rules

MQTT registry entries define communication contracts, not policy authority.

Every topic should identify:

- allowed publishers,
- allowed subscribers,
- payload family,
- schema or example reference where applicable,
- authority boundary,
- runtime mode allowance,
- QoS and retain assumptions,
- governance notes.

## 6. High-Value Topics

| Topic | Boundary |
| --- | --- |
| `safe_deferral/context/input` | Operational or controlled simulation context input |
| `safe_deferral/emergency/event` | Emergency evidence input aligned with policy |
| `safe_deferral/llm/candidate_action` | Candidate only; not execution authority |
| `safe_deferral/validator/output` | Validator result evidence for allowed dispatch |
| `safe_deferral/deferral/request` | Deferral or clarification control |
| `safe_deferral/escalation/class2` | Caregiver escalation or Class 2 notification |
| `safe_deferral/clarification/interaction` | Class 2 candidate/selection/timeout/transition evidence |
| `safe_deferral/caregiver/confirmation` | Manual confirmation evidence, not Class 1 validator approval |
| `safe_deferral/actuation/command` | Dispatch after validator approval or governed manual approval |
| `safe_deferral/actuation/ack` | Closed-loop evidence |
| `safe_deferral/audit/log` | Traceability evidence |
| `safe_deferral/sim/context` | Experiment-only controlled input |
| `safe_deferral/fault/injection` | Experiment-only controlled fault input |
| `safe_deferral/dashboard/observation` | Visibility only |
| `safe_deferral/experiment/progress` | Experiment status only |
| `safe_deferral/experiment/result` | Experiment artifact only |

## 7. Clarification Interaction Contract

Class 2 clarification artifacts use:

```text
topic: safe_deferral/clarification/interaction
payload_family: clarification_interaction_payload
schema: common/schemas/clarification_interaction_schema.json
authority_level: class2_interaction_evidence_not_authority
```

Selections on this topic are confirmed-candidate evidence. A confirmed
Class 1 selection re-enters the Deterministic Validator with the bounded
candidate; the selection alone does not bypass the validator, create
emergency evidence by itself, or authorize actuation.

The clarification record carries five optional fields that record how the
session was conducted (all introduced by docs 09–12 and backward-compatible —
legacy single-turn direct_select records validate unchanged):

| Field | Values | Meaning |
|---|---|---|
| `candidate_source` | `llm_generated` / `default_fallback` / `static_only_forced` | Provenance of the candidate set (doc 09 + PR #101). |
| `input_mode` | `direct_select` / `scanning` | Class 2 interaction model used (doc 12 §4.4 in 04_class2_clarification.md). |
| `scan_history` | array of per-option turns | One entry per scanning yes/no/silence/dropped turn. Empty / absent for direct_select. |
| `scan_ordering_applied` | object `{rule_source, matched_bucket, applied_overrides, final_order}` | Recorded only when `class2_scan_ordering_mode='deterministic'` ran (doc 12 §14). |
| `refinement_history` | array of refinement-turn entries | Recorded only when multi-turn refinement (doc 11 Phase 6.0) ran. |

All five are informational; none change validator gating, low-risk
catalog, or emergency normalization. They support audit, paper-eval, and
debugging.

### 7.1 Routing-metadata fields for paper-eval

`policy_router_input_schema.json::routing_metadata` carries four optional
experiment-mode fields. Production deployments leave them unset (the policy
defaults apply); paper-eval trial runners set them to isolate one factor
while holding others fixed. None of them enter the LLM prompt and none
affect Class 0 emergency routing or validator authority.

| Field | Values | Honored by |
|---|---|---|
| `experiment_mode` | `direct_mapping` / `rule_only` / `llm_assisted` | Class 1 intent-recovery branch in main.py (PR #79). |
| `class2_candidate_source_mode` | `static_only` / `llm_assisted` | `Class2ClarificationManager.start_session` candidate-source selection (doc 10 §3.3 P2.3, PR #101). |
| `class2_scan_ordering_mode` | `source_order` / `deterministic` | `Class2ClarificationManager.start_session` ordering layer when `input_mode='scanning'` (doc 12 §14, PR #110). |
| `class2_input_mode` | `direct_select` / `scanning` | `Class2ClarificationManager.start_session` interaction-model selection (doc 12 §9 Phase 5, PR #111). |

These four routing_metadata fields and the five clarification_interaction
fields together form the four orthogonal comparison spaces documented in
04_class2_clarification.md §4.7.

The Raspberry Pi evaluation host subscribes to
`safe_deferral/clarification/interaction` and `safe_deferral/escalation/class2`
(the Class 2 caregiver notification topic) for **evaluation capture only**.
Captured payloads land in `ClarificationStore` and `NotificationStore` ring
buffers consumed by Package D metrics. These RPi-side reads are
non-authoritative — they do not affect routing, validator approval, or
actuator commands. Mac mini remains the only authority for any Class 2
decision.

`common/schemas/class2_candidate_set_schema.json` is the schema for the
LocalLlmAdapter-internal payload returned by `generate_class2_candidates()`
to `Class2ClarificationManager`. This payload **never appears on any MQTT
topic** — it is internal evidence between adapter and manager only. The
clarification record is the on-the-wire artifact.

## 8. Governance Rule

Topic-drift reports, payload-validation reports, interface-matrix alignment
reports, and proposed-change reports are governance evidence. They support
review and maintenance, but cannot become operational authorization.

## 9. Source Notes

This active summary consolidates the stable material from:

- `common/docs/archive/architecture_legacy/15_interface_matrix.md`
- `common/docs/archive/architecture_legacy/17_payload_contract_and_registry.md`
- `common/mqtt/README.md`
- `common/payloads/README.md`
