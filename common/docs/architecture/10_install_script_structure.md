# 10_install_script_structure.md

## Install Script Structure

## Goal
Install the required components for the Mac mini, Raspberry Pi 5, supporting embedded node workflow, and optional timing/measurement workflow in a way that is:

- rerunnable where possible
- stage-verifiable
- device-aware
- aligned with the frozen asset strategy
- suitable for vibe-coding and reproducible bring-up

---

## Core Principles

- Use **bash/zsh shell scripts** on macOS rather than platform-specific batch tooling.
- Keep **installation**, **configuration**, and **verification** separated.
- Install Python-based applications inside **virtual environments**.
- Treat the Mac mini as the **primary operational hub**.
- Treat the Raspberry Pi 5 as the **simulation and evaluation node**, not as a replacement for the Mac mini runtime.
- Treat ESP32 as the **embedded physical node layer** when bounded button, sensor, or actuator/warning nodes are used.
- Treat optional timing/measurement infrastructure as an **evaluation-only support path**, not part of the operational control path.
- Ensure scripts fail fast and emit clear logs.
- Complete **shared frozen assets** before implementation-side installation logic depends on them.

---

## Repository-Aligned Script Structure

```text
safe_deferral/
├── common/
│   ├── policies/
│   ├── schemas/
│   ├── docs/
│   │   └── architecture/
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
│   ├── code/
│   ├── firmware/
│   └── docs/
└── integration/
    ├── tests/
    ├── scenarios/
    └── measurement/
```

---

## Shared Frozen Assets Required Before Installation-Dependent Work

The following shared assets should be prepared before implementation depends on them:

- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_0_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_0_0.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

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

#### `10_install_homebrew_deps.sh`
Install or verify required macOS package dependencies.

Recommended responsibilities:
- verify Homebrew
- run `brew update`
- install required tools such as:
  - git
  - python
  - make / just if used
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

#### `30_setup_python_venv_mac.sh`
Create the Mac mini Python virtual environment.

Recommended virtual environment:
- `.venv-mac`

Recommended responsibilities:
- create virtual environment
- upgrade pip / setuptools / wheel
- verify interpreter and pip versions

---

## Mac mini Install Design Notes

- Home Assistant and Mosquitto may be managed together through a single compose stack if that remains the chosen deployment strategy.
- Core operational services belong on the **Mac mini**, not on the Raspberry Pi.
- Hub-side implementation code such as:
  - Policy Router
  - Deterministic Validator
  - Context-Integrity Safe Deferral Handler
  - Audit Logging Service
  - Outbound Notification Interface
  - Caregiver Confirmation Backend

  should live under `mac_mini/code/`, not inside install scripts.

---

## Raspberry Pi Install Scripts

### Directory
- `rpi/scripts/install/`

### Role Boundary
Raspberry Pi 5 is an **evaluation-side node**, not the operational hub.

It should install only the dependencies required for:
- virtual context generation
- virtual emergency sensing
- fault injection
- scenario orchestration
- closed-loop automated verification
- Pi-side verification utilities

It should **not** install or host Mac mini operational hub services such as:
- Home Assistant
- Ollama
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- hub-side operational audit authority

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

#### `10_install_system_packages_rpi.sh`
Install Raspberry Pi system packages.

Recommended responsibilities:
- run package index update
- install:
  - python3
  - python3-venv
  - git
  - required CLI tools
  - mosquitto-clients if needed
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
- pytest-asyncio
- PyYAML
- jsonschema
- click or typer
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
- The purpose of the Raspberry Pi install layer is to prepare a stable base for simulation and experiment execution, not to recreate the Mac mini runtime stack.

---

## ESP32 Embedded Build and Install Readiness

### Directory
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

### Role
ESP32 nodes do not necessarily follow the same shell-script installation flow as Mac mini and Raspberry Pi.  
Instead, they require an embedded build and flash workflow that should still be documented and structured.

### Recommended responsibilities
- prepare PlatformIO or Arduino build environment assumptions
- define board-specific build targets
- define firmware flash procedure
- define serial monitor or debug procedure
- define device identity, topic namespace, and broker connection assumptions
- define reset and recovery steps for embedded nodes

### Typical embedded targets
- bounded button input node
- temperature / humidity sensor node
- gas sensor node
- fire detection sensor node
- lighting control node
- doorlock or warning interface node

---

## Timing and Measurement Install Readiness

### Directory
- `integration/measurement/`

### Role
Timing and measurement support is not part of the operational decision path.  
It is an optional evaluation support path for out-of-band class-wise latency measurement.

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

### Configuration
Goal:  
Installed components are aligned with the safe deferral architecture.

### Verification
Goal:  
Each component works correctly before integration begins.

Related directories:
- `mac_mini/scripts/configure/`
- `mac_mini/scripts/verify/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`
- `esp32/docs/`
- `integration/tests/`
- `integration/scenarios/`
- `integration/measurement/`

---

## Recommended Execution Order

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

### ESP32
Typical workflow should be documented rather than assumed to match shell-based host installation.  
Examples may include:
- board selection
- firmware build
- firmware flash
- serial verification
- broker connectivity check

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
- or `common/scripts/` only if the helpers are truly cross-device and stable

Examples:
- environment loading helpers
- logging helpers
- command checks
- file/path checks

These should remain auxiliary utilities, not replace the device-specific install structure.

---

## Script Writing Rules

- use `set -euo pipefail`
- fail fast with explicit messages
- prefer safe rerun behavior where possible
- print version or health information after installation
- keep installation logic separate from configuration logic
- keep installation logic separate from verification logic
- avoid placing application logic inside install scripts
- keep embedded build logic documented separately from host-side operational scripts when ESP32 nodes are used
- keep timing/measurement support documented separately from the operational control path when out-of-band evaluation is used

---

## Architectural Summary

- Mac mini install scripts prepare the operational hub
- Raspberry Pi install scripts prepare the simulation/evaluation node only
- Raspberry Pi does not replace the Mac mini runtime stack
- ESP32 embedded workflow documentation prepares bounded physical node deployment
- optional timing/measurement readiness prepares out-of-band latency evaluation support
- shared frozen assets in `common/` define the reference state
- install scripts and embedded build preparation establish the platform only
- configuration and verification remain separate follow-on stages
