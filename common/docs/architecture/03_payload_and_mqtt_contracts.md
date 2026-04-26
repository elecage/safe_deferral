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

Selections on this topic are evidence for Policy Router re-entry. They do not
bypass the Deterministic Validator, create emergency evidence by themselves, or
authorize actuation.

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
