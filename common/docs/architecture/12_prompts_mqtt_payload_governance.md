# 12_prompts_mqtt_payload_governance.md

## MQTT / Payload Governance Prompt Set

This document contains prompts for implementing the MQTT topic and payload governance layer.

It complements:

- `common/docs/architecture/12_prompts.md`
- `common/docs/architecture/12_prompts_core_system.md`
- `common/docs/architecture/12_prompts_nodes_and_evaluation.md`

## Scope

This prompt set is for:

- MQTT topic registry loading,
- topic CRUD governance service,
- payload reference management,
- publisher/subscriber role management,
- schema/payload validation,
- topic/payload hardcoding drift detection,
- interface-matrix alignment validation,
- dashboard UI integration,
- governance audit trail,
- clarification interaction payload validation,
- and non-authoritative inspection workflows.

## Required references

Before implementing any component from this prompt set, the agent must read:

- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`
- `common/docs/architecture/19_class2_clarification_architecture_alignment.md`
- `common/docs/architecture/20_scenario_data_flow_matrix.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json`
- `common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json`

## Payload family separation

Governance tooling must preserve the following payload-family separation:

```text
pure_context_payload
≠ class_2_notification_payload
≠ clarification_interaction_payload
≠ validator_output_payload
≠ actuation_command_payload
≠ audit_payload
```

`clarification_interaction_payload` may contain candidate choices, selection result, timeout result, transition target, and final safe outcome. It must not contain actuator authorization, emergency trigger authority, validator approval, or doorlock unlock approval.

## Non-negotiable authority boundary

The MQTT/payload manager is a governance and configuration-support component.

It must not become:

- policy authority,
- schema authority,
- Policy Router authority,
- Deterministic Validator authority,
- caregiver approval authority,
- audit authority,
- or direct actuator/doorlock dispatch authority.

It must not:

- directly modify canonical policies or schemas,
- publish actuator or doorlock commands,
- spoof caregiver approval,
- override Policy Router or Deterministic Validator decisions,
- treat `clarification_interaction_payload` as validator approval or actuator authorization,
- treat Class 2 candidate text as emergency trigger evidence,
- or convert draft/proposed registry changes into live operational authority without review.

The dashboard UI must remain a presentation and interaction layer only.  
The actual create/update/delete/validation/export operations must be handled by a separate governance backend/service.

---

## Prompt 36. Implement MQTT Topic Registry Loader and Contract Checker

```text
Implement an MQTT topic registry loader and contract checker for the safe_deferral project.

Target repository areas:
- mac_mini/code/ if used by operational runtime services
- rpi/code/ if used by experiment/dashboard/governance tooling
- integration/tests/ for shared validation tests

Requirements:
- Load topic definitions from:
  - common/mqtt/topic_registry_v1_0_0.json
- Do not hardcode MQTT topic strings where registry lookup is practical.
- Expose lookup functions such as:
  - get_topic(topic_id)
  - get_qos(topic_id)
  - get_retain(topic_id)
  - get_payload_family(topic_id)
  - get_schema_path(topic_id)
  - get_example_payload_path(topic_id)
  - get_allowed_publishers(topic_id)
  - get_allowed_subscribers(topic_id)
- Validate that every registry entry has:
  - topic or topic pattern
  - stable topic_id or equivalent key
  - publisher list
  - subscriber list
  - payload family
  - QoS
  - retain flag
  - authority level
- Validate that schema paths and example payload paths resolve when specified.
- Validate that MQTT-facing behavior remains aligned with:
  - common/docs/architecture/15_interface_matrix.md
  - common/mqtt/publisher_subscriber_matrix_v1_0_0.md
  - common/mqtt/topic_payload_contracts_v1_0_0.md
- Validate topic/payload hardcoding drift where implementation files are in scope.
- Validate that dashboard/governance topics are marked non-authoritative.
- Validate that RPi simulation/fault topics are marked experiment-only unless explicitly allowed otherwise.
- Validate that Class 2 clarification or notification topics do not imply actuator authorization.
- Validate that `clarification_interaction_payload` remains distinct from pure context, validator output, and actuation command payloads.
- Validate that doorbell-related topics do not authorize autonomous doorlock control.
- Produce a machine-readable validation report and a concise human-readable summary.
- Include unit tests for valid registry, missing topic_id, missing publisher/subscriber lists, missing payload family, unresolved schema path, unresolved example payload path, interface-matrix mismatch, topic drift, clarification payload authority escalation, and forbidden authority escalation.
```

---

## Prompt 37. Implement MQTT / Payload Governance Backend Service

```text
Implement a separate MQTT/payload governance backend service.

