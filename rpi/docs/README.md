# rpi/docs

이 디렉터리는 Raspberry Pi 5 기반 실험 지원 환경의 설치, 구성, 검증 절차를 설명한다.

현재 프로젝트에서 `rpi/`는 운영 허브가 아니다. Raspberry Pi는 Mac mini를 대체하지 않으며, 논문용 실험 실행, 가상 노드, fault injection, 모니터링, 결과 수집, MQTT/payload 정합성 검증을 지원하는 비권한 계층이다.

RPi는 다음 권한을 가져서는 안 된다.

- policy authority
- validator authority
- caregiver approval authority
- actuator authority
- doorlock execution authority

---

## 1. 역할

`rpi/`의 현재 역할은 다음과 같다.

- Mac mini runtime/reference asset의 로컬 mirror 소비
- virtual node 및 simulation runtime 준비
- fault injection profile 검증
- MQTT/payload reference alignment 확인
- closed-loop audit 관찰
- 실험 재현성을 위한 time sync 확인

장치별 경계는 다음과 같이 유지한다.

- `mac_mini/`: operational hub
- `rpi/`: experiment support host
- `esp32/`: bounded physical node layer
- `stm32/`: out-of-band timing/measurement support
- `integration/`: scenario, fixture, measurement, result assets

---

## 2. 디렉터리 구조

```text
rpi/
├── code/
├── docs/
│   ├── README.md
│   └── RPI_CLEANUP_PLAN.md
└── scripts/
    ├── install/
    │   ├── 00_preflight_rpi.sh
    │   ├── 10_install_system_packages_rpi.sh
    │   ├── 20_create_python_venv_rpi.sh
    │   ├── 30_install_python_deps_rpi.sh
    │   └── 40_install_time_sync_client_rpi.sh
    ├── configure/
    │   ├── 10_write_env_files_rpi.sh
    │   ├── 20_sync_runtime_assets_rpi.sh
    │   ├── 30_configure_time_sync_rpi.sh
    │   ├── 40_configure_simulation_runtime_rpi.sh
    │   └── 50_configure_fault_profiles_rpi.sh
    └── verify/
        ├── 00_verify_rpi_script_syntax.sh
        ├── 70_verify_rpi_base_runtime.sh
        ├── 75_verify_rpi_mqtt_payload_alignment.sh
        └── 80_verify_rpi_closed_loop_audit.sh
```

`rpi/code/`는 future RPi experiment app 구현 위치다. 현재 cleanup 단계에서는 구현 코드를 추가하지 않는다.

---

## 3. Runtime Layout

RPi 스크립트는 기본적으로 다음 local workspace를 사용한다.

```text
~/smarthome_workspace/
├── .env
├── .venv-rpi/
├── requirements-rpi-lock.txt
├── config/
│   ├── policies/
│   ├── schemas/
│   ├── mqtt/
│   └── payloads/
├── scenarios/
└── logs/
    ├── simulation/
    └── verification/
```

`config/` 아래의 파일들은 RPi 권한의 원본이 아니다. Mac mini runtime/reference asset을 실험 검증용으로 복사한 local mirror다.

---

## 4. Install Sequence

저장소 루트에서 실행한다.

```bash
bash rpi/scripts/install/00_preflight_rpi.sh
bash rpi/scripts/install/10_install_system_packages_rpi.sh
bash rpi/scripts/install/20_create_python_venv_rpi.sh
bash rpi/scripts/install/30_install_python_deps_rpi.sh
bash rpi/scripts/install/40_install_time_sync_client_rpi.sh
```

Install 단계는 다음을 준비한다.

- Raspberry Pi OS/Linux 환경 확인
- Python 3.11+ 확인
- `python3`, `python3-venv`, `git`, `mosquitto-clients`, `chrony`, `jq`, `rsync`, `curl` 설치
- `~/smarthome_workspace/.venv-rpi` 생성
- `requirements-rpi.txt` 기반 Python dependency 설치
- Chrony time sync client 활성화

---

## 5. Configure Sequence

권장 순서:

```bash
bash rpi/scripts/configure/10_write_env_files_rpi.sh
bash rpi/scripts/configure/20_sync_runtime_assets_rpi.sh
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh
```

### `10_write_env_files_rpi.sh`

