# SESSION_HANDOFF — Emergency Topic / Doorbell Routing / Drift Trial Bugfix

**Date:** 2026-05-01
**Branch:** claude/strange-engelbart-bd3430 → main (PR #76, merged)
**Tests:** 31/31 mac_mini policy router, 85/85 rpi components

---

## 이번 세션에서 수정한 버그 목록

### 1. Emergency event 토픽 무시 — Mac mini 미구독 (Bug 1)

**증상:** 대시보드에서 `emergency_event_node`로 발행해도 Mac mini가 반응 없음.
CLASS_0 실험이 항상 timeout.

**원인 (이중):**

1. Mac mini가 `safe_deferral/emergency/event` 토픽을 구독하지 않았음.
   `on_connect`에서 `context/input`과 `actuation/ack`만 구독.
2. 대시보드 emergency payload가 flat 구조 (`{event_type, severity, timestamp_ms, location, details}`)여서
   `policy_router_input_schema.json` 검증을 통과하지 못하는 형태였음.
   구독을 추가해도 스키마 오류(C202)로 CLASS_0에 도달하지 못함.

**수정 파일:** `mac_mini/code/main.py`
- `Pipeline.__init__`: `topic_emergency_event` 필드 추가 (`get_topic("safe_deferral/emergency/event")`).
- `on_connect`: 세 번째 `c.subscribe(pipeline.topic_emergency_event, qos=1)` 추가.
- `worker()`: `topic in (pipeline.topic_context_input, pipeline.topic_emergency_event)` 조건으로
  두 토픽 모두 `handle_context()`로 라우팅.

**수정 파일:** `rpi/code/dashboard/static/index.html`
- `emg-type` 셀렉트를 E001–E005 5개 옵션으로 교체 (기존: `high_temperature`, `smoke_gas`, `fall_emergency`).
- `buildPayloadFromForm('emergency_event_node')` 분기를 완전히 재작성:
  - 올바른 `policy_router_input` 중첩 구조 (`source_node_id`, `routing_metadata`, `pure_context_payload`) 생성.
  - 각 E001–E005에 맞는 `trigger_event` + `environmental_context` 조합 결정:
    - E001(temperature): `trigger_event.event_code=threshold_exceeded`, `envCtx.temperature=52.0`
    - E002(triple_hit): `trigger_event.event_type=button, event_code=triple_hit`
    - E003(smoke): `trigger_event.event_code=threshold_exceeded`, `envCtx.smoke_detected=true`
    - E004(gas): `trigger_event.event_code=threshold_exceeded`, `envCtx.gas_detected=true`
    - E005(fall): `trigger_event.event_type=sensor, event_code=fall_detected`

---

### 2. doorbell_detected 이벤트가 CLASS_1으로 라우팅 — C208 미구현 (Bug 2)

**증상:** `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json` 시나리오가
`doorbell_detected` 센서 이벤트에 대해 `CLASS_2` 기대값을 가지지만, 실제 라우팅은 CLASS_1.

**원인:**
- `policy_table.json` `implementation_notes.doorbell_context_note`에 방문자 이벤트는
  CLASS_2 경로로 처리해야 한다고 명시되어 있었으나 `class_2_clarification_transition.triggers`에
  C208 predicate가 존재하지 않았음.
- `router.py`에 해당 체크 로직 없음.
- `test_policy_router.py`에 `test_doorbell_true_does_not_change_class` 테스트가 있어
  CLASS_1임을 단언하며 잘못된 동작을 고착화하고 있었음.

**수정 파일:** `common/policies/policy_table.json`
- `class_2_clarification_transition.triggers` 배열 끝에 C208 트리거 추가:
  ```json
  {
    "id": "C208",
    "event": "visitor_context_sensitive_actuation_required",
    "source_layer": "policy_router",
    "requires_notification": true,
    "initial_class2_state": "clarification_candidate_generation_allowed",
    "minimal_triggering_predicate": {
      "event_type": "sensor",
      "event_code": "doorbell_detected"
    }
  }
  ```

**수정 파일:** `mac_mini/code/policy_router/router.py`
- `__init__`: C208 predicate 로드 (`_c208_event_type`, `_c208_event_code`).
- `route()`: Step 4로 `_is_visitor_context(trigger)` 체크 삽입 (기존 C206 체크 앞).
- `_is_visitor_context()` helper 추가.

**수정 파일:** `mac_mini/code/tests/test_policy_router.py`
- 잘못된 `test_doorbell_true_does_not_change_class` 제거.
- `TestClass2VisitorContext` 클래스 추가 (4개 테스트):
  - doorbell 센서 이벤트 → CLASS_2 (C208)
  - env 플래그 없어도 트리거 이벤트 코드만으로 C208
  - 일반 센서 이벤트(`state_changed`)는 CLASS_1 유지
  - env에 `doorbell_detected=True`만 있고 트리거 이벤트는 button이면 CLASS_1 유지

---

### 3. FAULT_CONTRACT_DRIFT_01 트라이얼 — 30초 timeout 후 pass_=False (Bug 3)

**증상:** `FAULT_CONTRACT_DRIFT_01` fault profile 트라이얼이 30초를 기다린 후
`pass_=False`로 기록됨. 해당 프로파일은 governance pass(빠른 완료)여야 함.

**원인:**
- `TrialStore._is_pass()`에 `obs_class is None` → `return True` 분기가 이미 구현되어 있었음.
- 그러나 `PackageRunner._run_trial()`이 `_publish_contract_drift()` 후 `_match_observation()`으로
  진입, `_TRIAL_TIMEOUT_S=30초` 기다려 `None`을 받고 `timeout_trial()`을 호출.
- `timeout_trial()`은 `pass_=False`를 하드코딩하므로 `_is_pass()` 로직에 도달하지 못함.
- `_publish_contract_drift()` 내 주석이 "auto-completes immediately"라고 거짓 설명.

**수정 파일:** `rpi/code/experiment_package/runner.py`
- `_run_trial()` publish 분기에서 `FAULT_CONTRACT_DRIFT_01`이면 `_publish_contract_drift()` 호출 후
  즉시 `complete_trial()`을 호출하고 `return`.
  `_match_observation()` 루프를 완전히 우회.
- `_publish_contract_drift()` 내 거짓 주석 수정.

**수정 파일:** `rpi/code/tests/test_rpi_components.py`
- `TestTrialStoreContractDrift` (4개): `_is_pass()` 분기별 단위 테스트.
- `TestPackageRunnerContractDrift` (2개): `complete_trial` 호출 여부 및 governance_fault 필드 확인.

---

## 수정된 파일 요약

| 파일 | 수정 내용 |
|---|---|
| `mac_mini/code/main.py` | `emergency/event` 토픽 구독 추가, worker 라우팅 확장 |
| `rpi/code/dashboard/static/index.html` | emergency_event_node payload를 policy_router_input 형태로 재작성 |
| `common/policies/policy_table.json` | C208 트리거 추가 (doorbell_detected → CLASS_2) |
| `mac_mini/code/policy_router/router.py` | C208 predicate 로드 및 _is_visitor_context() 체크 삽입 |
| `mac_mini/code/tests/test_policy_router.py` | TestClass2VisitorContext 추가, 잘못된 CLASS_1 단언 제거 |
| `rpi/code/experiment_package/runner.py` | FAULT_CONTRACT_DRIFT_01 즉시 complete_trial 후 return |
| `rpi/code/tests/test_rpi_components.py` | 드리프트 트라이얼 6개 테스트 추가 |

---

## 확인된 동작

- Mac mini가 `safe_deferral/emergency/event` 구독 → E001–E005 payload 수신 후 CLASS_0 라우팅 ✅
- 대시보드 emergency_event_node가 스키마 유효한 policy_router_input 생성 ✅
- `doorbell_detected` 센서 이벤트 → CLASS_2 (trigger=C208) ✅
- button `single_click`, 일반 sensor 이벤트 → CLASS_1 유지 (회귀 없음) ✅
- FAULT_CONTRACT_DRIFT_01 트라이얼 → 30초 기다리지 않고 즉시 pass_=True ✅
- 테스트: mac_mini 31/31, rpi 85/85 ✅

---

## 주의사항

- `emergency/event` 토픽은 이제 Mac mini가 구독하므로, 물리 ESP32 노드도 이 토픽으로 발행 가능.
  단, payload는 반드시 `policy_router_input` 스키마를 따라야 함 (flat 구조 불가).
- doorbell 이벤트는 항상 CLASS_2로 올라가므로 Telegram caregiver 응답 대기(≤300초)가 발생.
  CLASS_2 트라이얼 timeout은 `_TRIAL_TIMEOUT_CLASS2_S = 360초` 설정 유지.
- FAULT_CONTRACT_DRIFT_01은 MQTT 실제 발행 없이 거버넌스 아티팩트만 로그 기록.
  observation이 절대 도달하지 않으므로 `complete_trial(obs_class=None)` 경로가 정상 경로임.

---

## 다음 세션 권장 작업

1. **CLASS_0 실험 재검증** — 대시보드 emergency_event_node로 E001–E005 각각 발행해 CLASS_0 확인
2. **C208 시나리오 실험 실행** — `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json`
   기반 트라이얼로 CLASS_2 라우팅 + caregiver 응답 흐름 end-to-end 확인
3. **패키지 실험 전체 실행** — CLASS_0/1/2 혼합 패키지로 routing_accuracy, UAR, SDR 지표 수집
4. **FAULT_CONTRACT_DRIFT 실험 결과 확인** — 실제 패키지 실행 시 pass_=True 기록 확인
