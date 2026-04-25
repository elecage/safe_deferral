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
- MQTT/topic/payload governance boundary interpretation
- vibe-coding prompts and agent guidance

This document does not replace the canonical frozen policy/schema baseline.  
The shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

The current active interface, architecture-figure, payload-boundary, and MQTT references are:
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`

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
- registry/payload validation dependencies installed where implemented
- dashboard/governance backend dependencies installed where implemented
- payload export/report dependencies installed where implemented

### Repository mapping
- `mac_mini/scripts/install/`
- `rpi/scripts/install/`
- `esp32/firmware/`
- `esp32/code/`
- `integration/measurement/`
- install-dependent reference layers:
  - `common/mqtt/`
  - `common/payloads/`

### Interpretation
Installation means the required platform dependencies are available, but not yet configured for the safe deferral architecture.

`common/mqtt/` and `common/payloads/` may influence which validation, dashboard, or export dependencies are needed, but they are not installation targets that redefine runtime authority.

### Boundary note
Installation may include optional experimental infrastructure.  
The presence of a toolchain, package, dashboard dependency, or governance dependency does not by itself mean that the component belongs to the current canonical operational baseline or holds operational authority.

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
- MQTT topic registry path configured
- payload examples/templates path configured
- topic namespace and ACL assumptions aligned with publisher/subscriber matrix
- governance dashboard enable flag configured where implemented
- result export path configured where implemented
- simulation runtime parameters configured
- `doorbell_detected` visitor-response context generation and normalization configured where visitor-response or doorlock-sensitive experiments are used
- ESP32 node-side connection parameters aligned with the operational hub when needed
- timing-node measurement assumptions aligned when out-of-band latency measurement is used

### Repository mapping
- source of truth and reference layers:
  - `common/policies/`
  - `common/schemas/`
  - `common/mqtt/`
  - `common/payloads/`
  - `common/docs/`
  - `common/terminology/`
- deployment/configuration scripts:
  - `mac_mini/scripts/configure/`
  - `rpi/scripts/configure/`
- embedded device configuration assets when needed:
  - `esp32/code/`
  - `esp32/firmware/`

### Interpretation
Configuration means the installed components are now aligned with the project architecture, frozen assets, shared reference assets, runtime assumptions, and experimental validation design.

Payload placement and authority boundaries must follow:
- `common/docs/architecture/17_payload_contract_and_registry.md`

MQTT-facing interfaces and topic/payload contracts must remain aligned with:
- `common/docs/architecture/15_interface_matrix.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`

### Configuration separation principle
- frozen policy/schema/terminology assets are derived from `common/policies/`, `common/schemas/`, and `common/terminology/`
- MQTT registry and payload examples/templates are reference assets from `common/mqtt/` and `common/payloads/`
- host-local files such as `.env`, credentials, tokens, and machine-specific YAML are deployment-local configuration
- deployment-local `.env` files may point to MQTT registry and payload reference paths, but must not redefine them
- dashboard/governance configuration must remain non-authoritative
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
- MQTT topic registry readability passes
- publisher/subscriber matrix consistency passes
- topic-to-payload contract resolution passes
- schema-governed payload example validation passes
- governance/dashboard topics remain non-authoritative
- topic/payload hardcoding drift check passes where implemented
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
- `common/mqtt/`
- `common/payloads/`

### Interpretation
Verification is performed before full integration in order to confirm that each service and runtime layer behaves correctly in isolation, and that the experimental validation infrastructure is trustworthy.

### Verification principle
Verification must confirm not only service health, but also architectural consistency across:
- canonical frozen assets
- deployed runtime copies
- trigger semantics
- payload placement and authority boundaries
- MQTT topic contract consistency
- publisher/subscriber role consistency
- payload example/schema consistency
- governance non-authority boundary
- evaluation-side validation assumptions

---

## Role of Shared Frozen Assets and Shared Reference Assets

Before configuration and verification, the project depends on shared frozen authority assets and shared reference assets stored in the repository.

### Frozen authority asset locations
- `common/policies/`
- `common/schemas/`
- `common/terminology/`

### Shared reference asset locations
- `common/mqtt/`
- `common/payloads/`
- `common/docs/`

### Representative canonical frozen authority assets
- `policy_table_v1_1_2_FROZEN.json`
- `low_risk_actions_v1_1_0_FROZEN.json`
- `fault_injection_rules_v1_4_0_FROZEN.json`
- `context_schema_v1_0_0_FROZEN.json`
- `candidate_action_schema_v1_0_0_FROZEN.json`
- `policy_router_input_schema_v1_1_1_FROZEN.json`
- `validator_output_schema_v1_1_0_FROZEN.json`
- `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- canonical terminology records under `common/terminology/`

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
- output profile assets
- host-local configuration templates
- installation/configuration/verification script bundles
- reproducibility support assets

