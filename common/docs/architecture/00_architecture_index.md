# Architecture Index

## 1. Purpose

This index defines the active architecture document set for the current
`safe_deferral` cleanup baseline.

The repository still contains older architecture notes that were useful during
rapid iteration. Those notes are now treated as legacy/reference material unless
this index points to them as active source material.

## 2. Active Read Order

Read these documents first for current architecture work:

1. `00_architecture_index.md`
2. `01_system_architecture.md`
3. `02_safety_and_authority_boundaries.md`
4. `03_payload_and_mqtt_contracts.md`
5. `04_class2_clarification.md`
6. `05_implementation_plan.md`
7. `06_deployment_and_scripts.md`
8. `07_scenarios_and_evaluation.md`

These files are the active navigation layer. They intentionally summarize and
deduplicate the older numbered notes.

## 3. Canonical Assets

Current policy assets:

- `common/policies/policy_table.json`
- `common/policies/low_risk_actions.json`
- `common/policies/fault_injection_rules.json`
- `common/policies/output_profile.json`

Current schema assets:

- `common/schemas/policy_router_input_schema.json`
- `common/schemas/context_schema.json`
- `common/schemas/candidate_action_schema.json`
- `common/schemas/validator_output_schema.json`
- `common/schemas/class2_notification_payload_schema.json`
- `common/schemas/clarification_interaction_schema.json`

Current MQTT and payload reference assets:

- `common/mqtt/topic_registry.json`
- `common/mqtt/publisher_subscriber_matrix.md`
- `common/mqtt/topic_payload_contracts.md`
- `common/payloads/README.md`

`common/asset_manifest.json` records active and historical asset mapping.

## 4. Active Document Roles

| Document | Role |
| --- | --- |
| `01_system_architecture.md` | System shape, node roles, closed-loop path |
| `02_safety_and_authority_boundaries.md` | Non-negotiable safety, authority, Class 0/1/2, doorbell, doorlock, governance boundaries |
| `03_payload_and_mqtt_contracts.md` | Payload families, MQTT contract rules, topic authority limits |
| `04_class2_clarification.md` | Class 2 clarification, transition, timeout, and re-entry semantics |
| `05_implementation_plan.md` | Current implementation order and cleanup sequence |
| `06_deployment_and_scripts.md` | Install/configure/verify structure for Mac mini, RPi, ESP32 |
| `07_scenarios_and_evaluation.md` | Scenario contracts, evaluation boundaries, measurement direction |

## 5. Legacy Architecture Notes

The following older documents remain useful as source notes, but should not be
used as the first active read path:

- `01_installation_target_classification.md`
- `02_mac_mini_build_sequence.md`
- `03_deployment_structure.md`
- `04_project_directory_structure.md`
- `05_automation_strategy.md`
- `06_implementation_plan.md`
- `07_task_breakdown.md`
- `08_additional_required_work.md`
- `09_recommended_next_steps.md`
- `10_install_script_structure.md`
- `11_configuration_script_structure.md`
- `12_prompts.md`
- `12_prompts_core_system.md`
- `12_prompts_mqtt_payload_governance.md`
- `12_prompts_nodes_and_evaluation.md`
- `13_doorlock_access_control_and_caregiver_escalation.md`
- `14_system_components_outline_v2.md`
- `15_interface_matrix.md`
- `16_system_architecture_figure.md`
- `17_payload_contract_and_registry.md`
- `18_scenario_node_component_mapping.md`
- `19_class2_clarification_architecture_alignment.md`
- `20_scenario_data_flow_matrix.md`
- `scenario_data_flows/20_00_interface_role_alignment.md`

During this transition, the legacy notes remain in place to preserve review
history and fine-grained detail. New work should update the active document set
first, then update legacy notes only when a specific detailed reference still
depends on them.

## 6. Historical Areas

Historical assets and runtime handoff notes may retain old names or old
references:

- `common/history/`
- `common/docs/runtime/`
- `common/docs/archive/`

Active docs, active scenarios, scripts, and README-style guidance should use the
canonical names listed in this index.

## 7. Authority Rule

Architecture documents explain the system, but policy/schema authority lives in
the canonical assets. MQTT and payload references describe communication
contracts; they do not create policy authority, validator authority, caregiver
approval authority, direct actuation authority, or doorlock execution authority.
