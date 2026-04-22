# mac_mini/docs

이 디렉터리는 **Mac mini 기반 운영 허브(Mac mini Operational Hub)**의 설치, 구성, 배포, 검증 절차를 설명하는 문서 모음이다.

본 프로젝트에서 Mac mini는 다음 역할을 담당한다.

- Docker Compose 기반 로컬 서비스 실행
- MQTT 브로커, Home Assistant, Ollama 등 핵심 서비스 운영
- 현재 canonical policy / schema 자산의 런타임 배포
- SQLite 기반 단일 작성자(single-writer) 지향 감사 로깅 환경 준비
- 설치 후 서비스 정상 동작 여부 검증

> 주의  
> 이 디렉터리는 **Mac mini 운영 환경의 설치·구성·검증**을 설명한다.  
> 아직 개발되지 않은 실제 애플리케이션 코드(`mac_mini/code/`)의 내부 동작 설명은 포함하지 않는다.

---

## 1. Mac mini의 위치와 역할

프로젝트 전체 구조에서 Mac mini는 **운영 허브(operational hub)**이다.

- `mac_mini/`  
  운영용 서비스와 로컬 런타임 환경을 담당
- `rpi/`  
  시뮬레이션, fault injection, closed-loop evaluation 보조
- `esp32/`  
  물리 입력/출력 노드
- `integration/measurement/`  
  선택적 정밀 계측 경로

즉, Mac mini는 실제 운영 환경의 중심이며, 정책 자산과 스키마 자산을 읽기 전용으로 마운트하고, 로컬 서비스들을 실행하는 기준 노드로 사용한다.

---

## 2. 현재 Mac mini 운영 범위

현재 Mac mini 환경은 다음 범위를 기준으로 준비된다.

### 포함되는 운영 요소
- Docker Compose 실행 환경
- Home Assistant
- Mosquitto MQTT Broker
- Ollama 기반 로컬 LLM 런타임
- SQLite 기반 감사 로그 저장소
- 정책 및 스키마 frozen asset 런타임 배포
- Telegram 또는 mock fallback 알림 채널 준비
- 설치 후 단계별 verify 스크립트 실행

### 아직 포함하지 않는 설명
- 실제 `edge_controller_app` 내부 구현 로직
- Policy Router / Validator / Safe Deferral Handler의 세부 코드 구조
- 실제 FastAPI/앱 엔드포인트 구현
- Python 애플리케이션 내부 모듈 설계

즉, 본 README는 **운영 환경 준비와 검증까지**를 다룬다.

---

## 3. 기준이 되는 현재 canonical asset

Mac mini 런타임은 다음 current canonical frozen asset을 기준으로 동작한다.

