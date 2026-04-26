# 09_recommended_next_steps.md

## Recommended Immediate Next Steps

This document defines the recommended immediate next steps for the safe deferral project.

It is intended to guide:
- project bootstrap work
- repository initialization
- frozen asset preparation
- staged implementation readiness
- MQTT topic / payload governance readiness
- dashboard-supported experiment readiness
- vibe-coding startup order

This document does not replace the canonical frozen baseline.  
Shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

Current interface, communication, and payload references:
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`

---

## 1. Confirm the Frozen Reference Baseline Is Complete

Before implementation proceeds further, confirm that the shared frozen assets and shared reference assets under `common/` are complete and treated according to their authority level.

### Priority authority targets
- `common/policies/policy_table_v1_2_0_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json`
- `common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

### Priority communication / payload reference targets
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`
- `common/payloads/examples/`
- `common/payloads/templates/`

### Priority architecture / prompt targets
- `common/docs/architecture/12_prompts.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

### Optional or version-sensitive companion assets
- output profile assets
- auxiliary deployment templates
- reproducibility support assets

### Authority note
- `common/policies/` and `common/schemas/` are policy and validation authority.
- `common/mqtt/` defines communication-contract references.
- `common/payloads/` provides payload examples/templates.
- `common/docs/architecture/15_interface_matrix.md` defines the MQTT-aware interface contract reference.
- MQTT contracts and payload examples must not override canonical policies or schemas.

### Goal
Ensure the shared frozen assets, communication/payload references, MQTT-aware interface matrix, and implementation-generation prompt set form a stable baseline before additional code generation proceeds.

---

## 2. Confirm the Architecture Document Set Is Internally Aligned

The architecture reference documents under `common/docs/architecture/` should be treated as a cross-checked set rather than as isolated notes.

### Priority documents
- installation target classification
- Mac mini build sequence
- deployment structure
- project directory structure
- automation strategy
- implementation plan
- task breakdown
- additional required work
- recommended next steps
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

### Current active interface/figure/payload references
- `common/docs/architecture/15_interface_matrix.md` is the current MQTT-aware interface contract reference.
- `common/docs/architecture/16_system_architecture_figure.md` is the current active system architecture figure interpretation document.
- `common/docs/architecture/17_payload_contract_and_registry.md` is the current active payload boundary and registry interpretation document.

### Superseded active-path note
The following older active paths should not be treated as current active references:
- `common/docs/architecture/24_final_paper_architecture_figure.md`
- `common/docs/architecture/25_payload_contract_and_registry.md`

Historical figure-layout notes have been archived under:
- `common/docs/archive/system_layout_figure_notes/`

### Goal
Provide a stable and internally aligned reference set for implementation planning, repository maintenance, communication-contract governance, payload-boundary enforcement, MQTT-aware interface checking, and vibe-coding prompts.

---

## 3. Keep the Repository Structure and Dependency Manifests Stable

The repository structure should now be maintained as a staged, device-aware layout rather than repeatedly restructured.

### Required top-level areas
- `common/`
- `mac_mini/`
- `rpi/`
- `esp32/`
- `integration/`

### Important `common/` sub-areas
- `common/policies/`
- `common/schemas/`
- `common/mqtt/`
- `common/payloads/`
- `common/docs/`
- `common/terminology/`

### Important integration sub-areas
- `integration/tests/`
- `integration/scenarios/`
- `integration/measurement/`

### Root-level dependency manifests
- `requirements-mac.txt`
- `requirements-rpi.txt`

### Goal
Ensure shared assets, MQTT contracts, payload examples/templates, Mac mini scripts/code, Raspberry Pi dashboard/simulation/governance code, ESP32 scripts/code/firmware, and integration assets remain clearly separated and reproducible.

---

## 4. Keep Install / Configure / Verify Script Sets as the Primary Bring-Up Path

The staged script workflow should remain the primary bring-up path for each layer.

### Required script groups
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/scripts/verify/`
- `rpi/scripts/install/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`
- `esp32/scripts/install/`
- `esp32/scripts/configure/`
- `esp32/scripts/verify/`

### Measurement workflow readiness
- `integration/measurement/`
- optional timing-node support notes
- latency capture references
- reproducible measurement templates

### MQTT / payload governance readiness
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/examples/`
- `common/payloads/templates/`
- future registry/payload validation scripts under `mac_mini/scripts/verify/`, `rpi/scripts/verify/`, or `integration/tests/`
- future governance backend service checks under `rpi/scripts/verify/` or `integration/tests/`
- future governance dashboard UI checks under `rpi/scripts/verify/` or `integration/tests/`
- future topic drift checks under `mac_mini/scripts/verify/`, `rpi/scripts/verify/`, or `integration/tests/`
- future payload example validation checks under `rpi/scripts/verify/` or `integration/tests/`

