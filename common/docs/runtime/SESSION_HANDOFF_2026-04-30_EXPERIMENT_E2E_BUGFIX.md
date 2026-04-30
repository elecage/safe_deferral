# SESSION_HANDOFF — Experiment E2E Bugfix Complete

**Date:** 2026-04-30
**Branch:** fix/publish-once-both-timestamps → main (PR to be merged)
**Tests:** all prior tests passing

---

## 이번 세션에서 수정한 버그 목록

### 1. C204 staleness — RPi 클럭 7일 오차 (근본 원인)

**증상:** 모든 context payload가 CLASS_2 (trigger=C204)로 라우팅됨.

**원인:** RPi 시스템 클럭이 Mac mini보다 7일 뒤처져 있었음.
Mac mini는 `ingest_timestamp_ms`를 자신의 클럭으로 override하므로,
RPi가 `trigger_event.timestamp_ms`에 기록한 값과의 차이가 항상 7일 ≈ 581,000,000 ms >> freshness_threshold(3,000 ms).

**수정:** RPi에서 `sudo chronyc makestep`으로 NTP 즉시 동기화.

---

### 2. publish_once() — trigger_event.timestamp_ms 미갱신 (PR #55)

**증상:** 클럭 동기화 후에도 C204 지속.

**원인:** `publish_once()`가 `routing_metadata.ingest_timestamp_ms`만 갱신하고
`pure_context_payload.trigger_event.timestamp_ms`는 template 생성 시점 값으로 고정됨.
Mac mini가 `ingest_ts`를 자신의 now로 override하므로 차이가 노드 생성 이후 경과 시간만큼 벌어짐.

**수정 파일:** `rpi/code/virtual_node_manager/manager.py` — `publish_once()`
- `routing_metadata.ingest_timestamp_ms` 와 `pure_context_payload.trigger_event.timestamp_ms` 를
  동시에 `now_ms = int(time.time() * 1000)`으로 갱신.
- 차이 = 0 ms → freshness check 항상 통과.

---

### 3. LLM fallback — deferral_reason: null 스키마 거부

**증상:** LLM이 `light_on` 응답을 반환해도 `is_fallback=True` → CLASS_2 C207.

**원인:** Ollama가 `deferral_reason: null`을 포함한 JSON 반환.
`candidate_action_schema.json`이 해당 필드를 `type: string`으로 정의하여
`None is not of type 'string'` 에러로 jsonschema 검증 실패.

**수정 파일:** `mac_mini/code/local_llm_adapter/adapter.py` — `_parse_and_validate()`
```python
candidate = {k: v for k, v in candidate.items() if v is not None}
```
null 값을 검증 전에 제거. optional 필드가 없는 것과 null인 것은 동일하게 처리.

---

### 4. LLM 비결정성 — temperature 미설정

**증상:** 동일한 context에서 CLASS_1 성공/C207 결과가 무작위로 교차.

**원인:** Ollama 기본 temperature (~0.8)로 인해 응답이 매 실행마다 달라짐.

**수정 파일:** `mac_mini/code/local_llm_adapter/llm_client.py` — `OllamaClient.complete()`
```python
"options": {"temperature": 0.2}
```
실험 재현성을 위해 low-variance 설정.

---

### 5. trial pass_ 항상 False — observation 중첩 구조 불일치

**증상:** ACK resolved, actuation 성공인데 트라이얼 Pass=✗.

**원인:** `complete_trial()`이 flat key로 읽음:
```python
observation.get("route_class")       # → None
observation.get("validation_status") # → None
```
실제 Mac mini telemetry observation 구조는 중첩:
```json
{"route": {"route_class": "CLASS_1"}, "validation": {"validation_status": "approved"}, "generated_at_ms": ...}
```

**수정 파일:** `rpi/code/experiment_package/trial_store.py` — `complete_trial()`
중첩 구조 우선 읽기 + flat key fallback 처리.

---

### 6. trial timeout — LLM 응답 지연

**증상:** 5회 중 1회 trial timeout.

**원인:** trial observation timeout 15초 < Ollama 응답 시간.

**수정 파일:**
- `rpi/code/experiment_package/runner.py` — `_TRIAL_TIMEOUT_S`: 15 → 30초
- `mac_mini/code/local_llm_adapter/llm_client.py` — `OllamaClient.timeout_s`: 30 → 60초

---

### 7. CLASS_0 실험 — emergency_event_node 사용 오류 (설정 문제, 코드 수정 없음)

**증상:** CLASS_0 실험 시 맥미니 무반응.

**원인:**
- `emergency_event_node`는 `safe_deferral/emergency/event` 토픽으로 발행.
- Mac mini는 이 토픽을 구독하지 않음. `safe_deferral/context/input`과 `safe_deferral/actuation/ack`만 구독.
- CLASS_0은 별도 토픽이 아니라 `context/input` payload에서 temperature >= 50°C 등 응급 조건을 Policy Router가 감지해서 라우팅.

**해결:** context_node payload_template에 `temperature: 52.0`, `event_code: "threshold_exceeded"`로 설정 후 발행 → `Route: CLASS_0 (trigger=E001)` 확인.

---

## 수정된 파일 요약

| 파일 | 수정 내용 |
|---|---|
| `rpi/code/virtual_node_manager/manager.py` | `publish_once()` — 양쪽 timestamp 동시 갱신 |
| `mac_mini/code/local_llm_adapter/adapter.py` | null 값 제거 후 스키마 검증 |
| `mac_mini/code/local_llm_adapter/llm_client.py` | temperature=0.2, timeout=60s |
| `rpi/code/experiment_package/trial_store.py` | 중첩 observation 구조 파싱 |
| `rpi/code/experiment_package/runner.py` | trial timeout 30초 |

---

## 확인된 동작

- CLASS_1: context_node 발행 → LLM `light_on` → Validator approved → Dispatched → ACK resolved → trial pass_=True ✅
- CLASS_0: context_node temperature=52 → Route: CLASS_0 (trigger=E001) ✅
- trial pass/fail 판정 정상 작동 ✅
- 5회 trial 중 4회 이상 pass (LLM temperature=0.2 기준) ✅

---

## 다음 세션 권장 작업

1. **CLASS_2 실험 검증** — fault profile별 (staleness, schema_invalid, trigger_mismatch 등) trial 실행 및 pass 확인
2. **RPi 시간 동기화 자동화** — chrony 설정 점검, 재부팅 후에도 동기화 유지 확인
3. **패키지 A 전체 실행** — CLASS_0/1/2 혼합 trial로 routing_accuracy, UAR, SDR 계산
4. **패키지 B 레이턴시 측정** — `latency_ms` (ingest_ts → snapshot_ts) p50/p95 수집
5. **디버그 로그 제거 확인** — 이번 세션에서 추가한 모든 DEBUG 로그 제거 완료

---

## 주의사항

- RPi 재시작 시 가상 노드 메모리에서 소멸 → 재생성 필요. payload_template도 다시 설정해야 함.
- CLASS_0 실험은 반드시 context_node (`safe_deferral/context/input`)로 발행. emergency_event_node 사용 금지.
- 가상 노드 `audit_correlation_id`는 매 실험마다 다른 값 사용 권장 (중복 시 ObservationStore 매칭 오류 가능).
