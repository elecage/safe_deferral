# 05_automation_strategy.md

## Automation Strategy

This document defines the recommended automation strategy for the safe deferral system.

It reflects:
- the current frozen asset structure
- device-level separation between Mac mini, Raspberry Pi, ESP32, and optional timing infrastructure
- the staged workflow of installation, configuration, verification, and measurement-oriented evaluation
- the MQTT topic / payload contract governance layer
- the need for orchestration-friendly execution during development and vibe-coding

This document does not replace the canonical frozen baseline.  
Shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

Current interface, communication, and payload references:
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/mqtt/topic_registry.json`
- `common/mqtt/publisher_subscriber_matrix.md`
- `common/mqtt/topic_payload_contracts.md`
- `common/payloads/README.md`

---

## 1. Recommended Automation Layers

### A. Installation Scripts
Purpose:  
Prepare software, runtimes, system dependencies, SDK/toolchains, and optional measurement toolchains on each target device or development host.

Repository locations:
- `mac_mini/scripts/install/`
- `rpi/scripts/install/`
- `esp32/scripts/install/`
- measurement-related notes or support assets under:
  - `integration/measurement/`

Examples:
- developer tools installation
- Docker/runtime setup
- Python virtual environment creation
- system package installation
- time synchronization client installation
- ESP32 prerequisite/toolchain installation
- ESP-IDF installation and export readiness
- optional timing-node toolchain preparation when out-of-band latency measurement is used
- registry/payload validation dependencies installed where implemented
- governance backend service dependencies installed where implemented
- governance dashboard UI dependencies installed where implemented
- topic/payload validation utility dependencies installed where implemented
- payload export/report dependencies installed where implemented

Interpretation:
Installation prepares the target platform or host-side development environment, but it does not yet establish project-specific runtime alignment.

---

### B. Configuration Scripts
Purpose:  
Apply project-specific settings and deploy runtime-ready configuration.

Repository locations:
- `mac_mini/scripts/configure/`
- `rpi/scripts/configure/`
- `esp32/scripts/configure/`
- embedded firmware and node-implementation assets under:
  - `esp32/code/`
  - `esp32/firmware/`
- measurement-related configuration notes or assets when needed:
  - `integration/measurement/`

Examples:
- Home Assistant configuration
- Mosquitto configuration
- Ollama setup and model pull
- SQLite initialization
- notification channel configuration
- runtime `.env` generation
- policy/schema deployment or synchronization
- MQTT topic registry and publisher/subscriber contract reference deployment or synchronization when needed
- payload example/template references synchronized for test, simulation, dashboard, and governance tooling when needed
- simulation runtime configuration
- ESP32 workspace env generation
- ESP32 sample project preparation
- ESP32 managed component preparation
- embedded node-side connection parameters aligned with the operational hub when needed
- MQTT/payload governance backend configured when implemented
- governance dashboard UI configured as a presentation layer when implemented
- governance backend API endpoint configured when implemented
- governance dashboard UI prevented from directly editing registry files
- topic/payload governance dashboard runtime configured when implemented
- result export path configured when implemented
- timing-node measurement assumptions aligned when used
- out-of-band measurement profile preparation when class-wise latency evaluation is required

Configuration separation principle:
- frozen policy/schema/terminology assets are derived from `common/`
- MQTT topic contracts are derived from `common/mqtt/`
- payload examples/templates are derived from `common/payloads/`
- host-local `.env`, credentials, tokens, and machine-specific files are deployment-local configuration
- deployment-local configuration must not be treated as canonical frozen policy truth
- MQTT contracts and payload examples must not override canonical policy/schema authority
- governance dashboard UI must remain separated from the governance backend service
- governance configuration must not grant policy, validator, caregiver approval, audit, actuator, or doorlock authority

---

### C. Verification Scripts
Purpose:  
Verify that each configured service, dependency, runtime path, SDK/toolchain path, communication contract, payload contract, and measurement path works correctly before integration or large-scale evaluation begins.

Repository locations:
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`
- `esp32/scripts/verify/`
- `integration/tests/`
- `integration/scenarios/`
- `integration/measurement/`

