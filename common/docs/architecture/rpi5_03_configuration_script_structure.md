# Raspberry Pi 5 설정 스크립트 구조안 

## 목표

Raspberry Pi 5가 Mac mini의 Mosquitto broker와 안전하게 통신하고, 동기화된 정책/스키마 자산을 바탕으로 **정책 기반 동적 페이로드 생성**을 수행할 수 있도록 설정한다.

## 기본 원칙

* `.env` 기반으로 MQTT 접속 정보와 실험 파라미터를 주입한다.
* Phase 0 정책/스키마 자산은 **Mac mini 저장소를 authoritative source**로 두고 Pi 5에 read-only synced copy를 둔다.
* 시간 동기화는 **Mac mini를 authoritative local time source**로 사용한다.
* Pi 5는 외부 WAN NTP 서버를 사용하지 않는다.
* 시간 동기화는 “완벽한 ms 보장”이 아니라, **실험 전 offset 측정·기록 및 target bound 검증**으로 관리한다.
* 설정 후에는 MQTT 연결, 정책 자산 버전 일치, time sync 상태를 반드시 검증한다.

## 권장 디렉토리 구조

scripts/
├── configure/
│   ├── 10_write_env_files_rpi.sh
│   ├── 20_sync_phase0_artifacts_rpi.sh
│   ├── 30_configure_time_sync_rpi.sh
│   ├── 40_configure_simulation_runtime_rpi.sh
│   └── 50_configure_fault_profiles_rpi.sh
configs/
├── env/
│   └── rpi.env.template
├── sync/
│   └── artifact_manifest.json
└── simulation/
    ├── node_profiles.yaml
    ├── scenario_profiles.yaml
    └── fault_profiles.yaml

## 스크립트별 역할

### 10_write_env_files_rpi.sh

다음 정보를 .env 또는 동등한 설정 파일로 생성한다.

* MQTT broker host/IP
* MQTT broker port
* MQTT username/password
* topic namespace
* node count
* publish interval
* scenario profile
* fault profile
* schema sync path
* Mac mini time source host/IP
* verification audit topic
* time sync target bound

## 20_sync_phase0_artifacts_rpi.sh

Mac mini 저장소 또는 공유 경로에서 아래 파일을 Pi 5로 동기화한다.

* policy_table.json
* context_schema.json
* candidate_action_schema.json
* policy_router_input_schema.json
* validator_output_schema.json
* fault_injection_rules.json

### 필수 요구사항

* authoritative source는 Mac mini repository
* Pi 5에는 read-only synced copy 유지
* 동기화 후 버전/체크섬 비교 수행
* **비밀번호 입력이 필요한 대화형 sync 방식은 금지**
* 권장 방식:
  1. SSH key–based unattended sync (preferred)
  1. local read-only HTTP artifact server via wget/curl (fallback)

## 30_configure_time_sync_rpi.sh

* Mac mini를 authoritative local time source로 설정
* Pi 5는 외부 WAN NTP 서버를 사용하지 않도록 구성
* NTP 또는 동등 메커니즘 적용
* 실험 전 clock offset 측정 명령 준비
* offset과 jitter를 로그 파일로 저장하는 구조 준비
* 시간 동기화 원칙
* 목표는 측정·기록·검증 가능한 target bound 유지
* stale fault injection은 measured offset + jitter보다 충분히 큰 margin으로 생성

## 40_configure_simulation_runtime_rpi.sh

* topic namespace 반영
* node count 반영
* publish interval 반영
* scenario file 경로 반영
* verification audit topic 반영

## 50_configure_fault_profiles_rpi.sh

* deterministic fault case 설정
* randomized stress injection 설정
* stale/missing/conflict/threshold-crossing fault 설정 파일 배포

## 핵심 설정 원칙

### MQTT 접속 정보 배포

하드코딩 금지. 반드시 .env 또는 외부 설정 파일 사용.

### Phase 0 자산 동기화

결함 주입 수치나 payload 구조를 코드에 직접 적지 않고, 동기화된 정책/스키마 파일을 파싱하여 생성해야 한다.

### Time sync 운영 원칙
* Mac mini만 로컬 시간원으로 사용
* 외부 인터넷 시간원 사용 금지
* 실험 전 offset 측정 및 로그 기록
* stale margin은 measured offset + jitter를 초과해야 함

## 실행 순서 예시
```
bash scripts/configure/10_write_env_files_rpi.sh
bash scripts/configure/20_sync_phase0_artifacts_rpi.sh
bash scripts/configure/30_configure_time_sync_rpi.sh
bash scripts/configure/40_configure_simulation_runtime_rpi.sh
bash scripts/configure/50_configure_fault_profiles_rpi.sh
```