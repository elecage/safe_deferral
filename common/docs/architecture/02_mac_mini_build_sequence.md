# 02_mac_mini_build_sequence.md

## Mac mini Build Sequence

This document defines the recommended build and bring-up sequence for the Mac mini operational hub in the safe deferral system.

It is intended to be used as a reference for:
- system setup
- implementation planning
- repository organization
- deployment sequencing
- MQTT/topic/payload reference deployment
- registry-aware hub-side implementation
- vibe-coding prompts and agent guidance

This document assumes that the Mac mini is the **canonical operational hub** of the system and that shared frozen assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

This document should be read together with:
- `common/docs/architecture/01_installation_target_classification.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`

---

## Phase 0. Pre-build Freeze

Before installing or implementing anything, freeze the core shared artifacts and shared communication/payload references in the repository.

### Required frozen authority assets
1. Routing policy table
2. Low-risk action policy
3. Fault injection rules
4. Input/output JSON schemas
5. Class 2 notification payload schema
6. Canonical terminology
7. Environment variable templates
8. Verification and installation script set

### Required shared communication / payload references
1. MQTT topic registry
2. Publisher/subscriber matrix
3. Topic-to-payload contract references
4. Payload examples/templates
5. MQTT-aware interface matrix
6. Active system architecture figure interpretation
7. Payload-boundary and registry interpretation

### Repository locations
- `common/policies/`
- `common/schemas/`
- `common/mqtt/`
- `common/payloads/`
- `common/docs/`
- `common/terminology/`

### Representative frozen authority assets
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

### Representative shared reference assets
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`
- `common/payloads/examples/`
- `common/payloads/templates/`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

### Optional or version-sensitive companion assets
- output profile assets, if used in the current implementation baseline
- host-local configuration templates
- installation/configuration/verification script bundles

### Freeze principle
All hub-side implementation must be derived from the frozen shared asset set.  
The Mac mini must consume deployed runtime copies of these assets rather than inventing local policy truth.

`common/mqtt/` and `common/payloads/` are shared reference layers, not policy/schema authority. They may guide runtime topic lookup, payload validation, dashboard tooling, experiment fixtures, and governance checks, but they do not override frozen policies or schemas.

---

## Phase 1. Base System Preparation

Prepare the Mac mini as the primary operational hub.

1. Update macOS
2. Install developer tools
3. Create project workspace directories
4. Clone and prepare the Git repository
5. Prepare runtime environment templates and deployment targets
6. Prepare MQTT topic registry deployment/reference path
7. Prepare payload examples/templates deployment/reference path
8. Prepare runtime mount, copy, symlink, or path assumptions for registry/payload references

### Repository locations
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/runtime/`

### Representative tasks
- prepare workspace
- prepare `.env` structure
- prepare runtime directories
- prepare container/runtime templates
- prepare policy deployment targets
- prepare registry/payload reference targets
- prepare read-only or reviewed deployment strategy for shared reference assets

### Phase principle
This phase prepares the host boundary, directory layout, and deployment surfaces, but does not yet establish policy truth locally.

Registry/payload paths prepared during this phase are references to repository-managed assets or deployed copies. They must not become independent local communication or policy truth.

---

## Phase 2. System Service Installation

Install the core Mac mini runtime services.

1. Home Assistant
2. Mosquitto MQTT Broker
3. Ollama
4. Pull Llama 3.1 model
5. SQLite initialization
6. Optional local TTS runtime

### Operational principle
All core operational services are hosted on the Mac mini.

Mosquitto configuration should later align listener, namespace, authentication, and topic ACL assumptions with:
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`

Dashboard/governance topics must not be granted operational control authority through broker configuration or ACL shortcuts.

### Repository locations
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/runtime/`

### Expected service boundary
The Mac mini hosts the operational service plane.  
Raspberry Pi 5 and timing nodes must not replace this hub role.

---

