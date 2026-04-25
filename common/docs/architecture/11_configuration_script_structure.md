# 11_configuration_script_structure.md

## Configuration Script Structure

## Goal
Configure installed services, runtimes, embedded-node assumptions, MQTT topic/payload references, dashboard/governance tooling, and optional measurement support assumptions so that they are aligned with the current safe deferral architecture in a consistent and reproducible way.

This document does not replace the canonical frozen baseline.  
Shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

Current interface, communication, and payload references:
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`

---

## Core Principles

- Keep **configuration** separate from installation and verification.
- Write configuration scripts so they **copy templates or deploy frozen assets and inject only the necessary values**.
- Store sensitive values in `.env` or separate secret files, and never commit live secrets to Git.
- Always follow configuration with verification.
- Treat shared frozen assets in `common/` as the **single source of truth** before runtime deployment.
- Treat `common/mqtt/` and `common/payloads/` as shared reference layers for communication contracts and payload examples/templates, not as policy authority.
- Inject configuration into the **actual target runtime path** rather than hardcoding paths inside templates.
- Include a **reload or restart step** when required after configuration changes are applied.
- Allow service restart behavior to branch according to the **deployment mode**.
- Complete the shared frozen asset set before implementation-side configuration depends on it.
- Runtime apps, dashboard apps, and experiment tools should load topic/payload references from registry paths when practical.
- Treat ESP32 embedded nodes as bounded physical clients whose connection parameters, topic structure, device identity assumptions, and sample-build readiness must be configured consistently when they are used.
- Treat Raspberry Pi 5 as an **evaluation-side dashboard, simulation, orchestration, replay, fault-injection, result-artifact, and non-authoritative MQTT/payload governance support node**, not as a target for hub-side operational runtime configuration.
- Treat Raspberry Pi dashboard/governance tooling as non-authoritative inspection, validation, draft/report, and UI support.
- Keep governance dashboard UI separated from the MQTT/payload governance backend service.
- Configuration may prepare governance paths, ports, modes, and service endpoints, but it must not create policy, validator, caregiver approval, audit, actuator, or doorlock execution authority.
- Treat optional timing/measurement support as an **evaluation-only alignment layer**, not part of the operational control path.

---

## Shared Frozen Assets and Shared References Required Before Configuration

The following assets should be finalized before configuration deployment depends on them.

### Required canonical frozen authority assets
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

### Required communication / payload reference assets
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`
- `common/payloads/examples/`
- `common/payloads/templates/`

### Required architecture / terminology assets
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

### Optional or version-sensitive companion assets
- output profile assets
- auxiliary deployment templates
- reproducibility support assets

These are not just deployment files.  
They are design and reference assets that must be fixed before reliable runtime configuration is possible.

### Authority note
- `common/policies/` and `common/schemas/` remain policy and validation authority.
- `common/mqtt/` defines communication-contract references.
- `common/payloads/` provides payload examples/templates.
- `common/docs/architecture/15_interface_matrix.md` defines the MQTT-aware interface contract reference.
- MQTT contracts and payload examples must not override canonical policies or schemas.

---

## Repository-Aligned Directory Structure

```text
safe_deferral/
├── common/
│   ├── policies/
│   ├── schemas/
│   ├── mqtt/
│   │   ├── README.md
│   │   ├── topic_registry_v1_0_0.json
│   │   ├── publisher_subscriber_matrix_v1_0_0.md
│   │   └── topic_payload_contracts_v1_0_0.md
│   ├── payloads/
│   │   ├── README.md
│   │   ├── examples/
│   │   └── templates/
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

## Configuration Target Model

### Source of truth
- `common/policies/` stores canonical policy authority
- `common/schemas/` stores canonical validation authority
- `common/terminology/` stores canonical terminology

### Shared communication and payload references
- `common/mqtt/` stores MQTT topic, publisher/subscriber, and topic-payload communication contracts
- `common/payloads/` stores payload examples/templates for implementation, testing, simulation, and dashboard tooling
- `common/docs/architecture/15_interface_matrix.md` defines the MQTT-aware interface contract reference
- `common/docs/architecture/17_payload_contract_and_registry.md` defines payload placement and authority boundaries
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md` defines implementation prompt guidance for governance tooling

### Deployment targets
- `mac_mini/` contains hub-side configuration scripts and runtime deployment assets
- `rpi/` contains dashboard, simulation, orchestration, replay, fault-injection, result-export, non-authoritative governance support, and synchronized runtime/reference assets
- `esp32/` contains embedded-node implementation assets plus cross-platform configure/verify scaffolding for bounded physical nodes
- `integration/measurement/` contains optional timing and measurement support assets for out-of-band latency evaluation when that evaluation path is used

