# 02_mac_mini_build_sequence.md

## Mac mini Build Sequence

This document defines the recommended build and bring-up sequence for the Mac mini operational hub in the safe deferral system.

It is intended to be used as a reference for:
- system setup
- implementation planning
- repository organization
- vibe-coding prompts and agent guidance

---

## Phase 0. Pre-build Freeze

Before installing or implementing anything, freeze the core shared artifacts in the repository.

### Required frozen assets
1. Routing policy table
2. Low-risk action policy
3. Fault injection rules
4. Input/output JSON schemas
5. Output profile
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
- `common/policies/low_risk_actions_v1_0_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_0_0.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

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

### Repository locations
- `mac_mini/scripts/verify/`

### Verification principle
Each service should pass independently before integration begins.

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

---

## Phase 7. Integration Testing with Physical Nodes

Connect and validate operational flows with real or semi-real physical nodes.

1. Connect ESP32 button node
2. Connect ESP32 temperature / humidity sensor node
3. Connect ESP32 gas sensor node
4. Connect ESP32 fire detection sensor node
5. Connect ESP32 lighting control node
6. Connect ESP32 doorlock or warning interface node
7. Validate end-to-end Class 0 / Class 1 / Class 2 behavior
8. Validate safe deferral behavior under incomplete or conflicting context
9. Validate bounded physical input/output behavior without bypassing policy control

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

---

## Architectural Summary

- The **Mac mini** is the primary operational hub.
- The **ESP32** is the embedded physical node layer for bounded input, sensing, and actuator/warning interfacing where used.
- The **Raspberry Pi 5** is the scalable simulation and experiment orchestration node.
- **STM32 timing nodes or equivalent dedicated measurement nodes** may be used for out-of-band class-wise latency measurement.
- Shared frozen assets are maintained under **`common/`**.
- Hub-side setup, configuration, verification, and future code are maintained under **`mac_mini/`**.
- Embedded device firmware and device-specific implementation assets are maintained under **`esp32/`**.
- Simulation-side setup, configuration, verification, and future code are maintained under **`rpi/`**.
- End-to-end validation and experiment scenarios are maintained under **`integration/`**.