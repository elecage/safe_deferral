# 10_install_script_structure.md

> Legacy source note: The active architecture entry point is `00_architecture_index.md`. This file is retained for detailed source context and should not be used as the first active baseline.


## Install Script Structure

## Goal
Install the required components for the Mac mini, Raspberry Pi 5, ESP32 development environment, and optional timing/measurement workflow in a way that is:

- rerunnable where possible
- stage-verifiable
- device-aware
- aligned with the frozen asset strategy
- aligned with MQTT topic / payload contract governance
- aligned with Class 2 clarification / transition verification needs
- suitable for vibe-coding and reproducible bring-up

This document does not replace the canonical frozen baseline.  
Shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

Current interface, communication, and payload references:
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/19_class2_clarification_architecture_alignment.md`
- `common/docs/architecture/20_scenario_data_flow_matrix.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/mqtt/topic_registry.json`
- `common/mqtt/publisher_subscriber_matrix.md`
- `common/mqtt/topic_payload_contracts.md`
- `common/payloads/README.md`

---

## Core Principles

- Use **bash/zsh shell scripts** on macOS/Linux host environments where appropriate.
- Use **PowerShell** on Windows where that is the native operational path.
- Keep **installation**, **configuration**, and **verification** separated.
- Install Python-based applications inside **virtual environments** where host-side Python services are used.
- Treat the Mac mini as the **primary operational hub**.
- Treat the Raspberry Pi 5 as the **experiment dashboard, simulation, orchestration, replay, fault-injection, evaluation, Class 2 transition verification, and non-authoritative MQTT/payload governance support node**, not as a replacement for the Mac mini runtime.
- Treat ESP32 as the **embedded physical node layer** with its own cross-platform SDK/toolchain setup workflow.
- Treat optional timing/measurement infrastructure as an **evaluation-only support path**, not part of the operational control path.
- Ensure scripts fail fast and emit clear logs.
- Complete **shared frozen assets** before implementation-side installation logic depends on them.
- Prepare dependency support for MQTT topic registry loading, payload validation, clarification interaction payload validation, topic drift checks, validation report export, dashboard/governance backend/UI support, and Class 2 transition verifier execution where those components are implemented.
- Keep governance dashboard UI separated from the MQTT/payload governance backend service.
- Do not let install-time convenience rewrite canonical policy/schema truth.
- Do not let installation of governance tooling create policy, validator, caregiver approval, audit, actuator, Class 2 transition, or doorlock execution authority.

---

## Repository-Aligned Script Structure

```text
safe_deferral/
├── common/
│   ├── policies/
│   ├── schemas/
│   ├── mqtt/
│   ├── payloads/
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

## Shared Frozen Assets and Shared References Required Before Installation-Dependent Work

The following shared assets should be prepared before implementation depends on them.

### Required canonical frozen authority assets
- `common/policies/policy_table.json`
- `common/policies/low_risk_actions.json`
- `common/policies/fault_injection_rules.json`
- `common/schemas/context_schema.json`
- `common/schemas/candidate_action_schema.json`
- `common/schemas/policy_router_input_schema.json`
- `common/schemas/validator_output_schema.json`
- `common/schemas/class2_notification_payload_schema.json`
- `common/schemas/clarification_interaction_schema.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

### Required communication / payload reference assets
- `common/mqtt/topic_registry.json`
- `common/mqtt/publisher_subscriber_matrix.md`
- `common/mqtt/topic_payload_contracts.md`
- `common/payloads/README.md`
- `common/payloads/examples/`
- `common/payloads/templates/`

### Required architecture references
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/19_class2_clarification_architecture_alignment.md`
- `common/docs/architecture/20_scenario_data_flow_matrix.md`

### Required Class 2 clarification / transition references
- `common/schemas/clarification_interaction_schema.json`
- Class 2 clarification scenario fixtures under `integration/scenarios/` when implemented
- Class 2 transition verifier fixtures under `integration/tests/` when implemented
- Class 2-to-Class 1, Class 2-to-Class 0, and Class 2 timeout/safe-deferral scenario definitions when implemented