### Policies
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`

### Companion policy asset
- `common/policies/output_profile_v1_1_0.json`

### Schemas
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

이 자산들은 Mac mini 런타임에서 읽기 전용으로 배포되며, deployment-local `.env`나 runtime copy가 canonical truth를 덮어써서는 안 된다.

---

## 4. Mac mini 런타임 디렉터리 개요

현재 Mac mini 쪽 스크립트들은 기본적으로 다음 workspace를 사용한다.

- Workspace root: `~/smarthome_workspace`
- Docker Compose root: `~/smarthome_workspace/docker`

주요 런타임 경로는 다음과 같다.

- `~/smarthome_workspace/docker/docker-compose.yml`
- `~/smarthome_workspace/docker/.env`
- `~/smarthome_workspace/docker/volumes/homeassistant/config`
- `~/smarthome_workspace/docker/volumes/mosquitto/config`
- `~/smarthome_workspace/docker/volumes/mosquitto/data`
- `~/smarthome_workspace/docker/volumes/mosquitto/log`
- `~/smarthome_workspace/docker/volumes/ollama/data`
- `~/smarthome_workspace/docker/volumes/app/config/policies`
- `~/smarthome_workspace/docker/volumes/app/config/schemas`
- `~/smarthome_workspace/db/audit_log.db`
- `~/smarthome_workspace/.env`

즉, Compose stack 자체는 `docker/` 아래에 위치하고, SQLite DB와 Python runtime `.env`는 workspace root를 기준으로 유지한다.

---

## 5. 실행 전 공통 준비

아래 명령은 저장소 루트에서 실행하는 것을 권장한다.

```bash
cd /path/to/safe_deferral
```

스크립트 실행 권한이 없는 경우 한 번만 다음 명령을 수행한다.

```bash
chmod +x mac_mini/scripts/install/*.sh
chmod +x mac_mini/scripts/configure/*.sh
chmod +x mac_mini/scripts/verify/*.sh
```

각 단계는 **저장소 루트에서 그대로 실행**할 수 있도록 예시 명령을 제공한다.

---

## 6. 설치(install) 단계

설치 단계는 `mac_mini/scripts/install/` 아래 스크립트를 순서대로 실행하는 것을 기본으로 한다.

### 6.1 `00_preflight.sh`
Mac mini가 설치 가능한 상태인지 사전 점검한다.

주요 점검 항목:
- macOS 여부
- Homebrew 설치 여부
- Python 3.11 이상 여부
- 디스크 여유 공간
- 네트워크 연결 가능성

스크립트 경로:
- `mac_mini/scripts/install/00_preflight.sh`

실행 코드:

```bash
bash mac_mini/scripts/install/00_preflight.sh
```

### 6.2 `10_install_homebrew_deps.sh`
운영 및 검증에 필요한 기본 Homebrew 의존성을 설치한다.

현재 기준 설치 대상 예:
- `git`
- `python`
- `just`
- `sqlite`
- `jq`
- `mosquitto`

여기서 `mosquitto` formula는 브로커 자체를 운영하기 위한 것이 아니라, verify 단계에서 `mosquitto_pub`, `mosquitto_sub` 같은 MQTT client 도구를 사용하기 위한 목적도 포함한다.

스크립트 경로:
- `mac_mini/scripts/install/10_install_homebrew_deps.sh`

실행 코드:

```bash
bash mac_mini/scripts/install/10_install_homebrew_deps.sh
```

### 6.3 `20_install_docker_runtime_mac.sh`
Docker Desktop / Docker CLI / Docker Compose 가용성을 점검하고, 필요 시 Docker Desktop 설치를 유도한다.

주요 점검 항목:
- `docker` CLI 존재 여부
- Docker daemon 실행 여부
- `docker compose` plugin 가용성
- Docker network / volume 접근 가능 여부

스크립트 경로:
- `mac_mini/scripts/install/20_install_docker_runtime_mac.sh`

실행 코드:

```bash
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh
```

### 6.4 `21_prepare_compose_stack_mac.sh`
Mac mini Docker Compose workspace를 준비한다.

주요 작업:
- `~/smarthome_workspace/docker` 생성
- compose volume 디렉터리 생성
- SQLite DB용 디렉터리 권한 준비
- 템플릿으로부터 `docker-compose.yml` 생성

스크립트 경로:
- `mac_mini/scripts/install/21_prepare_compose_stack_mac.sh`

실행 코드:

```bash
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh
```

### 6.5 `30_setup_python_venv_mac.sh`
Python 가상환경을 만들고 `requirements-mac.txt`를 기준으로 의존성을 설치한다.

주요 작업:
- `.venv-mac` 생성 또는 재생성
- pip / setuptools / wheel 업그레이드
- requirements 설치
- lock 파일 저장

스크립트 경로:
- `mac_mini/scripts/install/30_setup_python_venv_mac.sh`

실행 코드:

```bash
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh
```

---

## 7. 구성(configure) 단계

구성 단계는 `mac_mini/scripts/configure/` 아래 스크립트로 수행한다.

### 7.1 `70_write_env_files.sh`
deployment-local `.env` 파일을 안전하게 작성한다.

핵심 원칙:
- 이미 존재하는 값을 함부로 덮어쓰지 않음
- canonical policy/schema truth를 env가 대체하지 않음
- endpoint, path, Telegram credentials 같은 runtime-local 설정만 저장

대표 변수 예:
- `MQTT_HOST`
- `MQTT_PORT`
- `OLLAMA_HOST`
- `SQLITE_PATH`
- `POLICY_DIR`
- `SCHEMA_DIR`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

스크립트 경로:
- `mac_mini/scripts/configure/70_write_env_files.sh`

실행 코드:

```bash
bash mac_mini/scripts/configure/70_write_env_files.sh
```

### 7.2 `50_deploy_policy_files.sh`
현재 canonical frozen policy/schema 자산을 Mac mini runtime 경로로 배포한다.

배포 대상:
- current canonical policy assets
- current canonical schema assets
- companion output profile

배포 원칙:
- runtime asset은 canonical filename 그대로 복사
- JSON 파일은 읽기 전용 권한(`chmod 444`) 적용

스크립트 경로:
- `mac_mini/scripts/configure/50_deploy_policy_files.sh`

실행 코드:

```bash
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
```

### 7.3 `40_configure_sqlite.sh`
SQLite DB를 초기화하고 WAL 모드를 적용한다.

현재 기준 핵심 테이블:
- `routing_events`
- `validator_results`
- `deferral_events`
- `timeout_events`
- `escalation_events`
- `caregiver_actions`
- `actuation_ack_events`

즉, 단순 DB 생성이 아니라 **감사 로그용 단일 작성자 지향(single-writer-oriented) 구조**를 준비하는 단계다.

스크립트 경로:
- `mac_mini/scripts/configure/40_configure_sqlite.sh`

실행 코드:

```bash
bash mac_mini/scripts/configure/40_configure_sqlite.sh
```

### 7.4 `20_configure_mosquitto.sh`
Mosquitto 브로커 설정 파일을 준비한다.

핵심 특징:
- LAN-only trust boundary 전제
- 기본 listener 1883 사용
- 익명 접근 기반 기본 설정
- 실제 외부 차단은 라우터/macOS firewall 계층과 함께 고려

스크립트 경로:
- `mac_mini/scripts/configure/20_configure_mosquitto.sh`

실행 코드:

```bash
bash mac_mini/scripts/configure/20_configure_mosquitto.sh
```

### 7.5 `10_configure_home_assistant.sh`
Home Assistant 설정 템플릿을 runtime 경로로 복사하고, 필요 시 컨테이너 재시작을 수행한다.

핵심 원칙:
- 기존 설정 파일이 있으면 덮어쓰지 않음
- 사용자 설정 보존 우선

스크립트 경로:
- `mac_mini/scripts/configure/10_configure_home_assistant.sh`

실행 코드:

```bash
bash mac_mini/scripts/configure/10_configure_home_assistant.sh
```

### 7.6 `30_configure_ollama.sh`
Ollama 서비스를 실행하고, 현재 baseline 모델인 `llama3.1`을 준비한 뒤 간단한 추론 검증까지 수행한다.

핵심 특징:
- `ollama` compose service 확인
- API 접근성 확인
- `llama3.1` model pull
- `READY` 응답 검증

스크립트 경로:
- `mac_mini/scripts/configure/30_configure_ollama.sh`

실행 코드:

```bash
bash mac_mini/scripts/configure/30_configure_ollama.sh
```

### 7.7 `60_configure_notifications.sh`
알림 채널을 구성한다.

동작 방식:
- Telegram token/chat ID가 정상 값이면 Telegram 모드
- placeholder 또는 미설정 상태면 mock fallback 모드
- 실제 API 연결 테스트 실패 시에도 mock fallback으로 전환 가능

스크립트 경로:
- `mac_mini/scripts/configure/60_configure_notifications.sh`

실행 코드:

```bash
bash mac_mini/scripts/configure/60_configure_notifications.sh
```

---

## 8. Compose 템플릿 개요

`mac_mini/scripts/templates/docker-compose.template.yml`은 Mac mini 운영 환경의 기본 Compose template이다.

현재 포함되는 핵심 서비스:
- `mosquitto`
- `homeassistant`
- `ollama`
- `edge_controller_app`

핵심 원칙:
- policy/schema 자산은 app 컨테이너에 읽기 전용으로 마운트
- SQLite DB는 별도 경로로 마운트
- Ollama는 로컬 API endpoint로 사용
- Home Assistant는 로컬 디스커버리 특성 때문에 host network를 사용할 수 있음

> 주의  
> 현재 `edge_controller_app`의 실제 구현 코드는 아직 본 README에서 설명하지 않는다.  
> 여기서는 오직 Compose 관점에서의 자리와 마운트 구조만 다룬다.

---

## 9. 검증(verify) 단계

검증 단계는 `mac_mini/scripts/verify/` 아래 스크립트로 수행한다.

### 9.1 `10_verify_docker_services.sh`
현재 핵심 Docker Compose 서비스가 실제 running 상태인지 확인한다.

현재 검증 대상:
- `homeassistant`
- `mosquitto`
- `ollama`
- `edge_controller_app`

스크립트 경로:
- `mac_mini/scripts/verify/10_verify_docker_services.sh`

실행 코드:

```bash
bash mac_mini/scripts/verify/10_verify_docker_services.sh
```

### 9.2 `20_verify_mqtt_pubsub.sh`
Mosquitto 브로커의 pub/sub 기능을 실제로 검증한다.

검증 방식:
- subscriber를 먼저 띄움
- test topic에 publish
- 실제 메시지가 수신되는지 확인

스크립트 경로:
- `mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh`

실행 코드:

```bash
bash mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh
```

### 9.3 `30_verify_ollama_inference.sh`
Ollama inference API가 실제로 동작하는지 확인한다.

검증 방식:
- `/api/generate` 호출
- `llama3.1` 모델에 `READY` 응답 요청
- 기대한 형식으로 응답이 오는지 확인

스크립트 경로:
- `mac_mini/scripts/verify/30_verify_ollama_inference.sh`

실행 코드:

```bash
bash mac_mini/scripts/verify/30_verify_ollama_inference.sh
```

### 9.4 `40_verify_sqlite.sh`
SQLite DB health와 schema readiness를 점검한다.

검증 항목:
- DB 파일 존재 여부
- WAL mode 여부
- integrity check
- 필수 audit tables 존재 여부

스크립트 경로:
- `mac_mini/scripts/verify/40_verify_sqlite.sh`

실행 코드:

```bash
bash mac_mini/scripts/verify/40_verify_sqlite.sh
```

### 9.5 `50_verify_env_and_assets.sh`
runtime `.env`와 배포된 canonical assets를 검증한다.

검증 항목:
- 필수 env 변수 존재 여부
- runtime policy/schema 디렉터리 존재 여부
- current canonical JSON asset 존재 여부
- JSON parse 가능 여부

스크립트 경로:
- `mac_mini/scripts/verify/50_verify_env_and_assets.sh`

실행 코드:

```bash
bash mac_mini/scripts/verify/50_verify_env_and_assets.sh
```

### 9.6 `60_verify_notifications.sh`
알림 채널 가용성 자체를 검증한다.

검증 방식:
- Telegram credentials가 유효하면 실제 Telegram API 송신 확인
- 아니면 mock log fallback 경로 확인

> 주의  
> 이 스크립트는 **notification channel availability**를 검증하는 것이며,  
> Class 2 payload schema 전체 정합성을 검증하는 스크립트는 아니다.

스크립트 경로:
- `mac_mini/scripts/verify/60_verify_notifications.sh`

실행 코드:

```bash
bash mac_mini/scripts/verify/60_verify_notifications.sh
```

### 9.7 `80_verify_services.sh`
개별 verify 스크립트를 순차 실행하는 aggregate wrapper이다.

즉, 더 이상 별도의 독자적 strict verifier라기보다,
- Docker
- MQTT
- Ollama
- SQLite
- env/assets
- notifications  
검증을 순서대로 실행하는 orchestration script 역할을 수행한다.

스크립트 경로:
- `mac_mini/scripts/verify/80_verify_services.sh`

실행 코드:

```bash
bash mac_mini/scripts/verify/80_verify_services.sh
```

---

## 10. 권장 실행 순서

Mac mini 환경을 처음 준비할 때는 아래 순서를 권장한다.

### 설치
```bash
bash mac_mini/scripts/install/00_preflight.sh
bash mac_mini/scripts/install/10_install_homebrew_deps.sh
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh
```

### 구성
```bash
bash mac_mini/scripts/configure/70_write_env_files.sh
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
bash mac_mini/scripts/configure/40_configure_sqlite.sh
bash mac_mini/scripts/configure/20_configure_mosquitto.sh
bash mac_mini/scripts/configure/10_configure_home_assistant.sh
bash mac_mini/scripts/configure/30_configure_ollama.sh
bash mac_mini/scripts/configure/60_configure_notifications.sh
```

### 검증
```bash
bash mac_mini/scripts/verify/10_verify_docker_services.sh
bash mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh
bash mac_mini/scripts/verify/30_verify_ollama_inference.sh
bash mac_mini/scripts/verify/40_verify_sqlite.sh
bash mac_mini/scripts/verify/50_verify_env_and_assets.sh
bash mac_mini/scripts/verify/60_verify_notifications.sh
bash mac_mini/scripts/verify/80_verify_services.sh
```

실제 사용 시에는 `80_verify_services.sh`만 실행해도 되지만, 문제 발생 시에는 개별 verify 스크립트를 직접 실행해 원인을 분리하는 것이 좋다.

---

## 11. 빠른 시작용 한 번에 실행 예시

아래는 처음 설정할 때 따라 할 수 있는 예시다.

```bash
cd /path/to/safe_deferral

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
cd -

bash mac_mini/scripts/verify/80_verify_services.sh
```

---

## 12. 운영 시 주의사항

### 12.1 canonical truth와 deployment-local 설정을 혼동하지 말 것
- policy table, low-risk action catalog, fault rules, schema는 canonical frozen asset이다.
- `.env`, runtime path, compose mount는 deployment-local 설정이다.
- deployment-local 값이 canonical truth를 대체해서는 안 된다.

### 12.2 Mac mini는 운영 허브이지 실험 노드가 아님
- fault injection
- 시뮬레이션 전용 경로
- 폐루프 평가 보조  
같은 역할은 Raspberry Pi 계층과 분리해 유지해야 한다.

### 12.3 LLM은 실행 권한의 주체가 아님
Mac mini에서 Ollama를 실행하더라도, 실제 프로젝트 원칙은 다음과 같다.

- LLM은 bounded Class 1 assistance만 담당
- deterministic validator가 실행 허용 여부를 결정
- ambiguity는 safe deferral 또는 Class 2 escalation로 처리
- unsafe autonomous actuation은 허용하지 않음

---

## 13. 아직 남아 있는 향후 작업

현재 README는 설치, 구성, 배포, 검증까지만 설명한다.  
아직 향후 작업으로 남아 있는 핵심은 다음과 같다.

- `mac_mini/code/` 실제 애플리케이션 구현
- Policy Router 구현
- Deterministic Validator 구현
- Context-integrity-based safe deferral stage 구현
- Audit Logger service 구현
- Notification backend / caregiver confirmation backend 구현

즉, **Mac mini 운영 환경의 바깥쪽 준비는 상당 부분 정리되었고, 앞으로는 실제 코드 구현이 핵심 단계**가 된다.

---

## 14. 문서 갱신 원칙

다음 중 하나가 바뀌면 이 README도 함께 갱신하는 것이 바람직하다.

- current canonical policy/schema asset set
- Mac mini runtime directory layout
- Docker Compose template
- install / configure / verify script 흐름
- current baseline model decision
- notification channel strategy

특히 asset version이 바뀌었는데 README가 그대로면, 설치/검증 절차와 설명이 다시 drift할 수 있다.
