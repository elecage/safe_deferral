# 04_project_directory_structure.md

## Recommended Project Directory Structure

This document defines the recommended repository structure for the safe deferral system.

It reflects:
- the current frozen asset strategy
- device-level separation between Mac mini, Raspberry Pi, ESP32, and optional timing infrastructure
- the distinction between shared assets, operational scripts, embedded firmware, measurement assets, and integration assets
- the canonical terminology of the project

---

## Repository Root Structure

```text
safe_deferral/
├── README.md
├── common/
│   ├── policies/
│   ├── schemas/
│   ├── docs/
│   │   └── architecture/
│   └── terminology/
├── mac_mini/
│   ├── scripts/
│   │   ├── install/
│   │   ├── configure/
│   │   └── verify/
│   ├── runtime/
│   ├── code/
│   └── docs/
├── rpi/
│   ├── scripts/
│   │   ├── install/
│   │   ├── configure/
│   │   └── verify/
│   ├── code/
│   └── docs/
├── esp32/
│   ├── code/
│   ├── firmware/
│   └── docs/
└── integration/
    ├── tests/
    ├── scenarios/
    └── measurement/
```

---

## 1. `common/`

The `common/` directory contains shared frozen assets and common reference documents.

These files act as the single source of truth before runtime deployment.

### `common/policies/`
Stores shared policy assets, including:
- routing policy tables
- low-risk action policies
- fault injection rules
- output profiles

Representative files:
- `policy_table_v1_1_2_FROZEN.json`
- `low_risk_actions_v1_0_0_FROZEN.json`
- `fault_injection_rules_v1_4_0_FROZEN.json`
- `output_profile_v1_0_0.json`

### `common/schemas/`
Stores shared schema assets, including:
- context schema
- candidate action schema
- policy router input schema
- validator output schema

Representative files:
- `context_schema_v1_0_0_FROZEN.json`
- `candidate_action_schema_v1_0_0_FROZEN.json`
- `policy_router_input_schema_v1_1_1_FROZEN.json`
- `validator_output_schema_v1_0_0_FROZEN.json`

### `common/docs/`
Stores shared documentation, including:
- installation and deployment references
- architecture documents
- output profile references
- evaluation planning documents

Recommended subfolders:
- `common/docs/architecture/`

### `common/terminology/`
Stores frozen terminology and naming records.