## Phase 3. Python Runtime Preparation

Prepare the Python execution environment for hub-side applications.

1. Create Python virtual environment
2. Install base dependencies
3. Install runtime libraries
4. Verify package availability
5. Freeze dependency versions if needed

### Representative dependencies
- FastAPI
- Pydantic
- paho-mqtt
- python-telegram-bot
- pytest
- uvicorn
- jsonschema
- MQTT/topic registry helper dependencies
- payload validation helper dependencies
- optional registry/report export dependencies

### Repository locations
- `mac_mini/scripts/install/`
- `mac_mini/code/`

### Phase principle
The Python runtime must be reproducible and sufficient for:
- hub-side control logic
- policy/schema validation
- outbound notification integration
- audit logging integration
- registry-based topic lookup
- payload-boundary validation
- topic/payload contract checking
- local verification tasks

---

## Phase 4. Configuration Deployment

Deploy configuration assets and runtime settings onto the Mac mini.

1. Apply Home Assistant configuration
2. Apply Mosquitto configuration
3. Configure Ollama model availability
4. Deploy frozen policy and schema files
5. Deploy or reference MQTT topic registry files
6. Deploy or reference payload examples/templates when needed
7. Configure Telegram or mock notification settings
8. Configure logging paths and SQLite DB schema
9. Write runtime `.env` files including registry/payload path variables
10. Align Mosquitto topic namespace / ACL assumptions with registry and publisher/subscriber matrix

### Repository locations
- source of truth: `common/`
- deployment scripts: `mac_mini/scripts/configure/`

### Deployment principle
The Git repository stores the frozen shared assets and shared communication/payload references.  
The Mac mini receives deployed runtime copies or path references for execution and validation support.

### Configuration separation principle
- frozen policy/schema/terminology assets come from `common/`
- MQTT registry and payload examples/templates come from `common/mqtt/` and `common/payloads/` as reference layers
- host-local secrets, runtime `.env`, and machine-specific files are deployment-local configuration
- deployment-local configuration must not be treated as canonical policy truth
- registry/payload deployment or reference paths must not redefine policy/schema authority

---

## Phase 5. Service Verification

Verify each service and runtime dependency independently before application development proceeds.

1. Home Assistant starts correctly
2. Mosquitto publish/subscribe works
3. Ollama returns model output
4. SQLite read/write works
5. Notification channel works
6. Environment variables and runtime assets are valid
7. Base service health checks pass
8. Deployed frozen assets exist and match the expected canonical version set
9. Policy table, low-risk action catalog, validator schema, and fault rules are mutually readable and version-consistent
10. Deployment-local configuration is present without overriding canonical frozen asset semantics
11. MQTT topic registry is readable
12. Publisher/subscriber matrix is consistent with the topic registry
13. Topic-to-payload contracts resolve
14. Schema-governed payload examples validate where applicable
15. Dashboard/governance topics remain non-authoritative
16. Registry/payload reference paths do not silently redefine policy/schema authority

### Repository locations
- `mac_mini/scripts/verify/`

### Verification principle
Each service should pass independently before integration begins.

MQTT/payload verification checks communication-contract and payload-boundary readiness. They do not convert reference assets into policy authority.

### Recommended verification outputs
- service health summary
- asset deployment summary
- configuration validation summary
- version alignment summary
- topic registry validation summary
- publisher/subscriber matrix validation summary
- payload example validation summary

---

## Phase 6. Application Development

Develop the hub-side applications in dependency order.

1. Policy Router
2. Deterministic Validator
3. Context-Integrity Safe Deferral Handler
4. Audit Logging Service integration
5. Outbound Notification Interface
6. Caregiver Confirmation Backend
7. MQTT Topic Registry Loader / Contract Checker
8. Payload Validation Helper
9. Hub-side integration tests

### Canonical terminology
The correct term is:

**context-integrity-based safe deferral stage**