### Optional or version-sensitive companion assets
- output profile assets
- auxiliary deployment templates
- reproducibility support assets

### Principle
Install scripts may depend on the existence of the frozen/reference baseline, but they do not redefine it.  
Canonical policy and schema truth remains under `common/policies/` and `common/schemas/`.

`common/mqtt/` and `common/payloads/` are shared reference layers for communication contracts and payload examples/templates. They must not override canonical policy or schema authority.

`common/docs/architecture/15_interface_matrix.md` is the MQTT-aware interface contract reference used to guide topic-facing installation, configuration, and later verification assumptions.

`clarification_interaction_schema.json` is the current Class 2 clarification interaction schema. Install scripts may verify that it is present and prepare dependencies for validating it, but they must not promote clarification payloads into validator approval, actuation authorization, emergency trigger authority, or doorlock authorization.

---

## Mac mini Install Scripts

### Directory
- `mac_mini/scripts/install/`

### Frozen / expected script set
- `00_preflight.sh`
- `10_install_homebrew_deps.sh`
- `20_install_docker_runtime_mac.sh`
- `21_prepare_compose_stack_mac.sh`
- `30_setup_python_venv_mac.sh`

### Role of each script

#### `00_preflight.sh`
Pre-install checks.

Recommended responsibilities:
- verify macOS environment
- verify CPU architecture
- verify Python availability
- verify Homebrew availability or installability
- verify Docker readiness expectations
- verify disk space
- verify network connectivity
- prepare workspace directories
- verify that required frozen asset baseline is present before install-dependent implementation proceeds
- verify that `common/schemas/clarification_interaction_schema.json` exists
- verify that `common/mqtt/`, `common/payloads/`, `15_interface_matrix.md`, `16_system_architecture_figure.md`, `17_payload_contract_and_registry.md`, `19_class2_clarification_architecture_alignment.md`, `20_scenario_data_flow_matrix.md`, and `12_prompts_mqtt_payload_governance.md` exist when registry/payload-aware implementation is in scope
- verify that install-time checks do not claim Class 2 transition or actuation correctness; those belong to configuration/verification/integration stages

#### `10_install_homebrew_deps.sh`
Install or verify required macOS package dependencies.

Recommended responsibilities:
- verify Homebrew
- run `brew update`
- install required tools such as:
  - git
  - python
  - make / just if used
  - jq or equivalent JSON inspection helper
  - mosquitto clients when local CLI pub/sub testing is needed
  - other required CLI dependencies

#### `20_install_docker_runtime_mac.sh`
Prepare Docker runtime on the Mac mini.

Recommended responsibilities:
- install or verify Docker Desktop / equivalent runtime
- verify `docker compose`
- verify base Docker health

#### `21_prepare_compose_stack_mac.sh`
Prepare the Mac mini compose stack.

Recommended deployment targets:
- Home Assistant
- Mosquitto MQTT Broker
- optional service skeletons for future hub-side runtime modules

Recommended responsibilities:
- prepare `docker-compose.yml` or `compose.yaml`
- prepare fixed internal network naming
- prepare service DNS expectations
- prepare volume mount paths
- prepare runtime configuration directories
- prepare mount/path assumptions for deployed or synchronized MQTT registry and payload reference files when needed
- prepare runtime path assumptions for `clarification_interaction_schema.json` and Class 2 audit output when implemented

#### `30_setup_python_venv_mac.sh`
Create the Mac mini Python virtual environment.

Recommended virtual environment:
- `.venv-mac`

Recommended responsibilities:
- create virtual environment
- upgrade pip / setuptools / wheel
- verify interpreter and pip versions
- prepare dependency support for JSON schema validation
- prepare dependency support for MQTT topic registry loading
- prepare dependency support for payload validation helpers
- prepare dependency support for clarification interaction payload validation
- prepare dependency support for Class 2 transition verifier adapters when implemented
- prepare dependency support for payload example validation
- prepare dependency support for topic drift checks where implemented
- prepare dependency support for validation report export where implemented
- prepare dependency support for MQTT testing utilities when implemented