Target repository areas:
- rpi/code/ as the preferred experiment/governance host
- mac_mini/code/ only if a read-only operational telemetry adapter is required
- integration/tests/ for contract validation tests

Purpose:
- Provide controlled CRUD and validation operations for MQTT topic and payload governance.
- Serve as the backend for a future dashboard UI.
- Keep the dashboard UI separate from the backend logic.

Requirements:
- Provide API endpoints for:
  - list topics
  - get topic detail
  - create draft topic entry
  - update draft topic entry
  - delete draft topic entry
  - validate topic entry
  - list publisher roles
  - add publisher role to topic
  - remove publisher role from topic
  - list subscriber roles
  - add subscriber role to topic
  - remove subscriber role from topic
  - list payload families
  - link payload family to topic
  - link schema path to topic
  - link example payload path to topic
  - validate payload example against referenced schema
  - validate clarification interaction payloads against common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
  - run interface-matrix alignment check
  - run topic/payload hardcoding drift check where implementation files are in scope
  - export proposed registry changes
  - generate a review report
- Support a clear distinction between:
  - draft registry edits,
  - validated proposed changes,
  - and committed repository changes.
- The service must not silently edit canonical policy or schema files.
- The service must not directly modify canonical policies or schemas.
- The service must not directly modify live operational MQTT subscriptions or publishers without explicit deployment workflow approval.
- The service must not publish direct actuation commands.
- The service must not publish actuator or doorlock commands.
- The service must not spoof caregiver approval.
- The service must not dispatch doorlock commands.
- The service must not treat clarification candidate text as Policy Router output, validator approval, actuator authorization, or emergency evidence.
- The service must not convert draft/proposed changes into live operational authority without review.
- Store edit history or change proposals as governance artifacts, not as policy truth.
- Include validation rules for:
  - required topic_id
  - unique topic string or topic pattern
  - valid publisher/subscriber role lists
  - valid payload family
  - schema path existence when required
  - example payload path existence when required
  - clarification interaction schema conformance
  - interface-matrix alignment
  - topic/payload hardcoding drift where applicable
  - forbidden dashboard/control authority escalation
  - forbidden clarification-to-actuation authority escalation
  - forbidden doorlock autonomous Class 1 topic semantics
- Include unit tests and API tests.
```

---

## Prompt 38. Implement MQTT / Payload Governance Dashboard UI

```text
Implement a dashboard UI for MQTT topic and payload governance.

Target repository areas:
- rpi/code/ as the preferred dashboard host
- rpi/docs/ for operation notes
- integration/tests/ for UI/backend contract tests where applicable

Architecture requirement:
- The dashboard UI is only the presentation and user-interaction layer.
- All create, update, delete, validation, and export operations must call the separate MQTT/payload governance backend service.
- The UI must not write directly to registry files.
- The UI must not directly publish MQTT control messages.
- The UI must not directly publish operational control topics.
- The UI must not directly alter canonical policy or schema files.

Required UI capabilities:
- topic registry browser
- topic detail viewer
- create topic draft form
- edit topic draft form
- delete topic draft action with confirmation
- publisher node management UI
- subscriber node management UI
- payload family selector
- schema path selector or resolver
- example payload selector or resolver
- QoS selector
- retain flag selector
- authority level viewer/editor for draft entries
- operational vs experiment-only flag viewer/editor for draft entries
- validation result panel
- clarification interaction payload validation result panel
- interface-matrix alignment result panel
- topic/payload drift warning panel where implemented
- diff/proposed-change preview
- export proposed registry change report
- live or replayed topic traffic viewer when available
- unauthorized topic warning panel
- missing required field warning panel
- Class 2 clarification authority-boundary warning panel
- doorbell/doorlock boundary warning panel

Required safety warnings:
- Highlight when a topic appears to grant dashboard/control authority.
- Highlight when a topic appears to allow unrestricted actuation.
- Highlight when a topic appears to allow doorlock control outside caregiver-mediated/manual-confirmation paths.
- Highlight when a clarification interaction payload appears to contain actuator authorization, emergency trigger authority, validator approval, or doorlock unlock approval.
- Highlight when a payload example omits `environmental_context.doorbell_detected` where context schema validity is required.
- Highlight when doorlock state appears inside current `pure_context_payload.device_states`.

