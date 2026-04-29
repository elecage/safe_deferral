# SESSION_HANDOFF — 2026-04-29 코드 리뷰 수정 완료

## 1. 이 문서의 목적

2026-04-29 전체 코드 리뷰에서 도출된 FIX-A~G 7개 항목이 단일 커밋
(`03207eb`, 브랜치 `claude/eager-cannon-9a532e`)으로 완료되었음을 기록한다.
수정 계획 원문:
`common/docs/runtime/SESSION_HANDOFF_2026-04-29_CODE_REVIEW_FIX_PLAN.md`

---

## 2. 완료된 수정 요약

### FIX-A — ACK FAILURE 미에스컬레이션 (High)

**변경 파일:** `mac_mini/code/main.py`

`Pipeline.handle_ack()`에 AckStatus.FAILURE 분기를 추가했다. ACK timeout 경로와
동일하게 `_escalate_c205(record.audit_correlation_id)`를 호출한다. 기존에는
명시적 FAILURE 응답이 텔레메트리 기록 후 조용히 흡수되고 있었다.

**신규 테스트:** `mac_mini/code/tests/test_pipeline_ack_escalation.py` (6개 케이스)
- explicit failure → C205 호출
- observed_state 불일치 → FAILURE → C205
- target_device 불일치 → FAILURE → C205
- success 시 C205 미호출
- 미등록 command_id 수신 시 C205 미호출
- audit_correlation_id가 C205 에스컬레이션에 올바르게 전달됨

---

### FIX-B — PolicyRouter._compare() TypeError 방어 (High)

**변경 파일:** `mac_mini/code/policy_router/router.py`

`_compare()`의 dict 리터럴 평가 전체를 `try/except TypeError`로 감쌌다.
`actual is None`이면 즉시 False를 반환한다. 기존에는 문자열 센서 값 등 타입
불일치 시 예외가 `handle_context()` 전체로 번졌다.

**신규 테스트:** `test_policy_router.py` — `TestCompareTypeDefence` 클래스 (4개 케이스)

---

### FIX-C — Telegram 재시도 블로킹 제거 (Medium)

**변경 파일:** `mac_mini/code/caregiver_escalation/telegram_client.py`

`HttpTelegramSender.send_message()`를 fire-and-forget daemon 스레드로 전환했다.
HTTP 재시도 로직은 `_send_with_retry()` 인스턴스 메서드로 분리되어 백그라운드에서
실행된다. 실패 시 `log.warning`으로 기록하며 파이프라인 워커 스레드는 즉시 반환된다.

`TelegramSendError`는 유지된다(test mock용 `_FailingTelegramSender`가 동기 raise로
사용). `HttpTelegramSender`는 절대 raise하지 않는다.

**신규 테스트:** `test_caregiver_escalation.py` — `TestHttpTelegramSenderAsync` 클래스 (3개 케이스)
- `send_message()`가 즉시 None 반환
- 런칭된 스레드가 daemon=True
- `CaregiverEscalationBackend`가 PENDING 상태를 반환

---

### FIX-D — MQTT 토픽 하드코딩 제거 (Medium)

**변경 파일:**
- `mac_mini/code/shared/asset_loader.py` — `load_topic_registry()`, `get_topic()` 추가
- `mac_mini/code/main.py` — 모듈 상수 `TOPIC_CONTEXT_INPUT`, `TOPIC_ACK` 제거
- `mac_mini/code/low_risk_dispatcher/dispatcher.py` — `COMMAND_TOPIC` 클래스 상수 제거
- `mac_mini/code/caregiver_escalation/backend.py` — `ESCALATION_TOPIC`, `CONFIRMATION_TOPIC` 모듈 상수 제거
- `mac_mini/code/telemetry_adapter/adapter.py` — `OBSERVATION_TOPIC` 모듈 상수 제거

각 컴포넌트가 `init` 시 `loader.get_topic(topic_string)`을 호출해 registry 검증을
거친다. 미등록 토픽이면 `KeyError`로 즉시 시작 중단된다.

`Pipeline`은 `topic_context_input`, `topic_ack`를 공개 인스턴스 속성으로 보유한다.
`main()` 내 `on_connect`, `worker` 클로저가 이 속성을 참조한다.

---

### FIX-E — AssetLoader 단일 인스턴스 공유 (Low)

**변경 파일:** `mac_mini/code/main.py`

`Pipeline.__init__()`에서 단일 `AssetLoader` 인스턴스(`_loader`)를 생성한 뒤
`LowRiskDispatcher`, `CaregiverEscalationBackend`, `TelemetryAdapter`에
`asset_loader=_loader`로 주입한다. 시작 시 schema 파일 I/O 중복이 감소한다.

---

### FIX-F — _handle_deferral() 단순화 (Low)

**변경 파일:** `mac_mini/code/main.py`

`_handle_deferral()`에서 `SafeDeferralHandler.start_clarification()` +
`handle_timeout()` 호출을 제거하고 `_handle_class2("C207", route_result)`를
직접 호출한다. 인터랙티브 UI 없이 항상 즉시 timeout 처리했던 불필요한
중간 세션을 없앴다. `SafeDeferralHandler`는 향후 UI 통합 시 재활성화 예정이다.

---

### FIX-G — NoOpTelegramSender 공개 이름 변경 (Low)

**변경 파일:**
- `mac_mini/code/caregiver_escalation/telegram_client.py`
- `mac_mini/code/caregiver_escalation/backend.py`
- `mac_mini/code/main.py`
- `mac_mini/code/tests/test_caregiver_escalation.py`

`_NoOpTelegramSender` → `NoOpTelegramSender`. import 경로와 테스트 내 주석 모두 갱신.

---

## 3. 테스트 결과

```
377 passed in 0.67s
```

FIX-A~G 수정 완료 후 기존 테스트 전체 + 신규 테스트 모두 통과.

---

## 4. 변경 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `mac_mini/code/main.py` | FIX-A, D, E, F, G |
| `mac_mini/code/policy_router/router.py` | FIX-B |
| `mac_mini/code/caregiver_escalation/telegram_client.py` | FIX-C, G |
| `mac_mini/code/caregiver_escalation/backend.py` | FIX-D, G |
| `mac_mini/code/low_risk_dispatcher/dispatcher.py` | FIX-D |
| `mac_mini/code/telemetry_adapter/adapter.py` | FIX-D |
| `mac_mini/code/shared/asset_loader.py` | FIX-D |
| `mac_mini/code/tests/test_pipeline_ack_escalation.py` | FIX-A (신규) |
| `mac_mini/code/tests/test_policy_router.py` | FIX-B |
| `mac_mini/code/tests/test_caregiver_escalation.py` | FIX-C, G |

---

## 5. 다음 세션 권고 사항

- PR 생성 및 main 브랜치 머지 (`claude/eager-cannon-9a532e`)
- `SafeDeferralHandler`의 향후 인터랙티브 UI 통합 설계 시
  `_handle_deferral()`에서 재활성화 필요 (현재 FIX-F로 우회 중)
- FIX-D로 `AssetLoader.get_topic()` 검증이 추가되었으므로,
  `topic_registry.json` 토픽 변경 시 반드시 코드 참조 문자열과 동기화 필요
