# rpi/docs

이 디렉터리는 **Raspberry Pi 5 기반 simulation / fault injection / closed-loop evaluation 환경**의 설치, 구성, 검증 구조를 정리하는 문서 모음이다.

현재 프로젝트에서 `rpi/`의 역할은 **운영 허브가 아니라 실험·검증 계층**이다.  
즉, Raspberry Pi는 Mac mini를 대체하지 않으며, 다음 목적에 집중한다.

- 가상 센서/상황 데이터 시뮬레이션
- 정책 정합적인 emergency / fault injection
- Phase 0 frozen artifact 동기화 및 로컬 mirror 운용
- time sync 확인
- closed-loop safety audit 검증

---

## 1. RPi 영역의 역할

프로젝트 전체 구조에서 `rpi/`는 다음 역할을 담당한다.

- simulation / fault injection / closed-loop evaluation
- Mac mini runtime asset의 read-only mirror 소비
- experiment-side verification
- reproducibility-oriented scenario execution

다음 구분을 반드시 유지해야 한다.

- `mac_mini/` = operational hub
- `rpi/` = simulation / fault injection / closed-loop evaluation
- `esp32/` = bounded physical node layer
- `integration/measurement/` = optional timing / latency evaluation support

즉, RPi는 **운영 제어 권한을 가지는 허브가 아니라 검증·재현성 지원 계층**이다.

---

## 2. 현재 RPi 구성 원칙

RPi 쪽은 `install / configure / verify` 3단계로 정리되어 있다.

### 2.1 install
RPi 로컬에 필요한 시스템 패키지와 Python 환경을 준비한다.

### 2.2 configure
- `.env` 작성
- Mac mini runtime artifact sync
- time sync 구성
- simulation runtime 디렉터리 준비
- current canonical fault profile 선택 및 runner config 작성

### 2.3 verify
- base runtime 검증
- MQTT publish reachability 검증
- synced asset 존재/정합성 확인
- time sync margin 점검
- closed-loop audit 검증

---

## 3. 현재 반영된 디렉터리/스크립트 구조

현재 정리된 RPi 스크립트 흐름은 아래와 같다.

```text
rpi/
├─ code/
├─ docs/
│  └─ README.md
└─ scripts/
   ├─ install/
   │  ├─ 00_preflight_rpi.sh
   │  ├─ 10_install_system_packages_rpi.sh
   │  ├─ 20_create_python_venv_rpi.sh
   │  ├─ 30_install_python_deps_rpi.sh
   │  └─ 40_install_time_sync_client_rpi.sh
   ├─ configure/
   │  ├─ 10_write_env_files_rpi.sh
   │  ├─ 20_sync_phase0_artifacts_rpi.sh
   │  ├─ 30_configure_time_sync_rpi.sh
   │  ├─ 40_configure_simulation_runtime_rpi.sh
   │  └─ 50_configure_fault_profiles_rpi.sh
   └─ verify/
      ├─ 70_verify_rpi_base_runtime.sh
      └─ 80_verify_rpi_closed_loop_audit.sh
```

관련 Python dependency manifest:

```text
requirements-rpi.txt
```

---

## 4. install 단계 역할 정의

### `00_preflight_rpi.sh`
목적:
- Linux/RPi 계열 환경인지 확인
- Python 3.11+ 여부 확인
- 디스크 여유 공간 확인
- 기본 네트워크 접근 가능성 확인

역할:
- 설치 전 fail-fast 사전 점검

### `10_install_system_packages_rpi.sh`
목적:
- RPi 시스템 패키지 설치

현재 install 대상 핵심:
- `python3`
- `python3-venv`
- `git`
- `mosquitto-clients`
- `chrony`
- `jq`
- `rsync`
- `curl`

중요 원칙:
- 특정 `python3.11` 패키지명에 고정하지 않는다.
- 시스템 기본 `python3`가 **3.11 이상**이면 허용한다.

역할:
- configure / verify 단계가 요구하는 CLI 의존성 보장