Representative file:
- `TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

---

## 2. `mac_mini/`

The `mac_mini/` directory contains all hub-side operational assets.

The Mac mini is the primary operational hub of the system.

### `mac_mini/scripts/install/`
Installation scripts for:
- developer tools
- runtime packages
- Docker/runtime dependencies
- Python virtual environment preparation

### `mac_mini/scripts/configure/`
Configuration scripts for:
- Home Assistant
- Mosquitto
- Ollama
- SQLite
- notification settings
- environment file generation
- policy deployment

### `mac_mini/scripts/verify/`
Verification scripts for:
- service health
- MQTT communication
- Ollama inference
- SQLite access
- notification path
- runtime environment validation

### `mac_mini/runtime/`
Stores runtime deployment templates and service-oriented runtime assets.

Examples:
- Docker Compose templates
- runtime configuration templates
- deployment-side environment scaffolding

### `mac_mini/code/`
Stores hub-side application code, including future implementations of:
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- Audit Logging Service
- Outbound Notification Interface
- Caregiver Confirmation Backend

### `mac_mini/docs/`
Stores Mac mini-specific implementation notes if needed.

---

## 3. `rpi/`

The `rpi/` directory contains Raspberry Pi-side simulation and evaluation assets.

The Raspberry Pi is the primary multi-node simulation, fault-injection, and experiment orchestration node.

### `rpi/scripts/install/`
Installation scripts for:
- system packages
- Python virtual environment
- Python dependencies
- time synchronization client

### `rpi/scripts/configure/`
Configuration scripts for:
- runtime `.env` generation
- frozen asset synchronization
- time synchronization
- simulation runtime setup
- fault profile preparation

### `rpi/scripts/verify/`
Verification scripts for:
- base runtime readiness
- network reachability
- simulation environment checks
- closed-loop audit validation

### `rpi/code/`
Stores Raspberry Pi-side future code, including:
- virtual sensor nodes
- virtual emergency sensors
- multi-node simulation runtime
- fault injector harness
- simulation publishers
- closed-loop evaluation orchestration logic
- large-scale experiment-side control logic

### `rpi/docs/`
Stores Raspberry Pi-specific implementation notes if needed.

---

## 4. `esp32/`

The `esp32/` directory contains embedded-device implementation assets.

ESP32 devices are used for bounded physical interaction, sensing, or actuator/warning interfacing where needed.

### `esp32/code/`
Stores device-specific source code and embedded logic.

Representative targets:
- bounded button node logic
- temperature / humidity sensor node logic
- gas sensor node logic
- fire detection sensor node logic
- lighting control node logic
- doorlock or warning interface logic
- MQTT publish/subscribe client behavior

### `esp32/firmware/`
Stores firmware projects and build-system files.

Representative contents:
- PlatformIO projects
- Arduino sketches
- board-specific configuration files
- firmware build artifacts or references
- representative physical node profiles

### `esp32/docs/`
Stores ESP32-specific implementation notes, including:
- node role descriptions
- wiring notes
- firmware flash guides
- bounded physical node validation notes

---

## 5. `integration/`

The `integration/` directory contains cross-device validation and experiment assets.

### `integration/tests/`
Stores:
- end-to-end test harnesses
- integration validation logic
- reproducibility scripts
- system-level behavioral checks

### `integration/scenarios/`
Stores:
- deterministic scenarios
- stress scenarios
- experiment profiles
- reproducible paper evaluation setups

### `integration/measurement/`
Stores:
- class-wise latency experiment profiles
- out-of-band timing notes
- measurement wiring references
- timing capture scripts or result templates
- optional STM32 or dedicated timing-node support notes

---

## 6. Directory Design Principles

### A. Shared assets must be separated from device-specific assets
- Shared frozen assets belong in `common/`
- Device-specific setup and runtime code belong in `mac_mini/`, `rpi/`, or `esp32/`

### B. Installation, configuration, and verification must remain separated
Each device directory should preserve:
- `install/`
- `configure/`
- `verify/`

This keeps the build lifecycle explicit and script responsibilities clear.

### C. Runtime code should remain separate from operational scripts
- scripts define setup and validation behavior
- code stores executable application logic
- firmware stores embedded-device build targets and deployable node logic

### D. Integration and measurement assets should remain independent from device-local scripts
System-wide tests, scenarios, and timing/measurement assets belong in `integration/`, not inside a single device folder.

### E. Physical-node validation and virtual-node evaluation should both be representable
The repository should support:
- **ESP32-based physical bounded input/output validation**
- **Raspberry Pi-based scalable virtual-node and fault-injection evaluation**
- **optional timing-node-based out-of-band latency measurement**

---

## 7. Canonical Terminology

The canonical project term is:

**context-integrity-based safe deferral stage**

Deprecated label:
- `iCR-based safe deferral stage`

Any old references such as:
- `icr_mapping`
- `icr_handler`

should be replaced with terminology aligned to the current canonical term.

---

## 8. Architectural Summary

- `common/` stores shared frozen assets and reference documents
- `mac_mini/` stores hub-side scripts, runtime files, and future code
- `rpi/` stores simulation-side scripts and future experiment orchestration code
- `esp32/` stores embedded firmware and device-specific physical node implementation assets
- `integration/` stores end-to-end tests, evaluation scenarios, and timing/measurement assets

This structure is intended to support:
- repository clarity
- implementation planning
- reproducibility
- vibe-coding guidance
- physical-node validation
- scalable virtual-node experimentation
- out-of-band latency measurement
- long-term system extension