Examples:
- Docker service checks
- MQTT pub/sub validation
- MQTT topic registry readability and consistency checks
- publisher/subscriber matrix consistency checks
- topic-to-payload contract checks
- payload example schema-validation checks
- `doorbell_detected` required-field checks for context payload examples
- forbidden doorlock-in-device-states checks
- governance dashboard UI does not directly write registry files
- governance backend does not modify canonical policies/schemas
- governance tooling cannot publish actuator or doorlock commands
- governance tooling cannot spoof caregiver approval
- governance/dashboard topics remain non-authoritative
- topic/payload hardcoding drift check passes where implemented
- Ollama inference validation
- SQLite validation
- notification validation
- runtime asset validation
- deployed frozen asset readability checks
- canonical policy/schema/rules version alignment checks
- trigger semantics consistency checks
- Raspberry Pi base runtime checks
- Raspberry Pi dashboard runtime checks when implemented
- MQTT/payload governance backend checks when implemented
- MQTT/payload governance dashboard UI checks when implemented
- closed-loop audit verification
- ESP-IDF CLI verification
- ESP32 target-selection verification
- ESP32 sample build verification
- ESP32-linked bounded input/output path validation through integration testing
- out-of-band class-wise latency measurement validation
- timing capture path validation when measurement infrastructure is used

Verification principle:
Verification should confirm not only service health, but also architectural consistency across:
- canonical frozen assets
- deployed runtime copies
- MQTT topic registry and publisher/subscriber contracts
- payload examples/templates and schema-governed payload boundaries
- governance backend/UI separation
- governance non-authority boundary
- topic/payload hardcoding drift checks where implemented
- trigger semantics
- evaluation-side validation assumptions
- ESP32 sample-build readiness before real node firmware generation proceeds

---

## 2. Role of Shared Frozen Assets and Shared Communication References

Automation does not begin from raw code alone.

The project depends on shared assets stored in:
- `common/policies/`
- `common/schemas/`
- `common/mqtt/`
- `common/payloads/`
- `common/docs/`
- `common/terminology/`

Representative canonical frozen assets include:
- `policy_table.json`
- `low_risk_actions.json`
- `fault_injection_rules.json`
- `context_schema.json`
- `candidate_action_schema.json`
- `policy_router_input_schema.json`
- `validator_output_schema.json`
- `class2_notification_payload_schema.json`

Representative communication and payload reference assets include:
- `common/mqtt/topic_registry.json`
- `common/mqtt/publisher_subscriber_matrix.md`
- `common/mqtt/topic_payload_contracts.md`
- `common/payloads/README.md`
- `common/payloads/examples/`
- `common/payloads/templates/`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

Optional or version-sensitive companion assets may include:
- output profile assets
- auxiliary deployment templates
- support bundles for reproducibility or measurement workflows

These files act as the shared reference state before runtime deployment and verification.

### Authority principle
- The authoritative policy/schema reference state is the frozen asset set in `common/policies/` and `common/schemas/`.
- MQTT topic contracts in `common/mqtt/` define communication contracts, not policy authority.
- Payload examples/templates in `common/payloads/` support implementation and testing, not policy authority.
- Mac mini and Raspberry Pi consume deployed or synchronized runtime copies as needed, but they must not redefine local policy truth.
- ESP32-oriented automation should remain consistent with the same canonical policy/schema and MQTT topic assumptions where applicable.
- Governance backend and dashboard automation may inspect, validate, draft, and report topic/payload changes, but must not create operational authority.

---

## 3. Recommended Orchestration Layer

### Recommended
- shell scripts under device-specific script folders
- PowerShell scripts on Windows where that is the native operational path
- a top-level `Makefile` or `justfile` for orchestration
- optional measurement-oriented targets for timing and latency evaluation
- topic/payload registry validation targets for MQTT and payload-governance checks
- separate governance backend and governance UI validation targets when implemented

### Why
- macOS-friendly and Raspberry Pi-friendly
- Windows-friendly for ESP32 host-side SDK/toolchain bring-up
- embedded-node-friendly when ESP32 build steps are introduced
- measurement-friendly when timing-node workflows are introduced
- topic/payload-governance-friendly as MQTT usage grows
- easy to rerun individual stages
- explicit separation of responsibilities
- easier fault isolation and debugging
- suitable for vibe-coding workflows and agent guidance

### Orchestration principle
The `Makefile` or `justfile` should orchestrate the workflow, but the primary automation units should remain device-specific scripts, embedded build targets, communication-contract checks, payload-validation checks, governance backend/UI checks, or measurement-oriented support assets.

---

## 4. Recommended Execution Model

Because the project is split across Mac mini, Raspberry Pi, ESP32, optional timing infrastructure, and shared MQTT/payload contracts, orchestration should be device-aware, evaluation-aware, and communication-contract-aware.

