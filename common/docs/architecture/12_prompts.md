# 12_prompts.md

## Prompt Set Index

The original prompt document has been split for maintainability.

Use the following files:

- `common/docs/architecture/12_prompts_core_system.md`
- `common/docs/architecture/12_prompts_nodes_and_evaluation.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`

## File roles

### `12_prompts_core_system.md`
Use this file for hub/backend/runtime generation tasks such as:

- policy router
- deterministic validator
- safe deferral handler
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
- MQTT/payload governance dashboard UI
- topic/payload validation reports

The governance dashboard UI must remain a presentation and interaction layer. Actual topic/payload create, update, delete, validation, and export operations should be handled by a separate governance backend/service.

## Numbering policy

Prompt numbering is intentionally preserved across the split files.

- `12_prompts_core_system.md` contains the earlier core prompt set.
- `12_prompts_nodes_and_evaluation.md` continues the numbering for node, measurement, and evaluation prompts.
- `12_prompts_mqtt_payload_governance.md` continues with MQTT/payload governance prompts.

Do not renumber prompts unless there is a deliberate repository-wide cleanup.
