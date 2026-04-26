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
9. `08_system_structure_figure_revision_plan.md`

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
| `08_system_structure_figure_revision_plan.md` | Stepwise revision plan for the system structure figure |

System-figure revision working notes live under:

- `figure_revision/`

## 5. Active Prompt Sets

Implementation-generation prompts are indexed from:

- `12_prompts.md`

Current prompt categories:

- `12_prompts_mac_mini_components.md`
- `12_prompts_rpi_experiment_apps.md`
- `12_prompts_physical_nodes.md`
- `12_prompts_experiment_physical_nodes.md`
- `12_prompts_stm32_time_sync_node.md`

Older prompt files remain source notes and should not be treated as the active
prompt structure.

## 6. Archived Architecture Notes

The following older documents remain useful as archived source notes, but should
not be used as the first active read path:

- `common/docs/archive/architecture_legacy/01_installation_target_classification.md`
- `common/docs/archive/architecture_legacy/02_mac_mini_build_sequence.md`
- `common/docs/archive/architecture_legacy/03_deployment_structure.md`
- `common/docs/archive/architecture_legacy/04_project_directory_structure.md`
- `common/docs/archive/architecture_legacy/05_automation_strategy.md`
- `common/docs/archive/architecture_legacy/06_implementation_plan.md`
- `common/docs/archive/architecture_legacy/07_task_breakdown.md`
- `common/docs/archive/architecture_legacy/08_additional_required_work.md`
- `common/docs/archive/architecture_legacy/09_recommended_next_steps.md`
- `common/docs/archive/architecture_legacy/10_install_script_structure.md`
- `common/docs/archive/architecture_legacy/11_configuration_script_structure.md`
- `common/docs/archive/architecture_legacy/12_prompts_core_system.md`
- `common/docs/archive/architecture_legacy/12_prompts_mqtt_payload_governance.md`
- `common/docs/archive/architecture_legacy/12_prompts_nodes_and_evaluation.md`
- `common/docs/archive/architecture_legacy/13_doorlock_access_control_and_caregiver_escalation.md`
- `common/docs/archive/architecture_legacy/14_system_components_outline_v2.md`
- `common/docs/archive/architecture_legacy/15_interface_matrix.md`
- `common/docs/archive/architecture_legacy/16_system_architecture_figure.md`
- `common/docs/archive/architecture_legacy/17_payload_contract_and_registry.md`
- `common/docs/archive/architecture_legacy/18_scenario_node_component_mapping.md`
- `common/docs/archive/architecture_legacy/19_class2_clarification_architecture_alignment.md`
- `common/docs/archive/architecture_legacy/20_scenario_data_flow_matrix.md`
- `common/docs/archive/architecture_legacy/scenario_data_flows/20_00_interface_role_alignment.md`

The legacy notes have been moved out of `common/docs/architecture/` to reduce
active-document noise. New work should update the active document set first,
then consult archived source notes only when fine-grained historical detail is
needed.

## 7. Historical Areas

Historical assets and runtime handoff notes may retain old names or old
references:

- `common/history/`
- `common/docs/runtime/`
- `common/docs/archive/`

Active docs, active scenarios, scripts, and README-style guidance should use the
canonical names listed in this index.

## 8. Authority Rule

Architecture documents explain the system, but policy/schema authority lives in
the canonical assets. MQTT and payload references describe communication
contracts; they do not create policy authority, validator authority, caregiver
approval authority, direct actuation authority, or doorlock execution authority.