These frozen authority files act as the single source of policy/schema truth before runtime deployment.  
Deployment targets must consume synchronized runtime copies derived from them.

`common/mqtt/` and `common/payloads/` are reference layers. They must not override canonical policy/schema truth, create operational authority, or authorize sensitive actuation.

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

It may also host hub-side helper components such as:
- MQTT Topic Registry Loader / Contract Checker
- Payload Validation Helper

These helpers support registry-driven topic lookup, communication-contract consistency, and payload-boundary checks. They do not replace canonical policy/schema authority.

### Raspberry Pi 5
The Raspberry Pi 5 is the experiment-side support node.  
It hosts the experiment and monitoring dashboard, virtual sensor nodes, multi-node simulation, emergency simulation, fault injection, scenario orchestration, replay, closed-loop experiment workflows, progress/status publication, result artifact generation, MQTT/payload governance backend, governance dashboard UI, topic/payload contract validation, payload example validation, and publisher/subscriber role review.

It does **not** host the core operational hub services or authorities of the system, such as:
- Home Assistant
- Ollama
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- hub-side operational audit authority
- direct actuator dispatch authority
- doorlock dispatch authority
- direct registry-file editing through dashboard UI
- canonical policy/schema editing authority

Instead, it consumes synchronized runtime copies of frozen assets and supports experiment-side execution, dashboard visibility, and non-authoritative governance support only.

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
- registry path variables
- payload example/template path variables
- dashboard/governance enable flags
- experiment result export paths

These assets are necessary for deployment, but they must not override or redefine canonical policy, schema, terminology, MQTT registry, or payload reference truth.

Deployment-local configuration may point to registry/payload references, but it must not redefine those references as local authority.

---

## Architectural Summary

- **Installation** prepares each target platform.
- **Configuration** aligns each platform with the safe deferral architecture and experimental validation assumptions.
- **Verification** confirms that each configured component works correctly before integration and large-scale evaluation.
- **Shared frozen authority assets** in `common/policies/`, `common/schemas/`, and `common/terminology/` provide the canonical policy/schema/terminology authority used by Mac mini, Raspberry Pi, and ESP32-related implementation work.
- **Shared reference assets** in `common/mqtt/`, `common/payloads/`, and `common/docs/` provide communication-contract, payload-example, architecture, and governance references without becoming policy/schema authority.
- `common/mqtt/` and `common/payloads/` provide shared reference layers for topic/payload governance.
- `common/docs/architecture/15_interface_matrix.md` provides the MQTT-aware interface contract reference.
- **Deployment-local configuration** remains host-specific and is not part of the canonical frozen policy baseline.
- **Mac mini** remains the only operational hub for core runtime services.
- **Raspberry Pi 5** remains an experiment-side dashboard, simulation, orchestration, replay, fault-injection, evaluation, result-export, and non-authoritative MQTT/payload governance support node rather than a replacement for the Mac mini runtime.
- **ESP32 physical nodes** support bounded real-world input/output validation, including visitor-response context sensing where applicable.
- **Optional STM32 timing infrastructure** supports out-of-band latency measurement.
- **Integration assets** validate cross-device behavior, topic/payload consistency, and experiment outcomes after isolated verification is complete.

---

## Final Interpretation Principle

The deployment structure should preserve the following order of meaning:

1. install the necessary platform dependencies
2. configure the installed components using canonical frozen references and shared communication/payload references
3. verify service health, runtime validity, asset consistency, and MQTT/payload contract consistency
4. integrate physical and virtual validation layers only after isolated checks pass
5. keep governance/dashboard support separate from operational authority

At no point should deployment-local convenience override the shared frozen architecture baseline or convert MQTT/payload governance support into policy, validator, caregiver approval, audit, actuator, or doorlock authority.