### `20_create_python_venv_rpi.sh`
목적:
- `~/smarthome_workspace/.venv-rpi` 생성
- Python 버전이 맞지 않으면 재생성

중요 원칙:
- `python3.11` 바이너리 고정이 아니라, 시스템 기본 `python3`가 3.11 이상이면 그 인터프리터로 venv를 생성한다.

역할:
- RPi simulation-side Python runtime 준비

### `30_install_python_deps_rpi.sh`
목적:
- `requirements-rpi.txt` 기반 Python dependency 설치
- lock 파일 생성

현재 baseline dependency:
- `paho-mqtt`
- `pytest`
- `PyYAML`
- `jsonschema`

### `40_install_time_sync_client_rpi.sh`
목적:
- time sync client service 활성화 준비
- `chrony` 서비스 enable/start

역할:
- 후속 configure 단계에서 실제 time source 구성 가능 상태 확보

---

## 5. configure 단계 역할 정의

### `10_write_env_files_rpi.sh`
목적:
- `~/smarthome_workspace/.env` 생성 또는 append-only 갱신

현재 핵심 변수 예시:
- `MAC_MINI_HOST`
- `MAC_MINI_USER`
- `MQTT_HOST`
- `MQTT_PORT`
- `POLICY_SYNC_PATH`
- `SCHEMA_SYNC_PATH`
- `TOPIC_NAMESPACE`
- `NODE_COUNT`
- `PUBLISH_INTERVAL_MS`
- `SCENARIO_PROFILE`
- `FAULT_PROFILE`
- `VERIFICATION_AUDIT_TOPIC`
- `TIME_SYNC_HOST`
- `TIME_SYNC_TARGET_BOUND_MS`

주의:
- `POLICY_SYNC_PATH`, `SCHEMA_SYNC_PATH`는 **RPi local mirror path**다.
- Mac mini runtime path 그 자체가 아니다.

### `20_sync_phase0_artifacts_rpi.sh`
목적:
- Mac mini current runtime asset을 RPi 로컬 mirror로 동기화

현재 remote source path 기준:
- `~/smarthome_workspace/docker/volumes/app/config/schemas`
- `~/smarthome_workspace/docker/volumes/app/config/policies`

