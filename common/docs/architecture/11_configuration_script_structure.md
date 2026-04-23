# 11_configuration_script_structure.md

## Configuration Script Structure

## Goal
Configure installed services, runtimes, embedded-node assumptions, and optional measurement support assumptions so that they are aligned with the current safe deferral architecture in a consistent and reproducible way.

This document does not replace the canonical frozen baseline.  
Shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

---

## Core Principles

- Keep **configuration** separate from installation and verification.
- Write configuration scripts so they **copy templates or deploy frozen assets and inject only the necessary values**.
- Store sensitive values in `.env` or separate secret files, and never commit live secrets to Git.
- Always follow configuration with verification.
- Treat shared frozen assets in `common/` as the **single source of truth** before runtime deployment.
- Inject configuration into the **actual target runtime path** rather than hardcoding paths inside templates.
- Include a **reload or restart step** when required after configuration changes are applied.
- Allow service restart behavior to branch according to the **deployment mode**.
- Complete the shared frozen asset set before implementation-side configuration depends on it.
- Treat ESP32 embedded nodes as bounded physical clients whose connection parameters, topic structure, device identity assumptions, and sample-build readiness must be configured consistently when they are used.
- Treat Raspberry Pi 5 as an **evaluation-side node**, not as a target for hub-side operational runtime configuration.
- Treat optional timing/measurement support as an **evaluation-only alignment layer**, not part of the operational control path.

---

## Shared Frozen Assets Required Before Configuration

The following assets should be finalized before configuration deployment depends on them:

### Required canonical frozen assets
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

### Terminology asset
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

### Optional or version-sensitive companion assets
- output profile assets
- auxiliary deployment templates
- reproducibility support assets

These are not just deployment files.  
They are design assets that must be fixed before reliable runtime configuration is possible.

---

## Repository-Aligned Directory Structure

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

## Configuration Target Model

### Source of truth
- `common/` stores the frozen shared reference assets

### Deployment targets
- `mac_mini/` contains hub-side configuration scripts and runtime deployment assets
- `rpi/` contains simulation-side configuration scripts and synchronized runtime assets
- `esp32/` contains embedded-node implementation assets plus cross-platform configure/verify scaffolding for bounded physical nodes
- `integration/measurement/` contains optional timing and measurement support assets for out-of-band latency evaluation when that evaluation path is used

### Principle
The Git repository stores the frozen reference state.  
The Mac mini, Raspberry Pi, ESP32 development workflow, and optional measurement workflow receive runtime-ready deployed copies or aligned configuration assumptions as needed.

Deployment-local configuration such as `.env`, secrets, host paths, and machine-specific runtime files must not redefine canonical policy or schema truth.

---

## Mac mini Configuration Scripts

### Directory
- `mac_mini/scripts/configure/`

### Frozen / expected script set
- `10_configure_home_assistant.sh`
- `20_configure_mosquitto.sh`
- `30_configure_ollama.sh`
- `40_configure_sqlite.sh`
- `50_deploy_policy_files.sh`
- `60_configure_notifications.sh`
- `70_write_env_files.sh`

---

### `10_configure_home_assistant.sh`

Recommended responsibilities:
- deploy `configuration.yaml` or equivalent runtime configuration
- apply MQTT integration settings
- deploy entity-related templates if required
- deploy automation defaults if required
- inject config into the target runtime path
- restart or reload Home Assistant as needed

---

### `20_configure_mosquitto.sh`

Recommended responsibilities:
- apply listener configuration
- apply authentication configuration if enabled
- apply persistence and log path configuration
- inject configuration into the target runtime path
- restart Mosquitto after applying settings

#### Trust-boundary rule
- The broker must be reachable from Raspberry Pi 5 on the same private LAN
- The broker must be reachable from ESP32 embedded clients on the intended trusted local network when those nodes are used
- Internet-originated inbound access must remain blocked by host or network firewall
- Optional local username/password authentication and topic ACL may be applied
- Listener settings and firewall policy should be treated as a single trust-boundary rule set

#### LAN-only operational principle
- Do not force localhost-only binding if Raspberry Pi 5 or ESP32 nodes must connect over the LAN
- A LAN-reachable bind interface may be used where appropriate
- WAN exposure must still remain blocked by firewall policy

