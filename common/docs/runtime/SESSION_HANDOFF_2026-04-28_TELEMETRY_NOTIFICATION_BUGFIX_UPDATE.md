# SESSION_HANDOFF — 2026-04-28 Telemetry / Notification 버그픽스 (PR #22~#26)

## 1. 이 addendum이 다루는 범위

이전 addendum(`SESSION_HANDOFF_2026-04-28_CODE_REVIEW_BUGFIX_UPDATE.md`)에 이어
이 세션에서 수행한 5건의 추가 버그픽스를 기록한다.
모든 수정은 PR로 제출되어 main에 머지되었다.

---

## 2. Fix 5 — CLASS_0 emergency notification 스키마 검증 실패 (PR #22)

### 문제

`_build_notification()`에 두 가지 스키마 위반이 있어 CLASS_0 긴급 알림 전체가
`ValidationError`로 실패하고 보호자에게 전달되지 않았다.

1. `source_layer="mac_mini_pipeline"` — 스키마 enum에 없음
2. `exception_trigger_id="E001"` 등 E-series — 스키마 enum은 C201~C207만 허용
3. `_escalate_c205()`, `_handle_class2()`의 `context_summary=""`
   — 스키마 `minLength: 1` 위반

### 수정

| 문제 | 수정 |
|------|------|
| `source_layer` | `"mac_mini_pipeline"` → `"system"` |
| `exception_trigger_id` | `Optional` 파라미터로 변경, CLASS_0에서는 필드 생략 |
| `context_summary=""` | `"컨텍스트 정보 없음"`, `"액추에이션 ACK 미수신"` 으로 대체 |

테스트: `TestBuildNotificationSchemaCompliance` (6케이스) 신규 추가 — 48/48 통과.

---

## 3. Fix 6 — Telemetry snapshot에 이전 이벤트 상태 누적 (PR #23)

### 문제

`TelemetryAdapter`는 상태를 누적하는데, `handle_context()` 진입 시 reset하지 않아
직전 CLASS_1 이벤트의 validation/ack 값이 다음 CLASS_0 snapshot에 섞였다.

### 수정

`handle_context()` 첫 줄에 `self._telemetry.reset()` 추가.
`reset()` 메서드는 이미 존재했으며 미호출 상태였다.

테스트: `TestReset`에 class2/escalation 케이스 추가,
`TestCrossEventIsolation` 클래스 신규 추가 (CLASS_1→CLASS_0, CLASS_0→CLASS_1 교차 오염 시나리오).

---

## 4. Fix 7 — ACK timeout 후 Class 2/escalation telemetry 미발행 (PR #24)

### 문제

`_escalate_c205()`가 class2/escalation telemetry를 갱신한 뒤 `publish()`를 호출하지
않아 dashboard에 C205 상태가 다음 이벤트 전까지 반영되지 않았다.

### 수정

`_escalate_c205()` 마지막에 `self._telemetry.publish()` 추가.

테스트: `test_c205_path_publishes_class2_and_escalation` 추가.

---

## 5. Fix 8 — 늦게 도착한 ACK가 다른 이벤트 route와 섞임 (PR #25)

### 문제

`handle_ack()`와 `_sweep_ack_timeouts()`가 공유 `TelemetryAdapter`의
`update_ack() + publish()`를 사용했다. handle_context()가 reset 후 다른 이벤트를
처리한 상태에서 이전 dispatch의 ACK가 도착하면 snapshot에 route=CLASS_0이면서
ack=이전 CLASS_1 light command 성공이 섞였다.

### 수정

`TelemetryAdapter`에 두 개의 독립 publish 메서드 추가:

- `publish_ack_only(record)` — 공유 상태 미사용, route/validation=None 격리 snapshot
- `publish_c205_snapshot(class2_result, esc_result)` — class2/escalation만 포함

| 경로 | 이전 | 이후 |
|------|------|------|
| `handle_ack()` | `update_ack() + publish()` | `publish_ack_only(record)` |
| `_sweep_ack_timeouts()` | 동일 | `publish_ack_only(record)` |
| `_escalate_c205()` | `update_class2() + update_escalation() + publish()` | `publish_c205_snapshot(class2_result, esc_result)` |

테스트 4케이스 추가 (isolation, 공유 상태 불변, topic 확인 등).

### snapshot 발행 매트릭스 (수정 후)

