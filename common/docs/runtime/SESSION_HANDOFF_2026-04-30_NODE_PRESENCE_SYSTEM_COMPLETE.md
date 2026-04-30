# SESSION_HANDOFF — Node Presence System Complete

**Date:** 2026-04-30
**Branch merged:** feat/node-presence-system → main (PR #51, squash merge)
**Tests:** 79/79 passed

---

## 이번 세션에서 완료한 작업

### 배경

이전 세션들에서 실험 패키지 인프라(PR #1~#6)를 완성했다.
물리 ESP32 노드는 MQTT LWT + explicit connect 로 presence를 알리고,
가상 노드(VirtualNodeManager)는 내부 상태만 추적하는 **비대칭** 구조였다.

사용자 지적: "동일한 하트비트를 버추얼 노드에서도 보내야 되는 것 아냐?"
→ Option A 확정: VirtualNodeManager가 동일한 `safe_deferral/node/presence` 토픽에 발행

### 완성된 파일

#### 신규 생성
- **`rpi/code/node_presence/__init__.py`** — 모듈 init
- **`rpi/code/node_presence/registry.py`** — `NodePresenceRegistry`

#### 수정
- **`rpi/code/virtual_node_manager/manager.py`** — presence publish 추가
- **`rpi/code/preflight/readiness.py`** — NodePresenceRegistry 주입 + optional 체크 2개
- **`rpi/code/main.py`** — presence 토픽 구독, registry 인스턴스화, on_message 라우팅
- **`rpi/code/dashboard/app.py`** — `/node_presence`, `/node_presence/{id}` 엔드포인트
- **`rpi/code/dashboard/static/index.html`** — 노드 설정 섹션에 통합 현황 패널
- **`rpi/code/tests/test_rpi_components.py`** — preflight 테스트 기대값 수정
- **`common/mqtt/topic_registry.json`** — `safe_deferral/node/presence` 항목 (전 세션에서 추가)

---

## NodePresenceRegistry 동작 요약

```
safe_deferral/node/presence  (retain=true, qos=1)
    ↑                              ↑
ESP32 노드                   VirtualNodeManager
  connect → online            start_node() → online
  LWT     → offline           stop_node()  → offline
                              delete_node()→ offline

    ↓
NodePresenceRegistry
  .handle_message(payload)
  .is_online(node_id)
  .find_by_source("physical"|"virtual")
  .find_by_type("context_node"|...)
  .snapshot() → list[dict]
  .online_count(source=None)

스테일 임계값: 2분 (_STALE_THRESHOLD_MS = 120_000)
```

Presence payload 스키마:
```json
{
  "node_id": "rpi.virtual_context_node_abc123",
  "node_type": "context_node",
  "source": "virtual",          // "physical" | "virtual"
  "status": "online",           // "online" | "offline"
  "timestamp_ms": 1746000000000,
  "source_node_id": "rpi.virtual_context_node"
}
```

---

## PreflightManager 변경 사항

`PreflightManager(node_presence_registry=...)` 로 주입.

추가된 체크 (둘 다 `required=False` → BLOCKED 아닌 DEGRADED):

| check_id | 조건 | 결과 |
|---|---|---|
| `physical_nodes_present` | 물리 노드 온라인 없음 | DEGRADED — 가상 전용 모드, 결과에 명시 필요 |
| `stm32_present` | `/dev/ttyUSB*`, `/dev/ttyACM*` 없음 | DEGRADED — GPIO 레이턴시 불가, 소프트웨어 MQTT 레이턴시로 대체 |

STM32 정책 근거: `required_experiments.md §6.5` — "바람직하다" (optional).
소프트웨어 파이프라인 레이턴시(ingest_timestamp_ms → snapshot_ts_ms)는 논문 유효.
결과 레이블에 "software pipeline latency" 명시 필요.

---

## 실험 패키지 시스템 전체 현황

이번 세션으로 실험 패키지 인프라가 완성됐다.

### 완성된 컴포넌트 (PR #1~#6 + 이번)

| PR | 내용 | 상태 |
|---|---|---|
| #1 | experiment_package 백엔드 (definitions, fault_profiles, trial_store) | ✅ merged |
| #2 | PackageRunner + Dashboard API 엔드포인트 | ✅ merged |
| #3 | 프론트엔드 패키지 선택 UI (패키지 카드 그리드, 폴트 선택, 조건) | ✅ merged |
| #4 | 트라이얼 실행 UI + 실시간 테이블 | ✅ merged |
| #5/6 | 결과 분석 섹션 (패키지 A/B/C 뷰, 메트릭, 내보내기) | ✅ merged |
| #51 | 노드 프레즌스 시스템 (물리+가상 통합 추적) | ✅ merged |

### 핵심 데이터 흐름

```
PackageRunner
  └─ start_trial_async(run_id, package_id, node_id, scenario_id, ...)
       └─ correlation_id = "pkg-{package_id}-{uuid}"
            └─ VirtualNodeManager.publish_once(node)  [payload에 correlation_id 삽입]
                 └─ Mac mini 처리
                      └─ safe_deferral/dashboard/observation 발행 [echo correlation_id]
                           └─ ObservationStore.find_by_correlation_id()
                                └─ TrialStore.complete_trial()
                                     └─ pass_ / latency_ms 계산
```

### fault_profiles 요약 (9개)

| ID | 유형 | 기대 결과 |
|---|---|---|
| FAULT_EMERGENCY_01_TEMP | 온도 임계 초과 | CLASS_0 |
| FAULT_STALENESS_01 | 타임스탬프 스테일 | safe_deferral |
| FAULT_SCHEMA_INVALID_01 | 필수 필드 제거 | safe_deferral |
| FAULT_TRIGGER_MISMATCH_01 | 트리거 불일치 | CLASS_2 또는 safe_deferral |
| FAULT_CONFLICT_01 | 동시 충돌 요청 | CLASS_2 |
| FAULT_GHOST_PRESS_01 | 고스트 프레스 | safe_deferral |
| FAULT_ENV_SENSOR_FAULT_01 | 환경 센서 이상 | safe_deferral |
| FAULT_DOORBELL_MISSING_01 | 도어벨 컨텍스트 누락 | CLASS_2 또는 safe_deferral |
| FAULT_CONTRACT_DRIFT_01 | 미등록 토픽 거버넌스 테스트 | 거버넌스 관찰 전용 |

임계값은 `policy_table.json`에서 동적 로드 (RpiAssetLoader). 하드코딩 없음.

---

## 다음 세션 권장 작업

### 즉시 가능한 작업

1. **실험 실행 검증**
   - RPi + Mac mini 연결 상태에서 패키지 런 생성 → 트라이얼 실행 → 결과 확인 E2E 테스트
   - 특히 `audit_correlation_id` 매칭 흐름 검증 필요

2. **ESP32 LWT 설정**
   - ESP32 펌웨어에 MQTT Last Will Testament 설정:
     ```
     topic: safe_deferral/node/presence
     payload: {"node_id": "...", "source": "physical", "status": "offline", "timestamp_ms": 0}
     retain: true, qos: 1
     ```
   - connect 시 explicit online publish 추가

3. **NodePresenceRegistry 테스트 추가**
   - `test_rpi_components.py`에 registry handle_message, is_online, find_by_source 유닛테스트
   - VirtualNodeManager start/stop/delete presence publish 통합 테스트

4. **STM32 타이밍 노드 (선택)**
   - USB-serial (CP2102 → /dev/ttyUSB0) 연결
   - pyserial 기반 GPIO interrupt 타이밍 수집 스크립트 (rpi/code/stm32_timing/)
   - required_experiments.md §6.5 참조 — optional, 소프트웨어 레이턴시로 대체 가능

### 논문 준비

- 실험 결과가 쌓이면 `/package_runs/{id}/export/markdown` 로 논문 테이블 초안 추출 가능
- Package A: 라우팅 정확도/UAR/SDR (Table 3 대응)
- Package B: 클래스별 레이턴시 p50/p95 (Table 4 대응)
- Package C: 폴트 조건 하 SFR/UAR (Table 5 대응)

---

## 주의사항 (변경 없음)

- LLM 출력은 후보 가이던스. 정책·검증기·보호자 승인·액추에이터 권한 없음.
- 도어락은 자율 Class 1 실행 범위 밖.
- 대시보드/거버넌스 UI는 운영 토픽 직접 발행 불가.
- virtual node는 실험 소스/관찰자. 생산 장치 권한 없음.
- NodePresenceRegistry는 모니터링 아티팩트. 정책·검증기 권한 부여 없음.
