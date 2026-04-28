# SESSION_HANDOFF_2026-04-28_ENTRYPOINT_AND_RUN_DOC_UPDATE.md

## Purpose

이 addendum은 2026-04-28 세션에서 진행된 진입점(entry point) 작성,
설치 문서 보완, 통합 실행 문서 신규 작성 작업을 기록합니다.

---

## What Was Completed

### 1. Mac mini / RPi 주소 탐색 분석 및 문서 수정

- RPi Python 코드와 스크립트를 검토한 결과, 자동 mDNS/Bonjour 탐색 코드는
  없지만 `rpi/scripts/configure/10_write_env_files_rpi.sh`의 기본값이
  `MAC_MINI_HOST=mac-mini.local`로 설정되어 있어 macOS Bonjour가 동작하는
  환경에서는 별도 IP 입력 없이 연결됨을 확인.
- `docs/setup/02_rpi_setup.md` 수정:
  - 전제조건 절에 Mac mini 주소 확인 방법 추가
    (`scutil --get LocalHostName`, `ping mac-mini.local`, IP 폴백 방법)
  - 섹션 4-1의 `MAC_MINI_HOST` 설명을 "IP 주소" → "호스트명 또는 IP"로 수정,
    스크립트 기본값(`mac-mini.local`)과 일치하도록 정렬

### 2. 진입점(entry point) 부재 확인

Mac mini와 RPi Python 코드(203 + 79 테스트)는 완성된 라이브러리 클래스로만
구성되어 있고 다음이 누락되어 있음을 확인:
- 실제 MQTT 클라이언트 연결 코드 (`paho-mqtt`)
- 컴포넌트 간 파이프라인을 연결하는 앱 진입점
- 환경변수 로딩 (`python-dotenv`)

### 3. `mac_mini/code/main.py` 신규 작성

파일 경로: `mac_mini/code/main.py` (389줄)

구현 내용:
- `~/smarthome_workspace/.env` 로드 (python-dotenv 설치 시)
- MQTT 연결 (`MQTT_HOST`, `MQTT_PORT`, `MQTT_USER`, `MQTT_PASS`)
- 별도 worker 스레드 + `queue.Queue`로 파이프라인 처리 (MQTT 콜백 블로킹 방지)
- 구독 토픽:
  - `safe_deferral/context/input` → 메인 파이프라인
  - `safe_deferral/actuation/ack` → AckHandler
- 파이프라인 흐름:
  - ContextIntake → PolicyRouter
  - CLASS_0 → CaregiverEscalationBackend (긴급 알림)
  - CLASS_1 → LocalLlmAdapter → DeterministicValidator
    - APPROVED → LowRiskDispatcher (command_id ACK 추적)
    - SAFE_DEFERRAL → SafeDeferralHandler.start_clarification() → handle_timeout() → Class2Manager
    - REJECTED_ESCALATION → Class2Manager
  - CLASS_2 → Class2Manager.start_session() → handle_timeout() → CaregiverEscalation
  - TelemetryAdapter.update_*() + publish() 매 단계 호출
- ACK 추적: `threading.Lock` 보호 dict (`command_id → DispatchRecord`)
- 환경변수:
  - `TELEGRAM_TOKEN` / `TELEGRAM_CHAT_ID` 미설정 시 NoOp sender 자동 선택
  - `OLLAMA_URL` 설정 시 OllamaClient, 미설정 시 MockLlmClient

### 4. `rpi/code/main.py` 신규 작성

파일 경로: `rpi/code/main.py` (195줄)

구현 내용:
- `~/smarthome_workspace/.env` 로드 (python-dotenv 설치 시)
- MQTT 연결 (`MQTT_HOST` 기본값: `mac-mini.local`)
- Dashboard FastAPI 앱 (port 8888) uvicorn 데몬 스레드로 실행
- Governance UI FastAPI 앱 (port 8889) uvicorn 데몬 스레드로 실행
- 모니터링 토픽 4개 구독 (observation only, 액추에이터 없음):
  - `safe_deferral/validator/output`
  - `safe_deferral/actuation/command`
  - `safe_deferral/audit/log`
  - `safe_deferral/dashboard/observation`
- `MqttStatusMonitor.observe_message()` 콜백 연결
- 연결 실패 시 오류 메시지에 `MQTT_HOST` 확인 안내 포함

### 5. `docs/setup/05_integration_run.md` 신규 작성