`~/smarthome_workspace/.env`를 생성하거나 누락된 키를 추가한다.

핵심 변수:

- `MAC_MINI_HOST`
- `MAC_MINI_USER`
- `MQTT_HOST`
- `MQTT_PORT`
- `POLICY_SYNC_PATH`
- `SCHEMA_SYNC_PATH`
- `MQTT_REGISTRY_SYNC_PATH`
- `PAYLOAD_EXAMPLES_SYNC_PATH`
- `TOPIC_NAMESPACE`
- `FAULT_PROFILE`
- `TIME_SYNC_HOST`
- `ALLOW_RPI_ACTUATION=false`
- `ALLOW_RPI_POLICY_AUTHORITY=false`
- `ALLOW_RPI_DOORLOCK_CONTROL=false`

주의: 이 스크립트는 기존 값을 보존한다. 오래된 값이나 placeholder가 있으면 직접 수정해야 한다.

### `20_sync_runtime_assets_rpi.sh`

Mac mini의 current runtime/reference asset을 RPi local mirror로 동기화한다.

동기화 대상:

- policy assets
- schema assets
- MQTT reference assets
- payload reference assets

기본 Mac mini source path:

```text
~/smarthome_workspace/docker/volumes/app/config/policies
~/smarthome_workspace/docker/volumes/app/config/schemas
~/smarthome_workspace/docker/volumes/app/config/mqtt
~/smarthome_workspace/docker/volumes/app/config/payloads
```

이 스크립트는 RPi에서 Mac mini로 SSH/rsync 무인 접속이 가능하다는 것을 전제로 한다.

필수 전제:

- `MAC_MINI_HOST`와 `MAC_MINI_USER`가 실제 값이어야 한다.
- Mac mini의 Remote Login/SSH가 켜져 있어야 한다.
- RPi에서 Mac mini로 key-based SSH 접속이 가능해야 한다.
- Mac mini에서 `mac_mini/scripts/configure/50_deploy_policy_files.sh`가 먼저 실행되어 runtime/reference asset이 배포되어 있어야 한다.

### `30_configure_time_sync_rpi.sh`

Chrony를 Mac mini 기준 time source에 맞춘다. Time sync는 freshness/staleness 관련 실험의 해석 margin을 안정화하기 위한 지원 기능이다.

### `40_configure_simulation_runtime_rpi.sh`

simulation 및 verification runtime directory를 준비하고, RPi Python venv와 `paho-mqtt` import 가능성을 확인한다.

### `50_configure_fault_profiles_rpi.sh`

동기화된 `fault_injection_rules.json`을 읽어 active fault profile을 검증하고 runner config를 작성한다.

---

## 6. Verify Sequence

권장 순서:

