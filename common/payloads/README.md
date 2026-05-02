# common/payloads

## Purpose

This directory stores shared payload examples and templates for the `safe_deferral` project.

It supports implementation, documentation, testing scaffolds, MQTT contract review, Package G governance-boundary validation, and dashboard/test-app planning.

This directory is **not** policy authority and does **not** replace JSON schemas.

Authoritative sources remain:

- `common/schemas/`
- `common/policies/`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/mqtt/topic_registry.json`
- `common/mqtt/topic_payload_contracts.md`

Historical MQTT registry baseline:

- `common/history/mqtt/topic_registry.json`

---

## Current structure

```text
common/payloads/
├── README.md
├── examples/
│   ├── policy_router_input_non_visitor.json
│   ├── policy_router_input_visitor_doorbell.json
│   ├── policy_router_input_emergency_temperature.json
│   ├── policy_router_input_paper_eval_all_modes.json
│   ├── candidate_action_light_on.json
│   ├── validator_output_execute_approved_light.json
│   ├── class_2_notification_doorlock_sensitive.json
│   ├── clarification_interaction_two_options_pending.json
│   ├── clarification_interaction_scanning_yes_first.json
│   ├── clarification_interaction_multi_turn_refinement.json
│   ├── safe_deferral_request_two_options.json
│   ├── manual_confirmation_doorlock_approved.json
│   ├── actuation_command_light_on.json
│   ├── actuation_ack_success.json
│   ├── audit_event_route_decision.json
│   ├── fault_injection_missing_doorbell_context.json
│   ├── dashboard_observation_doorlock_sensitive.json
│   ├── experiment_progress_running.json
│   └── result_export_summary.json
└── templates/
    └── scenario_fixture_template.json
