# 11_configuration_script_structure.md

## Configuration Script Structure

## Goal
Configure installed services, runtimes, and embedded-node assumptions so that they are aligned with the current safe deferral architecture in a consistent and reproducible way.

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
- Treat ESP32 embedded nodes as bounded physical clients whose connection parameters, topic structure, and device identity assumptions must be configured consistently when they are used.

---

## Shared Frozen Assets Required Before Configuration

The following assets should be finalized before configuration deployment depends on them:

### Shared policy assets
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_0_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_0_0.json`

### Shared schema assets
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_0_0_FROZEN.json`

### Terminology asset
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

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
│   ├── code/
│   ├── firmware/
│   └── docs/
└── integration/
    ├── tests/
    └── scenarios/
```

---

## Configuration Target Model

### Source of truth
- `common/` stores the frozen shared reference assets

### Deployment targets
- `mac_mini/` contains hub-side configuration scripts and runtime deployment assets
- `rpi/` contains simulation-side configuration scripts and synchronized runtime assets
- `esp32/` contains embedded-node implementation assets and configuration assumptions for bounded physical nodes when those nodes are used

### Principle
The Git repository stores the frozen reference state.  
The Mac mini, Raspberry Pi, and embedded-node workflow receive runtime-ready deployed copies or aligned configuration assumptions as needed.

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
- optional output profile deployment

Representative deployment sources:
- `common/policies/`
- `common/schemas/`

Representative deployed assets:
- routing policy table
- low-risk action policy
- fault injection rules
- output profile
- context schema
- candidate action schema
- policy router input schema
- validator output schema

---

### `60_configure_notifications.sh`

Recommended responsibilities:
- configure Telegram token and chat ID if available
- configure mock fallback mode if Telegram is unavailable or intentionally disabled
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

---

## Raspberry Pi Configuration Scripts

### Directory
- `rpi/scripts/configure/`

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
- synchronize frozen policy assets from the authoritative hub-side source
- synchronize frozen schema assets from the authoritative hub-side source
- verify required synchronized runtime assets exist

### Principle
The Raspberry Pi should not invent local policy truth.
It should consume synchronized frozen artifacts derived from the shared reference set.

---

### `30_configure_time_sync_rpi.sh`

Recommended responsibilities:
- configure LAN-referenced time synchronization
- align the Raspberry Pi time client with the Mac mini reference host
- record offset and RMS offset measurements if available
- verify acceptable time-sync bounds

---

### `40_configure_simulation_runtime_rpi.sh`

Recommended responsibilities:
- configure simulation log paths
- configure scenario directories
- configure verification directories
- verify required runtime variables for simulation are present
- verify required Python runtime dependencies for simulation-side execution

---

### `50_configure_fault_profiles_rpi.sh`

Recommended responsibilities:
- validate fault injection rules
- validate deterministic and randomized profiles
- verify structural consistency of fault definitions
- generate runtime configuration for fault execution and audit validation

---

## ESP32 Embedded Configuration Alignment

### Directory
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

### Role
ESP32 nodes do not necessarily follow the same shell-script configuration flow as Mac mini and Raspberry Pi.
Instead, the project should explicitly document and align embedded-node configuration assumptions.

### Recommended configuration concerns
- broker host, port, and authentication assumptions
- topic namespace and device identifier conventions
- button pattern or sensor event encoding assumptions
- actuator or warning interface topic assumptions when physical output is used
- Wi-Fi, reconnect, and fallback behavior assumptions
- firmware build, flash, and reset procedure references

### Principle
Embedded nodes should remain bounded physical clients under hub-side policy control rather than becoming independent policy authorities.

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

### ESP32
Typical workflow should be documented rather than assumed to match shell-based host configuration.
Examples may include:
- set or confirm broker connection assumptions
- set or confirm topic namespace and device identity
- build or rebuild firmware with aligned configuration
- flash firmware to device
- verify broker connectivity on the trusted local network

---

## Configuration Writing Rules

- use `set -euo pipefail`
- keep configuration separate from installation
- keep configuration separate from verification
- avoid committing live secrets
- prefer idempotent update or safe-skip behavior where possible
- emit explicit log messages
- verify configuration by handing off to the verify stage
- do not embed application logic inside configuration scripts
- keep embedded-node configuration assumptions documented separately from host-side operational scripts when ESP32 nodes are used

---

## Architectural Summary

- `common/` stores the frozen shared reference assets
- `mac_mini/scripts/configure/` configures the operational hub
- `rpi/scripts/configure/` configures the simulation and evaluation node
- `esp32/` stores embedded-node implementation assets and aligned configuration assumptions
- configuration scripts and embedded configuration alignment deploy runtime-ready values and assumptions
- runtime correctness is confirmed later in the verify stage