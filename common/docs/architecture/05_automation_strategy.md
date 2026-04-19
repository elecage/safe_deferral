# 05_automation_strategy.md

## Automation Strategy

This document defines the recommended automation strategy for the safe deferral system.

It reflects:
- the current frozen asset structure
- device-level separation between Mac mini and Raspberry Pi
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

Examples:
- developer tools installation
- Docker/runtime setup
- Python virtual environment creation
- system package installation
- time synchronization client installation

---

### B. Configuration Scripts
Purpose:
Apply project-specific settings and deploy runtime-ready configuration.

Repository locations:
- `mac_mini/scripts/configure/`
- `rpi/scripts/configure/`

Examples:
- Home Assistant configuration
- Mosquitto configuration
- Ollama setup and model pull
- SQLite initialization
- notification channel configuration
- runtime `.env` generation
- policy/schema deployment or synchronization
- simulation runtime configuration

---

### C. Verification Scripts
Purpose:
Verify that each configured service, dependency, and runtime path works correctly before integration begins.

Repository locations:
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`

Examples:
- Docker service checks
- MQTT pub/sub validation
- Ollama inference validation
- SQLite validation
- notification validation
- runtime asset validation
- Raspberry Pi base runtime checks
- closed-loop audit verification

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
- easy to rerun individual stages
- explicit separation of responsibilities
- easier fault isolation and debugging
- suitable for vibe-coding workflows and agent guidance

---

## 4. Recommended Execution Model

Because the project is split across Mac mini and Raspberry Pi, orchestration should be device-aware.

### Recommended examples
```bash
make mac-install
make mac-configure
make mac-verify

make rpi-install
make rpi-configure
make rpi-verify