### Goal
Ensure implementation continues only on top of a reproducible staged bring-up path and a reviewable topic/payload contract baseline.

---

## 5. Maintain the Python Runtime Foundations

The host-side Python runtime foundation should remain aligned with the maintained dependency manifests and installation scripts.

### Immediate actions
- keep Mac mini Python virtual environment and `requirements-mac.txt` aligned
- keep Raspberry Pi Python virtual environment and `requirements-rpi.txt` aligned
- verify runtime package availability after dependency changes
- include registry loading, JSON schema validation, MQTT testing, dashboard runtime, governance backend service, governance dashboard UI, validation report export, and result export dependencies when those components are implemented
- avoid undocumented drift between dependency manifests and install scripts

### Goal
Ensure the host-side runtime foundation remains stable before more hub-side, experiment-side, dashboard-side, and governance-side code is implemented.

---

## 6. Keep the Mac mini Operational Platform Stable

The Mac mini operational platform should now be treated as an actively maintained base rather than a one-time setup target.

### Immediate services
- Home Assistant
- Mosquitto MQTT Broker
- Ollama
- Llama 3.1 model
- SQLite
- notification path

### Immediate checks
- broker reachability for Raspberry Pi and ESP32 on the trusted LAN
- SQLite WAL and single-writer assumptions
- deployed runtime asset consistency with `common/`
- MQTT topic registry readability when deployed or synchronized
- payload example/schema-validation readiness when implemented
- environment-variable and secret handling hygiene

### Goal
Keep the Mac mini in a service-ready operational state before expanding hub-side implementation.

---

## 7. Begin or Continue Hub-side Implementation in Dependency Order

Once the frozen assets, architecture documents, repository layout, script layers, runtime foundation, and core services are stable, hub-side implementation should proceed in dependency order.

### First implementation targets
1. Policy Router
2. Deterministic Validator
3. Context-Integrity Safe Deferral Handler
4. Audit Logging Service
5. Outbound Notification Interface
6. Caregiver Confirmation Backend
7. MQTT Topic Registry Loader / Contract Checker
8. Payload Validation Helper

### Hardcoding boundary
Runtime apps should not hardcode MQTT topic strings or payload contracts where registry lookup is practical.

Apps should prefer:
- topic registry lookups,
- stable topic IDs or topic keys when available,
- schema paths from registry/configuration,
- payload examples/templates from `common/payloads/`,
- and payload-boundary rules from `common/docs/architecture/17_payload_contract_and_registry.md`.

### Goal
Ensure implementation proceeds on top of a stable, reproducible, policy-first, registry-aware foundation.

---

## 8. Treat ESP32 Bring-Up as Complete Enough to Move to Code Generation

The project is no longer at the stage where ESP32 is only a future documentation concern.

The following are already in place conceptually and should now serve as the base for code generation:
- cross-platform install scaffolding
- cross-platform configure scaffolding
- cross-platform verify scaffolding
- ESP32 execution-order documentation
- firmware-generation prompts in `12_prompts.md`
- MQTT topic/payload contract assumptions under `common/mqtt/`

### Immediate next ESP32 steps
- generate the minimal ESP-IDF template project using the maintained prompt
- validate that the generated template fits the current `esp32/scripts/configure/` and `esp32/scripts/verify/` flow
- then generate current canonical node firmware in order:
  1. button input node
  2. lighting control node
  3. representative environmental sensing node
  4. doorbell / visitor-arrival context node where visitor-response validation is included

### Optional follow-on targets
- gas sensor node
- fire detection sensor node
- fall-detection interface node
- warning / doorlock interface node

### Boundary notes
- Doorbell / visitor-arrival context must be represented as `environmental_context.doorbell_detected`.
- `doorbell_detected` is not emergency evidence and does not authorize doorlock control.
- Warning / doorlock interface nodes must not locally reinterpret doorlock as autonomous Class 1 authority.

### Goal
Move from ESP32 development-environment readiness to actual bounded node implementation without bypassing the current scaffolding or MQTT/payload contract assumptions.

---

## 9. Keep the Raspberry Pi Evaluation Path Bounded and Reproducible

The Raspberry Pi path should remain focused on dashboard-supported simulation, fault injection, orchestration, replay, progress/result publication, governance support, and closed-loop evaluation.

### Immediate targets
- experiment and monitoring dashboard
- MQTT/payload governance backend service
- governance dashboard UI as presentation layer
- topic/payload contract validation utility
- payload example manager / validator
- publisher/subscriber role manager
- multi-node virtual sensor/state runtime
- virtual `doorbell_detected` visitor-response context runtime
- virtual emergency sensor runtime
- fault injection harness
- repeatable scenario orchestrator
- scenario replay support
- progress/status publication
- result artifact export
- closed-loop automated verification support
- topic/payload contract validation
- canonical policy/schema/rules consistency checks
- canonical emergency trigger alignment for `E001`~`E005`
- visitor-response and doorlock-sensitive evaluation scenarios

