# 02_mac_mini_build_sequence.md

## Mac mini Build Sequence

This document defines the recommended build and bring-up sequence for the Mac mini operational hub in the safe deferral system.

It is intended to be used as a reference for:
- system setup
- implementation planning
- repository organization
- deployment sequencing
- vibe-coding prompts and agent guidance

This document assumes that the Mac mini is the **canonical operational hub** of the system and that shared frozen assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

---

## Phase 0. Pre-build Freeze

Before installing or implementing anything, freeze the core shared artifacts in the repository.

### Required frozen assets
1. Routing policy table
2. Low-risk action policy
3. Fault injection rules
4. Input/output JSON schemas
5. Class 2 notification payload schema
6. Canonical terminology
7. Environment variable templates
8. Verification and installation script set

### Repository locations
- `common/policies/`
- `common/schemas/`
- `common/docs/`
- `common/terminology/`

### Representative frozen assets
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

### Optional or version-sensitive companion assets
- output profile assets, if used in the current implementation baseline
- host-local configuration templates
- installation/configuration/verification script bundles

### Freeze principle
All hub-side implementation must be derived from the frozen shared asset set.  
The Mac mini must consume deployed runtime copies of these assets rather than inventing local policy truth.

---

## Phase 1. Base System Preparation

Prepare the Mac mini as the primary operational hub.

1. Update macOS
2. Install developer tools
3. Create project workspace directories
4. Clone and prepare the Git repository
5. Prepare runtime environment templates and deployment targets

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

### Phase principle
This phase prepares the host boundary, directory layout, and deployment surfaces, but does not yet establish policy truth locally.

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

### Repository locations
- `mac_mini/scripts/install/`
- `mac_mini/code/`

### Phase principle
The Python runtime must be reproducible and sufficient for:
- hub-side control logic
- policy/schema validation
- outbound notification integration
- audit logging integration
- local verification tasks

---

## Phase 4. Configuration Deployment

Deploy configuration assets and runtime settings onto the Mac mini.

1. Apply Home Assistant configuration
2. Apply Mosquitto configuration
3. Configure Ollama model availability
4. Deploy frozen policy and schema files
5. Configure Telegram or mock notification settings
6. Configure logging paths and SQLite DB schema
7. Write runtime `.env` files

### Repository locations
- source of truth: `common/`
- deployment scripts: `mac_mini/scripts/configure/`

### Deployment principle
The Git repository stores the frozen shared assets.  
The Mac mini receives deployed runtime copies for execution.

### Configuration separation principle
- frozen policy/schema/terminology assets come from `common/`
- host-local secrets, runtime `.env`, and machine-specific files are deployment-local configuration
- deployment-local configuration must not be treated as canonical policy truth

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

### Repository locations
- `mac_mini/scripts/verify/`

### Verification principle
Each service should pass independently before integration begins.

### Recommended verification outputs
- service health summary
- asset deployment summary
- configuration validation summary
- version alignment summary

---

## Phase 6. Application Development

Develop the hub-side applications in dependency order.

1. Policy Router
2. Deterministic Validator
3. Context-Integrity Safe Deferral Handler
4. Audit Logging Service integration
5. Outbound Notification Interface
6. Caregiver Confirmation Backend
7. Hub-side integration tests

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

The LLM must not become an autonomous execution authority.  
The deterministic validator remains the approval authority before any hub-side actuation dispatch.

---

## Phase 7. Integration Testing with Physical Nodes

Connect and validate operational flows with real or semi-real physical nodes.

### Current canonical physical-node validation targets
1. Connect ESP32 button node
2. Connect ESP32 lighting control node
3. Connect representative environmental sensing node used in the current canonical validation baseline
4. Validate end-to-end Class 0 / Class 1 / Class 2 behavior
5. Validate safe deferral behavior under incomplete or conflicting context
6. Validate bounded physical input/output behavior without bypassing policy control

### Optional experimental physical-node targets
- ESP32 gas sensor node
- ESP32 fire detection sensor node
- ESP32 fall-detection interface node

### Planned extension targets
- ESP32 doorlock or warning interface node beyond the current canonical low-risk action scope

### Canonical emergency alignment
Physical-node validation should remain consistent with the canonical emergency trigger family defined by policy:

- `E001`: temperature threshold crossing
- `E002`: emergency triple-hit input
- `E003`: smoke detected
- `E004`: gas detected
- `E005`: fall detected

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

Extend the operational hub with Raspberry Pi-based simulation, fault injection, and experiment orchestration tooling.

1. Connect Raspberry Pi 5 as simulation and evaluation node
2. Deploy multi-node virtual sensor/state runtime
3. Deploy virtual emergency sensors
4. Deploy fault injector harness
5. Run stale / missing / conflict / fail-safe experiments
6. Run closed-loop automated verification
7. Prepare optional STM32 timing node or equivalent dedicated timing node
8. Run out-of-band class-wise latency measurement
9. Run scalable routing, safety, latency, and fault-handling experiments

### Phase intent
This phase corresponds to the **virtual-node evaluation and experimental validation layer** of the project.  
It is intended to support repeatable large-scale experiments that would be impractical with only physical ESP32 nodes.

### Role separation
- **Mac mini**: operational hub
- **ESP32**: bounded physical node layer
- **Raspberry Pi 5**: multi-node simulation, fault injection, and closed-loop evaluation node
- **STM32 timing node or equivalent**: optional out-of-band latency measurement infrastructure

### Repository locations
- `rpi/scripts/install/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`
- `rpi/code/`
- `integration/scenarios/`
- `integration/tests/`

### Evaluation principle
The Raspberry Pi 5 extends evaluation capacity, but it does not redefine canonical operational policy.  
The operational hub remains the Mac mini.

---

## Architectural Summary

- The **Mac mini** is the primary operational hub.
- The **ESP32** is the embedded physical node layer for bounded input, sensing, and actuator/warning interfacing within the applicable scope.
- The **Raspberry Pi 5** is the scalable simulation and experiment orchestration node.
- **STM32 timing nodes or equivalent dedicated measurement nodes** may be used for out-of-band class-wise latency measurement.
- Shared frozen assets are maintained under **`common/`**.
- Hub-side setup, configuration, verification, and future code are maintained under **`mac_mini/`**.
- Embedded device firmware and device-specific implementation assets are maintained under **`esp32/`**.
- Simulation-side setup, configuration, verification, and future code are maintained under **`rpi/`**.
- End-to-end validation and experiment scenarios are maintained under **`integration/`**.

---

## Final Bring-up Principle

The Mac mini build sequence should preserve the following order of truth:

1. freeze canonical shared assets
2. prepare host runtime
3. install core services
4. deploy canonical runtime copies
5. verify services and asset alignment
6. develop bounded hub-side applications
7. validate physical-node integration
8. extend evaluation through virtual-node and timing infrastructure

At no point should deployment-local convenience override the canonical frozen policy/schema baseline.