### Principle
The Git repository stores the frozen/reference state.  
The Mac mini, Raspberry Pi, ESP32 development workflow, and optional measurement workflow receive runtime-ready deployed copies, synchronized copies, or aligned configuration assumptions as needed.

Deployment-local configuration such as `.env`, secrets, host paths, and machine-specific runtime files must not redefine canonical policy or schema truth.

Deployment-local `.env` files may point to MQTT registry and payload reference paths, but they must not redefine the registry, payload boundary rules, or canonical policies/schemas.

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

### Optional future script set
- `55_deploy_mqtt_payload_references.sh`

This optional script may become useful if MQTT topic registries and payload examples/templates need to be deployed separately from policy/schema assets.

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
- align configured topic namespace with `common/mqtt/topic_registry_v1_0_0.json`
- prepare topic ACL assumptions from publisher/subscriber matrix where applicable
- align topic ACL assumptions with `common/docs/architecture/15_interface_matrix.md`
- ensure dashboard/governance topics cannot publish control authority unless explicitly allowed by the registry, interface matrix, and runtime mode
- ensure governance backend/UI topics cannot publish actuator or doorlock commands
- inject configuration into the target runtime path
- restart Mosquitto after applying settings

#### Trust-boundary rule
- The broker must be reachable from Raspberry Pi 5 on the same private LAN
- The broker must be reachable from ESP32 embedded clients on the intended trusted local network when those nodes are used
- Internet-originated inbound access must remain blocked by host or network firewall
- Optional local username/password authentication and topic ACL may be applied
- Listener settings and firewall policy should be treated as a single trust-boundary rule set
- Topic ACLs should not accidentally grant dashboard/governance tooling policy, validator, caregiver approval, actuation, or doorlock authority

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
- runtime copies or path references for MQTT topic registry when needed
- runtime copies or path references for payload examples/templates when needed

Representative authority deployment sources:
- `common/policies/`
- `common/schemas/`

Representative communication/payload reference sources:
- `common/mqtt/`
- `common/payloads/`

Representative deployed canonical assets:
- routing policy table
- low-risk action policy
- fault injection rules
- context schema
- candidate action schema
- policy router input schema
- validator output schema
- Class 2 notification payload schema

Representative deployed reference assets:
- topic registry
- publisher/subscriber matrix
- topic-payload contract notes
- payload examples/templates where needed by runtime validation or test tooling

Optional or version-sensitive companion deployment may include:
- output profile assets
- auxiliary deployment templates

#### Deployment principle
This script deploys runtime-ready copies from the canonical frozen/reference baseline.  
It must not create local policy truth that diverges from `common/`.

If communication/payload references are deployed here, their reference-layer status must be preserved; they do not become policy/schema authority.

---

### `55_deploy_mqtt_payload_references.sh` future optional script

Recommended deployment targets:
- runtime copies or symlinks for `common/mqtt/`
- runtime copies or symlinks for `common/payloads/`
- registry path manifest for hub-side services
- payload example/template path manifest for validation helpers and test tools

Recommended responsibilities:
- deploy or link MQTT registry assets into the target runtime path
- deploy or link payload examples/templates into the target runtime path
- avoid editing canonical registry or payload examples during deployment
- leave structural consistency checks to the verify stage

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
- `MQTT_TOPIC_REGISTRY_PATH`
- `MQTT_PUBLISHER_SUBSCRIBER_MATRIX_PATH`
- `MQTT_TOPIC_PAYLOAD_CONTRACTS_PATH`
- `PAYLOAD_EXAMPLES_DIR`
- `PAYLOAD_TEMPLATES_DIR`
- `TOPIC_NAMESPACE_PREFIX`
- `DASHBOARD_OBSERVATION_TOPIC`
- `EXPERIMENT_PROGRESS_TOPIC`
- `EXPERIMENT_RESULT_TOPIC`
- `SIMULATION_MODE`
- `GOVERNANCE_DASHBOARD_ENABLED`
- `GOVERNANCE_BACKEND_HOST`
- `GOVERNANCE_BACKEND_PORT`
- `GOVERNANCE_BACKEND_API_BASE`
- `GOVERNANCE_UI_PORT`
- `REGISTRY_VALIDATION_MODE`
- `TOPIC_DRIFT_CHECK_MODE`
- `PAYLOAD_VALIDATION_MODE`
- `VALIDATION_REPORT_DIR`
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

Topic strings and payload contract references should be loaded from registry/configuration paths where practical instead of being hardcoded into generated runtime configs.

Governance dashboard UI configuration must point to the governance backend service API and must not grant direct registry-file write access or operational control-topic publish authority.

Topic drift check mode, payload validation mode, and validation report paths may be configured here, but the actual drift and contract checks belong to the verify stage.

---

## Raspberry Pi Configuration Scripts

### Directory
- `rpi/scripts/configure/`

