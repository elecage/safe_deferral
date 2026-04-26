# Deployment And Scripts

## 1. Purpose

This document summarizes active deployment and script structure for the current
baseline.

## 2. Lifecycle Split

Each device area should keep setup responsibilities separated:

- `install/`: install tools, packages, runtimes, and development dependencies,
- `configure/`: write local configuration, deploy runtime copies, select profiles,
- `verify/`: check readiness, connectivity, asset presence, and expected behavior.

Configuration and verification must not redefine canonical policy/schema truth.

## 3. Canonical Versus Deployment-Local

Canonical assets live under `common/`:

- `common/policies/`
- `common/schemas/`
- `common/mqtt/`
- `common/payloads/`
- `common/asset_manifest.json`

Deployment-local copies may exist under Mac mini or RPi runtime paths. Those
copies are runtime inputs, not canonical source files.

Host-local `.env`, credentials, tokens, machine-specific YAML, Docker mounts,
and synchronized mirrors are deployment-local configuration.

## 4. Mac Mini Script Scope

Mac mini scripts prepare and verify the operational hub:

- Homebrew and dependency setup,
- Docker/Compose runtime preparation,
- Mosquitto, Home Assistant, Ollama, SQLite, notification configuration,
- runtime `.env` generation,
- canonical asset deployment into runtime config directories,
- MQTT, LLM, SQLite, notification, service, and asset verification.

Mac mini deployment is the primary operational runtime path.

## 5. RPi Script Scope

RPi scripts prepare and verify the experiment-side support layer:

- Linux/RPi preflight,
- system packages and local environment,
- time-sync client,
- runtime `.env`,
- synchronized mirrors of Mac mini runtime assets,
- simulation runtime directories,
- virtual-node runtime directories and identity/config scaffolding,
- fault profile selection,
- experiment registry and node registry scaffolding,
- dashboard/preflight readiness wiring,
- base runtime checks,
- MQTT/payload alignment checks,
- closed-loop audit verification.

RPi scripts must treat synchronized policy/schema/MQTT/payload files as mirrors,
not as editable authority.

## 5.1 RPi Virtual Node Scope

RPi virtual nodes are experiment-only processes or services that emulate physical
node behavior for reproducible evaluation. They may be used to scale scenario
coverage beyond the available ESP32 hardware.

Allowed virtual node types:

- virtual bounded input node,
- virtual environmental sensor node,
- virtual emergency event node,
- virtual doorbell/visitor-arrival context node,
- virtual fault injector,
- virtual dashboard observation publisher,
- virtual ACK/mock actuator node when clearly marked as experiment-only.

Virtual nodes must:

- publish only through registry-aligned MQTT topics,
- emit payloads aligned with canonical schemas or documented payload families,
- preserve `source_node_id` or equivalent simulated identity,
- mark experiment/simulation mode in runtime metadata where practical,
- avoid live authority over policy, validator, caregiver approval, actuation, or
  doorlock execution.

Virtual doorlock-sensitive nodes are allowed only for boundary validation. They
must not create autonomous unlock authority.

## 5.2 Experiment Environment And Monitoring

The experiment environment must satisfy `common/docs/required_experiments.md`.
At minimum it should support:

- experiment registry entries with required nodes, services, topics, assets,
  runtime conditions, measurement nodes, and expected result artifacts,
- node registry or heartbeat/status records for Mac mini, RPi, ESP32 physical
  nodes, RPi virtual nodes, and optional STM32 timing nodes,
- preflight readiness states: `READY`, `DEGRADED`, `BLOCKED`, `UNKNOWN`,
- dashboard visibility for selected experiment, required dependencies,
  blocking reasons, measurement readiness, and start/stop eligibility,
- result artifact collection such as summary JSON, raw audit logs, latency CSV,
  timestamp export, run metadata, and governance reports,
- clear separation between operational control paths and monitoring/evaluation
  paths.

Dashboard and monitoring paths are visibility and readiness layers. They must
not publish operational controls or mutate canonical policy/schema assets.

## 6. ESP32 Script Scope

ESP32 scripts prepare and verify development environments for bounded physical
nodes:

- ESP-IDF setup by host platform,
- environment configuration,
- sample build verification,
- future firmware readiness.

ESP32 node behavior must remain aligned with Mac mini policy and validator
authority.

## 7. Script Validation Expectations

Scripts should prefer explicit checks for:

- required commands,
- runtime paths,
- canonical asset presence,
- JSON validity where JSON assets are copied or synced,
- MQTT topic references from the registry where practical,
- deployment-local versus canonical-source separation.

Scripts should not hardcode obsolete asset filenames.

## 8. Source Notes

This active summary consolidates the stable material from:

- `common/docs/archive/architecture_legacy/10_install_script_structure.md`
- `common/docs/archive/architecture_legacy/11_configuration_script_structure.md`
- `common/docs/archive/architecture_legacy/01_installation_target_classification.md`
- `common/docs/archive/architecture_legacy/02_mac_mini_build_sequence.md`
- `common/docs/archive/architecture_legacy/03_deployment_structure.md`
- `common/docs/archive/architecture_legacy/04_project_directory_structure.md`
- `mac_mini/docs/README.md`
- `rpi/docs/README.md`
