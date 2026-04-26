# 04_project_directory_structure.md

> Legacy source note: The active architecture entry point is `00_architecture_index.md`. This file is retained for detailed source context and should not be used as the first active baseline.


## Recommended Project Directory Structure

This document defines the recommended repository structure for the safe deferral system.

It reflects:
- the current frozen asset strategy
- device-level separation between Mac mini, Raspberry Pi, ESP32, and optional timing infrastructure
- the distinction between shared assets, operational scripts, embedded firmware, measurement assets, integration assets, MQTT contracts, and payload examples/templates
- the canonical terminology of the project

This document does not redefine policy truth.  
Canonical policy, schema, terminology, and related reference assets remain anchored in the shared frozen asset set under `common/`.

Current active structure references:
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/mqtt/topic_registry.json`
- `common/mqtt/publisher_subscriber_matrix.md`
- `common/mqtt/topic_payload_contracts.md`

Some Raspberry Pi governance and MQTT/payload support connections are documented in `15_interface_matrix.md` and `16_system_architecture_figure.md` but are not yet fully drawn in the current SVG figure.

---

## Repository Root Structure

```text
safe_deferral/
├── README.md
├── requirements-mac.txt
├── requirements-rpi.txt
├── common/
│   ├── policies/
│   ├── schemas/
│   ├── mqtt/
│   │   ├── README.md
│   │   ├── topic_registry.json
│   │   ├── publisher_subscriber_matrix.md
│   │   └── topic_payload_contracts.md
│   ├── payloads/
│   │   ├── README.md
│   │   ├── examples/
│   │   └── templates/
│   ├── docs/
│   │   ├── architecture/
│   │   ├── runtime/
│   │   └── archive/
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
│   ├── scripts/
│   │   ├── install/
│   │   │   ├── mac/
│   │   │   ├── linux/
│   │   │   └── windows/
│   │   ├── configure/
│   │   └── verify/
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

The `common/` directory contains shared frozen assets, common reference documents, MQTT communication contracts, and payload examples/templates.

These files act as the shared reference layer before runtime deployment.

### `common/policies/`
Stores shared policy assets, including:
- routing policy tables
- low-risk action policies
- fault injection rules
- optional or version-sensitive companion policy assets

Representative canonical files:
- `policy_table.json`
- `low_risk_actions.json`
- `fault_injection_rules.json`

Optional or version-sensitive companion assets may include:
- output profile assets
- auxiliary policy references
- transitional policy support files

### `common/schemas/`
Stores shared schema assets, including:
- context schema
- candidate action schema
- policy router input schema
- validator output schema
- escalation payload schema

Representative canonical files:
- `context_schema.json`
- `candidate_action_schema.json`
- `policy_router_input_schema.json`
- `validator_output_schema.json`
- `class2_notification_payload_schema.json`

### `common/mqtt/`
Stores MQTT topic, publisher/subscriber, and topic-payload communication contracts.

Representative files:
- `README.md`
- `topic_registry.json`
- `publisher_subscriber_matrix.md`
- `topic_payload_contracts.md`

This directory manages:
- topic namespace assumptions
- allowed publishers
- allowed subscribers
- payload family mapping
- schema/example references
- QoS and retain guidance
- operational vs experiment-only topic boundaries
- dashboard/observation topic boundaries

`common/mqtt/` is a communication-contract reference layer. It does not override `common/policies/` or `common/schemas/`.

### `common/payloads/`
Stores shared payload examples and templates.

Recommended subfolders:
- `common/payloads/examples/`
- `common/payloads/templates/`

Example payload categories:
- policy-router input examples
- pure context payload examples
- visitor-response / `doorbell_detected` examples
- candidate action examples
- validator output examples
- Class 2 notification examples
- manual confirmation examples
- actuation ACK examples
- dashboard observation examples
- experiment annotation examples
- scenario fixture templates
- result export templates

`common/payloads/` is not policy authority and does not replace JSON schemas. Any schema-governed section embedded in a payload example must validate against the corresponding schema under `common/schemas/`.

### `common/docs/`
Stores shared documentation, including:
- installation and deployment references
- architecture documents
- runtime handoff documents
- archived historical notes
- evaluation planning documents
- implementation-boundary guidance