---

### `30_configure_ollama.sh`

Recommended responsibilities:
- verify Ollama runtime availability
- pull `llama3.1`
- run a test prompt
- verify response behavior
- restart or reinitialize the service if the deployment mode requires it

---

### `40_configure_sqlite.sh`

Recommended responsibilities:
- create DB file if needed
- apply schema
- verify initial tables
- run initial write or initialization checks
- enable WAL mode

#### SQLite concurrency principle
- Do not allow multiple services to write directly to SQLite concurrently
- SQLite should be written by a **single Audit Logging Service**
- Other services should emit log events through MQTT topics or an internal async queue
- The Audit Logging Service consumes those events and writes them sequentially

---

### `50_deploy_policy_files.sh`

Recommended deployment targets:
- runtime copies of frozen policy assets
- runtime copies of frozen schema assets
- optional output profile deployment when used

Representative deployment sources:
- `common/policies/`
- `common/schemas/`

Representative deployed canonical assets:
- routing policy table
- low-risk action policy
- fault injection rules
- context schema
- candidate action schema
- policy router input schema
- validator output schema
- Class 2 notification payload schema

Optional or version-sensitive companion deployment may include:
- output profile assets
- auxiliary deployment templates

#### Deployment principle
This script deploys runtime-ready copies from the canonical frozen baseline.  
It must not create local policy truth that diverges from `common/`.

---

### `60_configure_notifications.sh`

