# SESSION_HANDOFF_2026-04-25_MAC_MINI_INSTALL_CONFIG_VERIFY_ALIGNMENT_UPDATE.md

## Purpose

This addendum records the Mac mini install/configure/verify alignment pass completed after the policy/schema/MQTT/payload alignment work.

It should be read before making further changes to:

- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/scripts/verify/`
- `mac_mini/scripts/templates/`
- `mac_mini/docs/README.md`
- `common/docs/architecture/02_mac_mini_build_sequence.md`

---

## Current Mac mini role

Mac mini remains the safety-critical operational edge hub.

It is responsible for:

- local Docker Compose service runtime,
- Mosquitto broker,
- Home Assistant,
- Ollama local LLM runtime,
- SQLite audit DB preparation,
- deployed runtime copies of frozen policies/schemas,
- deployed runtime copies of MQTT/payload reference assets,
- host-side runtime `.env`,
- Mac mini-side verification scripts.

Raspberry Pi 5 remains experiment/dashboard/simulation/fault-injection and non-authoritative MQTT/payload governance support. It must not replace Mac mini policy, validator, caregiver approval, actuator, or doorlock execution authority.

---

## Current runtime layout

The Mac mini runtime layout is now standardized as:

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

Important host-side paths:

- Home Assistant config: `~/smarthome_workspace/docker/volumes/homeassistant/config`
- SQLite audit DB: `~/smarthome_workspace/docker/volumes/sqlite/db/audit_log.db`
- Policies: `~/smarthome_workspace/docker/volumes/app/config/policies`
- Schemas: `~/smarthome_workspace/docker/volumes/app/config/schemas`
- MQTT references: `~/smarthome_workspace/docker/volumes/app/config/mqtt`
- Payload references: `~/smarthome_workspace/docker/volumes/app/config/payloads`

Important container-side paths:

- `POLICY_DIR=/app/config/policies`
- `SCHEMA_DIR=/app/config/schemas`
- `MQTT_REGISTRY_DIR=/app/config/mqtt`
- `PAYLOAD_EXAMPLES_DIR=/app/config/payloads`
- `SQLITE_PATH=/app/db/audit_log.db`

Host-side scripts use host paths. Container runtime uses container paths. Do not mix these two path domains.

---

## Install script changes

### `00_install_homebrew.sh`

Updated to:

- reject root execution,
- warn if the user may not have macOS admin privileges,
- keep official Homebrew installer bootstrap behavior.

### `20_install_docker_runtime_mac.sh`

Updated to:

- fail early if `brew` is not available,
- guide the user to run `00_install_homebrew.sh` first.

### `21_prepare_compose_stack_mac.sh`

Updated to create the following runtime directories:

- `volumes/app/config/policies`
- `volumes/app/config/schemas`
- `volumes/app/config/mqtt`
- `volumes/app/config/payloads`
- `volumes/sqlite/db`

### `30_setup_python_venv_mac.sh`

Updated to use:

```bash
${BASH_SOURCE[0]}
```

for path resolution.

---

## Compose template changes

### `mac_mini/scripts/templates/docker-compose.template.yml`

Updated to use Compose service DNS inside the app container:

- `MQTT_HOST=mosquitto`
- `OLLAMA_HOST=http://ollama:11434`

Added app container reference mounts:

- `/app/config/mqtt`
- `/app/config/payloads`

Added environment variables:

- `MQTT_REGISTRY_DIR=/app/config/mqtt`
- `PAYLOAD_EXAMPLES_DIR=/app/config/payloads`

`edge_controller_app` still depends on `mac_mini/code/Dockerfile`. Until the app Dockerfile/runtime is finalized, Docker service verification treats it as optional.

---

## Configure script changes

### `10_configure_home_assistant.sh`

Updated Home Assistant config path to:

```text
~/smarthome_workspace/docker/volumes/homeassistant/config
```

This matches the compose volume mount.

### `20_configure_mosquitto.sh`

Updated comments to clarify:

- `listener 1883 0.0.0.0` and `allow_anonymous true` are for controlled LAN lab setup only,
- production/shared-network deployments should use `password_file` and ACLs aligned with `common/mqtt/` publisher/subscriber contracts.

### `40_configure_sqlite.sh`

Updated SQLite DB path to:

```text
~/smarthome_workspace/docker/volumes/sqlite/db/audit_log.db
```

This matches the compose mount `/app/db/audit_log.db`.

### `50_deploy_policy_files.sh`

Expanded from policy/schema deployment to runtime reference asset deployment.

Now deploys:

- `common/policies/` selected policy assets,
- `common/schemas/` selected schema assets,
- `common/mqtt/` full reference directory,
- `common/payloads/` full reference directory.