```

Additional templates may be added later for result export, audit events, governance reports, topic-drift reports, and payload validation reports when those contracts stabilize.

---

## Rules

1. Payload examples are references, not policy truth.
2. Any schema-governed section embedded in an example must validate against the corresponding schema under `common/schemas/`.
3. `environmental_context.doorbell_detected` is required in valid context examples.
4. Non-visitor examples should normally set `doorbell_detected=false`.
5. Visitor-response examples may set `doorbell_detected=true`.
6. Doorlock state must not be placed inside current `pure_context_payload.device_states`.
7. Manual approval state and ACK state must not be placed inside `pure_context_payload`.
8. Dashboard observation examples are visibility artifacts, not policy truth.
9. Scenario fixture templates are not executable policy unless interpreted through integration/scenario tooling.
10. MQTT topic-payload linkage should be tracked under `common/mqtt/`.
11. `clarification_interaction_payload` must remain separate from `safe_deferral_event`, `class_2_notification_payload`, `validator_output_payload`, `actuation_command_payload`, and `pure_context_payload`.
12. `safe_deferral/clarification/interaction` carries Class 2 clarification evidence and must not be interpreted as validator approval, actuation command, emergency trigger authority, or doorlock authorization.
13. Governance change reports, interface-matrix alignment reports, topic-drift reports, payload validation reports, and proposed-change reports are evidence artifacts, not operational authorization mechanisms.
14. Governance dashboard UI must not directly edit registry files or publish operational control topics.
15. Governance backend must not directly modify canonical policies/schemas, publish actuator or doorlock commands, spoof caregiver approval, override the Policy Router or Deterministic Validator, or convert proposed changes into live authority without review.

---

## Schema-governed example coverage

| Example | Governing schema | Notes |
|---|---|---|
| `policy_router_input_non_visitor.json` | `policy_router_input_schema.json` + `context_schema.json` | Non-visitor baseline; `doorbell_detected=false` |
| `policy_router_input_visitor_doorbell.json` | `policy_router_input_schema.json` + `context_schema.json` | Strict visitor-response context example; doorlock/manual approval/ACK state belongs in fixture annotations, dashboard observation, manual confirmation payloads, or audit artifacts, not in this schema-governed example |
| `policy_router_input_emergency_temperature.json` | `policy_router_input_schema.json` + `context_schema.json` | E001-style temperature threshold case |
| `policy_router_input_paper_eval_all_modes.json` | `policy_router_input_schema.json` + `context_schema.json` | Paper-eval matrix variant exercising all four comparison dimensions (D1×D2×D3×D4) in one input shape; reference example only |
| `candidate_action_light_on.json` | `candidate_action_schema.json` | LLM candidate only, not authority |
| `validator_output_execute_approved_light.json` | `validator_output_schema.json` | Approved low-risk light action only |
| `class_2_notification_doorlock_sensitive.json` | `class2_notification_payload_schema.json` | Class 2 notification/manual confirmation review path, not actuation authority |
| `clarification_interaction_two_options_pending.json` | `clarification_interaction_schema.json` | Class 2 clarification interaction evidence for `safe_deferral/clarification/interaction`, not authorization |
| `clarification_interaction_scanning_yes_first.json` | `clarification_interaction_schema.json` | Scanning-mode interaction evidence with `scan_history` and `input_mode=scanning` (doc 12); user accepts the first announced option |
| `clarification_interaction_multi_turn_refinement.json` | `clarification_interaction_schema.json` | Multi-turn refinement interaction evidence with `refinement_history` (doc 11 Phase 6.0); parent + per-room refinement turn |

---

## Non-schema reference examples

| Example | Payload family | Authority boundary |
|---|---|---|
| `safe_deferral_request_two_options.json` | `safe_deferral_event` | Legacy/bounded safe-deferral request event; not a `clarification_interaction_payload` example |
| `manual_confirmation_doorlock_approved.json` | `manual_confirmation_payload` | Separately governed manual path, not Class 1 approval |
| `actuation_command_light_on.json` | `actuation_command_payload` | Valid only after validator approval |
| `actuation_ack_success.json` | `actuation_ack_payload` | Closed-loop evidence only |
| `audit_event_route_decision.json` | `audit_event_payload` | Evidence/traceability only |
| `fault_injection_missing_doorbell_context.json` | `fault_injection_payload` | Controlled schema/fault case only |
| `dashboard_observation_doorlock_sensitive.json` | `dashboard_observation_payload` | Visibility only, not policy truth |
| `experiment_progress_running.json` | `experiment_progress_payload` | Experiment status only |
| `result_export_summary.json` | `result_export_payload` | Experiment artifact only |

---

## Package G report artifacts

Package G may generate the following artifacts:

- interface-matrix alignment report,
- topic-drift report,
- payload validation report,
- governance backend/UI separation report,
- proposed-change review report.

These report artifacts may be stored under a future `common/payloads/templates/` or result-export directory when their contracts stabilize. They must not be treated as policy authority, schema authority, caregiver approval authority, actuator authority, or doorlock execution authority.

---

## Relationship to other directories

| Directory | Purpose |
|---|---|
| `common/schemas/` | Validation authority |
| `common/policies/` | Routing/action authority |
| `common/payloads/` | Shared examples and templates |
| `common/mqtt/` | Topic/publisher/subscriber/payload contracts |
| `integration/scenarios/` | Executable or evaluation-oriented scenario definitions |
| `rpi/**/fixtures` | Runtime or implementation-specific fixtures, when created |
| `mac_mini/**/tests` | Hub-side test fixtures, when created |

---

## Future dashboard / web app note

A future payload management dashboard may use this directory to:

- browse payload examples,
- validate examples against schemas,
- compare payload examples with MQTT topic contracts,
- detect field drift,
- detect topic/payload hardcoding drift,
- show missing required fields such as `doorbell_detected`,
- flag disallowed fields such as doorlock inside current `device_states`,
- validate `clarification_interaction_payload` examples,
- warn if a clarification interaction example appears to authorize actuation, validator approval, emergency handling, or doorlock control,
- export payload validation reports and proposed-change reports.

Such a dashboard must remain a governance/inspection tool, not policy authority, schema authority, caregiver approval authority, actuator control authority, or doorlock execution authority.