---

## Mac mini Install Design Notes

- Home Assistant and Mosquitto may be managed together through a single compose stack if that remains the chosen deployment strategy.
- Core operational services belong on the **Mac mini**, not on the Raspberry Pi.
- Hub-side implementation code such as:
  - Policy Router
  - Deterministic Validator
  - Context-Integrity Safe Deferral Handler
  - Class 2 Clarification Manager
  - Audit Logging Service
  - Outbound Notification Interface
  - Caregiver Confirmation Backend
  - MQTT Topic Registry Loader / Contract Checker
  - Payload Validation Helper

  should live under `mac_mini/code/`, not inside install scripts.
- Compose files, runtime directories, and local runtime assets under `mac_mini/runtime/` are deployment/runtime surfaces, not the canonical source of policy truth.
- Mac mini runtime apps should not hardcode MQTT topics or payload contracts where registry lookup is practical.
- Class 2 Clarification Manager installation support must remain platform/dependency preparation only; it does not create actuation authority.

---

## Raspberry Pi Install Scripts

### Directory
- `rpi/scripts/install/`

### Role Boundary
Raspberry Pi 5 is an **evaluation-side node**, not the operational hub.

It should install only the dependencies required for:
- experiment and monitoring dashboard
- MQTT/payload governance backend service
- governance dashboard UI
- topic/payload contract validation utility
- payload example manager / validator
- clarification interaction payload validator
- Class 2 transition verifier
- publisher/subscriber role manager
- virtual context generation
- virtual `doorbell_detected` visitor-response context generation
- virtual emergency sensing
- fault injection
- scenario orchestration
- scenario replay
- Class 2-to-Class 1 / Class 2-to-Class 0 / Class 2 timeout scenario replay
- progress/status publication
- result artifact export
- closed-loop automated verification
- Pi-side verification utilities

It should **not** install or host Mac mini operational hub services or authorities such as:
- Home Assistant
- Ollama
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- Class 2 Clarification Manager
- hub-side operational audit authority
- validator authority
- caregiver approval authority
- direct actuator dispatch authority
- doorlock dispatch authority
- direct registry-file editing through dashboard UI
- canonical policy/schema editing authority
- governance backend publishing actuator or doorlock commands
- Class 2 transition authority

### Frozen / expected script set
- `00_preflight_rpi.sh`
- `10_install_system_packages_rpi.sh`
- `20_create_python_venv_rpi.sh`
- `30_install_python_deps_rpi.sh`
- `40_install_time_sync_client_rpi.sh`

### Role of each script

#### `00_preflight_rpi.sh`
Pre-install checks for Raspberry Pi.

Recommended responsibilities:
- verify OS/runtime assumptions
- verify Python availability
- verify package manager availability
- verify network reachability
- verify disk space
- prepare workspace directories
- confirm evaluation-node-only installation assumptions
- verify registry/payload reference path expectations when synchronized copies are required later
- verify that the Class 2 clarification schema and scenario/test fixture directories are present when Class 2 transition evaluation is in scope

#### `10_install_system_packages_rpi.sh`
Install Raspberry Pi system packages.

Recommended responsibilities:
- run package index update
- install:
  - python3
  - python3-venv
  - git
  - required CLI tools
  - jq or equivalent JSON inspection helper
  - mosquitto-clients if needed
  - optional build/runtime packages required by dashboard/export tooling
  - other runtime dependencies

#### `20_create_python_venv_rpi.sh`
Create the Raspberry Pi Python virtual environment.

Recommended virtual environment:
- `.venv-rpi`

Recommended responsibilities:
- create virtual environment
- upgrade pip / setuptools / wheel
- verify interpreter and pip versions

#### `30_install_python_deps_rpi.sh`
Install Raspberry Pi Python dependencies.

