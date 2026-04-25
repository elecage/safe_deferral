# mac_mini/docs

이 디렉터리는 **Mac mini 기반 운영 허브(Mac mini Operational Hub)**의 설치, 구성, 배포, 검증 절차를 설명한다.

Mac mini는 본 시스템의 safety-critical operational edge hub이며, Raspberry Pi 5는 실험·대시보드·시뮬레이션·fault injection·비권한 MQTT/payload governance support host로 분리된다.

---

## 1. Mac mini 역할

Mac mini는 다음을 담당한다.

- Docker Compose 기반 로컬 서비스 실행
- Mosquitto MQTT broker 운영
- Home Assistant 운영
- Ollama 기반 로컬 LLM runtime 운영
- SQLite 기반 single-writer audit logging 환경 준비
- frozen policy/schema runtime asset 배포
- MQTT topic registry 및 payload reference asset 배포
- host-side runtime `.env` 작성
- 서비스 및 asset 검증

Mac mini는 정책 판단과 안전 검증의 중심이다. Dashboard, test app, RPi simulation, governance UI/backend가 Mac mini의 policy authority, validator authority, caregiver approval authority, actuator authority, doorlock execution authority를 대체해서는 안 된다.

---

## 2. Runtime directory layout

현재 Mac mini 스크립트는 다음 layout을 기준으로 한다.

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

중요 경로:

- Home Assistant config: `~/smarthome_workspace/docker/volumes/homeassistant/config`
- SQLite audit DB: `~/smarthome_workspace/docker/volumes/sqlite/db/audit_log.db`
- Policy runtime assets: `~/smarthome_workspace/docker/volumes/app/config/policies`
- Schema runtime assets: `~/smarthome_workspace/docker/volumes/app/config/schemas`
- MQTT runtime references: `~/smarthome_workspace/docker/volumes/app/config/mqtt`
- Payload runtime references: `~/smarthome_workspace/docker/volumes/app/config/payloads`

Container 내부 app 경로:

- `POLICY_DIR=/app/config/policies`
- `SCHEMA_DIR=/app/config/schemas`
- `MQTT_REGISTRY_DIR=/app/config/mqtt`
- `PAYLOAD_EXAMPLES_DIR=/app/config/payloads`
- `SQLITE_PATH=/app/db/audit_log.db`

Host-side Python/runtime `.env`는 host path를 사용하고, Compose service environment는 container path를 사용한다.

---

## 3. Canonical and reference assets

### Authoritative policy/schema assets

Mac mini runtime은 다음 frozen/reference assets를 배포해서 읽는다.

Policies:

- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_1_0.json`

Schemas:

- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

### MQTT/payload reference assets

Mac mini runtime also deploys:

- `common/mqtt/README.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`
- `common/payloads/examples/`
- `common/payloads/templates/`

These MQTT/payload files are communication/reference assets. They do not create policy, schema, validator, caregiver approval, audit, actuator, or doorlock execution authority.

---

## 4. Install sequence

Run from repository root.

```bash
bash mac_mini/scripts/install/00_install_homebrew.sh
bash mac_mini/scripts/install/00_preflight.sh
bash mac_mini/scripts/install/10_install_homebrew_deps.sh
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh
```

Install scripts prepare Homebrew, brew dependencies, Docker Desktop/Compose, the compose workspace, runtime asset directories, SQLite volume directory, and `.venv-mac` from `requirements-mac.txt`.

Notes:

- `00_install_homebrew.sh` must not be run as root.
- `20_install_docker_runtime_mac.sh` requires Homebrew before Docker Desktop installation/checks.
- `21_prepare_compose_stack_mac.sh` creates `policies`, `schemas`, `mqtt`, `payloads`, and SQLite volume directories.
- `30_setup_python_venv_mac.sh` uses Homebrew Python 3.11+ and `${BASH_SOURCE[0]}` for path resolution.

---

## 5. Configure sequence

Recommended order:

```bash
bash mac_mini/scripts/configure/70_write_env_files.sh
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
bash mac_mini/scripts/configure/40_configure_sqlite.sh
bash mac_mini/scripts/configure/20_configure_mosquitto.sh
bash mac_mini/scripts/configure/10_configure_home_assistant.sh
bash mac_mini/scripts/configure/30_configure_ollama.sh
bash mac_mini/scripts/configure/60_configure_notifications.sh
```

Configure responsibilities:

- `70_write_env_files.sh`
  - writes host runtime `.env` and compose `.env`
  - writes `POLICY_DIR`, `SCHEMA_DIR`, `MQTT_REGISTRY_DIR`, `PAYLOAD_EXAMPLES_DIR`, and `SQLITE_PATH`
  - uses host-side paths in `~/smarthome_workspace/`

- `50_deploy_policy_files.sh`
  - deploys policies, schemas, MQTT references, and payload references into `~/smarthome_workspace/docker/volumes/app/config/`
  - deploys MQTT/payload references read-only
  - does not convert reference assets into authority

- `40_configure_sqlite.sh`
  - initializes SQLite audit DB at `~/smarthome_workspace/docker/volumes/sqlite/db/audit_log.db`
  - enables WAL mode
  - creates audit tables

- `20_configure_mosquitto.sh`
  - writes Mosquitto config under `docker/volumes/mosquitto/config`
  - default `allow_anonymous true` is for controlled LAN lab setup only
  - production/shared-network use should replace this with password files and ACLs aligned with `common/mqtt/`

- `10_configure_home_assistant.sh`
  - writes Home Assistant config under `docker/volumes/homeassistant/config`
  - does not overwrite an existing `configuration.yaml`

- `30_configure_ollama.sh`
  - verifies Ollama API on host-side `127.0.0.1:11434`
  - pulls/verifies baseline model

- `60_configure_notifications.sh`
  - configures Telegram if credentials exist
  - otherwise uses mock notification fallback

---

## 6. Start containers

```bash
cd ~/smarthome_workspace/docker
docker compose up -d
docker compose ps
cd -
```

The compose template includes:

- `mosquitto`
- `homeassistant`
- `ollama`
- `edge_controller_app`

Current verification treats `edge_controller_app` as optional until `mac_mini/code/Dockerfile` and the operational app runtime are finalized.

Inside the Compose network:

- app should use `MQTT_HOST=mosquitto`
- app should use `OLLAMA_HOST=http://ollama:11434`