### Recommended preflight examples
```bash
make common-check
make policy-check
make schema-check
make mqtt-check
make payload-check
make topic-contract-check
```

### Device-oriented examples
```bash
make mac-install
make mac-configure
make mac-verify

make rpi-install
make rpi-configure
make rpi-verify

make esp32-install
make esp32-configure
make esp32-verify
```

### ESP32-oriented examples
```bash
make esp32-install
make esp32-configure
make esp32-verify
make esp32-build
make esp32-flash
make esp32-check
```

### Measurement-oriented examples
```bash
make measure-latency
make timing-check
```

### Governance-oriented examples
```bash
make registry-check
make governance-check
make governance-backend-check
make governance-ui-check
make governance-dashboard-check
make topic-drift-check
make payload-example-check
```

### Optional grouped targets
```bash
make mac-all
make rpi-all
make esp32-all
make verify-all
make integration-test
make scenario-run
make benchmark
make fault-eval
make latency-eval
make closed-loop-check
make topic-payload-check
make dashboard-check
```

### Interpretation
- `common-check`, `policy-check`, and `schema-check` should validate the canonical shared baseline before deployment-dependent steps run
- `mqtt-check`, `payload-check`, and `topic-contract-check` should validate topic registry readability, publisher/subscriber contract consistency, topic-to-payload references, and payload example/schema alignment
- `mac-*` targets operate on the Mac mini workflow
- `rpi-*` targets operate on the Raspberry Pi workflow and must remain bounded to dashboard, simulation, fault-injection, orchestration, replay, progress/result publication, non-authoritative MQTT/payload governance support, and evaluation tasks rather than hub-side operational runtime control
- `esp32-install`, `esp32-configure`, and `esp32-verify` operate on the cross-platform ESP-IDF development-environment workflow
- `esp32-build`, `esp32-flash`, and `esp32-check` operate on embedded build/flash/validation workflows when actual node firmware is present
- measurement targets operate on timing or latency evaluation workflows when used
- governance targets operate on MQTT/payload inspection and validation only, not policy override or actuation control
- `governance-backend-check` should verify backend API behavior, draft/change-report handling, and non-authority constraints
- `governance-ui-check` or `governance-dashboard-check` should verify UI/backend separation and direct-registry-edit prevention
- `topic-drift-check` should detect hardcoded topic/payload drift where practical
- grouped targets should compose lower-level scripts, not bypass them

### ESP32 check interpretation
`esp32-check` may include:
- firmware build validation
- board/profile selection validation
- MQTT behavior validation when applicable
- bounded input/output behavior checks
- representative node-role validation for the current or optional experimental scope

Before real node firmware exists, `esp32-verify` should primarily mean:
- ESP-IDF CLI verification
- target-selection verification
- component-resolution verification
- sample-build verification

---

## 5. Canonical Emergency Automation Alignment

Automation for emergency simulation, fault injection, verification, and replay must remain aligned with the canonical policy-declared emergency trigger family.

At the current canonical policy level, the project recognizes:
- `E001`: high temperature threshold crossing
- `E002`: emergency triple-hit bounded input
- `E003`: smoke detected state trigger
- `E004`: gas detected state trigger
- `E005`: fall detected event trigger

Accordingly:
- virtual emergency sensor workflows
- fault injection workflows
- physical-node validation workflows
- closed-loop verification logic

should remain semantically consistent with the same trigger set.

`doorbell_detected` is not part of the emergency trigger family. It is visitor-response context and must not be interpreted as Class 0 emergency evidence or autonomous doorlock authority.

This document does not redefine emergency semantics.  
The authoritative trigger definitions remain in the shared policy table.

---

## 6. Design Principles

### A. Keep installation, configuration, and verification separate
Do not merge these concerns into one large script.

### B. Keep device-specific workflows separate
Do not collapse Mac mini, Raspberry Pi, ESP32, and optional timing infrastructure automation into a single opaque execution path.

### C. Let orchestration call scripts, not replace them
The `Makefile` or `justfile` should orchestrate the workflow, while the actual operational logic remains in shell scripts, PowerShell scripts, embedded build targets, communication-contract checks, payload-validation checks, governance checks, or measurement-oriented support assets.

### D. Preserve rerunnability
Every step should be safe to rerun independently whenever possible.

### E. Respect frozen assets
Configuration and verification logic should use shared frozen assets from `common/` as reference inputs.