Representative dependencies:
- paho-mqtt
- pytest
- PyYAML
- jsonschema
- FastAPI or equivalent dashboard/backend dependency when experiment dashboard or governance backend is implemented
- uvicorn or equivalent ASGI server when dashboard/backend service is implemented
- governance backend service dependencies when implemented
- governance dashboard UI dependencies when implemented
- payload/schema validation helper dependencies
- clarification interaction payload validation dependencies
- Class 2 transition verifier dependencies
- payload example validation dependencies
- CSV/JSON export dependencies
- validation report export dependencies
- topic drift check dependencies where implemented
- publisher/subscriber role review dependencies where implemented
- optional plotting/export dependencies
- optional CLI helper packages
- optional data-generation libraries
- optional numeric libraries if needed by simulation logic

#### `40_install_time_sync_client_rpi.sh`
Install the time synchronization client for the simulation/evaluation node.

Recommended responsibilities:
- install chrony or equivalent supported client
- prepare the node for Mac mini-referenced or agreed LAN-referenced time synchronization
- record that actual offset validation belongs to the verify stage, not the install stage

### Raspberry Pi Install Design Notes

- Raspberry Pi 5 should consume synchronized runtime copies of frozen assets later during configuration, not invent local policy truth during installation.
- Install scripts should remain **rerunnable**, **stage-verifiable**, and clearly bounded to the evaluation path.
- The purpose of the Raspberry Pi install layer is to prepare a stable base for dashboard, simulation, orchestration, fault-injection, Class 2 transition verification, result export, governance support, and experiment execution, not to recreate the Mac mini runtime stack.
- MQTT/payload governance tooling on Raspberry Pi is allowed only as backend-supported inspection, validation, draft/report generation, and dashboard UI support.
- Governance dashboard UI must remain separated from the governance backend service.
- Governance dashboard installation must not introduce policy override, validator override, caregiver approval spoofing, direct registry-file editing, direct actuator command authority, Class 2 transition authority, or doorlock dispatch authority.
- Governance backend installation must not introduce canonical policy/schema editing authority or actuator/doorlock command publishing authority.
- Canonical policy/schema/rules consistency verification, topic/payload contract verification, clarification interaction schema verification, and Class 2 transition verification belong to the **verify/integration** stage, while install scripts only prepare the dependencies and runtime needed for those checks.

---

## ESP32 Install Scripts and Embedded Build Readiness

### Directories
- `esp32/scripts/install/mac/`
- `esp32/scripts/install/linux/`
- `esp32/scripts/install/windows/`
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

### Role
ESP32 nodes are bounded physical clients, but the repository contains an explicit cross-platform host-side setup path for ESP32 development.

The install layer prepares:
- host prerequisite packages
- ESP-IDF clone and toolchain installation
- board-build readiness on macOS / Linux / Windows

It does **not** yet represent finished node firmware implementation.

### Current reflected script set

#### macOS
- `00_preflight_esp32_mac.sh`
- `10_install_prereqs_esp32_mac.sh`
- `20_install_esp_idf_esp32_mac.sh`

#### Linux
- `00_preflight_esp32_linux.sh`
- `10_install_prereqs_esp32_linux.sh`
- `20_install_esp_idf_esp32_linux.sh`

#### Windows
- `00_preflight_esp32_windows.ps1`
- `10_install_prereqs_esp32_windows.ps1`
- `20_install_esp_idf_esp32_windows.ps1`

### Recommended responsibilities
- verify host OS suitability
- verify package manager or installer availability
- install prerequisite tools such as:
  - git
  - python
  - cmake
  - ninja
  - dfu-util where applicable
- clone ESP-IDF into a stable host workspace path
- run `install.sh` or `install.ps1`
- prepare `export.sh` / `export.ps1` activation readiness
- prepare later configure/verify stages for sample build execution

### Current embedded targets in scope

#### Current canonical targets
- bounded button input node
- lighting control node
- representative environmental sensing node used in the current validation baseline
- doorbell / visitor-arrival context node emitting `environmental_context.doorbell_detected` where visitor-response validation is included