Forbidden UI behavior:
- no direct doorlock command button
- no unrestricted actuator console
- no direct caregiver approval spoofing outside controlled test mode
- no direct Policy Router override
- no direct Deterministic Validator override
- no canonical schema/policy editing
- no direct registry-file editing
- no direct operational control-topic publishing
- no clarification-to-actuation promotion control

Include tests or verification notes for:
- topic list rendering
- topic detail rendering
- create draft flow
- edit draft flow
- delete draft flow
- publisher/subscriber role editing flow
- payload validation result display
- clarification interaction payload validation display
- interface-matrix alignment display
- topic/payload drift warning display where implemented
- Class 2 clarification authority-boundary warning display
- doorbell/doorlock boundary warning display
- UI cannot directly edit registry files
- UI cannot directly publish operational control topics
- UI uses backend API for create/update/delete/validation/export
- UI/backend API failure handling
- UI/backend contract failure handling
- non-authority UI constraints
```

---

## Prompt 39. Implement Payload Example Manager and Validator

```text
Implement a payload example manager and validator for the safe_deferral project.

Target repository areas:
- rpi/code/ if used by governance dashboard/backend
- integration/tests/ for validation tests
- common/payloads/ for reference examples/templates only when intentionally adding new examples

Requirements:
- Load payload examples from:
  - common/payloads/examples/
- Load payload templates from:
  - common/payloads/templates/
- Validate schema-governed examples against the corresponding schema files under common/schemas/.
- Support listing examples by payload family.
- Support viewing payload examples without modifying them.
- Support generating draft payload examples for review.
- Support exporting validation reports.
- Do not silently rewrite payload examples in common/payloads/ without explicit review workflow.
- Enforce current payload boundaries:
  - valid context examples must include environmental_context.doorbell_detected
  - doorbell_detected is visitor-response context only
  - doorbell_detected is not emergency evidence
  - doorbell_detected is not doorlock authorization
  - clarification_interaction_payload is separate from pure_context_payload and class_2_notification_payload
  - clarification_interaction_payload may contain candidate choices, selection result, timeout result, transition_target, and final_safe_outcome
  - clarification_interaction_payload must not contain actuator authorization, emergency trigger authority, validator approval, or doorlock unlock approval
  - doorlock state must not appear in current pure_context_payload.device_states
  - manual approval state must not appear in pure_context_payload
  - ACK state must not appear in pure_context_payload
- Include tests for valid examples, missing doorbell_detected, valid clarification interaction payload, invalid clarification interaction payload with actuator authority, doorlock-in-device-states, unresolved schema path, unresolved example path, and invalid payload family.
```

---

## Prompt 40. Implement Publisher / Subscriber Role Registry Support

```text
Implement publisher/subscriber role registry support for MQTT governance.

Target repository areas:
- rpi/code/ for governance tooling
- integration/tests/ for validation tests
- common/mqtt/ only if adding reviewed reference files

Requirements:
- Maintain or derive a list of known node/service roles such as:
  - mac_mini.policy_router
  - mac_mini.deterministic_validator
  - mac_mini.local_llm_adapter
  - mac_mini.class2_clarification_manager
  - mac_mini.audit_logging_service
  - mac_mini.dispatcher_low_risk_path
  - mac_mini.dispatcher_manual_path
  - mac_mini.caregiver_confirmation_backend
  - rpi.simulation_runtime_controlled_mode
  - rpi.fault_injector_harness
  - rpi.scenario_orchestrator
  - rpi.dashboard_backend
  - rpi.dashboard_frontend
  - rpi.mqtt_payload_governance_backend
  - esp32.button_node
  - esp32.lighting_control_node
  - esp32.environmental_sensor_node
  - esp32.doorbell_context_node
  - esp32.actuator_node
- Validate that topic publishers and subscribers refer to known roles or explicitly marked extension roles.
- Distinguish operational roles from experiment-only roles.
- Distinguish dashboard/gov roles from policy/validator/dispatcher roles.
- Prevent dashboard/gov roles from being assigned direct actuator or caregiver approval authority unless explicitly marked as controlled test-mode roles.
- Prevent Class 2 clarification publisher/subscriber roles from being assigned direct actuator, emergency trigger, validator approval, or doorlock unlock authority.
- Include tests for valid roles, unknown roles, dashboard role assigned to forbidden authority, Class 2 clarification role assigned to forbidden authority, RPi simulation role assigned to operational-only topic, and ESP32 role assigned to policy authority.
```
