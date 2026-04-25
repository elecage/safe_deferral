# 02_mac_mini_build_sequence.md

## Mac mini Build Sequence

This document defines the recommended build and bring-up sequence for the Mac mini operational hub in the `safe_deferral` system.

The Mac mini is the **safety-critical operational edge hub**. It is responsible for local service runtime, policy/schema validation support, local LLM runtime, MQTT broker operation, audit DB preparation, outbound notification support, and deployed runtime copies of repository-governed reference assets.

Raspberry Pi 5 remains the experiment/dashboard/simulation/fault-injection and non-authoritative MQTT/payload governance support host. It must not replace Mac mini policy authority, validator authority, caregiver approval authority, actuator authority, or doorlock execution authority.

This document should be read together with:

- `README.md`
- `CLAUDE.md`
- `mac_mini/docs/README.md`
- `common/docs/architecture/01_installation_target_classification.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/required_experiments.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`

---

## Current runtime layout

The current Mac mini scripts use the following runtime layout:

```text
~/smarthome_workspace/
├── .env
├── .venv-mac/
├── requirements-mac-lock.txt
├── logs/
└── docker/
    ├── .env
    ├── docker-compose.yml
    └── volumes/
        ├── homeassistant/config/
        ├── mosquitto/config/
        ├── mosquitto/data/
        ├── mosquitto/log/
        ├── ollama/data/
        ├── app/config/
        │   ├── policies/
        │   ├── schemas/
        │   ├── mqtt/
        │   └── payloads/
        └── sqlite/db/audit_log.db
```

Important runtime paths:

- Home Assistant config: `~/smarthome_workspace/docker/volumes/homeassistant/config`
- SQLite audit DB: `~/smarthome_workspace/docker/volumes/sqlite/db/audit_log.db`
- Policy runtime assets: `~/smarthome_workspace/docker/volumes/app/config/policies`
- Schema runtime assets: `~/smarthome_workspace/docker/volumes/app/config/schemas`
- MQTT runtime references: `~/smarthome_workspace/docker/volumes/app/config/mqtt`
- Payload runtime references: `~/smarthome_workspace/docker/volumes/app/config/payloads`

Inside the application container, the compose template exposes:

- `POLICY_DIR=/app/config/policies`
- `SCHEMA_DIR=/app/config/schemas`
- `MQTT_REGISTRY_DIR=/app/config/mqtt`
- `PAYLOAD_EXAMPLES_DIR=/app/config/payloads`
- `SQLITE_PATH=/app/db/audit_log.db`

Host-side scripts use host paths in `~/smarthome_workspace/`. Container-side services use container paths.

---

## Phase 0. Pre-build freeze

Before installation or implementation, freeze and review the shared repository assets.

### Authoritative policy/schema assets

- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_1_0.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

### Communication and payload reference assets

- `common/mqtt/README.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`
- `common/payloads/examples/`
- `common/payloads/templates/`

`common/mqtt/` and `common/payloads/` are communication/reference layers. They support registry-aware topic lookup, payload validation, governance checking, dashboard tooling, and Package G verification. They do not create policy, schema, validator, caregiver approval, audit, actuator, or doorlock execution authority.

---

## Phase 1. Host and workspace preparation

Run from repository root:

```bash
bash mac_mini/scripts/install/00_install_homebrew.sh
bash mac_mini/scripts/install/00_preflight.sh
bash mac_mini/scripts/install/10_install_homebrew_deps.sh
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh
```

Current install-script requirements:

- `00_install_homebrew.sh` must not be run as root and warns if the user may lack macOS admin privileges.
- `20_install_docker_runtime_mac.sh` requires Homebrew before Docker Desktop installation/checks.
- `21_prepare_compose_stack_mac.sh` prepares `policies`, `schemas`, `mqtt`, `payloads`, and SQLite volume directories.
- `30_setup_python_venv_mac.sh` uses Homebrew-managed Python 3.11+ and `${BASH_SOURCE[0]}` for path resolution.

---

## Phase 2. Core service configuration

Run the configure scripts in this order:

```bash
bash mac_mini/scripts/configure/70_write_env_files.sh
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
bash mac_mini/scripts/configure/40_configure_sqlite.sh
bash mac_mini/scripts/configure/20_configure_mosquitto.sh
bash mac_mini/scripts/configure/10_configure_home_assistant.sh
bash mac_mini/scripts/configure/30_configure_ollama.sh
bash mac_mini/scripts/configure/60_configure_notifications.sh
```

Current configure-script behavior:

- `70_write_env_files.sh` writes host runtime `.env` and compose `.env`, including `POLICY_DIR`, `SCHEMA_DIR`, `MQTT_REGISTRY_DIR`, `PAYLOAD_EXAMPLES_DIR`, and `SQLITE_PATH`.
- `50_deploy_policy_files.sh` deploys policies, schemas, MQTT references, and payload references into `~/smarthome_workspace/docker/volumes/app/config/` and marks them read-only.
- `40_configure_sqlite.sh` initializes the audit DB at `~/smarthome_workspace/docker/volumes/sqlite/db/audit_log.db`, enables WAL, and creates required audit tables.
- `20_configure_mosquitto.sh` writes Mosquitto config under `docker/volumes/mosquitto/config`.
- `10_configure_home_assistant.sh` writes Home Assistant config under `docker/volumes/homeassistant/config` and preserves existing user config.
- `30_configure_ollama.sh` verifies the host-side Ollama API at `127.0.0.1:11434` and prepares the baseline model.
- `60_configure_notifications.sh` uses Telegram credentials when available and otherwise falls back to mock notification logging.