### Role Boundary
Raspberry Pi 5 is a **dashboard, simulation, fault-injection, replay, orchestration, result-artifact, non-authoritative governance support, and evaluation node**.

It should be configured only for:
- experiment and monitoring dashboard
- MQTT/payload governance backend service
- governance dashboard UI
- topic/payload contract validation utility
- payload example manager / validator
- publisher/subscriber role manager
- multi-node simulation runtime
- virtual `doorbell_detected` visitor-response context generation
- virtual emergency sensing
- fault injection
- scenario orchestration
- scenario replay
- progress/status publication
- result artifact export
- topic/payload validation utilities
- closed-loop automated verification
- Pi-side time synchronization and verification utilities
- synchronized runtime copies of frozen/reference artifacts

It should **not** be configured as a host for Mac mini operational hub services or authorities such as:
- Home Assistant
- Ollama
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- hub-side operational audit authority
- validator authority
- caregiver approval authority
- direct actuator dispatch authority
- doorlock dispatch authority
- direct registry-file editing through dashboard UI
- canonical policy/schema editing authority
- governance backend publishing actuator or doorlock commands

Dashboard/governance tooling on Raspberry Pi must remain non-authoritative.

### Frozen / expected script set
- `10_write_env_files_rpi.sh`
- `20_sync_phase0_artifacts_rpi.sh`
- `30_configure_time_sync_rpi.sh`
- `40_configure_simulation_runtime_rpi.sh`
- `50_configure_fault_profiles_rpi.sh`

### Expected future script set
- `60_configure_dashboard_runtime_rpi.sh`
- `70_configure_mqtt_payload_governance_rpi.sh`
- `80_configure_result_export_rpi.sh`

---

### `10_write_env_files_rpi.sh`

Recommended responsibilities:
- generate RPi runtime `.env`
- configure Mac mini broker host reference
- configure simulation namespace and runtime variables
- configure dashboard observation topic
- configure experiment progress/result topics
- configure governance dashboard enable flag
- configure governance backend host, port, and API base
- configure governance UI port
- configure registry validation mode
- configure topic drift check mode
- configure payload validation mode
- configure validation report directory
- configure MQTT topic registry path
- configure publisher/subscriber matrix path
- configure topic-payload contracts path
- configure payload examples/templates path
- configure schema/policy sync paths
- configure time-sync target settings

---

### `20_sync_phase0_artifacts_rpi.sh`

Recommended responsibilities:
- synchronize frozen policy assets from the authoritative shared repository state
- synchronize frozen schema assets from the authoritative shared repository state
- synchronize MQTT topic registry references when needed
- synchronize publisher/subscriber matrix and topic-payload contract references when needed
- synchronize payload examples/templates when needed
- verify active architecture references `15_interface_matrix.md`, `16_system_architecture_figure.md`, `17_payload_contract_and_registry.md`, and `12_prompts_mqtt_payload_governance.md` exist
- verify required synchronized runtime assets exist

### Principle
The Raspberry Pi should not invent local policy truth.  
It should consume synchronized frozen/reference artifacts derived from the shared reference set.

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
- configure virtual `doorbell_detected` visitor-response context generation
- configure visitor-response and doorlock-sensitive scenario paths
- ensure `doorbell_detected=true` does not authorize autonomous doorlock control
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
- include missing `doorbell_detected` as a strict schema/context fault case where applicable
- ensure `doorbell_detected=true` is not treated as emergency evidence or unlock authorization

### `60_configure_dashboard_runtime_rpi.sh` future optional script

Recommended responsibilities:
- configure experiment dashboard host, port, and runtime path
- configure dashboard observation topic
- configure dashboard read-only telemetry sources
- configure retained observation state behavior when used
- ensure dashboard runtime cannot publish policy, validator, caregiver approval, or unrestricted actuation authority

### `70_configure_mqtt_payload_governance_rpi.sh` future optional script

Recommended responsibilities:
- configure MQTT/payload governance backend service runtime
- configure governance dashboard UI runtime
- configure governance backend API base for UI use
- configure registry path and payload examples/templates path
- configure publisher/subscriber matrix and topic-payload contract paths
- configure topic/payload validation report location
- configure draft/proposed/committed separation
- configure live topic traffic inspection mode when used
- configure topic drift check mode where implemented
- enforce non-authoritative governance mode
- ensure governance dashboard UI cannot directly edit registry files
- ensure governance dashboard UI cannot directly publish operational control topics
- ensure governance backend cannot directly modify canonical policies/schemas
- ensure governance tooling cannot publish actuator or doorlock commands

### `80_configure_result_export_rpi.sh` future optional script

Recommended responsibilities:
- configure result artifact output paths
- configure CSV/JSON export settings
- configure graph/report output paths where used
- configure experiment run ID and scenario ID metadata assumptions

