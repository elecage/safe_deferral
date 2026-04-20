# 05_automation_strategy.md

## Automation Strategy

This document defines the recommended automation strategy for the safe deferral system.

It reflects:
- the current frozen asset structure
- device-level separation between Mac mini, Raspberry Pi, and ESP32
- the staged workflow of installation, configuration, and verification
- the need for orchestration-friendly execution during development and vibe-coding

---

## 1. Recommended Automation Layers

### A. Installation Scripts
Purpose:
Prepare software, runtimes, and system dependencies on each target device.

Repository locations:
- `mac_mini/scripts/install/`
- `rpi/scripts/install/`
- `esp32/firmware/`
- `esp32/code/`

Examples:
- developer tools installation
- Docker/runtime setup
- Python virtual environment creation
- system package installation
- time synchronization client installation
- ESP32 toolchain or firmware project preparation when needed

---

### B. Configuration Scripts
Purpose:
Apply project-specific settings and deploy runtime-ready configuration.

Repository locations:
- `mac_mini/scripts/configure/`
- `rpi/scripts/configure/`
- embedded node-side configuration when needed:
  - `esp32/code/`
  - `esp32/firmware/`

Examples:
- Home Assistant configuration
- Mosquitto configuration
- Ollama setup and model pull
- SQLite initialization
- notification channel configuration
- runtime `.env` generation
- policy/schema deployment or synchronization
- simulation runtime configuration
- embedded node-side connection parameters aligned with the operational hub when needed

---

### C. Verification Scripts
Purpose:
Verify that each configured service, dependency, and runtime path works correctly before integration begins.

Repository locations:
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`
- `integration/tests/`
- `integration/scenarios/`

Examples:
- Docker service checks
- MQTT pub/sub validation
- Ollama inference validation
- SQLite validation
- notification validation
- runtime asset validation
- Raspberry Pi base runtime checks
- closed-loop audit verification
- ESP32-linked bounded input/output path validation through integration testing

---

## 2. Role of Shared Frozen Assets

Automation does not begin from raw code alone.

The project depends on frozen shared assets stored in:

- `common/policies/`
- `common/schemas/`
- `common/docs/`
- `common/terminology/`

These files act as the single source of truth before runtime deployment and verification.

Examples:
- routing policy tables
- low-risk action policies
- fault injection rules
- JSON schemas
- output profiles
- canonical terminology documents

---

## 3. Recommended Orchestration Layer

### Recommended
- shell scripts under device-specific script folders
- a top-level `Makefile` or `justfile` for orchestration

### Why
- macOS-friendly and Raspberry Pi-friendly
- embedded-node-friendly when ESP32 build steps are introduced
- easy to rerun individual stages
- explicit separation of responsibilities
- easier fault isolation and debugging
- suitable for vibe-coding workflows and agent guidance

---

## 4. Recommended Execution Model

Because the project is split across Mac mini, Raspberry Pi, and ESP32, orchestration should be device-aware.

### Recommended examples
```bash
make mac-install
make mac-configure
make mac-verify

make rpi-install
make rpi-configure
make rpi-verify
```

### ESP32-oriented examples
```bash
make esp32-build
make esp32-flash
make esp32-check
```

### Optional grouped targets
```bash
make common-check
make mac-all
make rpi-all
make verify-all
make integration-test
```

### Interpretation
- `mac-*` targets operate on the Mac mini workflow
- `rpi-*` targets operate on the Raspberry Pi workflow
- `esp32-*` targets operate on embedded device build or flash workflows when needed
- shared assets in `common/` should be validated before deployment-dependent steps run

---

## 5. Design Principles

### A. Keep installation, configuration, and verification separate
Do not merge these concerns into one large script.

### B. Keep device-specific workflows separate
Do not collapse Mac mini, Raspberry Pi, and ESP32 automation into a single opaque execution path.

### C. Let orchestration call scripts, not replace them
The `Makefile` or `justfile` should orchestrate the workflow, while the actual operational logic remains in shell scripts or device-specific build targets.

### D. Preserve rerunnability
Every step should be safe to rerun independently whenever possible.

### E. Respect frozen assets
Configuration and verification logic should use shared frozen assets from `common/` as reference inputs.

---

## 6. Recommended Future Extension

As implementation grows, the automation layer may be extended with:

- `make integration-test`
- `make scenario-run`
- `make benchmark`
- `make fault-eval`
- `make esp32-sim-check`

These targets should call device-specific scripts and shared integration assets, rather than bypassing the structured repository layout.

---

## 7. Architectural Summary

- Installation prepares each device or target platform
- Configuration aligns each platform with the safe deferral architecture
- Verification confirms correct behavior before integration
- Shared frozen assets in `common/` provide the reference state
- `Makefile` or `justfile` should orchestrate, not replace, the structured script hierarchy
- ESP32 workflows should be treated as embedded-node build and validation paths, not collapsed into Mac mini or Raspberry Pi automation