전체 시스템 통합 실행 절차 문서 (한국어/영어 병기):

| 절 | 내용 |
|----|------|
| 1. 기동 순서 개요 | Docker → Mac mini → RPi → ESP32 순서 |
| 2. Mac mini 기동 | `docker compose up -d`, 서비스 확인, `python main.py` 예상 로그 |
| 3. RPi 기동 | Mac mini 연결 확인, `python main.py` 예상 로그, 대시보드 URL |
| 4. ESP32 연결 | 최초 SoftAP 프로비저닝 절차, 노드별 토픽 확인 |
| 5. 헬스체크 | 테스트 페이로드 발행, RPi curl 확인, 폐쇄루프 감사 검증 |
| 6. 정지 절차 | 역순 종료 |
| 7. 트러블슈팅 | 7가지 증상별 원인 + 조치 |
| 8. 포트 요약 | 서비스별 호스트·포트 |

`docs/setup/README.md`에 항목 추가.

---

## 남은 작업 (Remaining Work)

### 즉시 가능 (하드웨어 불필요)

1. **`requirements-rpi.txt` 패키지 추가**
   - `fastapi`, `uvicorn`, `python-dotenv` 누락
   - `rpi/code/main.py`가 이 패키지들을 사용

2. **`requirements-mac.txt`에 `python-dotenv` 추가**
   - `mac_mini/code/main.py`가 optional import로 사용

3. **완성된 시나리오 픽스처 파일 작성**
   - `integration/scenarios/*.json`은 모두 스켈레톤 상태
   - `payload_fixture`로 참조되는 실제 MQTT 발행용 JSON 페이로드 파일 필요
   - `05_integration_run.md`에서 참조한 `sc01_light_on_request.json` 미존재

### 하드웨어 연결 후 가능

4. **실제 실험 실행** — `required_experiments.md` 기준
5. **ESP32 / STM32 펌웨어 하드웨어 검증**

### 실험 결과 후 가능

6. **시스템 구조 다이어그램 수정** — `08_system_structure_figure_revision_plan.md` 참조
7. **논문 작성** — `common/docs/paper/` 섹션 아웃라인 존재

---

## 현재 구현 상태 (업데이트)

| 레이어 | 상태 |
|--------|------|
| Mac mini (MM-01~10) | ✅ 구현 완료, 203 테스트 통과 |
| Mac mini 진입점 (`main.py`) | ✅ 신규 작성 |
| RPi 앱 (RPI-01~10) | ✅ 구현 완료, 79 테스트 통과 |
| RPi 진입점 (`main.py`) | ✅ 신규 작성 |
| ESP32 노드 (PN-01~08) | ✅ 구현 완료, 하드웨어 검증 대기 |
| STM32 타이밍 (STM32-01~05) | ✅ 스켈레톤 구현, 하드웨어 검증 대기 |
| 설치 문서 (01~04) | ✅ 완료 (스크립트 기반, Telegram/mDNS 보완) |
| 통합 실행 문서 (05) | ✅ 신규 작성 |
| requirements-rpi.txt | ⚠️ fastapi/uvicorn/python-dotenv 누락 |
| requirements-mac.txt | ⚠️ python-dotenv 누락 |
| 시나리오 픽스처 | ⚠️ 스켈레톤만 존재, 완성 필요 |
| 실제 실험 | ⬜ 미실행 |
| 시스템 구조 다이어그램 | ⬜ 개정 계획 존재 |
| 논문 작성 | ⬜ 아웃라인 존재, 실험 결과 대기 |

---

## 주요 파일 위치

```
mac_mini/code/main.py           — Mac mini 허브 앱 진입점
rpi/code/main.py                — RPi 실험 앱 진입점
docs/setup/05_integration_run.md — 통합 실행 절차
docs/setup/02_rpi_setup.md      — RPi 설치 가이드 (mDNS 주소 확인 추가)
requirements-mac.txt            — Mac mini Python 의존성
requirements-rpi.txt            — RPi Python 의존성 (fastapi 등 추가 필요)
```

## 실행 명령어 요약

```bash
# Mac mini
cd /path/to/safe_deferral_claude
source ~/smarthome_workspace/.venv-mac/bin/activate
python mac_mini/code/main.py

# RPi (Mac mini 기동 후)
cd /path/to/safe_deferral_claude
source ~/smarthome_workspace/.venv-rpi/bin/activate
python rpi/code/main.py
```