현재 sync 대상 canonical assets:
- `context_schema_v1_0_0_FROZEN.json`
- `candidate_action_schema_v1_0_0_FROZEN.json`
- `policy_router_input_schema_v1_1_1_FROZEN.json`
- `validator_output_schema_v1_1_0_FROZEN.json`
- `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- `policy_table_v1_1_2_FROZEN.json`
- `fault_injection_rules_v1_4_0_FROZEN.json`
- `low_risk_actions_v1_1_0_FROZEN.json`
- `output_profile_v1_1_0.json`

역할:
- experiment-side runtime이 current canonical asset set을 읽게 함

### `30_configure_time_sync_rpi.sh`
목적:
- RPi chrony를 Mac mini 기준 시각 source에 맞춤
- offset bound 내인지 확인

역할:
- experiment reproducibility support
- stale / freshness 기반 시나리오의 해석 margin 관리

### `40_configure_simulation_runtime_rpi.sh`
목적:
- simulation / verification용 runtime 디렉터리 준비

예상 준비 대상:
- `logs/simulation`
- `logs/verification`
- `scenarios`

역할:
- simulation-side 작업 공간 정리

### `50_configure_fault_profiles_rpi.sh`
목적:
- current canonical `fault_injection_rules_v1_4_0_FROZEN.json` 검증
- active deterministic profile 또는 randomized stress profile 선택
- runner config 작성

현재 핵심:
- `deterministic_profiles`는 object 구조로 해석
- `dynamic_references`는 top-level field로 해석
- active profile은 object key 기준으로 lookup

역할:
- current fault rules baseline과 RPi verification 실행을 정렬

---

## 6. verify 단계 역할 정의

### `70_verify_rpi_base_runtime.sh`
목적:
- base runtime / communication / synced asset / time sync 상태 검증

검증 항목:
- required CLI tools 존재
- Mac mini ICMP reachability
- MQTT publish reachability
- synced Phase 0 asset 9개 존재 여부
- synced JSON structural validity
- freshness threshold reference lookup
- time sync offset margin 확인

역할:
- experiment 시작 전 환경 준비 상태 확인

### `80_verify_rpi_closed_loop_audit.sh`
목적:
- selected fault profile 기준 closed-loop safety assessment 수행

검증 항목:
- fault profile lookup
- test payload publish
- audit topic 수신
- observed routing target 확인
- expected / prohibited outcome 비교

역할:
- unsafe autonomous actuation이 발생하지 않는지 점검
- fault injection defense의 closed-loop behavior 확인

---

## 7. 실제 실행 순서

저장소 루트에서 실행하는 것을 권장한다.

```bash
cd /path/to/safe_deferral
chmod +x rpi/scripts/install/*.sh
chmod +x rpi/scripts/configure/*.sh
chmod +x rpi/scripts/verify/*.sh
```

### 7.1 install

```bash
bash rpi/scripts/install/00_preflight_rpi.sh
bash rpi/scripts/install/10_install_system_packages_rpi.sh
bash rpi/scripts/install/20_create_python_venv_rpi.sh
bash rpi/scripts/install/30_install_python_deps_rpi.sh
bash rpi/scripts/install/40_install_time_sync_client_rpi.sh
```

### 7.2 configure

```bash
bash rpi/scripts/configure/10_write_env_files_rpi.sh
bash rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh
```

### 7.3 verify

```bash
bash rpi/scripts/verify/70_verify_rpi_base_runtime.sh
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

---

## 8. 성공 기준

RPi experiment-side environment 구축 성공의 기준은 단순 설치 완료가 아니다.

최종적으로 다음이 모두 만족되어야 한다.

- `.env`가 current baseline naming에 맞게 작성됨
- Mac mini runtime canonical assets 9개가 local mirror로 sync됨
- time sync offset이 실험 허용 margin 안에 들어옴
- base runtime verify가 통과함
- selected fault profile 기반 closed-loop audit verify가 통과함

즉, **최종 성공 기준은 base runtime + closed-loop audit verification success**다.

---

## 9. 현재 단계의 핵심 정리

현재 RPi 쪽은 다음 상태다.

- install 체인: 정리됨
- `requirements-rpi.txt`: 반영됨
- configure 체인: current canonical versioned asset naming 기준으로 정리됨
- verify 체인: current canonical fault rules / synced asset set 기준으로 정리됨

특히 다음 drift는 정리된 상태다.

- old normalized filename 의존성 제거
- current canonical versioned filename 사용
- current fault rules object-key 구조 반영
- current audit topic 기본값과 정렬
- Phase 0 synced asset set 9개 기준 정렬
- Python interpreter handling generalized from hardcoded `python3.11` to `python3` 3.11+

---

## 10. 현재 단계의 한계

현재 문서와 스크립트는 **experiment/runtime scaffold** 중심이다.

아직 남아 있는 작업:
- `rpi/code/` 실제 simulation / scenario / fault injector Python 구현
- scenario definition 파일 체계 정리
- deterministic reproducibility summary 출력 보강
- optional measurement linkage 보강
- 문서 수준의 더 상세한 example scenario 추가

즉, 지금은 **설치-구성-검증의 기반이 안정화된 상태**이고, 실제 simulation/fault code 구현은 그 다음 단계다.

---

## 11. 후속 작업 권장안

다음 단계로 권장되는 작업은 다음과 같다.

1. `rpi/code/`에 virtual sensor publisher 구현
2. virtual emergency sensor publisher 구현
3. fault injector harness 구현
4. scenario orchestrator 구현
5. reproducibility-oriented scenario summary 출력 보강
6. 필요 시 `rpi/docs/README.md`에 scenario 예시와 expected output 예시 추가

이후에야 RPi가 단순 runtime scaffold를 넘어, 완전한 simulation / fault injection / evaluation 계층으로 동작하게 된다.
