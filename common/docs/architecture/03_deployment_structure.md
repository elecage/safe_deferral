# 03_deployment_structure.md

## Deployment Structure

This document defines the high-level structure used to organize the project into three operational layers:

1. **Installation**
2. **Configuration**
3. **Verification**

It is intended to be used as a reference for:
- repository organization
- implementation planning
- script classification
- vibe-coding prompts and agent guidance

---

## A. Installation

### Goal
Software, runtimes, services, and required build or measurement toolchains are present on the target platform.

### Examples
- Home Assistant installed
- Mosquitto installed
- Ollama installed
- Python virtual environment created
- system packages installed
- time synchronization client installed
- ESP32 development toolchain prepared when needed
- optional timing-node toolchain prepared when out-of-band latency measurement is used

### Repository mapping
- `mac_mini/scripts/install/`
- `rpi/scripts/install/`
- `esp32/firmware/`
- `esp32/code/`

### Interpretation
Installation means the required platform dependencies are available, but not yet configured for the safe deferral architecture.

---

## B. Configuration

### Goal
Installed services, runtimes, and experimental node assumptions are configured for the safe deferral system architecture.

### Examples
- Home Assistant MQTT integration configured
- Mosquitto listener and authentication config applied
- Ollama model pulled and made available
- frozen policy and schema files deployed
- Telegram or mock notification settings configured
- SQLite schema initialized
- runtime `.env` files written
- simulation runtime parameters configured
- ESP32 node-side connection parameters aligned with the operational hub when needed
- timing-node measurement assumptions aligned when out-of-band latency measurement is used

### Repository mapping
- source of truth: `common/`
- deployment/configuration scripts:
  - `mac_mini/scripts/configure/`
  - `rpi/scripts/configure/`
- embedded device configuration assets when needed:
  - `esp32/code/`
  - `esp32/firmware/`

### Interpretation
Configuration means the installed components are now aligned with the project architecture, frozen assets, runtime assumptions, and experimental validation design.

---

## C. Verification

### Goal
Each service, dependency, runtime path, and experimental validation path works correctly before full integration or large-scale evaluation begins.

### Examples
- MQTT pub/sub test passes
- Home Assistant starts correctly
- Ollama inference returns expected output
- SQLite can store and read audit log entries
- notification channel works
- runtime assets are present and valid
- Raspberry Pi simulation runtime passes base checks
- closed-loop audit verification passes
- ESP32-linked bounded input/output path can be validated during integration testing
- out-of-band class-wise latency measurement passes when timing infrastructure is used

### Repository mapping
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`
- `integration/tests/`
- `integration/scenarios/`
- `integration/measurement/`

### Interpretation
Verification is performed before full integration in order to confirm that each service and runtime layer behaves correctly in isolation, and that the experimental validation infrastructure is trustworthy.

---

## Role of Shared Frozen Assets

Before configuration and verification, the project depends on shared frozen assets stored in the repository.

### Shared asset locations
- `common/policies/`
- `common/schemas/`
- `common/docs/`
- `common/terminology/`

### Examples
- routing policy tables
- low-risk action policies
- fault injection rules
- JSON schemas
- output profiles
- canonical terminology documents

These files act as the single source of truth before runtime deployment.

---

## Role of Device-Specific Layers

### Mac mini
The Mac mini is the primary operational hub.  
It hosts the core runtime services, hub-side applications, and operational verification flow.

### Raspberry Pi 5
The Raspberry Pi 5 is the simulation and evaluation node.  
It hosts virtual sensor nodes, multi-node simulation, emergency simulation, fault injection, scenario orchestration, and closed-loop experiment workflows.

It does **not** host the core operational hub services of the system, such as:
- Home Assistant
- Ollama
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- hub-side operational audit authority

Instead, it consumes synchronized runtime copies of frozen assets and supports experiment-side execution only.

### ESP32
ESP32 devices are embedded physical nodes used for bounded button input, sensing, or actuator/warning interfacing where required.  
They are implementation targets and also form the physical bounded input/output validation layer during integration testing.

### STM32 Timing Node or Equivalent
An STM32 timing node or another dedicated measurement node may be used as optional experimental timing infrastructure.  
Its role is to support out-of-band class-wise latency measurement without interfering with the operational service plane.

---

## Architectural Summary

- **Installation** prepares each target platform.
- **Configuration** aligns each platform with the safe deferral architecture and experimental validation assumptions.
- **Verification** confirms that each configured component works correctly before integration and large-scale evaluation.
- **Shared frozen assets** in `common/` provide the reference state used by Mac mini, Raspberry Pi, and ESP32-related implementation work.
- **Mac mini** remains the only operational hub for core runtime services.
- **Raspberry Pi 5** remains an experiment-side simulation, fault-injection, and evaluation node rather than a replacement for the Mac mini runtime.
- **ESP32 physical nodes** support bounded real-world input/output validation.
- **Optional STM32 timing infrastructure** supports out-of-band latency measurement.
- **Integration assets** validate cross-device behavior after isolated verification is complete.
