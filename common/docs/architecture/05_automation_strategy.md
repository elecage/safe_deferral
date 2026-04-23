# 05_automation_strategy.md

## Automation Strategy

This document defines the recommended automation strategy for the safe deferral system.

It reflects:
- the current frozen asset structure
- device-level separation between Mac mini, Raspberry Pi, ESP32, and optional timing infrastructure
- the staged workflow of installation, configuration, verification, and measurement-oriented evaluation
- the need for orchestration-friendly execution during development and vibe-coding

This document does not replace the canonical frozen baseline.  
Shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

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
- simulation runtime configuration
- ESP32 workspace env generation
- ESP32 sample project preparation
- ESP32 managed component preparation
- embedded node-side connection parameters aligned with the operational hub when needed
- timing-node measurement assumptions aligned when used
- out-of-band measurement profile preparation when class-wise latency evaluation is required

Configuration separation principle:
- frozen policy/schema/terminology assets are derived from `common/`
- host-local `.env`, credentials, tokens, and machine-specific files are deployment-local configuration
- deployment-local configuration must not be treated as canonical frozen policy truth

---

### C. Verification Scripts
Purpose:  
Verify that each configured service, dependency, runtime path, SDK/toolchain path, and measurement path works correctly before integration or large-scale evaluation begins.

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
- Ollama inference validation
- SQLite validation
- notification validation
- runtime asset validation
- deployed frozen asset readability checks
- canonical policy/schema/rules version alignment checks
- trigger semantics consistency checks
- Raspberry Pi base runtime checks
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
- trigger semantics
- evaluation-side validation assumptions
- ESP32 sample-build readiness before real node firmware generation proceeds

---

## 2. Role of Shared Frozen Assets

Automation does not begin from raw code alone.

The project depends on frozen shared assets stored in:
- `common/policies/`
- `common/schemas/`
- `common/docs/`
- `common/terminology/`

Representative canonical frozen assets include:
- `policy_table_v1_1_2_FROZEN.json`
- `low_risk_actions_v1_1_0_FROZEN.json`
- `fault_injection_rules_v1_4_0_FROZEN.json`
- `context_schema_v1_0_0_FROZEN.json`
- `candidate_action_schema_v1_0_0_FROZEN.json`
- `policy_router_input_schema_v1_1_1_FROZEN.json`
- `validator_output_schema_v1_1_0_FROZEN.json`
- `class_2_notification_payload_schema_v1_0_0_FROZEN.json`

Optional or version-sensitive companion assets may include:
- output profile assets
- auxiliary deployment templates
- support bundles for reproducibility or measurement workflows

These files act as the single source of truth before runtime deployment and verification.

### Authority principle
- The authoritative reference state is the frozen asset set in the Git repository.
- Mac mini and Raspberry Pi consume deployed or synchronized runtime copies as needed, but they must not redefine local policy truth.
- ESP32-oriented automation should remain consistent with the same canonical policy/schema assumptions where applicable.

---

## 3. Recommended Orchestration Layer

### Recommended
- shell scripts under device-specific script folders
- PowerShell scripts on Windows where that is the native operational path
- a top-level `Makefile` or `justfile` for orchestration
- optional measurement-oriented targets for timing and latency evaluation

### Why
- macOS-friendly and Raspberry Pi-friendly
- Windows-friendly for ESP32 host-side SDK/toolchain bring-up
- embedded-node-friendly when ESP32 build steps are introduced
- measurement-friendly when timing-node workflows are introduced
- easy to rerun individual stages
- explicit separation of responsibilities
- easier fault isolation and debugging
- suitable for vibe-coding workflows and agent guidance

### Orchestration principle
The `Makefile` or `justfile` should orchestrate the workflow, but the primary automation units should remain device-specific scripts, embedded build targets, or measurement-oriented support assets.

---

## 4. Recommended Execution Model

Because the project is split across Mac mini, Raspberry Pi, ESP32, and optional timing infrastructure, orchestration should be device-aware and evaluation-aware.

### Recommended preflight examples
```bash
make common-check
make policy-check
make schema-check
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
```

### Interpretation
- `common-check`, `policy-check`, and `schema-check` should validate the canonical shared baseline before deployment-dependent steps run
- `mac-*` targets operate on the Mac mini workflow
- `rpi-*` targets operate on the Raspberry Pi workflow and must remain bounded to simulation, fault-injection, and evaluation tasks rather than hub-side operational runtime control
- `esp32-install`, `esp32-configure`, and `esp32-verify` operate on the cross-platform ESP-IDF development-environment workflow
- `esp32-build`, `esp32-flash`, and `esp32-check` operate on embedded build/flash/validation workflows when actual node firmware is present
- measurement targets operate on timing or latency evaluation workflows when used
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

This document does not redefine emergency semantics.  
The authoritative trigger definitions remain in the shared policy table.

---

## 6. Design Principles

### A. Keep installation, configuration, and verification separate
Do not merge these concerns into one large script.

### B. Keep device-specific workflows separate
Do not collapse Mac mini, Raspberry Pi, ESP32, and optional timing infrastructure automation into a single opaque execution path.

### C. Let orchestration call scripts, not replace them
The `Makefile` or `justfile` should orchestrate the workflow, while the actual operational logic remains in shell scripts, PowerShell scripts, embedded build targets, or measurement-oriented support assets.

### D. Preserve rerunnability
Every step should be safe to rerun independently whenever possible.

### E. Respect frozen assets
Configuration and verification logic should use shared frozen assets from `common/` as reference inputs.

### F. Keep measurement automation bounded to evaluation use
Timing capture and latency evaluation should support reproducible experiments without becoming part of the operational decision path.

### G. Preserve Raspberry Pi evaluation boundary
Raspberry Pi automation should prepare and run experiment-side simulation, fault-injection, scenario orchestration, and closed-loop verification workflows only.  
It should not automate Mac mini hub-side operational runtime control.

### H. Preserve ESP32 bounded-node boundary
ESP32 automation should prepare SDK/toolchain bring-up, sample-build readiness, and later bounded node validation, but it should not be treated as an independent policy authority or collapsed into the Mac mini or Raspberry Pi runtime path.

### I. Prefer closed-loop automation over bypassed shortcuts
Automation should support scenario publication through the same input plane used by the operational system and should validate outcomes through observed audit behavior rather than bypassed internal control paths.

### J. Validate shared assets before deployment-dependent automation
Automation should fail early if canonical policy/schema/rules assets are missing, unreadable, or version-inconsistent.

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

These targets should call device-specific scripts and shared integration or measurement assets, rather than bypassing the structured repository layout.

---

## 8. Architectural Summary

- Installation prepares each device, target platform, or optional measurement toolchain
- Configuration aligns each platform with the safe deferral architecture
- Verification confirms correct behavior before integration
- Shared frozen assets in `common/` provide the reference state
- `Makefile` or `justfile` should orchestrate, not replace, the structured script hierarchy
- device-specific scripts remain the primary automation units
- ESP32 workflows should be treated as cross-platform SDK/toolchain bring-up plus later embedded-node build and validation paths, not collapsed into Mac mini or Raspberry Pi automation
- Raspberry Pi workflows should remain bounded to simulation, fault-injection, scenario orchestration, and closed-loop evaluation rather than hub-side runtime control
- optional timing-node workflows should be treated as experimental measurement automation, not as part of the operational control path
- automation should validate canonical assets before deployment-dependent steps proceed
