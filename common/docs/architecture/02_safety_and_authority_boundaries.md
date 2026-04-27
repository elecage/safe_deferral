# Safety And Authority Boundaries

## 1. Purpose

This document records the non-negotiable safety and authority boundaries for the
current architecture.

## 2. Core Authority Rule

Only canonical policy and schema assets define current execution constraints.
Architecture documents, MQTT topics, payload examples, dashboard views,
governance reports, LLM output, and experiment fixtures do not create execution
authority.

## 3. Class Boundaries

| Class | Meaning | Current handling |
| --- | --- | --- |
| Class 0 | Emergency evidence | Route to emergency handling according to `policy_table.json` |
| Class 1 | Autonomous low-risk assistance | Limited to the low-risk catalog and deterministic validator approval |
| Class 2 | Ambiguous, insufficient, sensitive, or transition-oriented state | Clarification, safe deferral, caregiver escalation, or re-entry to Class 0/Class 1 after valid evidence |

Class 1 autonomous execution is intentionally narrow. It must not expand through
LLM inference, topic naming, dashboard controls, or scenario convenience.

## 4. LLM Boundary

The LLM may:

- summarize context,
- interpret bounded user intent,
- propose candidate actions,
- generate user-facing guidance,
- support clarification prompts.

The LLM must not:

- approve execution,
- bypass the Policy Router,
- bypass the Deterministic Validator,
- create emergency evidence by text alone,
- spoof caregiver approval,
- dispatch actuator commands,
- turn doorlock-sensitive behavior into autonomous Class 1 execution.

## 5. Deterministic Validator Boundary

The validator is the execution gate for low-risk autonomous action. It must
approve exactly the admissible action within policy/schema bounds before a
low-risk dispatcher may publish an actuation command.

Validator output is evidence for dispatch. It is not a general-purpose override
for sensitive actuation.

## 6. Doorbell Boundary

`doorbell_detected` is visitor-response context under `context_schema.json`.

It may help the system interpret a visitor-related situation, but it does not:

- create emergency evidence,
- authorize autonomous door unlock,
- imply caregiver approval,
- add doorlock state to `device_states`,
- promote any action into Class 1.

## 7. Doorlock Boundary

Doorlock opening is a sensitive actuation domain, not an ordinary low-risk
Class 1 action in the current baseline.

Doorlock-related requests should route toward:

- safe deferral,
- bounded clarification,
- caregiver escalation,
- separately governed manual confirmation,
- ACK and audit evidence if a governed manual path dispatches a command.

Doorlock state is not currently part of `context_schema.device_states`. If
future work adds doorlock state, policy, schema, MQTT, payload, caregiver
confirmation, ACK, audit, and tests must be reviewed together.

## 8. Caregiver Confirmation Boundary

Caregiver confirmation is manual approval evidence. It is not the same thing as
Class 1 validator approval.

Sensitive actuation may proceed only through a separately governed manual path
that preserves:

- confirmation source,
- command dispatch boundary,
- ACK verification,
- audit trace.

Telegram, if used, is only an outbound notification and response-collection
transport for caregiver confirmation evidence. It must not be treated as a
remote-control channel, a direct actuator interface, a doorlock console, or a
replacement for Mac mini policy routing, validation, dispatch, ACK, or audit.

## 9. MQTT, Payload, Dashboard, And Governance Boundary

MQTT topics and payload contracts describe communication behavior. They do not
authorize policy routes or execution.

Dashboard and governance tooling may inspect, validate, compare, export, and
propose changes. They must not:

- directly edit canonical policies or schemas as live authority,
- publish operational control topics,
- expose unrestricted actuator consoles,
- expose direct doorlock command controls,
- spoof caregiver approval,
- convert draft changes into live operational authority without review.

Governance reports are evidence artifacts, not authorization mechanisms.

## 10. Source Notes

This active summary consolidates the stable material from:

- `common/docs/archive/architecture_legacy/13_doorlock_access_control_and_caregiver_escalation.md`
- `common/docs/archive/architecture_legacy/15_interface_matrix.md`
- `common/docs/archive/architecture_legacy/17_payload_contract_and_registry.md`
- `common/docs/archive/architecture_legacy/19_class2_clarification_architecture_alignment.md`
