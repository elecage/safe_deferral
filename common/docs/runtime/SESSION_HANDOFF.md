# SESSION_HANDOFF.md

## Purpose

This file is the runtime handoff **index** for the `safe_deferral` project.

The previous long-running master handoff has been preserved as:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_MASTER_LEGACY_HANDOFF.md`

Read this index first, then the latest dated addenda relevant to the current task.

If older wording in the legacy master handoff conflicts with newer dated addenda, prefer the newer dated addenda.

---

## Current priority read order

For current architecture, policy/schema, dashboard, experiment, doorbell, doorlock-sensitive, MQTT, payload, governance, interface-matrix, Mac mini install/configure/verify, Raspberry Pi install/configure/verify, ESP32 install/configure/verify, and architecture-document-structure work, read in this order:

1. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_ESP32_SCRIPT_ALIGNMENT_PLAN.md`
2. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_RPI_SCRIPT_ALIGNMENT_UPDATE.md`
3. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_MAC_MINI_INSTALL_CONFIG_VERIFY_ALIGNMENT_UPDATE.md`
4. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_RPI_SCRIPT_ALIGNMENT_PLAN.md`
5. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_MQTT_PAYLOAD_ALIGNMENT_UPDATE.md`
6. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_MQTT_PAYLOAD_GOVERNANCE_AND_ARCH_DOC_ALIGNMENT_UPDATE.md`
7. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_ARCHITECTURE_DOC_CONSOLIDATION_AND_PAYLOAD_REGISTRY_UPDATE.md`
8. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_DOORBELL_VISITOR_CONTEXT_UPDATE.md`
9. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_DOC_ALIGNMENT_UPDATE.md`
10. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_ALIGNMENT_UPDATE.md`
11. `common/docs/runtime/SESSION_HANDOFF_2026-04-24_DASHBOARD_TEST_APP_AND_ORCHESTRATION_UPDATE.md`
12. `common/docs/runtime/SESSION_HANDOFF_2026-04-24_PROMPT_REFACTOR_AND_EVAL_UPDATE.md`
13. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_MASTER_LEGACY_HANDOFF.md`

Use the legacy handoff as historical context and operational history, not as the final authority when it conflicts with newer addenda.

---

## Current non-negotiable interpretation

### 1. Role separation

- Mac mini = safety-critical operational edge hub.
- Raspberry Pi 5 = experiment dashboard, orchestration, simulation, replay, fault injection, progress/status publication, result artifact generation support host, and non-authoritative MQTT/payload governance support host when implemented.
- ESP32 = bounded physical node layer.
- STM32 or equivalent timing node = optional out-of-band measurement node, not part of the operational control plane.

### 2. Class 1 low-risk boundary

Current Class 1 autonomous low-risk execution remains limited to the frozen light-control catalog:

- `light_on` → `living_room_light`
- `light_on` → `bedroom_light`
- `light_off` → `living_room_light`
- `light_off` → `bedroom_light`

Authoritative source:

- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`

Do not silently expand autonomous Class 1 execution beyond this catalog.

### 3. Doorbell / visitor-response context

`doorbell_detected` is a required boolean field in:

- `environmental_context.doorbell_detected`

Authoritative source:

- `common/schemas/context_schema_v1_0_0_FROZEN.json`

Interpretation:

- `doorbell_detected=true` means a recent doorbell or visitor-arrival event has been detected.
- It is a visitor-response intent interpretation context signal.
- It does **not** authorize autonomous doorlock control.
- Non-visitor scenarios should normally set it to `false`.
- Visitor-response scenarios may set it to `true` when appropriate.

### 4. Doorlock-sensitive boundary

Doorlock may be implementation-facing and experiment-facing, but it is not current Class 1 autonomous low-risk execution.

Do not generate or approve:

- `door_unlock` as a Class 1 candidate action,
- `front_door_lock` as a Class 1 target device,
- doorlock fields in `validator_output_schema.executable_payload`,
- unrestricted dashboard/test-app door unlock controls,
- direct door unlock dispatch that bypasses caregiver approval and audit.

Doorlock-sensitive actions must route to:

- Class 2 escalation, or
- a separately governed manual confirmation path,

with explicit caregiver approval, ACK verification, and local audit logging.

### 5. Doorlock state boundary

Doorlock state is not currently part of `context_schema.device_states`.

Current valid `device_states` are:

- `living_room_light`
- `bedroom_light`
- `living_room_blind`
- `tv_main`

Do not insert `doorlock`, `front_door_lock`, or `door_lock_state` into `pure_context_payload.device_states` unless a future schema revision explicitly adds it.

Doorlock state, manual approval state, and ACK state should be represented through one of the following until future schema support exists:

- experiment annotation,
- mock approval state,
- dashboard-side observation field,
- audit artifact,
- manual confirmation path internal state,
- future schema revision.

### 6. MQTT / payload governance boundary

`common/mqtt/` and `common/payloads/` are shared reference layers.

They support:

- topic namespace review,
- publisher/subscriber role review,
- topic-to-payload contract review,
- schema/example payload linkage,
- governance dashboard and validation tooling.

They do **not** create policy, schema, validator, caregiver approval, audit, actuator, or doorlock execution authority.

The governance dashboard UI must remain a UI layer. Topic/payload create, update, delete, validation, and export operations should be handled by a separate governance backend/service.

### 7. Current active architecture figure, interface, and payload docs

The current active architecture-figure, interface, and payload-boundary documents are:

- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

Historical system-layout figure notes have been moved to:

- `common/docs/archive/system_layout_figure_notes/`

Do not treat old active paths such as `common/docs/architecture/24_final_paper_architecture_figure.md` or `common/docs/architecture/25_payload_contract_and_registry.md` as current active references.

---

## Current authoritative and reference documents

### Policies

- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_1_0.json`

### Schemas

- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

### MQTT / payload references

- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`
- `common/payloads/examples/`
- `common/payloads/templates/`

### Architecture / experiment docs

- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/01_installation_target_classification.md`
- `common/docs/architecture/02_mac_mini_build_sequence.md`
- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/docs/required_experiments.md`
- `CLAUDE.md`
- `README.md`
- `mac_mini/docs/README.md`

---

## Implementation reminders

1. Every valid context payload must include `environmental_context.doorbell_detected`.
2. Default `doorbell_detected` to `false` for non-visitor scenarios.
3. Use `doorbell_detected=true` only for recent doorbell or visitor-arrival context.
4. Do not treat `doorbell_detected=true` as unlock authorization.
5. Do not add doorlock state to current `device_states`.
6. Do not add doorlock to Class 1 candidate or validator executable payloads.
7. Keep RPi dashboard/orchestration/governance as experiment-side support, not policy authority.
8. Keep Mac mini as safety-critical operational hub.
9. Keep scenario fixtures, dashboards, and test apps from becoming policy truth.
10. Use `common/docs/architecture/17_payload_contract_and_registry.md` when deciding where payload fields belong.
11. Keep `common/docs/architecture/15_interface_matrix.md` aligned with `common/mqtt/topic_registry_v1_0_0.json`.
12. Do not hardcode MQTT topic strings in apps where registry lookup is practical.
13. Keep governance dashboard UI separate from governance backend/service.
14. Do not allow governance tooling to publish actuator commands, spoof caregiver approval, or create doorlock execution authority.
15. If a future task intentionally expands policy or schema scope, update frozen assets, required experiments, prompts, README, CLAUDE, interface matrix, topic registry, payload docs, and a new dated handoff addendum together.
16. For Mac mini install/configure/verify changes, check `SESSION_HANDOFF_2026-04-25_MAC_MINI_INSTALL_CONFIG_VERIFY_ALIGNMENT_UPDATE.md`, `mac_mini/docs/README.md`, and `02_mac_mini_build_sequence.md` together.
17. For Raspberry Pi install/configure/verify changes, check `SESSION_HANDOFF_2026-04-25_RPI_SCRIPT_ALIGNMENT_UPDATE.md` and preserve the non-authoritative RPi boundary.
18. For ESP32 install/configure/verify changes, check `SESSION_HANDOFF_2026-04-25_ESP32_SCRIPT_ALIGNMENT_PLAN.md` and preserve the bounded physical-node boundary.

---

## Addendum update rule

For future major changes:

1. Add a new dated addendum in `common/docs/runtime/`.
2. Update this index with the new addendum near the top of the priority read order.
3. Do not rewrite the legacy handoff unless performing a deliberate consolidation pass.
4. If the new addendum supersedes older wording, state that explicitly in the new addendum.
