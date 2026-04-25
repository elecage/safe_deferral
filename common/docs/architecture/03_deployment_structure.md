# 03_deployment_structure.md

## Deployment Structure

This document defines the high-level structure used to organize the project into three major deployment layers:

1. **Installation**
2. **Configuration**
3. **Verification**

It is intended to be used as a reference for:
- repository organization
- implementation planning
- script classification
- deployment-boundary interpretation
- vibe-coding prompts and agent guidance

This document does not replace the canonical frozen policy/schema baseline.  
The shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

The current active architecture-figure and payload-boundary references are:
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

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

### Boundary note
Installation may include optional experimental infrastructure.  
The presence of a toolchain or package does not by itself mean that the component belongs to the current canonical operational baseline.

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
- `doorbell_detected` visitor-response context generation and normalization configured where visitor-response or doorlock-sensitive experiments are used
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

Payload placement and authority boundaries must follow:
- `common/docs/architecture/17_payload_contract_and_registry.md`

### Configuration separation principle
- frozen policy/schema/terminology assets are derived from `common/`
- host-local files such as `.env`, credentials, tokens, and machine-specific YAML are deployment-local configuration
- deployment-local configuration must not be treated as canonical frozen policy truth

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
- canonical frozen assets are deployed and readable
- canonical policy/schema/rules version alignment passes
- schema-valid context payload generation verifies required `environmental_context.doorbell_detected`
- visitor-response / doorlock-sensitive experiment payloads verify that `doorbell_detected` is context only, not doorlock authorization
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

### Verification principle
Verification must confirm not only service health, but also architectural consistency across:
- canonical frozen assets
- deployed runtime copies
- trigger semantics
- payload placement and authority boundaries
- evaluation-side validation assumptions

---

## Role of Shared Frozen Assets

Before configuration and verification, the project depends on shared frozen assets stored in the repository.

### Shared asset locations
- `common/policies/`
- `common/schemas/`
- `common/docs/`
- `common/terminology/`

### Representative canonical frozen assets
- `policy_table_v1_1_2_FROZEN.json`
- `low_risk_actions_v1_1_0_FROZEN.json`
- `fault_injection_rules_v1_4_0_FROZEN.json`
- `context_schema_v1_0_0_FROZEN.json`
- `candidate_action_schema_v1_0_0_FROZEN.json`
- `policy_router_input_schema_v1_1_1_FROZEN.json`
- `validator_output_schema_v1_1_0_FROZEN.json`
- `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- canonical terminology records under `common/terminology/`

### Optional or version-sensitive companion assets
- output profile assets
- host-local configuration templates
- installation/configuration/verification script bundles
- reproducibility support assets

These frozen files act as the single source of truth before runtime deployment.  
Deployment targets must consume synchronized runtime copies derived from them.

---

## Canonical Emergency Consistency

Emergency simulation, validation, and verification should remain consistent with the canonical policy-declared emergency trigger family.

At the current canonical policy level, the project recognizes:

- `E001`: high temperature threshold crossing
- `E002`: emergency triple-hit bounded input
- `E003`: smoke detected state trigger
- `E004`: gas detected state trigger
- `E005`: fall detected event trigger

Accordingly:
- physical sensing paths
- virtual emergency sensor paths
- fault injection profiles
- verification logic

must remain semantically aligned with the same canonical trigger set.

`doorbell_detected` is not part of the current canonical emergency trigger family. It is a visitor-response context signal and must not be interpreted as Class 0 emergency evidence or autonomous doorlock authority.

This document does not redefine emergency semantics.  
The authoritative trigger definitions remain in the shared policy table.

---

## Role of Device-Specific Layers

### Mac mini
The Mac mini is the primary operational hub.  
It hosts the core runtime services, hub-side applications, and operational verification flow.

### Raspberry Pi 5
The Raspberry Pi 5 is the experiment-side support node.  
It hosts the experiment and monitoring dashboard, virtual sensor nodes, multi-node simulation, emergency simulation, fault injection, scenario orchestration, replay, closed-loop experiment workflows, progress/status publication, and result artifact generation.

It does **not** host the core operational hub services of the system, such as:
- Home Assistant
- Ollama
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- hub-side operational audit authority

Instead, it consumes synchronized runtime copies of frozen assets and supports experiment-side execution only.

### ESP32
ESP32 devices are embedded physical nodes used for bounded button input, environmental sensing, doorbell / visitor-arrival context sensing, or actuator/warning interfacing where required.  
They are implementation targets and also form the physical bounded input/output validation layer during integration testing.

ESP32 doorlock or warning interface nodes must not locally reinterpret doorlock as autonomous Class 1 authority.

### STM32 Timing Node or Equivalent
An STM32 timing node or another dedicated measurement node may be used as optional experimental timing infrastructure.  
Its role is to support out-of-band class-wise latency measurement without interfering with the operational service plane.

This timing infrastructure is optional and should not be interpreted as part of the minimum canonical hub deployment.

---

## Deployment-Local Configuration

Deployment-local configuration refers to host-specific files or secrets that are required for execution but are not canonical frozen reference assets.

### Examples
- `.env`
- API tokens
- service credentials
- machine-specific YAML
- host-local runtime paths
- local secrets for notification integration

These assets are necessary for deployment, but they must not override or redefine canonical policy, schema, or terminology truth.

---

## Architectural Summary

- **Installation** prepares each target platform.
- **Configuration** aligns each platform with the safe deferral architecture and experimental validation assumptions.
- **Verification** confirms that each configured component works correctly before integration and large-scale evaluation.
- **Shared frozen assets** in `common/` provide the canonical reference state used by Mac mini, Raspberry Pi, and ESP32-related implementation work.
- **Deployment-local configuration** remains host-specific and is not part of the canonical frozen policy baseline.
- **Mac mini** remains the only operational hub for core runtime services.
- **Raspberry Pi 5** remains an experiment-side dashboard, simulation, orchestration, replay, fault-injection, and evaluation node rather than a replacement for the Mac mini runtime.
- **ESP32 physical nodes** support bounded real-world input/output validation, including visitor-response context sensing where applicable.
- **Optional STM32 timing infrastructure** supports out-of-band latency measurement.
- **Integration assets** validate cross-device behavior after isolated verification is complete.

---

## Final Interpretation Principle

The deployment structure should preserve the following order of meaning:

1. install the necessary platform dependencies
2. configure the installed components using canonical frozen references
3. verify service health, runtime validity, and asset consistency
4. integrate physical and virtual validation layers only after isolated checks pass

At no point should deployment-local convenience override the shared frozen architecture baseline.