```bash
bash rpi/scripts/verify/00_verify_rpi_script_syntax.sh
bash rpi/scripts/verify/70_verify_rpi_base_runtime.sh
bash rpi/scripts/verify/75_verify_rpi_mqtt_payload_alignment.sh
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

### `00_verify_rpi_script_syntax.sh`

RPi shell scripts의 문법과 기본 heredoc 형태를 확인한다.

### `70_verify_rpi_base_runtime.sh`

다음을 확인한다.

- required CLI tools
- RPi authority boundary flags
- Mac mini network reachability
- MQTT publish reachability
- policy/schema/MQTT/payload local mirror 존재 및 JSON readability
- `doorbell_detected` schema alignment
- payload examples의 doorlock state misuse 여부
- time sync offset margin

### `75_verify_rpi_mqtt_payload_alignment.sh`

MQTT registry, publisher/subscriber matrix, topic-payload contract, payload examples, context schema가 current reference structure와 맞는지 확인한다.

특히 다음을 확인한다.

- `safe_deferral/*` topic namespace
- `.env` topic values
- legacy `smarthome/*` drift
- payload JSON validity
- `doorbell_detected` example coverage
- `pure_context_payload.device_states` 아래 doorlock state 금지

### `80_verify_rpi_closed_loop_audit.sh`

선택된 fault profile을 기준으로 fault payload를 publish하고 audit topic을 관찰한다.

이 검증은 RPi에 권한을 주기 위한 것이 아니다. RPi는 fault injection source와 observer로만 동작하며, 결과가 safe non-dispatch outcome 또는 profile이 허용한 outcome인지 확인한다.

---

## 7. Quick Start

```bash
cd /path/to/safe_deferral

bash rpi/scripts/install/00_preflight_rpi.sh
bash rpi/scripts/install/10_install_system_packages_rpi.sh
bash rpi/scripts/install/20_create_python_venv_rpi.sh
bash rpi/scripts/install/30_install_python_deps_rpi.sh
bash rpi/scripts/install/40_install_time_sync_client_rpi.sh

bash rpi/scripts/configure/10_write_env_files_rpi.sh
```

`~/smarthome_workspace/.env`에서 `MAC_MINI_HOST`, `MAC_MINI_USER`, `MQTT_HOST`, `MQTT_PASS`를 실제 환경에 맞게 확인한 뒤 계속 진행한다.

```bash
bash rpi/scripts/configure/20_sync_runtime_assets_rpi.sh
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh

bash rpi/scripts/verify/00_verify_rpi_script_syntax.sh
bash rpi/scripts/verify/70_verify_rpi_base_runtime.sh
bash rpi/scripts/verify/75_verify_rpi_mqtt_payload_alignment.sh
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

---

## 8. Success Criteria

RPi 환경 준비 성공 기준은 단순 설치 완료가 아니다. 다음이 모두 만족되어야 한다.

- `.env`가 current `safe_deferral/*` topic namespace와 실제 Mac mini 접속 정보에 맞게 작성되어 있다.
- Mac mini runtime/reference assets가 RPi local mirror로 동기화되어 있다.
- RPi authority boundary flags가 모두 `false`다.
- base runtime verification이 통과한다.
- MQTT/payload alignment verification이 통과한다.
- selected fault profile 기반 closed-loop audit verification이 통과한다.

---

## 9. Common SSH/Sync Issues

### Placeholder 값이 남아 있는 경우

`MAC_MINI_HOST`, `MAC_MINI_USER`, `MQTT_HOST`, `MQTT_PASS`가 예시값이면 artifact sync 또는 MQTT verification이 실패한다.

```bash
grep -E 'MAC_MINI_HOST|MAC_MINI_USER|MQTT_HOST|MQTT_PASS' ~/smarthome_workspace/.env
```

### Mac mini SSH가 꺼져 있는 경우

Mac mini에서 Remote Login을 켠다.

```bash
sudo systemsetup -setremotelogin on
sudo systemsetup -getremotelogin
sudo lsof -iTCP:22 -sTCP:LISTEN -n -P
```

### Key-based SSH가 안 되는 경우

RPi에서 Mac mini 접속 키를 등록한다.

```bash
ssh-keygen -t ed25519 -C "rpi-sync"
ssh-copy-id <MAC_MINI_USER>@<MAC_MINI_HOST>
ssh <MAC_MINI_USER>@<MAC_MINI_HOST>
```

마지막 명령이 비밀번호 입력 없이 들어가야 unattended rsync가 안정적으로 동작한다.

### Mac mini runtime/reference asset 경로가 없는 경우

Mac mini에서 먼저 asset 배포를 실행한다.

```bash
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
```

그리고 경로를 확인한다.

```bash
ls -al ~/smarthome_workspace/docker/volumes/app/config/policies
ls -al ~/smarthome_workspace/docker/volumes/app/config/schemas
ls -al ~/smarthome_workspace/docker/volumes/app/config/mqtt
ls -al ~/smarthome_workspace/docker/volumes/app/config/payloads
```

---

## 10. Current Limitations

현재 `rpi/`는 install/configure/verify scaffold 중심이다. 다음 구현은 아직 별도 작업으로 남아 있다.

- virtual node manager
- virtual behavior / fault injection manager
- scenario execution manager
- experiment dashboard
- result store / analysis tooling
- graph/CSV export
- reproducibility summary generation

---

## 11. Next Implementation Targets

문서/스크립트 정리가 끝난 뒤의 구현 후보는 다음과 같다.

1. `rpi/code/` virtual sensor publisher
2. virtual emergency event publisher
3. fault injector harness
4. scenario orchestrator
5. experiment run manager and result store
6. monitoring/dashboard backend
7. MQTT/payload governance support backend