### Boundary notes
- Raspberry Pi dashboard and governance tooling are non-authoritative.
- Raspberry Pi must not replace Mac mini policy routing, deterministic validation, caregiver approval, or actuation dispatch authority.
- Simulation and fault traffic should enter through the same MQTT input plane used by operational inputs.
- Dashboard observation payloads are visibility artifacts, not policy truth.
- Governance dashboard UI must remain separated from the governance backend service.
- Governance dashboard UI must not directly edit registry files or directly publish operational control topics.
- Governance backend must not directly modify canonical policies/schemas.
- Governance tooling must not publish actuator or doorlock commands.
- `doorbell_detected=true` supports visitor-response interpretation but does not authorize autonomous doorlock control.

### Goal
Ensure the evaluation path supports scalable dashboard-assisted fault-injection and visitor-response experiments without becoming part of the operational decision path.

---

## 10. Establish MQTT / Payload Governance Before Broad App Implementation

Before broad runtime app, dashboard app, or experiment-tool implementation proceeds, establish a stable enough MQTT/payload governance baseline.

### Immediate targets
- ensure `common/mqtt/topic_registry_v1_0_0.json` exists and is readable
- ensure publisher/subscriber matrix exists and is consistent enough for current implementation planning
- ensure topic-to-payload contract references exist
- ensure payload examples/templates exist under `common/payloads/`
- add stable `topic_id` or equivalent topic key fields before runtime apps depend heavily on the registry
- define a `TopicRegistryLoader` pattern for runtime apps and dashboard apps
- define a payload validation helper pattern for schema-governed examples
- validate payload examples against schemas where applicable
- verify required `environmental_context.doorbell_detected` in valid context examples
- verify doorlock state is not accepted inside current `pure_context_payload.device_states`
- verify governance backend/UI separation
- verify governance dashboard UI cannot directly edit registry files
- verify governance backend cannot directly modify canonical policies/schemas
- verify governance tooling cannot publish actuator or doorlock commands
- verify topic/payload hardcoding drift checks where implemented
- keep governance dashboard UI and governance backend non-authoritative

### App implementation rule
Apps should not hardcode MQTT topic strings, schema paths, or payload contracts where registry/configuration lookup is practical.

### Governance backend/UI rule
A future MQTT/payload governance backend may inspect, validate, draft, export, and report on topic/payload coverage.

The governance dashboard UI is a presentation and interaction layer that should call the backend service for create/update/delete/validation/export operations.

The governance backend and dashboard UI must not:
- directly modify canonical policies or schemas,
- directly edit registry files through the UI,
- override Policy Router decisions,
- override Deterministic Validator decisions,
- spoof caregiver approval outside controlled test mode,
- publish unrestricted actuation commands,
- publish actuator or doorlock commands,
- dispatch doorlock commands,
- convert proposed registry changes into live operational authority without review,
- or treat dashboard observation as policy truth.

### Goal
Reduce downstream implementation churn by making topic and payload changes registry-driven rather than hardcoded across apps, while keeping governance tooling separate from operational authority.

---

## 11. Keep Timing and Measurement as an Optional Evaluation Track

When the target experiment package includes class-wise latency measurement, keep the timing infrastructure path explicit and separate.

### Immediate targets
- optional STM32 timing node or equivalent dedicated measurement node
- out-of-band class-wise latency capture notes
- measurement result templates for reproducible evaluation
- timing capture path validation

### Goal
Ensure latency evaluation remains trustworthy and reproducible without becoming part of the operational decision path.

---

## Final Principle

Do not begin broad implementation expansion unless:
- shared frozen assets are committed and stable
- shared communication and payload references are stable enough for the current implementation stage
- architecture documents are aligned
- repository structure is stable
- install/configure/verify scripts remain in place as the primary bring-up path
- the Mac mini operational platform is ready
- core services pass independent verification
- root-level dependency manifests remain aligned with maintained runtime assumptions
- MQTT topic registry and payload references are available for registry-based app implementation
- `common/docs/architecture/15_interface_matrix.md` alignment passes
- apps do not hardcode topic/payload contracts where registry lookup is practical
- topic/payload hardcoding drift checks pass where implemented
- governance backend/UI separation is verified
- governance tooling cannot create operational authority
- dashboard/governance tools remain non-authoritative
- `doorbell_detected` is treated as required visitor-response context, not emergency evidence or doorlock authorization
- doorlock state is not inserted into current `pure_context_payload.device_states`
- ESP32 bring-up is stable enough to support prompt-driven code generation
- Raspberry Pi evaluation assumptions remain bounded to dashboard/simulation/fault/evaluation/governance-support tasks
- measurement infrastructure assumptions are documented when out-of-band class-wise latency evaluation is part of the target experiment package
- deployment-local runtime files and synchronized copies are prevented from overriding canonical frozen policy truth
