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

## 10. Class 2 Modes Preserve Boundaries

The Class 2 layer ships several opt-in interaction modes (docs 11, 12) and
four orthogonal paper-eval comparison dimensions (doc 12 §4.7 in
`04_class2_clarification.md`). All of these are presentation / generation /
ordering choices — none introduce a new authority surface. The invariant
each mode honours:

- **Same candidate set, same Validator gating.** Whether candidates come
  from `_DEFAULT_CANDIDATES`, the LLM, or a refinement template, they pass
  through `Class2ClarificationManager` and a confirmed Class 1 selection
  re-enters the Deterministic Validator. No mode bypasses validator gating.
- **Same low-risk catalog.** No mode (including refinement and
  deterministic ordering) can produce an `(action_hint, target_hint)`
  outside `low_risk_actions.json`. The catalog grows only via human
  governance (§4 LLM Boundary above). Refinement templates and ordering
  rules never inject candidates; ordering is pure permutation.
- **Silence ≠ consent.** Direct-select per-phase timeout, scanning
  per-option silence on the final option, and refinement-turn timeout all
  escalate to caregiver — none of them treat silence as approval.
- **Authority surface unchanged.** Scanning, multi-turn refinement, and
  deterministic ordering each add audit fields (`input_mode`,
  `scan_history`, `refinement_history`, `scan_ordering_applied`) but do
  not unlock new actuators, new transition targets, or new validator
  outcomes. Doorlock remains outside autonomous Class 1 across every mode.
- **Telegram caregiver path unchanged.** Caregiver Phase 2 is shared by
  all interaction modes via the `_run_caregiver_phase` helper — caregiver
  still sees the same inline-keyboard candidate set and can still override.

The four routing-metadata comparison fields (`experiment_mode`,
`class2_candidate_source_mode`, `class2_scan_ordering_mode`,
`class2_input_mode`) are honored only by the corresponding manager
branches. They never enter the LLM prompt and never affect Class 0
emergency triggers, Class 1 routing, or validator authority.

## 11. Source Notes

This active summary consolidates the stable material from:

- `common/docs/archive/architecture_legacy/13_doorlock_access_control_and_caregiver_escalation.md`
- `common/docs/archive/architecture_legacy/15_interface_matrix.md`
- `common/docs/archive/architecture_legacy/17_payload_contract_and_registry.md`
- `common/docs/archive/architecture_legacy/19_class2_clarification_architecture_alignment.md`