| 트리거 | route | validation | ack | class2 | escalation |
|--------|-------|-----------|-----|--------|-----------|
| `handle_context()` CLASS_0 | ✅ | — | — | — | ✅ |
| `handle_context()` CLASS_1 | ✅ | ✅ | — | — | — |
| `handle_context()` CLASS_2 | ✅ | ✅ | — | ✅ | ✅ |
| `handle_ack()` | — | — | ✅ | — | — |
| sweep timeout | — | — | ✅ | — | — |
| `_escalate_c205()` | — | — | — | ✅ | ✅ |

---

## 6. Fix 9 — CLASS_0 escalation telemetry 미반영 (PR #26)

### 문제

`_handle_emergency()`가 `send_notification()`의 반환값인 `EscalationResult`를
`self._telemetry.update_escalation()`에 반영하지 않았다.
dashboard observation에서 CLASS_0 이벤트는 `route=CLASS_0`, `escalation=null`로 표시됐다.

### 수정

```python
# _handle_emergency()
esc_result = self._caregiver.send_notification(notification)
self._telemetry.update_escalation(esc_result)
```

테스트: `test_class0_escalation_visible_in_same_event_snapshot` 추가.

---

## 7. 변경 파일 요약

| 파일 | 변경 내용 |
|------|----------|
| `mac_mini/code/main.py` | Fix 5: `_build_notification()` source_layer/exception_trigger_id/context_summary |
| `mac_mini/code/main.py` | Fix 6: `handle_context()` 상단 `reset()` 추가 |
| `mac_mini/code/main.py` | Fix 7: `_escalate_c205()` 끝 `publish()` 추가 |
| `mac_mini/code/main.py` | Fix 8: ACK/C205 경로에 격리 snapshot 메서드 사용 |
| `mac_mini/code/main.py` | Fix 9: `_handle_emergency()`에 `update_escalation()` 추가 |
| `mac_mini/code/telemetry_adapter/adapter.py` | Fix 8: `publish_ack_only()`, `publish_c205_snapshot()` 추가 |
| `mac_mini/code/tests/test_caregiver_escalation.py` | Fix 5: `TestBuildNotificationSchemaCompliance` 추가 (6케이스) |
| `mac_mini/code/tests/test_telemetry_adapter.py` | Fix 6~9: 테스트 다수 추가 |

---

## 8. 머지된 PR 목록 (이 세션)

| PR | 제목 | 상태 |
|----|------|------|
| #22 | fix: CLASS_0 emergency notification schema validation failures | ✅ merged |
| #23 | fix: reset telemetry at the start of each handle_context() call | ✅ merged |
| #24 | fix: publish telemetry after C205 class2/escalation update | ✅ merged |
| #25 | fix: isolate ACK/C205 telemetry snapshots from context event state | ✅ merged |
| #26 | fix: reflect CLASS_0 caregiver escalation in telemetry snapshot | ✅ merged |

누적 버그픽스 PR: #17~#26 (총 10건).

---

## 9. 현재 테스트 현황

| 테스트 파일 | 케이스 수 |
|------------|---------|
| `test_caregiver_escalation.py` | 48 |
| `test_telemetry_adapter.py` | 43 |
| 기타 (audit, intake, router, validator, dispatcher 등) | 각 파일 기존 케이스 유지 |

---

## 10. 현재 WORK_PLAN 상태

| 항목 | 상태 |
|------|------|
| Mac mini 라이브러리 코드 (MM-01~10) | ✅ 완료 + 버그픽스 10건 반영 |
| Mac mini 진입점 (`main.py`) | ✅ 완료 + 버그픽스 10건 반영 |
| RPi 라이브러리 코드 (RPI-01~10) | ✅ 완료 |
| RPi 진입점 (`main.py`) | ✅ 완료 |
| ESP32 노드 펌웨어 (PN-01~08) | ✅ 완료 (하드웨어 검증 대기) |
| STM32 타이밍 펌웨어 | ✅ 스켈레톤 완료 (하드웨어 검증 대기) |
| 설치 문서 (01~04) | ✅ 완료 |
| 통합 실행 문서 (05) | ✅ 완료 |
| Phase 1 전체 (1-1 ~ 1-3) | ✅ 완료 |
| 하드웨어 기동 확인 (Phase 2) | ⬜ 미시작 |
| 실험 실행 A/B/C (Phase 3) | ⬜ 미시작 |
| 논문 작성 (Phase 4) | ⬜ 미시작 |

---

## 11. 다음 세션 진입점

코드 측 미결 사항 없음. 추가 코드 리뷰가 있으면 이 addendum 이후에 이어서 수정.

Phase 2 진행을 원할 경우:
`SESSION_HANDOFF_2026-04-28_PHASE1_FIXTURE_BOM_UPDATE.md` §7 선택지 A 참조.
