# Mac mini 운영 허브 설치 및 설정 / Mac mini Operational Hub Setup

---

## 1. 개요 / Overview

**한국어**  
Mac mini는 `safe_deferral` 시스템의 안전-임계 운영 엣지 허브입니다. MQTT/컨텍스트 수신, 로컬 LLM 어댑터, Policy Router, Deterministic Validator, 안전 유예(safe deferral), 보호자 에스컬레이션, ACK/감사 로깅, 원격 측정 어댑터가 여기서 실행됩니다.

설치는 세 단계로 구성되며 모두 `mac_mini/scripts/` 하위의 스크립트로 처리됩니다:
- **install/** — Homebrew, 의존성, Docker, Python venv 설치
- **configure/** — Mosquitto·Ollama·SQLite·정책 파일·알림 설정
- **verify/** — 전체 서비스 동작 검증

**English**  
The Mac mini is the safety-critical operational edge hub of the `safe_deferral` system. It hosts MQTT/context intake, the local LLM adapter, Policy Router, Deterministic Validator, safe deferral, caregiver escalation, ACK/audit logging, and the telemetry adapter.

Installation is divided into three phases, all handled by scripts under `mac_mini/scripts/`:
- **install/** — Homebrew, dependencies, Docker, Python venv
- **configure/** — Mosquitto, Ollama, SQLite, policy files, notifications
- **verify/** — Full service verification

---

## 2. 사전 요구사항 / Prerequisites

**한국어**
- macOS (Apple Silicon 또는 Intel)
- 관리자(admin) 계정으로 로그인
- 인터넷 연결 (Homebrew, Docker, Ollama 모델 다운로드)
- 저장 공간 15 GB 이상 (Ollama 모델 + Docker 이미지 포함)

**English**
- macOS (Apple Silicon or Intel)
- Logged in as an admin user
- Internet connection (required for Homebrew, Docker, and Ollama model downloads)
- At least 15 GB of free disk space (including Ollama model and Docker images)

---

## 3. 설치 (install) / Installation

**한국어**  
스크립트는 숫자 순서로 실행합니다. 저장소 루트에서 실행하거나 각 스크립트 경로를 직접 지정합니다.

```bash
# 저장소 루트로 이동
cd /path/to/safe_deferral_claude
```

### 3-1. Homebrew 설치

```bash
bash mac_mini/scripts/install/00_install_homebrew.sh
```

**결과 확인:** `[PASS] Homebrew is ready`  
이미 설치된 경우 자동으로 건너뜁니다. 설치 후 인스톨러가 `~/.zprofile`에 shellenv 추가를 안내하면 지시에 따르고 새 터미널을 엽니다.

### 3-2. 사전 검사

```bash
bash mac_mini/scripts/install/00_preflight.sh
```

**결과 확인:** `[PASS] All preflight checks completed successfully`  
디스크 공간 부족, 네트워크 불가 등의 경고가 있으면 해결 후 진행합니다.

### 3-3. Homebrew 패키지 설치

```bash
bash mac_mini/scripts/install/10_install_homebrew_deps.sh
```

설치 패키지: `git`, `python@3.12`, `just`, `sqlite`, `jq`, `mosquitto`  
**결과 확인:** `[PASS] Homebrew base dependencies installed successfully`

### 3-4. Docker 런타임 확인

```bash
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh
```

Docker Desktop이 없으면 Homebrew Cask로 설치합니다.  
> **주의**: 설치 후 Docker Desktop 앱을 직접 열어 초기 설정을 완료하고 Docker 엔진이 시작된 것을 확인한 뒤 스크립트를 다시 실행합니다.

**결과 확인:** `[PASS] Docker daemon and compose are running and ready`

### 3-5. Docker Compose 워크스페이스 준비

```bash
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh
```

`~/smarthome_workspace/docker/` 하위에 볼륨 디렉터리와 `docker-compose.yml`을 생성합니다.  
**결과 확인:** `[PASS] Docker Compose workspace prepared`

### 3-6. Python 가상환경 생성

```bash
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh
```

`~/smarthome_workspace/.venv-mac`에 Python 3.12 가상환경을 생성하고 `requirements-mac.txt`의 패키지를 설치합니다.  
**결과 확인:** `[PASS] Python virtual environment ready`

---

**English**  
Run scripts in numeric order from the repository root.

```bash
cd /path/to/safe_deferral_claude
```

### 3-1. Install Homebrew

```bash
bash mac_mini/scripts/install/00_install_homebrew.sh
```

**Success:** `[PASS] Homebrew is ready`  
Already installed installs are skipped. If the installer suggests adding shellenv to `~/.zprofile`, apply it and open a new terminal.

### 3-2. Preflight checks

```bash
bash mac_mini/scripts/install/00_preflight.sh
```

**Success:** `[PASS] All preflight checks completed successfully`  
Resolve any warnings about disk space or network before continuing.

### 3-3. Install Homebrew packages

```bash
bash mac_mini/scripts/install/10_install_homebrew_deps.sh
```

Packages: `git`, `python@3.12`, `just`, `sqlite`, `jq`, `mosquitto`  
**Success:** `[PASS] Homebrew base dependencies installed successfully`

### 3-4. Verify Docker runtime

```bash
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh
```

Installs Docker Desktop via Homebrew Cask if not present.  
> **Note**: After installation, open Docker Desktop manually, complete initial setup, wait for the engine to start, then re-run this script.

**Success:** `[PASS] Docker daemon and compose are running and ready`

### 3-5. Prepare Docker Compose workspace

```bash
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh
```

Creates volume directories and `docker-compose.yml` under `~/smarthome_workspace/docker/`.  
**Success:** `[PASS] Docker Compose workspace prepared`

### 3-6. Create Python virtual environment

```bash
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh
```

Creates a Python 3.12 venv at `~/smarthome_workspace/.venv-mac` and installs packages from `requirements-mac.txt`.  
**Success:** `[PASS] Python virtual environment ready`

---

## 4. 설정 (configure) / Configuration

**한국어**  
configure 단계는 먼저 환경 변수 파일(`.env`)을 작성한 뒤 나머지 스크립트를 실행합니다.

### 4-1. 환경 변수 파일 작성

```bash
bash mac_mini/scripts/configure/70_write_env_files.sh
```

`~/smarthome_workspace/.env`와 `~/smarthome_workspace/docker/.env`를 생성합니다.  
스크립트 실행 후 아래 항목을 실제 값으로 편집합니다:

```bash
# 편집할 파일
nano ~/smarthome_workspace/.env
```

필수 입력 항목:
| 키 | 설명 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram 보호자 알림 봇 토큰 (없으면 mock 로그로 대체) |
| `TELEGRAM_CHAT_ID` | 보호자 Telegram 채널 ID |
| `MQTT_HOST` | Mac mini의 LAN IP 주소 (예: `192.168.1.100`) |

**결과 확인:** `>>> [70_write_env_files] Writing deployment-local environment files...`

### 4-2. Mosquitto 설정

```bash
bash mac_mini/scripts/configure/20_configure_mosquitto.sh
```

Docker 볼륨 경로에 `mosquitto.conf`를 생성합니다 (LAN-only, anonymous 허용).  
**결과 확인:** `[PASS] Mosquitto configuration complete`

### 4-3. Ollama 설정 및 모델 다운로드

```bash
bash mac_mini/scripts/configure/30_configure_ollama.sh
```

Docker Compose로 Ollama 서비스를 시작하고 `llama3.1` 모델을 다운로드합니다.  
> 첫 실행 시 모델 다운로드에 수 분이 소요됩니다.

**결과 확인:** `[PASS] Ollama is running and Llama 3.1 model is ready`

### 4-4. SQLite DB 초기화

```bash
bash mac_mini/scripts/configure/40_configure_sqlite.sh
```

`audit_log.db`를 생성하고 WAL 모드 및 감사 로그 스키마를 적용합니다.  
**결과 확인:** `[PASS] SQLite database initialized`

### 4-5. 정책·스키마 파일 배포

```bash
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
```

`common/policies/`, `common/schemas/`, `common/mqtt/`, `common/payloads/`를 Docker 볼륨 경로로 복사합니다.  
**결과 확인:** `[PASS] Canonical runtime reference assets deployed`

### 4-6. 알림 설정

```bash
bash mac_mini/scripts/configure/60_configure_notifications.sh
```

`.env`의 Telegram 설정이 유효하면 실제 전송을 시도합니다. 미설정이면 mock 로그 파일(`~/smarthome_workspace/logs/mock_notifications.log`)로 대체합니다.  
**결과 확인:** `[PASS] Notification interface configured`

### 4-7. Home Assistant 설정 (선택)

```bash
bash mac_mini/scripts/configure/10_configure_home_assistant.sh
```

HA 설정 파일이 없는 경우에만 템플릿을 적용합니다. 기존 파일은 덮어쓰지 않습니다.  
**결과 확인:** `[PASS] Home Assistant configuration step complete`

---

**English**

### 4-1. Write environment variables

```bash
bash mac_mini/scripts/configure/70_write_env_files.sh
```

Creates `~/smarthome_workspace/.env` and `~/smarthome_workspace/docker/.env`. After running, edit the file to fill in real values:

```bash
nano ~/smarthome_workspace/.env
```

Required values:
| Key | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram caregiver notification bot token (uses mock log if unset) |
| `TELEGRAM_CHAT_ID` | Caregiver Telegram channel ID |
| `MQTT_HOST` | Mac mini LAN IP address (e.g. `192.168.1.100`) |

### 4-2. Configure Mosquitto

```bash
bash mac_mini/scripts/configure/20_configure_mosquitto.sh
```

Writes `mosquitto.conf` to the Docker volume path (LAN-only, anonymous allowed).  
**Success:** `[PASS] Mosquitto configuration complete`

### 4-3. Configure Ollama and download model

```bash
bash mac_mini/scripts/configure/30_configure_ollama.sh
```

Starts the Ollama service via Docker Compose and pulls the `llama3.1` model.  
> First run may take several minutes to download the model.

**Success:** `[PASS] Ollama is running and Llama 3.1 model is ready`

### 4-4. Initialize SQLite database

```bash
bash mac_mini/scripts/configure/40_configure_sqlite.sh
```

Creates `audit_log.db` and applies WAL mode and audit log schema.  
**Success:** `[PASS] SQLite database initialized`

### 4-5. Deploy policy and schema files

```bash
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
```

Copies `common/policies/`, `common/schemas/`, `common/mqtt/`, and `common/payloads/` to the Docker volume path.  
**Success:** `[PASS] Canonical runtime reference assets deployed`

### 4-6. Configure notifications

```bash
bash mac_mini/scripts/configure/60_configure_notifications.sh
```

Tests Telegram delivery if the `.env` tokens are valid. Falls back to a mock log at `~/smarthome_workspace/logs/mock_notifications.log` if unset.  
**Success:** `[PASS] Notification interface configured`

### 4-7. Configure Home Assistant (optional)

```bash
bash mac_mini/scripts/configure/10_configure_home_assistant.sh
```

Applies the template only if no configuration file exists. Existing files are not overwritten.  
**Success:** `[PASS] Home Assistant configuration step complete`

---

## 5. 검증 (verify) / Verification

**한국어**  
개별 검증 스크립트를 순서대로 실행하거나, 통합 스크립트로 한 번에 실행합니다.

```bash
# 전체 검증 (권장)
bash mac_mini/scripts/verify/80_verify_services.sh
```

개별 실행:
```bash
bash mac_mini/scripts/verify/10_verify_docker_services.sh   # Docker Compose 서비스 상태
bash mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh       # MQTT pub/sub 동작
bash mac_mini/scripts/verify/30_verify_ollama_inference.sh  # Ollama 추론 API
bash mac_mini/scripts/verify/40_verify_sqlite.sh            # SQLite 스키마·WAL 모드
bash mac_mini/scripts/verify/50_verify_env_and_assets.sh    # 환경 변수·배포 자산
bash mac_mini/scripts/verify/60_verify_notifications.sh     # 알림 채널
```

모든 단계가 `[PASS]`로 끝나면 Mac mini 허브가 정상 동작 준비 완료입니다.

**English**  
Run individual verification scripts in order, or use the aggregated script.

```bash
# Full verification (recommended)
bash mac_mini/scripts/verify/80_verify_services.sh
```

Individual:
```bash
bash mac_mini/scripts/verify/10_verify_docker_services.sh   # Docker Compose service health
bash mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh       # MQTT pub/sub operation
bash mac_mini/scripts/verify/30_verify_ollama_inference.sh  # Ollama inference API
bash mac_mini/scripts/verify/40_verify_sqlite.sh            # SQLite schema and WAL mode
bash mac_mini/scripts/verify/50_verify_env_and_assets.sh    # Environment vars and deployed assets
bash mac_mini/scripts/verify/60_verify_notifications.sh     # Notification channel
```

All steps passing `[PASS]` confirms the Mac mini hub is ready for operation.

---

## 6. 단위 테스트 실행 / Running Unit Tests

**한국어**

```bash
source ~/smarthome_workspace/.venv-mac/bin/activate
cd /path/to/safe_deferral_claude/mac_mini/code

# 전체 테스트
python -m pytest tests/ -v

# 특정 모듈만
python -m pytest tests/test_policy_router.py -v
python -m pytest tests/test_deterministic_validator.py -v
python -m pytest tests/test_audit_logger.py -v
```

예상 결과: `203 passed`

**English**

```bash
source ~/smarthome_workspace/.venv-mac/bin/activate
cd /path/to/safe_deferral_claude/mac_mini/code

# All tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_policy_router.py -v
python -m pytest tests/test_deterministic_validator.py -v
python -m pytest tests/test_audit_logger.py -v
```

Expected result: `203 passed`

---

## 7. 모듈 구조 / Module Structure

**한국어**

```
mac_mini/code/
├── shared/             # RpiAssetLoader (정책·스키마 파일 읽기 전용)
├── context_intake/     # MM-01: MQTT 컨텍스트 입력 검증
├── policy_router/      # MM-03: CLASS_0/1/2 라우팅
├── deterministic_validator/ # MM-04: JSON 스키마 검증
├── local_llm_adapter/  # MM-02: Ollama LLM 어댑터
├── safe_deferral_handler/   # MM-05: 안전 유예 처리
├── class2_clarification_manager/ # MM-06: Class 2 명확화
├── low_risk_dispatcher/ # MM-07: 저위험 명령 디스패치 + ACK
├── caregiver_escalation/ # MM-08: 보호자 Telegram 에스컬레이션
├── audit_logger/       # MM-09: SQLite WAL 감사 로그
└── telemetry_adapter/  # MM-10: 측정 집계·발행
```

**English**

```
mac_mini/code/
├── shared/             # RpiAssetLoader (read-only policy/schema access)
├── context_intake/     # MM-01: MQTT context input validation
├── policy_router/      # MM-03: CLASS_0/1/2 routing
├── deterministic_validator/ # MM-04: JSON schema validation
├── local_llm_adapter/  # MM-02: Ollama LLM adapter
├── safe_deferral_handler/   # MM-05: Safe deferral handling
├── class2_clarification_manager/ # MM-06: Class 2 clarification
├── low_risk_dispatcher/ # MM-07: Low-risk dispatch + ACK
├── caregiver_escalation/ # MM-08: Caregiver Telegram escalation
├── audit_logger/       # MM-09: SQLite WAL audit log
└── telemetry_adapter/  # MM-10: Telemetry aggregation and publish
```

---

## 8. 권한 경계 확인 / Authority Boundary Verification

**한국어**  
아래 사항은 코드 변경 시 반드시 유지해야 합니다:
- LLM 출력은 후보 안내(candidate guidance)일 뿐, 정책 권한이 아닙니다.
- `doorbell_detected`는 도어락 인가가 아닙니다.
- 타임아웃/무응답은 항상 에스컬레이션이며 승인이 아닙니다.
- 모든 감사 레코드에 `authority_note` 필드가 포함됩니다.

**English**  
The following must be preserved across code changes:
- LLM output is candidate guidance only, not policy authority.
- `doorbell_detected` is not doorlock authorization.
- Timeout/no-response always escalates; it never approves.
- Every audit record includes an `authority_note` field.
