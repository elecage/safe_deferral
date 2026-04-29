# SESSION_HANDOFF — 2026-04-29 코드 리뷰 수정 계획

## 1. 이 문서의 목적

2026-04-29 전체 코드 리뷰(코드 리뷰 대화 세션)에서 도출된 버그 및 설계 이슈의
수정 계획을 기록한다. 우선순위 High → Medium → Low 순서로 수정한다.

---

## 2. 수정 항목 목록

### FIX-A (High): ACK FAILURE 미에스컬레이션

**파일:** `mac_mini/code/main.py` — `handle_ack()` 메서드

**문제:**
`AckHandler.handle_ack()`가 `AckStatus.FAILURE`를 반환해도 파이프라인이 아무런
에스컬레이션 조치를 취하지 않는다. ACK timeout은 C205로 에스컬레이션되는데,
명시적 FAILURE 응답은 그냥 흡수된다.

**수정 내용:**
- `handle_ack()` 반환값(`ack_result`)을 검사
- `ack_result.ack_status == AckStatus.FAILURE`이면 `_escalate_c205()`를 호출

**테스트:**
- `test_low_risk_dispatcher.py` 또는 신규 `test_pipeline_ack.py`에
  ACK FAILURE → C205 에스컬레이션 경로 케이스 추가

---

### FIX-B (High): `PolicyRouter._compare()` TypeError 방어

**파일:** `mac_mini/code/policy_router/router.py` — `_compare()` 메서드

**문제:**
```python
ops = {">=": actual >= value, ">": actual > value, ...}
```
모든 연산자를 dict 생성 시점에 eager 평가한다. `actual`과 `value`의 타입이
맞지 않으면(예: 문자열 vs 숫자) `TypeError`가 발생하며, 이 예외는 `_match_emergency()`
호출 경로에서 잡히지 않아 `handle_context()` 전체 예외로 번진다.

**수정 내용:**
```python
@staticmethod
def _compare(actual, operator: str, value) -> bool:
    if actual is None:
        return False
    try:
        ops = {">=": actual >= value, ">": actual > value,
               "<=": actual <= value, "<": actual < value, "==": actual == value}
        return ops.get(operator, False)
    except TypeError:
        return False
```

**테스트:**
- `test_policy_router.py`에 타입 불일치 케이스 추가 (예: string vs int threshold)

---

### FIX-C (Medium): Telegram 재시도 중 파이프라인 블로킹

**파일:** `mac_mini/code/caregiver_escalation/telegram_client.py`
         `mac_mini/code/caregiver_escalation/backend.py`

**문제:**
`HttpTelegramSender.send_message()`가 재시도 간 `time.sleep(1)`을 실행한다.
이 메서드는 pipeline-worker 스레드에서 직접 호출되므로 재시도 횟수만큼 다음
이벤트 처리가 지연된다.

**수정 내용:**
`CaregiverEscalationBackend.send_notification()`에서 Telegram 전송을
daemon 스레드로 분리. 반환값(`EscalationResult`)은 즉시 PENDING 상태로 구성하고,
전송 완료/실패는 비동기적으로 기록.

**주의:** 전송 결과를 telemetry에 반영하는 경로를 보존해야 함.

**테스트:**
- `test_caregiver_escalation.py`에 slow-sender 시뮬레이션 케이스 추가

---

### FIX-D (Medium): MQTT 토픽 문자열 하드코딩 제거

**파일:**
- `mac_mini/code/main.py` (2개)
- `mac_mini/code/telemetry_adapter/adapter.py` (1개)
- `mac_mini/code/caregiver_escalation/backend.py` (2개)
- `mac_mini/code/low_risk_dispatcher/dispatcher.py` (1개)

**문제:**
6개 토픽 문자열이 코드에 하드코딩되어 있어 `common/mqtt/topic_registry.json`과
분리 관리된다. 토픽이 registry에서 변경되면 코드 4개 파일을 따로 수정해야 한다.

**수정 내용:**
- `AssetLoader`에 `load_topic_registry()` 메서드 추가
- 각 컴포넌트가 init 시 topic ID를 registry에서 조회
- 조회 실패 시 명확한 에러 메시지로 시작 중단

