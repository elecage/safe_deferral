# SESSION_HANDOFF — 2026-04-28 Phase 1 완료 및 ESP32 BOM 추가

## 1. 이 addendum이 다루는 범위

이 세션에서 완료한 작업:

- **Phase 1-1**: `requirements-rpi.txt`, `requirements-mac.txt` 의존성 보완
- **Phase 1-2**: `integration/tests/data/` 픽스처 파일 스키마 준수 수정 및 신규 생성
- **Phase 1-3**: 시스템 구조 다이어그램 — 이미 완료 상태였음, WORK_PLAN 상태 표시만 정정
- **ESP32 BOM**: `esp32/docs/BOM.md` 신규 작성

Phase 1 전체가 완료되었으며, 다음 세션은 **Phase 2 (하드웨어 연결 및 기본 동작 확인)** 또는 **ESP32 노드 구현**에서 시작한다.

---

## 2. Phase 1-1: requirements 의존성 보완

### 변경 파일

**`requirements-rpi.txt`**
- 기존: `paho-mqtt`, `pytest`, `PyYAML`, `jsonschema` (버전 지정 없음)
- 추가: `fastapi>=0.115.0`, `uvicorn>=0.32.0`, `python-dotenv>=1.0.0`
- 수정: 기존 패키지에 버전 하한 추가

**`requirements-mac.txt`**
- 추가: `python-dotenv>=1.0.0`

**`rpi/scripts/install/30_install_python_deps_rpi.sh`**
- `fastapi`, `uvicorn`, `python-dotenv`를 선택 패키지(feature flag 기반)에서 **필수 패키지 검증 목록**으로 이동
- `ENABLE_RPI_DASHBOARD_BACKEND` 플래그 제거 (관련 패키지들이 이제 필수가 됨)

### 이유
`rpi/code/main.py`가 `fastapi`, `uvicorn`을 직접 import하며, 두 `main.py` 모두 `python-dotenv`를 optional try/except로 사용. 설치되지 않으면 `.env` 자동 로딩이 침묵하여 실패함.

---

## 3. Phase 1-2: 시나리오 픽스처 파일

### 발견된 문제 (수정 전)

기존 `integration/tests/data/sample_*.json` 파일들이 `policy_router_input_schema.json` 및 `context_schema.json`을 위반하고 있었음:

| 문제 | 해당 필드 |
|------|----------|
| required 필드 누락 | `routing_metadata.ingest_timestamp_ms` |
| required 필드 누락 | `trigger_event.timestamp_ms` |
| 잘못된 필드명 | `temperature_c` → `temperature`, `illuminance_lux` → `illuminance` |
| 스키마에 없는 event_code | `ambient_state_update`, `temperature_alert`, `smoke_detected`, `gas_detected`, `single_hit` |
| required device_states 누락 | `living_room_blind`, `tv_main` |
| additionalProperties 위반 | 최상위 `notes` 필드, `routing_metadata.fault_injection` 필드 |

### 수정 내용

**스키마 준수로 수정한 파일 (10개):**

| 파일 | 주요 수정 |
|------|----------|
| `sample_policy_router_input_class1.json` | `button/single_click`, 타임스탬프 추가, 필드명 정정, 누락 필드 보완 |
| `sample_policy_router_input_class0_e001.json` | `sensor/threshold_exceeded`, 온도 52.0°C, 전체 필드 완성 |
| `sample_policy_router_input_class0_e002_button_triple_hit.json` | 타임스탬프, 누락 필드 추가 |
| `sample_policy_router_input_class0_e003_smoke.json` | `state_changed`로 event_code 수정, 전체 필드 완성 |
| `sample_policy_router_input_class0_e004_gas.json` | `state_changed`로 event_code 수정, 전체 필드 완성 |
| `sample_policy_router_input_class0_e005_fall.json` | 타임스탬프, 누락 필드 추가 |
| `sample_policy_router_input_class2_insufficient_context.json` | `double_click` + 모든 장치 ON으로 재설계 (의도 모호, 스키마 완전 준수) |
| `sample_policy_router_input_fault_stale.json` | `trigger_event.timestamp_ms` = `ingest_timestamp_ms - 6000` (3000ms 임계값 초과) |
| `sample_policy_router_input_fault_conflict_multiple_candidates.json` | `single_hit`→`single_click`, `occupancy_detected: false` (ghost press 시나리오) |
| `sample_policy_router_input_fault_missing_device_state.json` | `tv_main` 의도적 누락, 스키마 위반 필드 제거 |

**신규 생성 파일 (1개):**
- `integration/scenarios/sc01_light_on_request.json` — `docs/setup/05_integration_run.md`가 참조하는 CLASS_1 헬스체크 픽스처

### 타임스탬프 규약

| 픽스처 종류 | `ingest_timestamp_ms` | `trigger_event.timestamp_ms` |
|------------|----------------------|------------------------------|
| 정상 (CLASS_0/1/2) | 1777104000000 | 1777103999900 (100ms 이전) |
| staleness fault | 1777104000000 | 1777103994000 (6000ms 이전, 임계값 3000ms 초과) |

실제 테스트 시 freshness 검증이 필요하면 타임스탬프를 현재 epoch ms로 교체해야 함.