### F. Keep measurement automation bounded to evaluation use
Timing capture and latency evaluation should support reproducible experiments without becoming part of the operational decision path.

### G. Preserve Raspberry Pi evaluation, dashboard, and governance boundary
Raspberry Pi automation should prepare and run experiment-side dashboard, simulation, fault-injection, scenario orchestration, replay, progress/status publication, result artifact generation, non-authoritative MQTT/payload governance support, and closed-loop verification workflows only.  
It should not automate Mac mini hub-side operational runtime control.

### H. Preserve ESP32 bounded-node boundary
ESP32 automation should prepare SDK/toolchain bring-up, sample-build readiness, and later bounded node validation, but it should not be treated as an independent policy authority or collapsed into the Mac mini or Raspberry Pi runtime path.

### I. Prefer closed-loop automation over bypassed shortcuts
Automation should support scenario publication through the same input plane used by the operational system and should validate outcomes through observed audit behavior rather than bypassed internal control paths.

### J. Validate shared assets before deployment-dependent automation
Automation should fail early if canonical policy/schema/rules assets are missing, unreadable, or version-inconsistent.

### K. Do not hardcode MQTT topics or payload contracts in apps
Runtime apps, dashboard apps, experiment tools, and firmware adapters should load topic names, publisher/subscriber rules, payload families, schema paths, and example payload references from `common/mqtt/topic_registry.json` whenever practical.

Code should prefer stable topic identifiers or registry lookups over direct hardcoded topic strings. This makes topic renaming, payload migration, and publisher/subscriber policy review easier.

### L. Keep MQTT/payload governance dashboards non-authoritative
A future MQTT/payload management web app or dashboard may inspect topic contracts, validate payloads, show publisher/subscriber coverage, and visualize live experiment traffic.

The dashboard UI must remain a presentation and interaction layer.

Create, update, delete, validation, and export operations should be handled by a separate MQTT/payload governance backend service.

The dashboard UI must not:
- directly edit registry files,
- directly publish operational control topics,
- directly publish unrestricted actuation commands,
- dispatch doorlock commands,
- spoof caregiver approval,
- override validator decisions,
- modify canonical policies or schemas,
- or treat dashboard observation payloads as policy truth.

The governance backend must not:
- silently modify canonical policies or schemas,
- publish actuator or doorlock commands,
- spoof caregiver approval,
- override validator decisions,
- or convert draft/proposed registry changes into live operational authority.

---

## 7. Recommended Future Extension

As implementation grows, the automation layer may be extended with:
- `make integration-test`
- `make scenario-run`
- `make benchmark`
- `make fault-eval`
- `make esp32-sim-check`
- `make latency-eval`
- `make timing-capture`
- `make closed-loop-check`
- `make mqtt-check`
- `make payload-check`
- `make payload-example-check`
- `make topic-contract-check`
- `make topic-drift-check`
- `make registry-check`
- `make governance-check`
- `make governance-backend-check`
- `make governance-ui-check`
- `make governance-dashboard-check`
- `make dashboard-check`

These targets should call device-specific scripts and shared integration, communication-contract, payload-validation, governance, or measurement assets, rather than bypassing the structured repository layout.

---

## 8. Architectural Summary

- Installation prepares each device, target platform, or optional measurement toolchain
- Configuration aligns each platform with the safe deferral architecture
- Verification confirms correct behavior before integration
- Shared frozen assets in `common/` provide the reference state
- MQTT contracts in `common/mqtt/` define topic, publisher/subscriber, and topic-payload communication assumptions
- Payload examples/templates in `common/payloads/` support implementation and testing without becoming policy authority
- `Makefile` or `justfile` should orchestrate, not replace, the structured script hierarchy
- device-specific scripts remain the primary automation units
- ESP32 workflows should be treated as cross-platform SDK/toolchain bring-up plus later embedded-node build and validation paths, not collapsed into Mac mini or Raspberry Pi automation
- Raspberry Pi workflows should remain bounded to dashboard, simulation, fault-injection, scenario orchestration, replay, progress/status publication, result artifact generation, non-authoritative MQTT/payload governance support, and closed-loop evaluation rather than hub-side runtime control
- optional timing-node workflows should be treated as experimental measurement automation, not as part of the operational control path
- MQTT/payload governance dashboards may inspect and validate contracts but must remain non-authoritative
- governance dashboard UI and governance backend service should be verified separately when implemented
- automation should validate canonical assets, topic contracts, payload examples, governance boundaries, and topic/payload drift before deployment-dependent steps proceed
