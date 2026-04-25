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
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`

---

## Current structure

```text
common/payloads/
├── README.md
├── examples/
│   ├── policy_router_input_non_visitor.json
│   ├── policy_router_input_visitor_doorbell.json
│   ├── policy_router_input_emergency_temperature.json
│   ├── candidate_action_light_on.json
│   ├── validator_output_execute_approved_light.json
│   ├── class_2_notification_doorlock_sensitive.json
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
11. Governance change reports, interface-matrix alignment reports, topic-drift reports, payload validation reports, and proposed-change reports are evidence artifacts, not operational authorization mechanisms.
12. Governance dashboard UI must not directly edit registry files or publish operational control topics.
13. Governance backend must not directly modify canonical policies/schemas, publish actuator or doorlock commands, spoof caregiver approval, override the Policy Router or Deterministic Validator, or convert proposed changes into live authority without review.

---

## Schema-governed example coverage

| Example | Governing schema | Notes |
|---|---|---|
| `policy_router_input_non_visitor.json` | `policy_router_input_schema_v1_1_1_FROZEN.json` + `context_schema_v1_0_0_FROZEN.json` | Non-visitor baseline; `doorbell_detected=false` |
| `policy_router_input_visitor_doorbell.json` | `policy_router_input_schema_v1_1_1_FROZEN.json` + `context_schema_v1_0_0_FROZEN.json` | Visitor-response context; doorlock state only in experiment annotation |
| `policy_router_input_emergency_temperature.json` | `policy_router_input_schema_v1_1_1_FROZEN.json` + `context_schema_v1_0_0_FROZEN.json` | E001-style temperature threshold case |
| `candidate_action_light_on.json` | `candidate_action_schema_v1_0_0_FROZEN.json` | LLM candidate only, not authority |
| `validator_output_execute_approved_light.json` | `validator_output_schema_v1_1_0_FROZEN.json` | Approved low-risk light action only |
| `class_2_notification_doorlock_sensitive.json` | `class_2_notification_payload_schema_v1_0_0_FROZEN.json` | Escalation/manual confirmation review path, not actuation authority |

---

## Non-schema reference examples

| Example | Payload family | Authority boundary |
|---|---|---|
| `safe_deferral_request_two_options.json` | `safe_deferral_event` | Bounded clarification only |
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
- export payload validation reports and proposed-change reports.

Such a dashboard must remain a governance/inspection tool, not policy authority, schema authority, caregiver approval authority, actuator control authority, or doorlock execution authority.
