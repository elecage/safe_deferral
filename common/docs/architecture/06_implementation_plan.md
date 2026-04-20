# 06_implementation_plan.md

## Implementation Plan

## Project Goal
Build a policy-first, safety-oriented edge smart-home prototype with the Mac mini as the primary operational hub, while restricting LLM use to bounded low-risk assistance within the approved Class 1 path.

## Non-Goals
- No autonomous door unlocking
- No free-form LLM actuation
- No user-study implementation in this phase
- No cloud-dependent inference in the core architecture

## Architecture Scope
- The Mac mini hosts all core operational runtime services
- Raspberry Pi 5 is used only as a simulation, virtual sensing, and fault-injection node
- ESP32 devices are used as embedded physical nodes for bounded button input, sensing, or actuator/warning interfacing where required
- The LLM is sandboxed and invoked only after policy approval
- Shared frozen assets in the Git repository act as the single source of truth before runtime deployment

---

## Repository Scope

### Shared frozen assets
- `common/policies/`
- `common/schemas/`
- `common/docs/`
- `common/terminology/`

### Mac mini operational assets
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/scripts/verify/`
- `mac_mini/runtime/`
- `mac_mini/code/`

### Raspberry Pi simulation assets
- `rpi/scripts/install/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`
- `rpi/code/`

### ESP32 embedded assets
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

### End-to-end and experiment assets
- `integration/tests/`
- `integration/scenarios/`

---

## Core Operational Modules

### Mac mini hub-side modules
1. Policy Router
2. Deterministic Validator
3. Context-Integrity Safe Deferral Handler
4. Audit Logging Service / DB Access Layer
5. Outbound Notification Interface
6. Caregiver Confirmation Backend

### Raspberry Pi experiment-side modules
7. Virtual Sensor Node Runtime
8. Virtual Emergency Sensor Runtime
9. Fault Injection Harness
10. Closed-loop Audit Evaluation Harness

### ESP32 embedded modules when used
11. Button Node Firmware
12. Sensor Node Firmware
13. Actuator / Warning Interface Firmware

---

## Canonical Terminology

The canonical project term is:

**context-integrity-based safe deferral stage**

Deprecated label:
- `iCR-based safe deferral stage`

Any implementation references such as:
- `iCR Handler`
- `iCR mapping`

should be replaced with names aligned to the canonical term.

---

## Milestones

### M1. Frozen Specification Ready
Freeze the shared reference assets before implementation begins.

#### Required assets
- routing policy table
- low-risk action policy
- fault injection rules
- output profile
- JSON schemas
- canonical terminology
- environment variable templates
- installation/configuration/verification script set

#### Representative frozen files
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_0_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_0_0.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

#### Completion criterion
The shared frozen assets are committed in the repository and treated as the single source of truth.

---

### M2. Platform Ready
Prepare the Mac mini operational platform.

#### Tasks
- install and configure Home Assistant
- install and configure Mosquitto
- install Ollama and pull Llama 3.1
- prepare SQLite DB
- prepare notification configuration
- prepare runtime `.env` and deployment paths

#### Primary repository locations
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/runtime/`

#### Completion criterion
All core services are present and configured on the Mac mini.

---

### M3. Core Runtime Ready
Implement the hub-side core decision pipeline.

#### Tasks
- implement Policy Router
- implement Deterministic Validator
- implement Context-Integrity Safe Deferral Handler
- implement Audit Logging Service integration

#### Primary repository location
- `mac_mini/code/`

#### Completion criterion
The core decision pipeline can receive input, validate it, and produce auditable routing outcomes.

---

### M4. External Communication Ready
Implement bounded external communication paths.

#### Tasks
- implement Telegram or mock outbound notification path
- implement caregiver confirmation path
- connect notification and confirmation logic to validator outcomes

#### Primary repository location
- `mac_mini/code/`

#### Completion criterion
The system can safely escalate approved external communication events without bypassing policy validation.

---

### M5. Integration Ready
Connect the operational hub to real or semi-real inputs and outputs.

#### Tasks
- connect ESP32 button node
- connect physical sensor input
- connect low-risk actuator or warning output
- validate Class 0 / Class 1 / Class 2 transitions
- validate safe deferral under incomplete or conflicting context

#### Primary repository locations
- `integration/tests/`
- `integration/scenarios/`
- `esp32/code/`
- `esp32/firmware/`

#### Completion criterion
End-to-end operational flows are validated against the intended policy behavior.

---

### M6. Evaluation Ready
Prepare the Raspberry Pi-based evaluation and experiment environment.

#### Tasks
- deploy virtual sensor network on Raspberry Pi 5
- deploy virtual emergency sensors
- deploy fault injector
- run scenario-based routing, safety, latency, and fault-handling experiments
- validate closed-loop audit behavior under injected faults

#### Primary repository locations
- `rpi/code/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`
- `integration/scenarios/`

#### Completion criterion
The system supports reproducible simulation and fault-injection experiments.

---

## Implementation Principles

### A. Policy-first implementation
All runtime logic must respect frozen policy assets before any actuation-related decision path is allowed.

### B. Deterministic safety before bounded LLM assistance
The deterministic validator and safe deferral logic must remain authoritative.
The LLM is only used in the bounded Class 1 assistance path after policy approval.

### C. Device-role separation
- Mac mini = operational hub
- Raspberry Pi 5 = simulation and evaluation node
- ESP32 = embedded physical node layer for bounded input, sensing, or actuator/warning interfacing where required

### D. Auditable outcomes
All meaningful routing and validation outcomes should be observable through logs, notifications, or audit channels.

### E. Repository-structured implementation
Code, scripts, frozen assets, embedded firmware, and integration scenarios should be placed according to the repository structure rather than mixed into a single flat project layout.

---

## Final Delivery Objective

The final prototype should demonstrate that:
- the Mac mini can safely host the operational decision pipeline
- bounded LLM assistance is restricted to approved low-risk contexts
- incomplete, stale, or conflicting context leads to safe deferral rather than unsafe autonomous actuation
- ESP32-based bounded physical input/output paths can be integrated without bypassing policy control
- the Raspberry Pi-based evaluation environment can reproduce fault-handling behavior in a controlled and auditable way