# Mac mini 운영 허브 설치 및 설정 / Mac mini Operational Hub Setup

---

## 1. 개요 / Overview

**한국어**  
Mac mini는 `safe_deferral` 시스템의 안전-임계 운영 엣지 허브입니다. MQTT/컨텍스트 수신, 로컬 LLM 어댑터, Policy Router, Deterministic Validator, 안전 유예(safe deferral), 보호자 에스컬레이션, ACK/감사 로깅, 원격 측정 어댑터가 여기서 실행됩니다.

**English**  
The Mac mini is the safety-critical operational edge hub of the `safe_deferral` system. It hosts MQTT/context intake, the local LLM adapter, Policy Router, Deterministic Validator, safe deferral, caregiver escalation, ACK/audit logging, and the telemetry adapter.

---

## 2. 사전 요구사항 / Prerequisites

**한국어**

| 구성요소 | 버전 | 비고 |
|---|---|---|
| Python | 3.9 이상 | `python3 --version` 으로 확인 |
| pip | 최신 권장 | `pip3 install --upgrade pip` |
| Mosquitto MQTT Broker | 2.x | `brew install mosquitto` |
| Ollama | 최신 | LLM 추론 엔진, `brew install ollama` |
| SQLite | 내장 (Python stdlib) | 별도 설치 불필요 |

**English**

| Component | Version | Notes |
|---|---|---|
| Python | 3.9+ | Verify with `python3 --version` |
| pip | Latest recommended | `pip3 install --upgrade pip` |
| Mosquitto MQTT Broker | 2.x | `brew install mosquitto` |
| Ollama | Latest | Local LLM inference engine, `brew install ollama` |
| SQLite | Bundled (Python stdlib) | No separate installation needed |

---

## 3. Python 패키지 설치 / Python Package Installation

**한국어**

```bash
# 저장소 루트에서 실행
cd /path/to/safe_deferral_claude

pip3 install jsonschema requests pytest
```

패키지 역할:
- `jsonschema` — Policy Router 입력·스키마 및 페이로드 검증
- `requests` — Telegram HTTP 알림 전송 (선택, 실제 배포 시 필요)
- `pytest` — 단위 테스트 실행

**English**

```bash
# Run from repository root
cd /path/to/safe_deferral_claude

pip3 install jsonschema requests pytest
```

Package roles:
- `jsonschema` — Policy Router input schema and payload validation
- `requests` — Telegram HTTP notification delivery (optional; required for production)
- `pytest` — Unit test execution

---

## 4. 환경 변수 설정 / Environment Variable Configuration

**한국어**  
아래 환경 변수를 `.env` 파일 또는 쉘 프로파일에 설정합니다. `.env`는 저장소에 커밋하지 마세요.

```bash
# MQTT 브로커
export SD_MQTT_BROKER_HOST="127.0.0.1"
export SD_MQTT_BROKER_PORT="1883"

# Telegram 보호자 알림 (실제 배포 시 필요)
export SD_TELEGRAM_BOT_TOKEN="<your-bot-token>"
export SD_TELEGRAM_CHAT_ID="<caregiver-chat-id>"

# Ollama LLM 엔드포인트
export SD_OLLAMA_BASE_URL="http://127.0.0.1:11434"
export SD_OLLAMA_MODEL="llama3"

# 감사 로그 SQLite 경로 (기본값: 인메모리)
export SD_AUDIT_DB_PATH="/var/lib/safe_deferral/audit.db"
```

**English**  
Set the following environment variables in a `.env` file or shell profile. Do **not** commit `.env` to the repository.

```bash
# MQTT broker
export SD_MQTT_BROKER_HOST="127.0.0.1"
export SD_MQTT_BROKER_PORT="1883"

# Telegram caregiver notification (required for production)
export SD_TELEGRAM_BOT_TOKEN="<your-bot-token>"
export SD_TELEGRAM_CHAT_ID="<caregiver-chat-id>"

# Ollama LLM endpoint
export SD_OLLAMA_BASE_URL="http://127.0.0.1:11434"
export SD_OLLAMA_MODEL="llama3"

# Audit log SQLite path (default: in-memory)
export SD_AUDIT_DB_PATH="/var/lib/safe_deferral/audit.db"
```

---

## 5. Mosquitto 설정 / Mosquitto Configuration

**한국어**

```bash
# /usr/local/etc/mosquitto/mosquitto.conf (macOS Homebrew 경로)
listener 1883
allow_anonymous true   # 개발 환경 전용. 운영 시 인증 설정 권장
```

시작:
```bash
brew services start mosquitto
# 또는 직접 실행:
mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf
```

**English**

```bash
# /usr/local/etc/mosquitto/mosquitto.conf (macOS Homebrew path)
listener 1883
allow_anonymous true   # Development only. Use authentication in production.
```

Start:
```bash
brew services start mosquitto
# or directly:
mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf
```

---

## 6. Ollama 설정 / Ollama Configuration

**한국어**

```bash
# Ollama 시작
ollama serve

# 모델 다운로드 (최초 1회)
ollama pull llama3

# 동작 확인
curl http://127.0.0.1:11434/api/tags
```

**English**

```bash
# Start Ollama
ollama serve

# Download model (first time only)
ollama pull llama3

# Verify
curl http://127.0.0.1:11434/api/tags
```

---

## 7. 단위 테스트 실행 / Running Unit Tests

**한국어**

```bash
cd /path/to/safe_deferral_claude/mac_mini/code

# 전체 테스트
python3 -m pytest tests/ -v

# 특정 모듈만
python3 -m pytest tests/test_policy_router.py -v
python3 -m pytest tests/test_deterministic_validator.py -v
python3 -m pytest tests/test_audit_logger.py -v
```

예상 결과: `203 passed`

**English**

```bash
cd /path/to/safe_deferral_claude/mac_mini/code

# All tests
python3 -m pytest tests/ -v

# Specific module
python3 -m pytest tests/test_policy_router.py -v
python3 -m pytest tests/test_deterministic_validator.py -v
python3 -m pytest tests/test_audit_logger.py -v
```

Expected result: `203 passed`

---

## 8. 모듈 구조 / Module Structure

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

## 9. 권한 경계 확인 / Authority Boundary Verification

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