Recommended responsibilities:
- configure Telegram token and chat ID if available
- configure mock fallback mode if Telegram is unavailable or intentionally disabled
- align outbound escalation payload behavior with `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- send or simulate a test notification
- preserve fallback behavior for offline or development environments

---

### `70_write_env_files.sh`

Recommended environment variables include:
- `MQTT_HOST`
- `MQTT_PORT`
- `OLLAMA_HOST`
- `OLLAMA_MODEL`
- `SQLITE_PATH`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- safe deferral timeout and bounded timing variables
- `DEPLOYMENT_MODE`

#### Terminology note
Old variable names or labels containing `ICR` should be renamed over time to align with the canonical term:  
**context-integrity-based safe deferral stage**

#### Deployment-local rule
`.env` files, credentials, tokens, and host-local paths are deployment-local configuration.  
They support runtime execution, but they must not redefine canonical frozen policy or schema truth.

---

## Raspberry Pi Configuration Scripts

### Directory
- `rpi/scripts/configure/`

### Role Boundary
Raspberry Pi 5 is a **simulation, fault-injection, and evaluation node**.

It should be configured only for:
- multi-node simulation runtime
- virtual emergency sensing
- fault injection
- scenario orchestration
- closed-loop automated verification
- Pi-side time synchronization and verification utilities
- synchronized runtime copies of frozen artifacts

It should **not** be configured as a host for Mac mini operational hub services such as:
- Home Assistant
- Ollama
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- hub-side operational audit authority

### Frozen / expected script set
- `10_write_env_files_rpi.sh`
- `20_sync_phase0_artifacts_rpi.sh`
- `30_configure_time_sync_rpi.sh`
- `40_configure_simulation_runtime_rpi.sh`
- `50_configure_fault_profiles_rpi.sh`

---

### `10_write_env_files_rpi.sh`

Recommended responsibilities:
- generate RPi runtime `.env`
- configure Mac mini broker host reference
- configure simulation namespace and runtime variables
- configure schema/policy sync paths
- configure time-sync target settings

---

### `20_sync_phase0_artifacts_rpi.sh`

Recommended responsibilities:
- synchronize frozen policy assets from the authoritative shared repository state
- synchronize frozen schema assets from the authoritative shared repository state
- verify required synchronized runtime assets exist

### Principle
The Raspberry Pi should not invent local policy truth.  
It should consume synchronized frozen artifacts derived from the shared reference set.

---

### `30_configure_time_sync_rpi.sh`

Recommended responsibilities:
- configure LAN-referenced time synchronization
- align the Raspberry Pi time client with the Mac mini reference host or agreed LAN time reference
- record offset and RMS offset measurements if available
- verify acceptable time-sync bounds

---

### `40_configure_simulation_runtime_rpi.sh`

Recommended responsibilities:
- configure simulation log paths
- configure scenario directories
- configure verification directories
- configure multi-node runtime assumptions
- verify required runtime variables for simulation are present
- verify required Python runtime dependencies for simulation-side execution

---

### `50_configure_fault_profiles_rpi.sh`

Recommended responsibilities:
- validate fault injection rules
- validate deterministic and randomized profiles
- verify structural consistency of fault definitions
- generate runtime configuration for fault execution and audit validation
- keep fault-profile execution assumptions aligned with canonical emergency trigger family `E001`~`E005`

### Raspberry Pi Configuration Notes
- Raspberry Pi configuration should stay bounded to the evaluation path.
- It should prepare experiment-side execution only, not recreate the Mac mini hub runtime.
- Shared frozen assets remain authoritative at the repository level, and Raspberry Pi consumes synchronized runtime copies only.
- Canonical policy/schema/rules consistency verification belongs to the **verify** stage, while configuration prepares the synchronized runtime copies and execution assumptions needed for those checks.

---

## ESP32 Configuration and Verify Alignment

### Directories
- `esp32/scripts/configure/`
- `esp32/scripts/verify/`
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

### Role
ESP32 nodes are bounded physical clients, but the repository now includes explicit cross-platform host-side configure and verify scaffolding so that ESP-IDF sample projects and later node firmware can be aligned consistently before full firmware implementation begins.

### Current reflected configure script set

#### POSIX (macOS/Linux)
- `10_write_env_files_esp32.sh`
- `20_prepare_idf_workspace_esp32.sh`
- `30_prepare_managed_components_esp32.sh`
- `40_prepare_sample_project_esp32.sh`

#### Windows
- `10_write_env_files_esp32_windows.ps1`
- `20_prepare_idf_workspace_esp32_windows.ps1`
- `30_prepare_managed_components_esp32_windows.ps1`
- `40_prepare_sample_project_esp32_windows.ps1`

### Current reflected verify script set

#### POSIX (macOS/Linux)
- `10_verify_idf_cli_esp32.sh`
- `20_verify_toolchain_target_esp32.sh`
- `30_verify_component_resolution_esp32.sh`
- `40_verify_sample_build_esp32.sh`

#### Windows
- `10_verify_idf_cli_esp32_windows.ps1`
- `20_verify_toolchain_target_esp32_windows.ps1`
- `30_verify_component_resolution_esp32_windows.ps1`
- `40_verify_sample_build_esp32_windows.ps1`

### Recommended configuration concerns
- broker host, port, and authentication assumptions
- topic namespace and device identifier conventions
- button pattern or sensor event encoding assumptions
- environmental and safety sensor topic assumptions when physical sensing is used
- actuator or warning interface topic assumptions when physical output is used
- Wi-Fi, reconnect, and fallback behavior assumptions
- firmware build, flash, and reset procedure references
- ESP-IDF workspace path and sample project path alignment
- managed component preparation and sample-build readiness

### Scope note
Configuration assumptions should distinguish:
- current canonical physical-node targets
- optional experimental targets
- planned extension targets

Examples currently include:
- current canonical: bounded button, lighting control, representative environmental sensing
- optional experimental: gas, fire, fall-detection interface
- planned extension: doorlock or warning interface

### Principle
Embedded nodes should remain bounded physical clients under hub-side policy control rather than becoming independent policy authorities.

The current ESP32 configure/verify layer is primarily a **development-environment alignment and sample-build readiness layer**.  
It is not a replacement for later real node-firmware implementation under `esp32/code/` and `esp32/firmware/`.

---

## Optional Timing and Measurement Configuration Alignment

### Directory
- `integration/measurement/`

### Role
Timing and measurement support is not part of the operational decision path.  
When used, it should be configured as an evaluation-only support layer for out-of-band class-wise latency measurement.

### Recommended configuration concerns
- timing capture assumptions for Class 0 / Class 1 / Class 2 paths
- measurement profile alignment
- latency capture reference formats
- wiring or trigger/capture note alignment
- optional STM32 timing node or dedicated measurement node assumptions
- result-template or export-format alignment for reproducible evaluation

### Principle
Measurement infrastructure should support trustworthy latency evaluation without influencing operational runtime decisions.

---

## Target Runtime Path Injection

Configuration templates and deployment files should be injected into the actual runtime target path.

Examples:
- Docker Compose environment: volume-mounted target directory
- containerized service environment: runtime bind mount or service-specific config path
- native environment: local service configuration path

The configuration document or script should describe the deployment target clearly rather than hardcoding a single universal path.

---

## Deployment Mode-Dependent Restart

After configuration changes are applied, service reloading or restarting may depend on deployment mode.

Examples:
- Docker Compose: `docker compose restart <service>`
- Native service manager: service-specific restart command
- direct runtime invocation: explicit restart or relaunch script

The configuration logic should branch according to the deployment mode where necessary.

---

## Recommended Execution Order

### Recommended preflight baseline check
Before device-specific configuration proceeds:
- verify required frozen assets exist
- verify synchronized or deployed copies will be sourced from the canonical baseline
- ensure configuration is not starting from an incomplete frozen reference state

### Mac mini
```bash
bash mac_mini/scripts/configure/70_write_env_files.sh
bash mac_mini/scripts/configure/20_configure_mosquitto.sh
bash mac_mini/scripts/configure/10_configure_home_assistant.sh
bash mac_mini/scripts/configure/30_configure_ollama.sh
bash mac_mini/scripts/configure/40_configure_sqlite.sh
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
bash mac_mini/scripts/configure/60_configure_notifications.sh
```

### Raspberry Pi
```bash
bash rpi/scripts/configure/10_write_env_files_rpi.sh
bash rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh
```

### ESP32 macOS / Linux
```bash
bash esp32/scripts/configure/10_write_env_files_esp32.sh
bash esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh
bash esp32/scripts/configure/30_prepare_managed_components_esp32.sh
bash esp32/scripts/configure/40_prepare_sample_project_esp32.sh

