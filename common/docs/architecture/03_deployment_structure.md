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
Software, runtimes, and services are present on the target machine.

### Examples
- Home Assistant installed
- Mosquitto installed
- Ollama installed
- Python virtual environment created
- system packages installed
- time synchronization client installed

### Repository mapping
- `mac_mini/scripts/install/`
- `rpi/scripts/install/`

### Interpretation
Installation means the required platform dependencies are available, but not yet configured for the safe deferral architecture.

---

## B. Configuration

### Goal
Installed services and runtimes are configured for the safe deferral system architecture.

### Examples
- Home Assistant MQTT integration configured
- Mosquitto listener and authentication config applied
- Ollama model pulled and made available
- frozen policy and schema files deployed
- Telegram or mock notification settings configured
- SQLite schema initialized
- runtime `.env` files written
- simulation runtime parameters configured

### Repository mapping
- source of truth: `common/`
- deployment/configuration scripts:
  - `mac_mini/scripts/configure/`
  - `rpi/scripts/configure/`

### Interpretation
Configuration means the installed components are now aligned with the project architecture, frozen assets, and runtime assumptions.

---

## C. Verification

### Goal
Each service, dependency, and runtime path works correctly before integration begins.

### Examples
- MQTT pub/sub test passes
- Home Assistant starts correctly
- Ollama inference returns expected output
- SQLite can store and read audit log entries
- notification channel works
- runtime assets are present and valid
- Raspberry Pi simulation runtime passes base checks
- closed-loop audit verification passes

### Repository mapping
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`

### Interpretation
Verification is performed before full integration in order to confirm that each service and runtime layer behaves correctly in isolation.

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

## Architectural Summary

- **Installation** prepares the platform.
- **Configuration** aligns the platform with the safe deferral architecture.
- **Verification** confirms that each configured component works correctly before integration.
- **Shared frozen assets** provide the reference state used by both Mac mini and Raspberry Pi workflows.