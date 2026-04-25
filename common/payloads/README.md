# common/payloads

## Purpose

This directory stores shared payload examples and templates for the `safe_deferral` project.

It supports implementation, documentation, testing scaffolds, MQTT contract review, and dashboard/test-app planning.

This directory is **not** policy authority and does **not** replace JSON schemas.

Authoritative sources remain:

- `common/schemas/`
- `common/policies/`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/mqtt/topic_registry_v1_0_0.json`

---

## Recommended structure

```text
common/payloads/
├── README.md
├── examples/
│   ├── policy_router_input_non_visitor.json
│   ├── policy_router_input_visitor_doorbell.json
│   ├── candidate_action_light_on.json
│   ├── validator_output_execute_approved_light.json
│   ├── class_2_notification_doorlock_sensitive.json
│   ├── dashboard_observation_doorlock_sensitive.json
│   └── experiment_annotation_doorlock_sensitive.json
└── templates/
    ├── scenario_fixture_template.json
    ├── result_export_template.json
    └── audit_event_template.json
```

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
- show missing required fields such as `doorbell_detected`,
- flag disallowed fields such as doorlock inside current `device_states`.

Such a dashboard must remain a governance/inspection tool, not policy authority or actuator control authority.
