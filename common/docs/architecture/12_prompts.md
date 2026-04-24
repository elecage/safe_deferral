# 12_prompts.md

## Prompt Set Index

The original prompt document has been split for maintainability.

Use the following files:

- `common/docs/architecture/12_prompts_core_system.md`
- `common/docs/architecture/12_prompts_nodes_and_evaluation.md`

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

## Numbering policy

Prompt numbering is intentionally preserved across the split files.

- `12_prompts_core_system.md` contains the earlier core prompt set.
- `12_prompts_nodes_and_evaluation.md` continues the numbering for node, measurement, and evaluation prompts.

Do not renumber prompts unless there is a deliberate repository-wide cleanup.