The previous label **iCR-based safe deferral stage** is deprecated.

### Repository locations
- `mac_mini/code/`

### Development principle
Hub-side application development must remain bounded by:
- canonical policy table
- canonical low-risk action catalog
- canonical schemas
- canonical escalation semantics
- registry-aware topic lookup where practical
- payload-boundary validation where practical
- MQTT/payload contract references where practical

Hub-side apps should not hardcode MQTT topic strings or payload contracts where registry lookup is practical.

Hub-side context models and adapters must include `environmental_context.doorbell_detected` as a required field. Non-visitor scenarios should default it to `false`; visitor-response scenarios may set it to `true`.

The LLM must not become an autonomous execution authority.  
The deterministic validator remains the approval authority before any hub-side actuation dispatch.

`doorbell_detected=true` may support visitor-response interpretation, but it must not authorize autonomous doorlock control. Doorlock-related sensitive actuation must remain outside the Class 1 validator executable payload and route to Class 2 escalation or a separately governed manual confirmation path unless future frozen policy/schema revisions explicitly change this boundary.

Registry loader and payload validation helper components support communication consistency and payload-boundary checks. They do not create policy, schema, validator, caregiver approval, audit, actuator, or doorlock execution authority.

---

## Phase 7. Integration Testing with Physical Nodes

Connect and validate operational flows with real or semi-real physical nodes.

### Current canonical physical-node validation targets
1. Connect ESP32 button node
2. Connect ESP32 lighting control node
3. Connect representative environmental sensing node used in the current canonical validation baseline
4. Connect ESP32 doorbell / visitor-arrival context node where visitor-response or doorlock-sensitive validation is included
5. Validate end-to-end Class 0 / Class 1 / Class 2 behavior
6. Validate safe deferral behavior under incomplete or conflicting context
7. Validate bounded physical input/output behavior without bypassing policy control

### Optional experimental physical-node targets
- ESP32 gas sensor node
- ESP32 fire detection sensor node
- ESP32 fall-detection interface node

### Planned extension targets
- ESP32 doorlock or warning interface node beyond the current canonical low-risk action scope; doorlock must remain caregiver-mediated or manually governed unless future frozen policy/schema revisions explicitly promote it

### Canonical emergency alignment
Physical-node validation should remain consistent with the canonical emergency trigger family defined by policy:

- `E001`: temperature threshold crossing
- `E002`: emergency triple-hit input
- `E003`: smoke detected
- `E004`: gas detected
- `E005`: fall detected

`doorbell_detected` is not a current emergency trigger. It is visitor-response context and must not be interpreted as Class 0 emergency evidence or doorlock execution authority.

### MQTT/payload alignment
Physical-node integration should remain aligned with:

- `common/mqtt/topic_registry_v1_0_0.json`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

ESP32 firmware and test harnesses should avoid silently inventing topic strings or payload contracts that conflict with the registry and payload-boundary documents.

### Phase intent
This phase corresponds to the **physical-node validation layer** of the project.  
It is intended to verify that real bounded input and output paths behave correctly under the operational hub architecture.

### Repository locations
- `integration/tests/`
- `integration/scenarios/`
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

---

## Phase 8. Evaluation Extension with Virtual Nodes and Timing Infrastructure

Extend the operational hub with Raspberry Pi-based simulation, fault injection, experiment dashboard, MQTT/payload governance support, and experiment orchestration tooling.