Recommended subfolders:
- `common/docs/architecture/`
- `common/docs/runtime/`
- `common/docs/archive/`

### `common/terminology/`
Stores frozen terminology and naming records.

Representative file:
- `TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

### Interpretation
The `common/` directory is the shared reference layer.  
Runtime copies may be deployed elsewhere, but authoritative frozen policy and schema baselines remain in `common/policies/` and `common/schemas/`.

MQTT and payload files support communication governance, implementation guidance, testing, and documentation consistency; they do not create autonomous policy or actuation authority.

---

## 2. Root-Level Dependency Manifests

### `requirements-mac.txt`
Stores the current baseline Python dependency manifest for Mac mini host-side services and related runtime tooling.

Representative use:
- Mac mini virtual environment setup
- hub-side Python service dependencies
- audit / notification / API-side runtime preparation

### `requirements-rpi.txt`
Stores the current baseline Python dependency manifest for Raspberry Pi experiment-side Python runtime.

Representative use:
- simulation-side Python runtime preparation
- MQTT publishing utilities
- schema validation support
- experiment / verification dependency setup
- dashboard-side runtime dependencies when applicable
- governance backend and dashboard UI dependencies when implemented
- result export dependencies when implemented

### Interpretation
These files are host-side dependency manifests.  
They support install/runtime preparation, but they do not redefine the canonical shared frozen policy or schema baseline.

---

## 3. `mac_mini/`

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
- frozen asset deployment
- MQTT topic/payload contract deployment or reference checks when needed

### `mac_mini/scripts/verify/`
Verification scripts for:
- service health
- MQTT communication
- Ollama inference
- SQLite access
- notification path
- runtime environment validation
- deployed asset/version consistency checks
- topic/payload contract consistency checks when implemented

### `mac_mini/runtime/`
Stores runtime deployment templates and service-oriented runtime assets.

Examples:
- deployed runtime copies of frozen assets
- Docker Compose templates
- runtime configuration templates
- deployment-side environment scaffolding
- service-oriented local runtime files

### `mac_mini/code/`
Stores hub-side application code, including future implementations of:
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- Audit Logging Service
- Outbound Notification Interface
- Caregiver Confirmation Backend
- MQTT intake/dispatch adapters when implemented
- MQTT Topic Registry Loader / Contract Checker
- Payload Validation Helper

### `mac_mini/docs/`
Stores Mac mini-specific implementation notes if needed.

### Interpretation
`mac_mini/runtime/` is a deployment/runtime zone, not the canonical source of frozen policy truth.  
Canonical policy and schema definitions remain under `common/`.

Mac mini may consume MQTT/payload contracts for validation and runtime governance, but those contracts do not override policy or schema authority.

---

## 4. `rpi/`

The `rpi/` directory contains Raspberry Pi-side dashboard, simulation, orchestration, replay, fault-injection, governance support, result-export, and evaluation assets.

The Raspberry Pi is the primary experiment-side dashboard, multi-node simulation, replay, fault-injection, governance support, and experiment orchestration node.

### `rpi/scripts/install/`
Installation scripts for:
- system packages
- Python virtual environment
- Python dependencies
- time synchronization client
- dashboard/governance backend dependencies when implemented
- payload validation and result export dependencies when implemented

### `rpi/scripts/configure/`
Configuration scripts for:
- runtime `.env` generation
- frozen asset synchronization
- MQTT/payload contract synchronization or reference checks when needed
- time synchronization
- simulation runtime setup
- fault profile preparation
- dashboard runtime preparation when implemented
- governance dashboard/backend runtime preparation when implemented
- result export path preparation

### `rpi/scripts/verify/`
Verification scripts for:
- base runtime readiness
- network reachability
- simulation environment checks
- dashboard runtime checks when implemented
- governance backend non-authority checks when implemented
- closed-loop audit validation
- evaluation-side asset consistency checks
- topic registry / publisher-subscriber / payload contract consistency checks when implemented
- payload example validation checks when implemented

### `rpi/code/`
Stores Raspberry Pi-side future code, including:
- virtual sensor nodes
- virtual emergency sensors
- virtual `doorbell_detected` visitor-response context generation
- multi-node simulation runtime
- fault injector harness
- simulation publishers
- scenario orchestration logic
- replay logic
- experiment and monitoring dashboard runtime
- MQTT/payload governance backend service
- governance dashboard UI support
- topic/payload contract validation utilities
- payload example manager / validator
- publisher/subscriber role manager
- progress/status publication
- result summary / graph / CSV export support
- closed-loop evaluation orchestration logic
- large-scale experiment-side control logic

### `rpi/docs/`
Stores Raspberry Pi-specific implementation notes if needed.

### Interpretation
The Raspberry Pi consumes synchronized runtime copies derived from canonical frozen assets.  
It supports experiment-side execution, dashboarding, governance support, and evaluation scaling, but it does not redefine canonical operational policy truth.

RPi dashboard, simulation, fault-injection, governance, and experiment result payloads are visibility/evaluation/governance artifacts unless explicitly validated through canonical schemas and allowed by the MQTT topic registry.

Governance backend and dashboard UI components on the Raspberry Pi must remain non-authoritative. The dashboard UI should remain a presentation and interaction layer; create/update/delete/validation/export operations should be handled by a separate MQTT/payload governance backend service. The UI must not directly edit registry files or publish operational control topics.

---

## 5. `esp32/`

The `esp32/` directory contains embedded-device implementation assets and cross-platform development-environment scaffolding.

ESP32 devices are used for bounded physical interaction, sensing, visitor-response context generation, or actuator/warning interfacing within the applicable scope.

### `esp32/scripts/install/`
Stores cross-platform ESP32 SDK/toolchain setup scripts.

Representative structure:
- `esp32/scripts/install/mac/`
- `esp32/scripts/install/linux/`
- `esp32/scripts/install/windows/`

Representative responsibilities:
- host preflight checks
- prerequisite package installation
- ESP-IDF clone and install
- build-tool readiness preparation

### `esp32/scripts/configure/`
Stores cross-platform ESP32 development-environment alignment scripts.

Representative responsibilities:
- workspace `.env` generation
- ESP-IDF workspace preparation
- managed component preparation
- sample project preparation
- broker/topic configuration references when needed

### `esp32/scripts/verify/`
Stores cross-platform ESP32 development-environment verification scripts.

Representative responsibilities:
- `idf.py` and toolchain verification
- target selection verification
- component resolution verification
- sample build verification
- bounded MQTT publish/subscribe verification when implemented

### `esp32/code/`
Stores device-specific source code and embedded logic.

Representative target categories:
- **current canonical targets**
  - bounded button node logic
  - lighting control node logic
  - representative environmental sensing node logic used in the current validation baseline
  - doorbell / visitor-arrival context node logic emitting `environmental_context.doorbell_detected`
- **optional experimental targets**
  - gas sensor node logic
  - fire detection sensor node logic
  - fall-detection interface logic
- **planned extension targets**
  - doorlock or warning interface logic beyond the current canonical low-risk action scope

Common embedded behaviors may include:
- MQTT publish/subscribe client behavior
- bounded input interpretation
- sensing payload generation
- `doorbell_detected` visitor-response context generation
- actuator/warning interfacing logic

### `esp32/firmware/`
Stores firmware projects, build-system files, and reusable template or example assets.

Representative contents:
- ESP-IDF template projects
- firmware template directories
- board-specific configuration files
- firmware build artifacts or references
- representative physical node profiles

### `esp32/docs/`
Stores ESP32-specific implementation notes, including:
- node role descriptions
- wiring notes
- firmware flash guides
- bounded physical node validation notes
- cross-platform install / configure / verify workflow references

### Interpretation
The ESP32 directory supports both present validation targets and future physical-node extensions.  
It includes explicit install / configure / verify scaffolding for ESP-IDF-based development-environment bring-up before full node-firmware implementation.

ESP32 doorlock or warning interface nodes must not locally reinterpret doorlock as autonomous Class 1 authority.

---

## 6. `integration/`

The `integration/` directory contains cross-device validation and experiment assets.

### `integration/tests/`
Stores:
- end-to-end test harnesses
- integration validation logic
- canonical asset consistency tests
- reproducibility scripts
- system-level behavioral checks
- MQTT topic/payload contract tests when implemented

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

### Interpretation
`integration/` is the cross-device validation layer.  
It should contain system-wide tests and evaluation assets that do not belong to only one device-specific directory.

`common/payloads/` provides reusable reference examples and templates.  
`integration/scenarios/` stores executable or evaluation-oriented scenario definitions.

---

## 7. Directory Design Principles

### A. Shared assets must be separated from device-specific assets
- Shared frozen assets belong in `common/`
- Device-specific setup and runtime code belong in `mac_mini/`, `rpi/`, or `esp32/`

### B. Policy/schema authority must be separated from MQTT and payload examples
- `common/policies/` defines routing/action authority
- `common/schemas/` defines validation authority
- `common/mqtt/` defines topic/publisher/subscriber/payload communication contracts
- `common/payloads/` stores shared examples and templates

MQTT contracts and payload examples help implementation and review, but they do not override canonical policy or schema truth.

### C. Installation, configuration, and verification must remain separated
Each device directory should preserve:
- `install/`
- `configure/`
- `verify/`

This keeps the build lifecycle explicit and script responsibilities clear.

### D. Runtime code should remain separate from operational scripts
- scripts define setup and validation behavior
- code stores executable application logic
- firmware stores embedded-device build targets, templates, and deployable node logic

### E. Integration and measurement assets should remain independent from device-local scripts
System-wide tests, scenarios, timing/measurement assets, and canonical consistency tests belong in `integration/`, not inside a single device folder.

### F. Physical-node validation and virtual-node evaluation should both be representable
The repository should support:
- **ESP32-based physical bounded input/output validation**
- **Raspberry Pi-based scalable virtual-node and fault-injection evaluation**
- **Raspberry Pi-based experiment dashboard and result artifact generation**
- **Raspberry Pi-based non-authoritative MQTT/payload governance support**
- **optional timing-node-based out-of-band latency measurement**

### G. Deployment-local files must not be confused with canonical frozen assets
Host-local runtime files, `.env`, credentials, and machine-specific configuration belong to deployment/runtime handling and must not be treated as canonical frozen policy truth.

### H. MQTT/payload dashboard boundary
A future MQTT/payload management web app or dashboard may inspect topic contracts, publisher/subscriber coverage, payload examples, schema validation results, and live experiment traffic.

Such a dashboard must remain a governance, inspection, and validation tool. It must not become policy authority, validator authority, caregiver approval authority, or direct actuator control authority.

The dashboard UI must remain a presentation and interaction layer. Create/update/delete/validation/export operations should be handled by a separate MQTT/payload governance backend service. The UI must not directly edit registry files or publish operational control topics.

### I. Topic and payload hardcoding should be avoided where practical
Runtime apps, dashboard apps, experiment tools, and firmware adapters should not hardcode MQTT topic strings or payload contracts where registry lookup or configuration lookup is practical.

---

## 8. Canonical Terminology

The canonical project term is:

**context-integrity-based safe deferral stage**

Deprecated label:
- `iCR-based safe deferral stage`

Older internal names may still appear in transitional assets or source-layer references, but new architecture-facing naming should align with the current canonical term.

---

## 9. Architectural Summary

- `common/` stores shared frozen assets, MQTT contracts, payload examples/templates, and reference documents
- `common/policies/` stores policy authority
- `common/schemas/` stores validation authority
- `common/mqtt/` stores MQTT topic/publisher/subscriber/payload communication contracts
- `common/payloads/` stores shared payload examples and templates
- root-level `requirements-*.txt` files store host-side Python dependency manifests
- `mac_mini/` stores hub-side scripts, runtime files, and future code
- `rpi/` stores dashboard, simulation, replay, fault-injection, governance support, result-export, and experiment orchestration-side scripts and future code
- `esp32/` stores embedded firmware assets, cross-platform ESP-IDF development-environment scaffolding, and device-specific physical node implementation assets
- `integration/` stores end-to-end tests, evaluation scenarios, timing/measurement assets, topic/payload validation tests, and canonical consistency checks

This structure is intended to support:
- repository clarity
- implementation planning
- reproducibility
- vibe-coding guidance
- MQTT communication-contract governance
- payload example/template reuse
- physical-node validation
- scalable virtual-node experimentation
- dashboard-supported experiment monitoring
- non-authoritative MQTT/payload governance support
- out-of-band latency measurement
- long-term system extension