### Raspberry Pi Configuration Notes
- Raspberry Pi configuration should stay bounded to the evaluation path.
- It should prepare experiment-side execution only, not recreate the Mac mini hub runtime.
- Shared frozen assets remain authoritative at the repository level, and Raspberry Pi consumes synchronized runtime copies only.
- Communication/payload references remain reference assets and do not become policy authority on the Raspberry Pi.
- Dashboard/governance tooling may inspect, validate, visualize, draft, export, and report, but must not override policy routing, validator decisions, caregiver approval, or dispatch.
- Governance dashboard UI must remain separated from the governance backend service.
- Configuration may prepare topic drift and validation report settings, but actual drift, contract, and non-authority checks belong to the verify stage.
- Canonical policy/schema/rules consistency verification and topic/payload contract verification belong to the **verify** stage, while configuration prepares the synchronized runtime copies and execution assumptions needed for those checks.

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
- doorbell / visitor-arrival context topic assumptions
- `environmental_context.doorbell_detected` payload normalization assumptions
- actuator or warning interface topic assumptions when physical output is used
- warning/doorlock interface non-authority boundary
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
- current canonical: bounded button, lighting control, representative environmental sensing, doorbell / visitor-arrival context node
- optional experimental: gas, fire, fall-detection interface
- planned extension: doorlock or warning interface

### Principle
Embedded nodes should remain bounded physical clients under hub-side policy control rather than becoming independent policy authorities.

The current ESP32 configure/verify layer is primarily a **development-environment alignment and sample-build readiness layer**.  
It is not a replacement for later real node-firmware implementation under `esp32/code/` and `esp32/firmware/`.

Doorbell / visitor-arrival context must not be emitted as emergency evidence or doorlock authorization.  
Doorlock or warning interface nodes must not locally reinterpret doorlock as autonomous Class 1 authority.

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
- registry/payload reference paths: mounted, copied, symlinked, or externally configured according to deployment mode

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
- verify MQTT topic registry and payload reference directories exist
- verify active architecture references `15_interface_matrix.md`, `16_system_architecture_figure.md`, `17_payload_contract_and_registry.md`, and `12_prompts_mqtt_payload_governance.md` exist
- ensure configuration is not starting from an incomplete frozen/reference state

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

Optional future Mac mini reference deployment:
```bash
bash mac_mini/scripts/configure/55_deploy_mqtt_payload_references.sh
```

### Raspberry Pi
```bash
bash rpi/scripts/configure/10_write_env_files_rpi.sh
bash rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh
```

Optional future Raspberry Pi dashboard/governance/result configuration:
```bash
bash rpi/scripts/configure/60_configure_dashboard_runtime_rpi.sh
bash rpi/scripts/configure/70_configure_mqtt_payload_governance_rpi.sh
bash rpi/scripts/configure/80_configure_result_export_rpi.sh
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
- do not hardcode MQTT topic strings or payload contracts in generated runtime configs where registry lookup is practical
- configuration scripts may write registry/payload paths but must not rewrite canonical policies/schemas
- configuration scripts may write topic drift mode, payload validation mode, and validation report paths, but actual drift and contract checks belong to verification
- Raspberry Pi dashboard/governance configuration must remain non-authoritative
- governance dashboard UI must not directly edit registry files
- governance backend must not directly modify canonical policies or schemas
- governance tooling must not publish actuator or doorlock commands
- prevent deployment-local runtime files or synchronized copies from redefining canonical frozen policy truth
- prevent silent drift from the canonical policy/schema/rules baseline

---

## Architectural Summary

- `common/policies/` and `common/schemas/` store canonical policy/schema authority
- `common/mqtt/` and `common/payloads/` store communication/payload reference assets
- `common/docs/architecture/15_interface_matrix.md` defines the MQTT-aware interface contract reference
- `mac_mini/scripts/configure/` configures the operational hub
- `rpi/scripts/configure/` configures the dashboard, simulation, orchestration, replay, fault-injection, result-export, non-authoritative governance support, and evaluation node only
- Raspberry Pi does not replace the Mac mini hub runtime
- Raspberry Pi governance support must preserve governance backend/UI separation and cannot create operational authority
- `esp32/scripts/configure/` and `esp32/scripts/verify/` align the cross-platform ESP-IDF workspace and sample-build readiness for bounded node development, including doorbell / visitor-arrival context node assumptions where relevant
- `esp32/code/` and `esp32/firmware/` remain the later target areas for real node-firmware implementation
- `integration/measurement/` stores optional timing and measurement support alignment assets
- configuration scripts and embedded/measurement configuration alignment deploy runtime-ready values and assumptions
- runtime correctness, topic/payload consistency, topic drift checks, governance non-authority checks, and canonical asset consistency are confirmed later in the verify stage
