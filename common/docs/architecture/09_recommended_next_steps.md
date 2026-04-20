# 09_recommended_next_steps.md

## Recommended Immediate Next Steps

This document defines the recommended immediate next steps for the safe deferral project.

It is intended to guide:
- project bootstrap work
- repository initialization
- frozen asset preparation
- staged implementation readiness
- vibe-coding startup order

---

## 1. Finalize and Commit Shared Frozen Assets

Before implementation begins, complete and commit the shared frozen assets under `common/`.

### Priority targets
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_0_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_0_0.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

### Goal
Ensure the shared frozen assets become the single source of truth before code generation or runtime implementation proceeds.

---

## 2. Finalize Core Architecture Documents

Prepare the architecture reference documents under `common/docs/architecture/`.

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

### Goal
Provide a stable reference set for implementation planning and vibe-coding prompts.

---

## 3. Stabilize Repository Structure

Prepare the repository structure so implementation can proceed in a device-aware and experiment-aware way.

### Required top-level areas
- `common/`
- `mac_mini/`
- `rpi/`
- `esp32/`
- `integration/`

### Important integration sub-areas
- `integration/tests/`
- `integration/scenarios/`
- `integration/measurement/`

### Goal
Ensure shared assets, Mac mini scripts/code, Raspberry Pi scripts/code, ESP32 embedded assets, and integration assets including measurement support are clearly separated.

---

## 4. Prepare Install / Configure / Verify Script Sets

Complete and organize the staged shell-script workflow for Mac mini and Raspberry Pi, and make the embedded workflow explicit for ESP32-based nodes.

### Required script groups
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/scripts/verify/`
- `rpi/scripts/install/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`

### Embedded workflow readiness
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

### Measurement workflow readiness
- `integration/measurement/`
- optional timing-node support notes
- latency capture references
- reproducible measurement templates

### Goal
Ensure implementation begins only after the setup, configuration, validation, embedded-node workflow assumptions, and optional timing/measurement workflow assumptions are reproducible.

---

## 5. Prepare the Python Runtime Environment

Create the Python runtime foundation for implementation.

### Immediate actions
- create Python virtual environments
- install base dependencies
- verify runtime package availability
- align dependency setup with installation scripts

### Goal
Ensure the runtime foundation is stable before hub-side code is implemented.

---

## 6. Prepare the Mac mini Operational Platform

Install and configure the core Mac mini services.

### Immediate services
- Home Assistant
- Mosquitto MQTT Broker
- Ollama
- Llama 3.1 model
- SQLite
- optional local TTS runtime

### Goal
Bring the Mac mini to a service-ready operational state.

---

## 7. Verify Each Core Service Independently

Before implementation begins, confirm that the installed and configured services work in isolation.

### Required checks
- Home Assistant starts correctly
- Mosquitto pub/sub works
- Ollama inference returns expected output
- SQLite read/write and WAL mode work
- notification path works
- environment variables and runtime assets validate correctly
- out-of-band latency measurement support path validates correctly when used

### Goal
Avoid starting code implementation on top of an unstable runtime base.

---

## 8. Begin Hub-side Implementation Only After the Above Is Stable

Once the frozen assets, architecture documents, repository layout, script layers, runtime foundation, and core services are stable, begin implementation in dependency order.

### First implementation targets
1. Policy Router
2. Deterministic Validator
3. Context-Integrity Safe Deferral Handler
4. Audit Logging Service
5. Outbound Notification Interface
6. Caregiver Confirmation Backend

### Goal
Ensure implementation proceeds on top of a stable, reproducible, policy-first foundation.

---

## 9. Prepare the Embedded Node Implementation Path

When the target prototype includes physical bounded nodes, prepare the ESP32 implementation path explicitly.

### Immediate targets
- bounded button node firmware
- temperature / humidity sensor node firmware when physical sensing is used
- gas sensor node firmware when physical sensing is used
- fire detection sensor node firmware when physical sensing is used
- lighting control node firmware when physical output is used
- doorlock or warning interface firmware when physical output is used
- broker connection assumptions
- topic namespace and device identity conventions
- firmware build, flash, and reset workflow notes

### Goal
Ensure the embedded node layer can be integrated without bypassing policy control, auditability, or bounded interaction assumptions.

---

## 10. Prepare the Simulation and Measurement Evaluation Path

When the target experiment package includes large-scale virtual-node evaluation or class-wise latency measurement, prepare the Raspberry Pi and timing infrastructure path explicitly.

### Immediate targets
- multi-node virtual sensor/state runtime
- virtual emergency sensor runtime
- fault injection harness
- repeatable scenario orchestration
- closed-loop automated verification support
- optional STM32 timing node or equivalent dedicated measurement node
- out-of-band class-wise latency capture notes
- measurement result templates for reproducible evaluation

### Goal
Ensure the evaluation path supports scalable fault-injection experiments and trustworthy latency measurement without becoming part of the operational decision path.

---

## Final Principle

Do not begin full implementation until:
- shared frozen assets are committed
- architecture documents are aligned
- repository structure is stable
- install/configure/verify scripts are in place
- the Mac mini operational platform is ready
- core services pass independent verification
- embedded node assumptions are documented when ESP32 is part of the prototype
- measurement infrastructure assumptions are documented when out-of-band class-wise latency evaluation is part of the target experiment package