### 변경하지 않은 파일 (의도적 스키마 위반)

- `sample_policy_router_input_fault_missing_doorbell_detected.json` — `doorbell_detected` 필드를 의도적으로 누락한 음성(negative) 테스트 픽스처. 변경하지 않음.

---

## 4. Phase 1-3: 시스템 구조 다이어그램

`common/docs/architecture/figures/system_layout.svg` (1800×1300px, 339줄)가 이미 완성 상태였음.

`figure_revision/10_render_validation.md` 및 `11_documentation_update.md` 모두 완료 확인. WORK_PLAN의 상태 표시("⚠️ 미완")만 "✅ 완료"로 정정함.

---

## 5. ESP32 BOM

`esp32/docs/BOM.md` 신규 작성.

8개 노드(PN-01 ~ PN-08) 각각에 대해:
- GPIO 매핑 표
- 추가 부품 표
- 특수 회로 (해당 노드만)

**특수 회로가 필요한 노드:**

| 노드 | 회로 | 이유 |
|------|------|------|
| PN-02 | NPN 드라이버 (조건부) | 릴레이 모듈이 3.3V 트리거 미지원 시 |
| PN-03 | DHT22 DATA 풀업 10kΩ | 필수, 생략 시 읽기 오류 다발 |
| PN-04 | PC817 옵토커플러 (조건부) | 기존 유선 도어벨 AC 배선 절연 |
| PN-05 | 전압 분배기 10kΩ+20kΩ | MQ-2 아날로그 5V→3.3V 변환 필수 |
| PN-07 | BC547 NPN 드라이버 | 부저 GPIO 직결 금지 (과전류) |
| PN-08 | IRF540N MOSFET (조건부) | 솔레노이드락 12V 구동 |

---

## 6. 현재 WORK_PLAN 상태

| 항목 | 상태 |
|------|------|
| Mac mini 라이브러리 코드 (MM-01~10) | ✅ 완료 |
| Mac mini 진입점 (`main.py`) | ✅ 완료 |
| RPi 라이브러리 코드 (RPI-01~10) | ✅ 완료 |
| RPi 진입점 (`main.py`) | ✅ 완료 |
| ESP32 노드 펌웨어 (PN-01~08) | ✅ 완료 (하드웨어 검증 대기) |
| STM32 타이밍 펌웨어 | ✅ 스켈레톤 완료 (하드웨어 검증 대기) |
| 설치 문서 (01~04) | ✅ 완료 |
| 통합 실행 문서 (05) | ✅ 완료 |
| requirements 의존성 보완 (1-1) | ✅ 완료 |
| 시나리오 픽스처 파일 (1-2) | ✅ 완료 |
| 시스템 구조 다이어그램 (1-3) | ✅ 완료 |
| ESP32 노드 BOM | ✅ 완료 |
| 하드웨어 기동 확인 (Phase 2) | ⬜ 미시작 |
| 실험 실행 A/B/C (Phase 3) | ⬜ 미시작 |
| 논문 작성 (Phase 4) | ⬜ 미시작 |

---

## 7. 다음 세션 진입점

### 선택지 A: Phase 2 — 하드웨어 연결 (Mac mini + RPi SSH)

하드웨어가 준비되어 있고 같은 네트워크에 있으면 SSH로 진행 가능.

```bash
# 1. Mac mini 접속
ssh <user>@mac-mini.local

# 2. Docker 기동
cd ~/smarthome_workspace
docker compose up -d

# 3. 서비스 검증
bash mac_mini/scripts/verify/80_verify_services.sh

# 4. Mac mini 앱 실행
python mac_mini/code/main.py

# 5. 헬스체크 페이로드 발행 (이 컴퓨터 또는 Mac mini에서)
mosquitto_pub -h <mac-mini-ip> -p 1883 \
  -t safe_deferral/context/input \
  -f integration/scenarios/sc01_light_on_request.json
```

예상 로그:
```
[INFO] sd.main — Route: CLASS_1
[INFO] sd.main — Validation: approved
[INFO] sd.main — Dispatched command_id=<uuid>
```

### 선택지 B: ESP32 노드 구현

`esp32/docs/BOM.md` 기준으로 부품 조달 후 각 노드 펌웨어 플래싱 및 프로비저닝.

```bash
# 빌드 및 플래싱 (예: PN-01)
cd esp32/code/pn01_button_input
idf.py build flash monitor
```

프로비저닝 후 토픽 수신 확인:
```bash
mosquitto_sub -h <mac-mini-ip> -p 1883 -t "safe_deferral/#" -v
```

---

## 8. 주의사항

- `integration/tests/data/sample_policy_router_input_fault_missing_doorbell_detected.json`은 의도적 음성 테스트 픽스처로 스키마 위반 상태 유지. Phase 2-3 정상 동작 테스트에 사용하지 말 것.
- 픽스처 타임스탬프가 정적 값이므로, freshness 검증(3000ms 임계값)이 활성화된 환경에서는 `ingest_timestamp_ms`와 `trigger_event.timestamp_ms`를 현재 epoch ms로 교체 후 발행할 것.
- PN-05 MQ-2 센서는 통전 후 약 30초 예열 필요. 예열 전 ADC 값 무시.