Mosquitto default generated config uses:

```conf
listener 1883 0.0.0.0
allow_anonymous true
```

This is for controlled LAN lab setup only. Production or shared-network deployments should use `password_file` and ACL rules aligned with `common/mqtt/` publisher/subscriber contracts.

---

## Phase 3. Container startup

Start the compose stack:

```bash
cd ~/smarthome_workspace/docker
docker compose up -d
docker compose ps
cd -
```

The compose template currently includes:

- `mosquitto`
- `homeassistant`
- `ollama`
- `edge_controller_app`

Inside the compose network, the app service should use:

- `MQTT_HOST=mosquitto`
- `OLLAMA_HOST=http://ollama:11434`

Host-side configure/verify scripts continue to use:

- `MQTT_HOST=127.0.0.1`
- `OLLAMA_HOST=http://127.0.0.1:11434`

This distinction is intentional.

`edge_controller_app` currently remains optional in service verification until `mac_mini/code/Dockerfile` and the operational app runtime are finalized.

---

## Phase 4. Verification

Run individual checks:

```bash
bash mac_mini/scripts/verify/10_verify_docker_services.sh
bash mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh
bash mac_mini/scripts/verify/30_verify_ollama_inference.sh
bash mac_mini/scripts/verify/40_verify_sqlite.sh
bash mac_mini/scripts/verify/50_verify_env_and_assets.sh
bash mac_mini/scripts/verify/60_verify_notifications.sh
```

Or run the aggregate wrapper:

```bash
bash mac_mini/scripts/verify/80_verify_services.sh
```

Current verification expectations:

- Docker required core services: `homeassistant`, `mosquitto`, `ollama`.
- Docker optional app service: `edge_controller_app`.
- MQTT verify topic: `safe_deferral/verify/mqtt_pubsub`.
- SQLite DB path: `~/smarthome_workspace/docker/volumes/sqlite/db/audit_log.db`.
- Runtime env must include `MQTT_REGISTRY_DIR` and `PAYLOAD_EXAMPLES_DIR`.
- Runtime asset verification includes policies, schemas, MQTT docs, payload examples, and templates.
- Topic registry `example_payload` references are checked for existence.
- Schema-governed payload examples are validated with `jsonschema`.
- Context examples must include `environmental_context.doorbell_detected`.
- Context examples must not include `doorlock`, `front_door_lock`, or `door_lock_state` in `pure_context_payload.device_states`.

These checks provide the current Mac mini-side minimum for Package G readiness. They do not create operational authority.

---

## Phase 5. Application development

Develop the hub-side applications in dependency order:

1. Policy Router
2. Deterministic Validator
3. Context-Integrity Safe Deferral Handler
4. Audit Logging Service integration
5. Outbound Notification Interface
6. Caregiver Confirmation Backend
7. MQTT Topic Registry Loader / Contract Checker
8. Payload Validation Helper
9. Hub-side integration tests

Development constraints:

- Current autonomous Class 1 remains limited to the lighting catalog.
- `doorbell_detected` is required visitor-response context, not unlock authorization.
- Doorlock is sensitive actuation and is not current autonomous Class 1.
- Doorlock state must not be inserted into current `pure_context_payload.device_states`.
- LLM candidate output is not execution authority.
- Validator-approved executable payload remains constrained to the low-risk catalog.
- MQTT/payload references support communication consistency; they do not create execution authority.

---

## Phase 6. Physical-node and integration validation

Physical-node and integration work should remain aligned with:

- `common/mqtt/topic_registry_v1_0_0.json`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/required_experiments.md`

ESP32 firmware and integration tests should avoid silently inventing topic strings or payload contracts that conflict with the registry and payload-boundary documents.

---

## Phase 7. Evaluation extension

Raspberry Pi 5 can extend evaluation through:

- simulation runtime,
- scenario orchestration,
- fault injection,
- experiment dashboard,
- closed-loop evaluation,
- progress/result publication,
- non-authoritative MQTT/payload governance support.

The Raspberry Pi 5 dashboard and governance backend may inspect, validate, draft, and report MQTT/payload changes. They must not directly edit canonical policy/schema authority, publish actuator commands, spoof caregiver approval, or create doorlock execution authority.

---

## Final bring-up principle

The Mac mini build sequence should preserve the following order of truth:

1. freeze canonical shared authority assets and communication/payload references,
2. prepare host runtime,
3. install core services,
4. deploy runtime copies and registry/payload references,
5. verify services and asset alignment,
6. verify MQTT/payload contract alignment,
7. develop bounded hub-side applications,
8. validate physical-node integration,
9. extend evaluation through virtual-node, dashboard, governance, orchestration, and timing infrastructure.

At no point should deployment-local convenience override the canonical frozen policy/schema baseline or convert MQTT/payload reference assets into operational authority.