1. Connect Raspberry Pi 5 as simulation, dashboard, orchestration, and evaluation node
2. Deploy multi-node virtual sensor/state runtime
3. Deploy virtual `doorbell_detected` visitor-response context generation when required for visitor-response or doorlock-sensitive experiments
4. Deploy virtual emergency sensors
5. Deploy fault injector harness
6. Deploy the Raspberry Pi 5 experiment and monitoring dashboard for scenario selection, node readiness, progress visualization, result summaries, and CSV/graph export
7. Deploy MQTT/payload governance backend service
8. Deploy governance dashboard UI
9. Deploy topic/payload contract validation utilities
10. Deploy payload example validator
11. Deploy publisher/subscriber role review utilities
12. Run stale / missing / conflict / fail-safe experiments
13. Run visitor-response and doorlock-sensitive evaluation scenarios using `doorbell_detected`, autonomous-unlock-blocked checks, caregiver escalation state, manual approval state, ACK state, and audit completeness
14. Run closed-loop automated verification
15. Prepare optional STM32 timing node or equivalent dedicated timing node
16. Run out-of-band class-wise latency measurement
17. Run scalable routing, safety, latency, and fault-handling experiments

### Phase intent
This phase corresponds to the **virtual-node evaluation and experimental validation layer** of the project.  
It is intended to support repeatable large-scale experiments that would be impractical with only physical ESP32 nodes.

### Role separation
- **Mac mini**: operational hub
- **ESP32**: bounded physical node layer
- **Raspberry Pi 5**: experiment dashboard, multi-node simulation, fault injection, scenario orchestration, replay, closed-loop evaluation, progress/status publication, result artifact generation, and non-authoritative MQTT/payload governance support
- **STM32 timing node or equivalent**: optional out-of-band latency measurement infrastructure

### Repository locations
- `rpi/scripts/install/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`
- `rpi/code/`
- `integration/scenarios/`
- `integration/tests/`
- `common/mqtt/`
- `common/payloads/`

### Evaluation principle
The Raspberry Pi 5 extends evaluation capacity, but it does not redefine canonical operational policy.  
The operational hub remains the Mac mini.

The Raspberry Pi 5 dashboard and orchestration layers may visualize visitor-response or doorlock-sensitive experiment state, but they must not bypass policy routing, deterministic validation, caregiver approval, ACK verification, or audit logging.

The Raspberry Pi 5 governance backend and governance dashboard may inspect, validate, draft, and report MQTT/payload changes, but they must not directly edit canonical policy/schema authority, publish actuator commands, spoof caregiver approval, or create doorlock execution authority.

---

## Architectural Summary

- The **Mac mini** is the primary operational hub.
- The **ESP32** is the embedded physical node layer for bounded input, sensing, visitor-response context generation, and actuator/warning interfacing within the applicable scope.
- The **Raspberry Pi 5** is the scalable simulation, experiment dashboard, scenario orchestration, fault injection, replay, result artifact generation, and non-authoritative MQTT/payload governance support node.
- **STM32 timing nodes or equivalent dedicated measurement nodes** may be used for out-of-band class-wise latency measurement.
- Shared frozen authority assets are maintained under **`common/policies/`**, **`common/schemas/`**, and **`common/terminology/`**.
- Shared MQTT contracts are maintained under **`common/mqtt/`**.
- Shared payload examples/templates are maintained under **`common/payloads/`**.
- Hub-side setup, configuration, verification, and future code are maintained under **`mac_mini/`**.
- Embedded device firmware and device-specific implementation assets are maintained under **`esp32/`**.
- Simulation-side setup, configuration, verification, dashboard, governance support, and future code are maintained under **`rpi/`**.
- End-to-end validation, topic/payload validation, and experiment scenarios are maintained under **`integration/`**.

---

## Final Bring-up Principle

The Mac mini build sequence should preserve the following order of truth:

1. freeze canonical shared authority assets and shared communication/payload references
2. prepare host runtime
3. install core services
4. deploy canonical runtime copies and registry/payload references
5. verify services and asset alignment
6. verify MQTT/payload contract alignment
7. develop bounded hub-side applications
8. validate physical-node integration
9. extend evaluation through virtual-node, dashboard, governance, orchestration, and timing infrastructure

At no point should deployment-local convenience override the canonical frozen policy/schema baseline or convert MQTT/payload reference assets into operational authority.