**테스트:**
- `test_context_intake.py` 등 기존 테스트에 영향 없는지 확인
- topic_registry에 없는 ID 요청 시 에러 케이스 추가

---

### FIX-E (Low): `AssetLoader` 중복 인스턴스화 및 스키마 중복 로드

**파일:** `mac_mini/code/main.py` — `Pipeline.__init__()`

**문제:**
8개 컴포넌트가 각자 `AssetLoader()`를 생성해 `make_schema_resolver()`를
호출한다. `make_schema_resolver()`는 `common/schemas/*.json` 전체를 파일에서
읽어 dict에 적재하므로 시작 시 8회 중복 파일 I/O가 발생한다.

**수정 내용:**
`Pipeline.__init__()`에서 단일 `AssetLoader` 인스턴스를 생성한 뒤,
모든 컴포넌트 생성자에 `asset_loader=` 인자로 주입.

**테스트:**
- 기존 테스트에서 각 컴포넌트가 여전히 독립 AssetLoader를 사용하고 있으므로
  그대로 유지. Pipeline 레벨 smoke test만 추가하면 충분.

---

### FIX-F (Low): `_handle_deferral()` 불필요한 session 생성 제거

**파일:** `mac_mini/code/main.py` — `_handle_deferral()` 메서드

**문제:**
```python
session = self._deferral.start_clarification(...)
deferral_result = self._deferral.handle_timeout(session)  # 즉시 timeout
```
인터랙티브 UI 없이 항상 즉시 timeout 처리하므로 `start_clarification` 세션
생성이 불필요하다. 이 경로의 clarification_record가 항상
`timeout_or_no_response` 상태로 audit에 기록되는 것도 오독 가능.

**수정 내용:**
`_handle_deferral()`을 `_handle_class2("C207", route_result)` 직접 호출로
단순화. `SafeDeferralHandler`는 향후 인터랙티브 UI 통합 시 재활성화.

**테스트:**
- `test_safe_deferral_handler.py` 기존 케이스 보존
- `_handle_deferral` 경로가 C207로 올바르게 위임되는지 확인

---

### FIX-G (Low): `_NoOpTelegramSender` 공개 이름으로 변경

**파일:** `mac_mini/code/caregiver_escalation/telegram_client.py`
         `mac_mini/code/main.py`

**문제:**
`_NoOpTelegramSender`(비공개 이름)를 `main.py`에서 직접 import한다.

**수정 내용:**
`NoOpTelegramSender`로 이름 변경 후 `__init__.py`에서 export.
`main.py` import 경로 업데이트.

---

## 3. 수정 순서 및 PR 계획

| PR | 항목 | 변경 파일 수 |
|----|------|------------|
| PR-A | FIX-A (ACK FAILURE 에스컬레이션) | 2 |
| PR-B | FIX-B (_compare TypeError 방어) | 1 |
| PR-C | FIX-C (Telegram 비동기) | 2 |
| PR-D | FIX-D (토픽 하드코딩 제거) | 5 |
| PR-E | FIX-E + FIX-F + FIX-G (Low 3건 묶음) | 3 |

High 항목(FIX-A, FIX-B)을 먼저 수정해 안전성을 확보한 뒤 Medium/Low를 진행한다.

---

## 4. 수정 완료 기준

- 각 수정 후 기존 테스트 전체 통과 (`pytest mac_mini/code/`)
- 각 항목별 신규 테스트 케이스 추가
- 수정된 내용이 아키텍처 문서 또는 SESSION_HANDOFF 원칙과 충돌하지 않을 것

---

## 5. 현재 상태

| 항목 | 상태 |
|------|------|
| FIX-A | ✅ 완료 (커밋 03207eb) |
| FIX-B | ✅ 완료 (커밋 03207eb) |
| FIX-C | ✅ 완료 (커밋 03207eb) |
| FIX-D | ✅ 완료 (커밋 03207eb) |
| FIX-E | ✅ 완료 (커밋 03207eb) |
| FIX-F | ✅ 완료 (커밋 03207eb) |
| FIX-G | ✅ 완료 (커밋 03207eb) |

→ 전체 완료. 완료 핸드오프:
`common/docs/runtime/SESSION_HANDOFF_2026-04-29_CODE_REVIEW_FIX_COMPLETE.md`