#### Optional experimental targets
- gas sensor node
- fire detection sensor node
- fall-detection interface node

#### Planned extension targets
- doorlock or warning interface node

### Principle
ESP32 install scripts prepare the **SDK/toolchain environment**, while later prompts and firmware templates define the actual node code.  
ESP32 nodes remain bounded physical clients under hub-side policy control rather than becoming independent policy authorities.

Doorbell / visitor-arrival context must not be emitted as emergency evidence or doorlock authorization.  
Doorlock or warning interface nodes must not locally reinterpret doorlock as autonomous Class 1 authority.

---

## Timing and Measurement Install Readiness

### Directory
- `integration/measurement/`

### Role
Timing and measurement support is not part of the operational decision path.  
It is an optional evaluation support path for out-of-band class-wise latency measurement and must not become part of the operational control plane.

### Recommended responsibilities
- prepare timing-node support notes when used
- prepare optional timing-node toolchain assumptions
- prepare measurement workspace and result templates
- prepare latency capture references
- prepare measurement wiring or capture notes
- prepare reusable measurement profile files when needed

### Typical support targets
- optional STM32 timing node
- optional dedicated measurement node
- class-wise latency experiment profiles
- timing capture templates

---

## Relationship to Configure and Verify Stages

Installation or build preparation is not responsible for full runtime correctness.

### Installation
Goal:  
Software, runtimes, toolchains, or build prerequisites are present on the target platform.

Installation may prepare dependency support and filesystem paths for later MQTT registry loading, payload example/template access, dashboard runtime, governance backend service, governance dashboard UI, topic drift checks, clarification interaction payload validation, Class 2 transition verification, validation report export, and topic/payload validation, but actual topic/payload/Class 2 consistency checks belong to verification or integration tests.

### Configuration
Goal:  
Installed components are aligned with the safe deferral architecture.

### Verification
Goal:  
Each component works correctly before integration begins.

Required Class 2 verification targets prepared by install/configure but executed in verify/integration stages:
- clarification interaction schema installation check
- Class 2 clarification fixture installation check
- Class 2 transition verifier dependency check
- Class 2-to-Class 1 replay/verification support
- Class 2-to-Class 0 replay/verification support
- Class 2 timeout/safe-deferral replay/verification support
- audit path readiness for clarification candidates, selections, timeouts, transition targets, and final safe outcomes

Related directories:
- `common/mqtt/`
- `common/payloads/`
- `common/schemas/`
- `mac_mini/scripts/configure/`
- `mac_mini/scripts/verify/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`
- `esp32/scripts/configure/`
- `esp32/scripts/verify/`
- `esp32/docs/`
- `integration/tests/`
- `integration/scenarios/`
- `integration/measurement/`

---

## Recommended Execution Order

### Recommended preflight baseline check
Before device-specific installation proceeds:
- verify required frozen assets exist
- verify canonical baseline version set is present
- verify `common/schemas/clarification_interaction_schema.json` exists
- verify MQTT topic registry and payload reference directories exist
- verify legacy source references and prompt support files still exist when this legacy script guidance is consulted
- verify Class 2 clarification fixture directories or planned locations exist when Class 2 transition evaluation is in scope
- ensure install-dependent work is not starting from an incomplete frozen/reference state

### Mac mini
```bash
bash mac_mini/scripts/install/00_preflight.sh
bash mac_mini/scripts/install/10_install_homebrew_deps.sh
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh
```

### Raspberry Pi
```bash
bash rpi/scripts/install/00_preflight_rpi.sh
bash rpi/scripts/install/10_install_system_packages_rpi.sh
bash rpi/scripts/install/20_create_python_venv_rpi.sh
bash rpi/scripts/install/30_install_python_deps_rpi.sh
bash rpi/scripts/install/40_install_time_sync_client_rpi.sh
```