Host-side scripts still use:

- `MQTT_HOST=127.0.0.1`
- `OLLAMA_HOST=http://127.0.0.1:11434`

This distinction is intentional.

---

## 7. Verify sequence

Individual verification:

```bash
bash mac_mini/scripts/verify/10_verify_docker_services.sh
bash mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh
bash mac_mini/scripts/verify/30_verify_ollama_inference.sh
bash mac_mini/scripts/verify/40_verify_sqlite.sh
bash mac_mini/scripts/verify/50_verify_env_and_assets.sh
bash mac_mini/scripts/verify/60_verify_notifications.sh
```

Aggregate verification:

```bash
bash mac_mini/scripts/verify/80_verify_services.sh
```

Verify behavior:

- `10_verify_docker_services.sh`
  - required core services: `homeassistant`, `mosquitto`, `ollama`
  - optional service: `edge_controller_app`

- `20_verify_mqtt_pubsub.sh`
  - uses test topic `safe_deferral/verify/mqtt_pubsub`

- `40_verify_sqlite.sh`
  - verifies DB at `~/smarthome_workspace/docker/volumes/sqlite/db/audit_log.db`
  - checks WAL mode, integrity, and required audit tables

- `50_verify_env_and_assets.sh`
  - verifies required env vars including `MQTT_REGISTRY_DIR` and `PAYLOAD_EXAMPLES_DIR`
  - validates policy/schema/MQTT/payload JSON readability
  - checks required MQTT/payload files
  - verifies topic registry `example_payload` references exist
  - validates schema-governed payload examples using `jsonschema`
  - verifies context examples include `doorbell_detected`
  - rejects forbidden doorlock state fields in `pure_context_payload.device_states`

---

## 8. Quick start

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

## 9. Important boundaries

### Canonical truth vs deployment-local copies

- `common/policies/` and `common/schemas/` are authoritative source assets.
- Runtime copies under `~/smarthome_workspace/docker/volumes/app/config/` are deployed copies.
- `.env` and Compose mounts are deployment-local configuration.
- Deployment-local configuration must not redefine canonical policy/schema authority.

### MQTT/payload references

- `common/mqtt/` and `common/payloads/` support topic lookup, payload validation, governance checks, dashboard tooling, and Package G verification.
- They do not create execution authority.
- Governance reports are evidence artifacts only.

### Doorbell/doorlock boundary

- `environmental_context.doorbell_detected` is required context.
- `doorbell_detected=true` does not authorize door unlock.
- Doorlock state is not part of current `pure_context_payload.device_states`.
- Doorlock-sensitive actuation must route through Class 2 escalation or a separately governed manual confirmation path with caregiver approval, ACK, and audit.

### Mosquitto security boundary

Default generated config uses:

```conf
listener 1883 0.0.0.0
allow_anonymous true
```

This is for controlled LAN lab setup only. Production or shared-network deployments should use `password_file` and ACL rules aligned with `common/mqtt/` publisher/subscriber contracts.

---

## 10. Known follow-up

`edge_controller_app` remains optional in Docker service verification until the following are finalized:

- `mac_mini/code/Dockerfile`
- Policy Router implementation
- Deterministic Validator implementation
- Safe Deferral Handler implementation
- Audit/notification integration
- runtime app entrypoint

When finalized, `edge_controller_app` can be promoted from optional to required in `10_verify_docker_services.sh`.
