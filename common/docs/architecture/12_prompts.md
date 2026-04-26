# 12_prompts.md

## Prompt Set Index

The original prompt document has been split for maintainability.

Use the following files:

- `common/docs/architecture/12_prompts_core_system.md`
- `common/docs/architecture/12_prompts_nodes_and_evaluation.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`

## Current prompt references

All prompt files should remain aligned with:

- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/docs/architecture/19_class2_clarification_architecture_alignment.md`
- `common/docs/architecture/20_scenario_data_flow_matrix.md`
- `common/mqtt/topic_registry.json`
- `common/mqtt/publisher_subscriber_matrix.md`
- `common/mqtt/topic_payload_contracts.md`
- `common/payloads/README.md`

## Repository-wide prompt boundary

All generated artifacts must preserve:

- Mac mini as the operational hub,
- Raspberry Pi as dashboard, simulation, orchestration, replay, fault-injection, result-export, and non-authoritative MQTT/payload governance support,
- ESP32 as the bounded physical node layer,
- optional timing/measurement infrastructure as evaluation-only support,
- `common/policies/` and `common/schemas/` as policy/schema authority,
- `common/mqtt/` and `common/payloads/` as shared communication/payload reference layers,
- `common/docs/architecture/15_interface_matrix.md` as the MQTT-aware interface contract reference,
- governance dashboard UI as a presentation and interaction layer,
- governance backend service as the draft/create/update/delete/validate/export service,
- Class 2 clarification as bounded interaction and transition handling, not autonomous actuation or terminal caregiver escalation by default,
- Class 2 transition outcomes as Policy Router re-entry events after user/caregiver confirmation, timeout, or deterministic evidence,
- and the rule that governance tooling must not create policy, schema, validator, caregiver approval, audit, actuator, or doorlock execution authority.

## Runtime generation tasks that must remain covered

The split prompt set must keep explicit coverage for:

- Class 2 Clarification Manager,
- clarification interaction payload handling,
- Class 2 transition tests,
- audit logging for clarification candidates, selections, timeouts, transition targets, and final safe outcomes,
- MQTT/payload governance checks for `clarification_interaction_payload`,
- Class 2 → Class 1 transition evaluation,
- Class 2 → Class 0 transition evaluation,
- Class 2 → Safe Deferral / Caregiver Confirmation evaluation.

## File roles

### `12_prompts_core_system.md`
Use this file for hub/backend/runtime generation tasks such as:

- policy router
- deterministic validator
- safe deferral handler
- Class 2 Clarification Manager
- audit logging
- notification and caregiver confirmation backend
- Raspberry Pi virtual sensors, emergency simulation, fault injection, and orchestration
- install/configure/verify scripts

### `12_prompts_nodes_and_evaluation.md`
Use this file for node firmware, measurement, and paper-oriented evaluation tasks such as:

- ESP32 node firmware
- STM32 measurement node support
- preflight readiness backend
- constrained-input intent recovery evaluation
- Class 2 clarification and transition evaluation flows
- visitor-response / doorlock-sensitive evaluation flows
- experiment dashboard control surface
- developer/test-app flows

### `12_prompts_mqtt_payload_governance.md`
Use this file for MQTT topic and payload governance tasks such as:

- topic registry loader / contract checker
- MQTT topic create/update/delete governance backend
- publisher node management
- subscriber node management
- payload example manager and validator
- clarification interaction payload validation
- MQTT/payload governance dashboard UI
- topic/payload validation reports
- topic/payload hardcoding drift detection
- interface-matrix alignment validation

The governance dashboard UI must remain a presentation and interaction layer. Actual topic/payload create, update, delete, validation, and export operations should be handled by a separate governance backend/service.

## Numbering policy

Prompt numbering is intentionally preserved across the split files.

- `12_prompts_core_system.md` contains the earlier core prompt set.
- `12_prompts_nodes_and_evaluation.md` continues the numbering for node, measurement, and evaluation prompts.
- `12_prompts_mqtt_payload_governance.md` continues with MQTT/payload governance prompts.

Do not renumber prompts unless there is a deliberate repository-wide cleanup.
