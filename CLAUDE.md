# CLAUDE.md

## Role

This file is a compact operating guide for coding agents working in this
repository. It is not canonical truth by itself.

The system is a privacy-aware edge smart-home architecture for users with severe
physical or speech limitations. It uses local edge processing, bounded LLM
assistance, deterministic policy/validation, safe deferral, caregiver escalation,
and controlled experiment infrastructure.

## Read First

Read in this order before making implementation or documentation changes:

1. `README.md`
2. `common/docs/architecture/00_architecture_index.md`
3. `common/docs/architecture/01_system_architecture.md`
4. `common/docs/architecture/02_safety_and_authority_boundaries.md`
5. `common/docs/architecture/03_payload_and_mqtt_contracts.md`
6. `common/docs/architecture/04_class2_clarification.md`
7. `common/docs/architecture/05_implementation_plan.md`
8. `common/docs/architecture/06_deployment_and_scripts.md`
9. `common/docs/architecture/07_scenarios_and_evaluation.md`
10. `common/docs/required_experiments.md`
11. `common/docs/paper/01_paper_contributions.md`
12. `common/docs/runtime/SESSION_HANDOFF.md`

Use `common/docs/architecture/12_prompts.md` as the active prompt-set index when
implementation-generation prompts are needed. The active prompt sets are grouped
by Mac mini components, RPi experiment apps, physical nodes, experiment physical
nodes, and STM32 timing/measurement support.

## Canonical Assets

Policy assets:

- `common/policies/policy_table.json`
- `common/policies/low_risk_actions.json`
- `common/policies/fault_injection_rules.json`
- `common/policies/output_profile.json`

Schema assets:

- `common/schemas/policy_router_input_schema.json`
- `common/schemas/context_schema.json`
- `common/schemas/candidate_action_schema.json`
- `common/schemas/validator_output_schema.json`
- `common/schemas/class2_notification_payload_schema.json`
- `common/schemas/clarification_interaction_schema.json`

MQTT/payload references:

- `common/mqtt/topic_registry.json`
- `common/mqtt/publisher_subscriber_matrix.md`
- `common/mqtt/topic_payload_contracts.md`
- `common/payloads/README.md`

Do not invent alternate filenames or versioned active names. Historical assets
belong under `common/history/`, and runtime handoff history belongs under
`common/docs/runtime/`.

## Non-Negotiable Boundaries

- LLM output is candidate guidance only. It is not policy authority, validator
  authority, caregiver approval, emergency evidence, or actuator authority.
- Current autonomous Class 1 execution is limited to the canonical low-risk
  lighting catalog: `light_on` / `light_off` for `living_room_light` and
  `bedroom_light`.
- Doorbell context is not doorlock authorization. `doorbell_detected` is required
  in valid context payloads and defaults to `false` for non-visitor scenarios.
- Doorlock is a representative sensitive actuation case. It must stay outside
  autonomous Class 1 execution unless future canonical policy/schema changes
  explicitly add that authority.
- Do not add `doorlock`, `front_door_lock`, or `door_lock_state` to
  `pure_context_payload.device_states` unless the canonical schema changes.
- Doorlock state, manual approval state, ACK state, and dashboard observations
  must remain in experiment annotations, mock approval state, audit artifacts,
  dashboard-side observations, manual-confirmation internal state, or future
  schema revisions.
- MQTT topics, payload examples, dashboards, governance reports, and experiment
  fixtures do not create operational authority.
- Governance UI must not directly edit registry files, publish operational
  control topics, expose unrestricted actuator consoles, or expose direct
  doorlock command controls.
- Governance backend must not directly modify canonical policy/schema assets,
  publish actuator or doorlock commands, spoof caregiver approval, override the
  Policy Router or Deterministic Validator, or convert proposed changes into live
  authority without review.

## Device Roles

- Mac mini: safety-critical operational edge hub. It owns MQTT/state intake,
  local LLM adapter, Policy Router, Deterministic Validator, safe deferral,
  caregiver escalation/approval handling, ACK/audit logging, and runtime loading
  of canonical references.
- Raspberry Pi 5: experiment-side support host. It may run monitoring dashboard,
  scenario orchestration, simulation/replay, fault injection, RPi virtual nodes,
  result export, and non-authoritative MQTT/payload governance support.
- ESP32: bounded physical node layer for input, context, emergency event,
  lighting/warning interface, and controlled physical-node validation.
- Optional STM32 or timing node: out-of-band measurement support only.

RPi virtual nodes are controlled experiment sources or observers. They are not
production devices and do not create policy, validator, caregiver approval,
actuator, or doorlock authority.

## Scenario And Experiment Work

`integration/scenarios/` contains active scenario-contract assets, not scratch
examples. Keep scenarios aligned with:

- active architecture documents,
- canonical policy/schema assets,
- canonical MQTT topic registry and payload contracts,
- `common/docs/required_experiments.md`,
- Class 2 clarification topic `safe_deferral/clarification/interaction`,
- RPi virtual-node and monitoring boundaries.

Python implementation and verifier code has been removed for the current cleanup
phase. Do not reference deleted Python runners or verifiers as active tools.
Reintroduce implementation code only after the document, scenario, and asset
contract baseline is stable.

## Coding Rules

- Prefer existing repository structure and local conventions.
- Keep device-specific code under `mac_mini/`, `rpi/`, or `esp32/`.
- Keep shared policy/schema/MQTT/payload truth under `common/`.
- Keep scenario, fixture, measurement, and result assets under `integration/`.
- Use registry/configuration lookup for topic strings, schema paths, payload
  families, and publisher/subscriber roles where practical.
- Do not hardcode obsolete topic names, payload names, or asset filenames.
- If implementation changes affect architecture, scenarios, experiments, or
  canonical assets, update the relevant documents in the same change.
- Canonical policy/schema assets are not casual edit targets. Modify them only
  when a documented consistency issue requires it.

## Do Not

- Do not add cloud API dependencies for the core system.
- Do not bypass policy or validator logic.
- Do not treat deployment-local `.env`, runtime copies, synced mirrors, or
  dashboard observations as canonical truth.
- Do not promote implementation-facing device scope into autonomous Class 1
  authority.
- Do not interpret `safe_deferral/caregiver/confirmation` as autonomous Class 1
  validator approval.
- Do not publish operational control topics from dashboard/governance UI.
- Do not treat report artifacts as authorization mechanisms.

## Conflict Priority

When documents disagree, resolve in this order:

1. Canonical policy/schema assets
2. `common/docs/architecture/00_architecture_index.md`
3. `common/docs/architecture/02_safety_and_authority_boundaries.md`
4. `common/docs/architecture/03_payload_and_mqtt_contracts.md`
5. `common/docs/architecture/04_class2_clarification.md`
6. `common/docs/architecture/07_scenarios_and_evaluation.md`
7. `common/docs/required_experiments.md`
8. `README.md`
9. `common/docs/paper/01_paper_contributions.md`
10. `common/docs/runtime/SESSION_HANDOFF.md` and relevant addenda
11. Device-layer README files and integration documents
12. `CLAUDE.md`