### ESP32 macOS
```bash
bash esp32/scripts/install/mac/00_preflight_esp32_mac.sh
bash esp32/scripts/install/mac/10_install_prereqs_esp32_mac.sh
bash esp32/scripts/install/mac/20_install_esp_idf_esp32_mac.sh
```

### ESP32 Linux
```bash
bash esp32/scripts/install/linux/00_preflight_esp32_linux.sh
bash esp32/scripts/install/linux/10_install_prereqs_esp32_linux.sh
bash esp32/scripts/install/linux/20_install_esp_idf_esp32_linux.sh
```

### ESP32 Windows
```powershell
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\install\windows\00_preflight_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\install\windows\10_install_prereqs_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\install\windows\20_install_esp_idf_esp32_windows.ps1
```

### Optional timing / measurement path
Typical workflow may include:
- timing support notes check
- measurement workspace preparation
- optional timing-node toolchain preparation
- latency capture reference check
- result template preparation

---

## Optional Future Extensions

If common shell helpers are introduced later, they should not collapse the repository into a single flat `scripts/` root.

Recommended future locations:
- `mac_mini/scripts/lib/`
- `rpi/scripts/lib/`
- `esp32/scripts/lib/` where a stable cross-platform helper layout becomes justified
- or `common/scripts/` only if the helpers are truly cross-device and stable

Examples:
- environment loading helpers
- logging helpers
- command checks
- file/path checks
- topic registry loading helpers
- payload validation helpers
- clarification interaction validation helpers
- Class 2 transition verifier helpers
- topic drift check helpers
- governance backend/UI separation check helpers
- validation report export helpers

These should remain auxiliary utilities, not replace the device-specific install structure.

---

## Script Writing Rules

- use `set -euo pipefail` in POSIX shell scripts
- use explicit fail-fast handling in PowerShell scripts on Windows
- fail fast with explicit messages
- prefer safe rerun behavior where possible
- print version or health information after installation
- keep installation logic separate from configuration logic
- keep installation logic separate from verification logic
- avoid placing application logic inside install scripts
- keep embedded SDK/toolchain setup separate from actual firmware implementation
- keep timing/measurement support documented separately from the operational control path when out-of-band evaluation is used
- do not hardcode MQTT topic strings or payload contracts in install-time generated app configs where registry lookup is practical
- install scripts may prepare registry/payload/schema paths but must not rewrite policy/schema truth
- install scripts may prepare dependencies for clarification interaction payload validation and Class 2 transition verification, but actual Class 2 verification belongs to verify/integration stages
- install scripts may prepare dependencies for topic drift checks, but actual drift checks belong to verification
- dashboard/governance tooling installed by Raspberry Pi scripts must remain non-authoritative
- governance dashboard UI must not directly edit registry files
- governance backend must not directly modify canonical policies or schemas
- governance tooling must not publish actuator or doorlock commands
- governance or install tooling must not convert clarification payloads into authorization payloads
- prevent deployment-local runtime files or synchronized copies from redefining canonical frozen policy truth

---

## Architectural Summary

- Mac mini install scripts prepare the operational hub
- Raspberry Pi install scripts prepare the dashboard/simulation/orchestration/fault-injection/evaluation/governance-support/Class 2 transition verification node only
- Raspberry Pi does not replace the Mac mini runtime stack
- Raspberry Pi governance support remains non-authoritative and must preserve governance backend/UI separation
- ESP32 install scripts prepare the cross-platform ESP-IDF development environment for bounded physical node implementation, including future doorbell / visitor-arrival context node work
- optional timing/measurement readiness prepares out-of-band latency evaluation support
- shared frozen assets in `common/policies/` and `common/schemas/` define the policy/schema authority state
- `clarification_interaction_schema.json` defines the current Class 2 clarification interaction payload structure
- shared MQTT contracts in `common/mqtt/` and payload examples/templates in `common/payloads/` define reference state for communication and payload governance
- `common/docs/architecture/15_interface_matrix.md` defines the MQTT-aware interface contract reference
- install scripts and embedded build preparation establish the platform only
- configuration and verification remain separate follow-on stages