The deployed runtime copies are marked read-only.

Important boundary:

- Deployed runtime copies do not become canonical truth.
- MQTT/payload references do not become policy/schema/execution authority.

### `70_write_env_files.sh`

Updated host runtime `.env` to include:

- `MQTT_REGISTRY_DIR`
- `PAYLOAD_EXAMPLES_DIR`

Updated `SQLITE_PATH` to:

```text
~/smarthome_workspace/docker/volumes/sqlite/db/audit_log.db
```

---

## Verify script changes

### `10_verify_docker_services.sh`

Core and optional services are now separated.

Required core services:

- `homeassistant`
- `mosquitto`
- `ollama`

Optional service:

- `edge_controller_app`

Rationale:

- `edge_controller_app` depends on future `mac_mini/code/Dockerfile` and app runtime.
- Core infrastructure verification should not fail before the app runtime is finalized.
- When app implementation is complete, this service can be promoted to required.

### `20_verify_mqtt_pubsub.sh`

Updated test topic to:

```text
safe_deferral/verify/mqtt_pubsub
```

This keeps the verification topic inside the project namespace.

### `40_verify_sqlite.sh`

Updated fallback DB path to:

```text
~/smarthome_workspace/docker/volumes/sqlite/db/audit_log.db
```

### `50_verify_env_and_assets.sh`

Expanded to verify:

- required env variables including `MQTT_REGISTRY_DIR` and `PAYLOAD_EXAMPLES_DIR`,
- deployed policies,
- deployed schemas,
- deployed MQTT references,
- deployed payload references,
- JSON validity for policy/schema/MQTT/payload JSON files,
- topic registry `example_payload` referenced file existence,
- schema-governed payload examples via `jsonschema`,
- `environmental_context.doorbell_detected` presence in context examples,
- forbidden doorlock state fields not present in `pure_context_payload.device_states`.

This provides the current Mac mini-side minimum Package G readiness check.

---

## Documentation updates

### `mac_mini/docs/README.md`

Rewritten/updated to match current script behavior:

- current runtime directory layout,
- host/container path distinction,
- policy/schema/MQTT/payload runtime asset deployment,
- install/configure/start/verify sequence,
- optional `edge_controller_app`,
- Package G-related asset verification,
- Mosquitto LAN lab security boundary,
- doorbell/doorlock authority boundary.

### `common/docs/architecture/02_mac_mini_build_sequence.md`

Updated to match current bring-up sequence:

- current runtime layout,
- install script behavior,
- configure script behavior,
- compose app networking distinction,
- optional app verification,
- MQTT/payload runtime reference deployment,
- Package G minimal verification,
- operational authority boundaries.

---

## Current recommended bring-up sequence

```bash
cd /path/to/safe_deferral

bash mac_mini/scripts/install/00_install_homebrew.sh
bash mac_mini/scripts/install/00_preflight.sh
bash mac_mini/scripts/install/10_install_homebrew_deps.sh
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh

bash mac_mini/scripts/configure/70_write_env_files.sh
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
bash mac_mini/scripts/configure/40_configure_sqlite.sh
bash mac_mini/scripts/configure/20_configure_mosquitto.sh
bash mac_mini/scripts/configure/10_configure_home_assistant.sh
bash mac_mini/scripts/configure/30_configure_ollama.sh
bash mac_mini/scripts/configure/60_configure_notifications.sh

cd ~/smarthome_workspace/docker
docker compose up -d
docker compose ps
cd -

bash mac_mini/scripts/verify/80_verify_services.sh
```

---

## Non-negotiable boundaries after this pass

1. Mac mini is the operational hub.
2. Runtime copies do not replace canonical repository assets.
3. MQTT/payload references support communication consistency but do not create authority.
4. Host-side scripts use host paths; container services use container paths.
5. SQLite audit DB path is unified under `docker/volumes/sqlite/db/audit_log.db`.
6. Home Assistant config path is unified under `docker/volumes/homeassistant/config`.
7. `edge_controller_app` remains optional until app runtime is finalized.
8. `allow_anonymous true` in Mosquitto config is controlled LAN lab default only.
9. `doorbell_detected` remains required context, not unlock authorization.
10. Doorlock state remains outside current `pure_context_payload.device_states`.

---

## Next implementation target

The next major Mac mini-side work should focus on the actual runtime application layer:

1. `mac_mini/code/Dockerfile`
2. Policy Router implementation
3. Deterministic Validator implementation
4. Safe Deferral Handler implementation
5. Audit logger integration
6. Notification backend integration
7. MQTT registry loader / contract checker
8. Payload validation helper

When the app runtime is finalized, revisit `10_verify_docker_services.sh` and consider promoting `edge_controller_app` from optional to required.
