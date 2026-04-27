# 12_prompts.md

## Purpose

This document is the active prompt-set index for implementation generation.

The prompt set is organized by implementation target rather than by the older
historical prompt numbering. Use this index when choosing which prompt document
to give to an implementation agent.

Prompt documents do not define policy, schema, MQTT, scenario, or experiment
authority. They must remain aligned with the active architecture documents and
canonical assets.

## Required Read Order

Before using any prompt set, read:

1. `common/docs/architecture/00_architecture_index.md`
2. `common/docs/architecture/01_system_architecture.md`
3. `common/docs/architecture/02_safety_and_authority_boundaries.md`
4. `common/docs/architecture/03_payload_and_mqtt_contracts.md`
5. `common/docs/architecture/04_class2_clarification.md`
6. `common/docs/architecture/05_implementation_plan.md`
7. `common/docs/architecture/06_deployment_and_scripts.md`
8. `common/docs/architecture/07_scenarios_and_evaluation.md`
9. `common/docs/required_experiments.md`

## Active Prompt Sets

| File | Use for |
|---|---|
| `12_prompts_mac_mini_components.md` | Mac mini operational hub components |
| `12_prompts_rpi_experiment_apps.md` | Raspberry Pi experiment apps, managers, dashboard, and governance support |
| `12_prompts_physical_nodes.md` | Actual physical nodes and optional physical evaluation interfaces |
| `12_prompts_stm32_time_sync_node.md` | STM32 timing, synchronization, and measurement node support |

## Category Boundaries

Mac mini prompt sets are for safety-critical operational services:

- MQTT/context intake,
- local LLM adapter,
- Policy Router,
- Deterministic Validator,
- Class 2 Clarification Manager,
- safe deferral handling,
- low-risk dispatcher,
- caregiver escalation and confirmation handling,
- ACK and audit logging,
- read-only telemetry exposed to experiment tools.

Raspberry Pi prompt sets are for experiment-side apps:

- paper experiment batch execution,
- result storage and analysis,
- experiment manager,
- virtual node creation/deletion,
- virtual behavior execution,
- virtual fault injection,
- scenario generation and execution,
- MQTT/interface status management,
- web-based monitoring dashboard,
- non-authoritative MQTT/payload governance support.

Physical-node prompts are handled as one bounded physical-node category:

- actual prototype nodes required by the baseline,
- optional physical evaluation interfaces needed by experiments,
- representative sensitive interfaces such as a governed doorlock interface.

Do not create a separate authority category for experiment-only physical nodes.
If a physical node is used only for an experiment, document that usage in the
experiment setup while keeping it under the same bounded physical-node authority
rules.

Fault injection should be implemented through RPi virtual nodes and virtual
behavior managers by default. A physical fault-injection node is intentionally
not part of the active prompt set.

## Repository-Wide Prompt Boundary

All generated work must preserve these rules:

- LLM output is candidate guidance only.
- Policy/schema authority lives in `common/policies/` and `common/schemas/`.
- MQTT/payload references live in `common/mqtt/` and `common/payloads/`.
- Scenario contracts live in `integration/scenarios/`.
- Required experiment intent lives in `common/docs/required_experiments.md`.
- Mac mini remains the operational edge hub.
- Raspberry Pi remains experiment support, dashboard, orchestration,
  simulation, replay, monitoring, and result-export infrastructure.
- Actual physical nodes remain bounded input/context/evidence/output/actuator
  interfaces and do not create policy authority.
- STM32 timing support remains out-of-band measurement infrastructure.
- Doorlock remains a sensitive actuation case outside autonomous Class 1 unless
  future canonical policy/schema changes explicitly add that authority.
- `doorbell_detected` is visitor-response context, not doorlock authorization.
- `safe_deferral/clarification/interaction` is Class 2 interaction evidence,
  not validator approval, actuator authority, emergency trigger authority, or
  doorlock authorization.

## Legacy Source Notes

The following older prompt files remain as source notes during the transition:

- `common/docs/archive/architecture_legacy/12_prompts_core_system.md`
- `common/docs/archive/architecture_legacy/12_prompts_nodes_and_evaluation.md`
- `common/docs/archive/architecture_legacy/12_prompts_mqtt_payload_governance.md`

Do not use their old numbering as the active implementation plan. When older
prompt wording conflicts with the active prompt sets or active architecture
documents, prefer the active prompt sets and active architecture documents.
