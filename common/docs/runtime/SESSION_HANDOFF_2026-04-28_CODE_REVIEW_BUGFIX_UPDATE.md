# SESSION_HANDOFF — 2026-04-28 코드 리뷰 버그픽스 (PR #17~#20)

## 1. 이 addendum이 다루는 범위

이 세션에서 코드 리뷰 결과를 바탕으로 `mac_mini/code/main.py` 및
`mac_mini/code/caregiver_escalation/telegram_client.py`의 버그 4건을 수정했다.
모든 수정은 PR로 제출되어 main에 머지되었다.

---

## 2. Fix 1 — `_handle_class1()` AttributeError + 스키마 위반 (PR #17)

### 문제

`_handle_class1()` 내부에서 candidate dict를 구성할 때 `llm_result.deferral_reason`,
`llm_result.rationale_summary` 속성을 직접 참조했으나 `LLMCandidateResult` 모델에
해당 속성이 없다. 런타임 `AttributeError`로 즉시 크래시.

또한 `deferral_reason`을 항상 dict에 포함시켜 `candidate_action_schema.json`의
`allOf` 규칙(light_on/light_off는 `deferral_reason` 불허)을 위반했다.

### 수정

```python
# mac_mini/code/main.py — _handle_class1()
candidate: dict = {
    "proposed_action": llm_result.proposed_action,
    "target_device":   llm_result.target_device,
}
rationale = llm_result.candidate.get("rationale_summary", "")
if rationale:
    candidate["rationale_summary"] = rationale
if llm_result.is_safe_deferral:
    candidate["deferral_reason"] = (
        llm_result.candidate.get("deferral_reason") or "insufficient_context"
    )
```

- `llm_result.candidate` dict에서 값 추출
- `deferral_reason`은 `is_safe_deferral`일 때만 포함

---

## 3. Fix 2 — ACK 타임아웃 미처리 + C205 에스컬레이션 누락 (PR #18)

### 문제

`_pending_acks`에 dispatch record를 적재했으나 타임아웃을 감시하는 sweep 루프가
없어 ACK가 영원히 도착하지 않아도 C205 에스컬레이션이 발생하지 않았다.
`ack_handler.handle_ack_timeout()`은 구현되어 있었으나 호출된 적 없었다.

### 수정

`__init__`에서 daemon 스레드로 `_sweep_ack_timeouts()` 기동.
1초마다 `_pending_acks`를 순회하여 `ack_timeout_ms` 초과 항목을 pop 후
`handle_ack_timeout()` 호출 → `_escalate_c205()` 호출.

```python
# mac_mini/code/main.py — __init__
threading.Thread(
    target=self._sweep_ack_timeouts,
    daemon=True,
    name="ack-timeout-sweep",
).start()
```

`_escalate_c205(audit_correlation_id)`는 Class2Manager로 C205 세션을 시작하고
`CaregiverEscalationBackend.send_notification()`을 호출한다.

---

## 4. Fix 3 — staleness 판정이 payload 타임스탬프를 신뢰 (PR #19)

### 문제

`PolicyRouter.route(intake_result.raw_payload)`로 원본 payload를 그대로 전달하면
`routing_metadata.ingest_timestamp_ms` 필드가 공격자(또는 오동작하는 퍼블리셔)에
의해 조작되어 C204 freshness check를 우회할 수 있었다.

`ContextIntake`가 이미 로컬 수신 시각(`intake_result.ingest_timestamp_ms`)을
신뢰할 수 있는 값으로 계산하고 있었음에도 이를 사용하지 않았다.

### 수정

```python
# mac_mini/code/main.py — handle_context()
payload_to_route = {
    **intake_result.raw_payload,
    "routing_metadata": {
        **intake_result.raw_payload["routing_metadata"],
        "ingest_timestamp_ms": intake_result.ingest_timestamp_ms,
    },
}
route_result = self._router.route(payload_to_route)
```

PolicyRouter에 전달하기 전에 `ingest_timestamp_ms`를 로컬 관측값으로 덮어쓴다.

---

## 5. Fix 4 — Telegram HTML 메시지 payload 문자열 미이스케이프 (PR #20)

### 문제

`format_notification_message()`에서 6개의 payload 유래 문자열이
`html.escape()` 처리 없이 `parse_mode=HTML` 메시지에 직접 삽입되었다.
센서/컨텍스트 유래 값에 `<`, `>`, `&` 등이 포함되면 메시지 포맷 파괴 또는
의도치 않은 HTML 태그 생성이 발생했다.

### 수정

```python
# mac_mini/code/caregiver_escalation/telegram_client.py
import html

event    = html.escape(notification_payload.get("event_summary", ""))
reason   = html.escape(notification_payload.get("unresolved_reason", ""))
context  = html.escape(notification_payload.get("context_summary", ""))
path     = html.escape(notification_payload.get("manual_confirmation_path", ""))
trigger  = html.escape(notification_payload.get("exception_trigger_id") or "—")
audit_id = html.escape(notification_payload.get("audit_correlation_id", ""))
```

구조적 태그(`<b>`, `<i>`)는 정적 문자열이므로 escape 대상 아님.

회귀 테스트 2건 추가 (`test_html_special_chars_are_escaped`,
`test_html_in_event_summary_is_escaped`) — 42/42 통과 확인.

---

## 6. 변경 파일 요약

| 파일 | 변경 내용 |
|------|----------|
| `mac_mini/code/main.py` | Fix 1: candidate dict 구성 수정 |
| `mac_mini/code/main.py` | Fix 2: ACK sweep 스레드 + `_escalate_c205()` 추가 |
| `mac_mini/code/main.py` | Fix 3: `ingest_timestamp_ms` 로컬값으로 덮어쓰기 |
| `mac_mini/code/caregiver_escalation/telegram_client.py` | Fix 4: `html.escape()` 적용 |
| `mac_mini/code/tests/test_caregiver_escalation.py` | Fix 4 회귀 테스트 2건 추가 |

---

## 7. 머지된 PR 목록

| PR | 제목 | 상태 |
|----|------|------|
| #17 | fix: LLM candidate dict construction in `_handle_class1` | ✅ merged |
| #18 | fix: add ACK timeout sweep thread and C205 escalation | ✅ merged |
| #19 | fix: trust local ingest time for staleness check | ✅ merged |
| #20 | fix: html.escape() all payload fields in Telegram notification | ✅ merged |

---

## 8. 현재 WORK_PLAN 상태

| 항목 | 상태 |
|------|------|
| Mac mini 라이브러리 코드 (MM-01~10) | ✅ 완료 |
| Mac mini 진입점 (`main.py`) | ✅ 완료 + 버그픽스 4건 반영 |
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

## 9. 다음 세션 진입점

Phase 2 (하드웨어 연결)로 진행 가능. 선행 조건:

- Mac mini와 RPi가 같은 네트워크에 있고 SSH 접근 가능
- `SESSION_HANDOFF_2026-04-28_PHASE1_FIXTURE_BOM_UPDATE.md` §7 선택지 A 참조

코드 측 미결 사항은 없다. 추가 코드 리뷰가 있는 경우 이 addendum을 기준으로
이어서 수정하면 된다.