bash esp32/scripts/verify/10_verify_idf_cli_esp32.sh
bash esp32/scripts/verify/20_verify_toolchain_target_esp32.sh
bash esp32/scripts/verify/30_verify_component_resolution_esp32.sh
bash esp32/scripts/verify/40_verify_sample_build_esp32.sh
```

### ESP32 Windows
```powershell
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\configure\10_write_env_files_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\configure\20_prepare_idf_workspace_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\configure\30_prepare_managed_components_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\configure\40_prepare_sample_project_esp32_windows.ps1

powershell -ExecutionPolicy Bypass -File .\esp32\scripts\verify\10_verify_idf_cli_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\verify\20_verify_toolchain_target_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\verify\30_verify_component_resolution_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\verify\40_verify_sample_build_esp32_windows.ps1
```

### Optional timing / measurement path
Typical workflow may include:
- confirm measurement support notes
- align timing capture settings
- align measurement profile files
- confirm wiring or trigger/capture assumptions
- prepare result-template or export-format references

---

## Configuration Writing Rules

- use `set -euo pipefail` in POSIX shell scripts
- use explicit fail-fast handling in PowerShell scripts on Windows
- keep configuration separate from installation
- keep configuration separate from verification
- avoid committing live secrets
- prefer idempotent update or safe-skip behavior where possible
- emit explicit log messages
- verify configuration by handing off to the verify stage
- do not embed application logic inside configuration scripts
- keep embedded-node configuration and sample-build alignment separate from full node-firmware implementation
- keep timing/measurement configuration support documented separately from the operational control path when out-of-band evaluation is used
- prevent deployment-local runtime files or synchronized copies from redefining canonical frozen policy truth
- prevent silent drift from the canonical policy/schema/rules baseline

---

## Architectural Summary

- `common/` stores the frozen shared reference assets
- `mac_mini/scripts/configure/` configures the operational hub
- `rpi/scripts/configure/` configures the simulation and evaluation node only
- Raspberry Pi does not replace the Mac mini hub runtime
- `esp32/scripts/configure/` and `esp32/scripts/verify/` align the cross-platform ESP-IDF workspace and sample-build readiness for bounded node development
- `esp32/code/` and `esp32/firmware/` remain the later target areas for real node-firmware implementation
- `integration/measurement/` stores optional timing and measurement support alignment assets
- configuration scripts and embedded/measurement configuration alignment deploy runtime-ready values and assumptions
- runtime correctness is confirmed later in the verify stage
