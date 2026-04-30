# Session Handoff — 2026-04-30
## CLASS_2 Telegram Inline Keyboard & Telemetry Route Class Fix

---

## 작업 범위

이전 세션(SESSION_HANDOFF_2026-04-30_EXPERIMENT_E2E_BUGFIX.md)의 연속.  
이번 세션에서 완료한 작업:

1. CLASS_2 Telegram 인라인 키보드 보호자 응답 구현
2. Paho MQTT CallbackAPIVersion.VERSION2 경고 수정
3. 파이프라인 워커 스레드 블로킹 문제 수정 (300s wait 백그라운드 분리)
4. 실험 관찰 route_class CLASS_1→CLASS_2 수정

---

## 변경 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `mac_mini/code/caregiver_escalation/telegram_client.py` | `send_message_with_buttons()`, `answer_callback_query()`, `TelegramPoller`, `build_inline_keyboard()` 추가 |
| `mac_mini/code/main.py` | `TelegramPoller` 연동, `_handle_class2` 리팩토링, `handle_telegram_callback()`, `_await_caregiver_response()`, Paho VERSION2 콜백 수정, `escalate_to_class2()` 호출 |
| `mac_mini/code/telemetry_adapter/adapter.py` | `escalate_to_class2()` 메서드 추가 |

---

## 수정 1: Telegram 인라인 키보드 구현

### `telegram_client.py`

| 추가 항목 | 설명 |
|-----------|------|
| `TelegramSender` 프로토콜 확장 | `send_message_with_buttons()`, `answer_callback_query()` 메서드 추가 |
| `NoOpTelegramSender` | 위 두 메서드 no-op 구현 |
| `HttpTelegramSender.send_message_with_buttons()` | 동기식(블로킹). `reply_markup.inline_keyboard` 포함. 성공 시 `message_id` 반환, 실패 시 `None` 반환 |
| `HttpTelegramSender.answer_callback_query()` | 버튼 로딩 스피너 해제. fire-and-forget 데몬 스레드 |
| `TelegramPoller` | `/getUpdates?timeout=20` 장기 폴링 데몬 스레드. `callback_query` 수신 시 등록된 handler 호출 |
| `build_inline_keyboard()` | `ClarificationChoice` 목록 → Telegram `InlineKeyboardMarkup` 행 변환. `callback_data = "c2:{clarification_id}:{candidate_id}"` |

### `main.py` 추가 사항

```python
CAREGIVER_RESPONSE_TIMEOUT_S = int(os.environ.get("CAREGIVER_RESPONSE_TIMEOUT_S", "300"))
```

- `Pipeline._telegram_sender`: `HttpTelegramSender` / `NoOpTelegramSender` 직접 저장
- `Pipeline._pending_class2: dict[str, threading.Event]`: clarification_id → Event
- `Pipeline._class2_selections: dict[str, str]`: clarification_id → candidate_id
- `Pipeline._class2_lock`: 위 두 dict 보호
- `TelegramPoller` 시작: `TELEGRAM_TOKEN`이 있을 때 `Pipeline.__init__`에서 자동 시작
- `handle_telegram_callback(callback_query)`: Poller에서 호출. `c2:` 프리픽스 확인 → clarification_id 조회 → `Event.set()`

---

## 수정 2: Paho MQTT DeprecationWarning 제거

**증상**: `main.py:551: DeprecationWarning: Callback API version 1 is deprecated`

**수정**:
```python
# 이전
client = mqtt.Client(client_id="sd-mac-mini-hub", clean_session=True)

# 이후
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="sd-mac-mini-hub",
    clean_session=True,
)
# Paho < 2.0 폴백: AttributeError 시 레거시 생성자 사용
```

콜백 시그니처 업데이트:
- `on_connect(c, userdata, flags, reason_code, properties=None)`
- `on_disconnect(c, userdata, flags, reason_code=None, properties=None)`
- `reason_code.value == 0` 으로 연결 성공 판단

---

## 수정 3: 파이프라인 워커 블로킹 → 백그라운드 스레드 분리

### 문제

```
_handle_class2 → send_buttons → event.wait(300s) [워커 스레드 블로킹]
                                                          ↓
                                              텔레메트리 발행 지연 300s
                                              RPi 실험 트라이얼 30s 타임아웃
```

### 해결

`_handle_class2`를 즉시 반환하도록 리팩토링:

```
_handle_class2 → send_buttons → _await_caregiver_response 데몬 스레드 시작 → 즉시 return
                                         ↓ (백그라운드)                    ↓
                                  event.wait(300s)             handle_context: telemetry.publish()
                                  응답 → submit_selection()     → RPi 실험 관찰 수신 ✓
                                  타임아웃 → 에스컬레이션 알림
```

`_await_caregiver_response(session, event, trigger_id, audit_correlation_id)`:
- `event.wait(CAREGIVER_RESPONSE_TIMEOUT_S)` 대기
- 응답 있으면: `Class2ClarificationManager.submit_selection()` 호출
- 타임아웃 시: `handle_timeout()` + 에스컬레이션 알림 전송

---

## 수정 4: 실험 관찰 route_class 오류 수정

### 문제

C207 시나리오 (doorbell → CLASS_2):
```
PolicyRouter → CLASS_1 → update_route(CLASS_1)
  → LLM safe_deferral → _handle_class2()
    → update_class2()  ← class2 필드만 추가, route.route_class는 CLASS_1 유지
    → telemetry.publish() → observation.route.route_class = "CLASS_1"
```

실험 기대값: CLASS_2 / 관찰값: CLASS_1 → 트라이얼 실패

### 해결

`TelemetryAdapter.escalate_to_class2()` 추가:
```python
def escalate_to_class2(self) -> None:
    if self._route is not None:
        self._route = RouteTelemetry(
            route_class="CLASS_2",
            trigger_id=self._route.trigger_id,
            timestamp_ms=self._route.timestamp_ms,
        )
```

`_handle_class2()` 진입 시 두 경로 모두에서 호출:
- 인라인 키보드 경로 (전송 성공)
- 폴백 경로 (Telegram 미설정 / 전송 실패)

### 부가 수정

`handle_telegram_callback`에서 이미 만료된 세션의 버튼 누름:
- `WARNING` → `INFO` (이전 실험 메시지 재클릭 시 정상 발생하는 상황)

---

## 환경 변수 신규 추가

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `CAREGIVER_RESPONSE_TIMEOUT_S` | `300` | CLASS_2 인라인 키보드 보호자 응답 대기 시간(초) |

---

## 현재 시스템 상태

- CLASS_1 실험: 정상 동작 확인
- CLASS_0 실험: 정상 동작 확인
- CLASS_2 doorbell(C207) 실험: route_class 수정 완료, 텔레메트리 즉시 발행, 보호자 응답 대기 백그라운드
- Telegram: 인라인 키보드 전송 → 보호자 버튼 클릭 → `handle_telegram_callback` → `Event.set()` → `submit_selection()` 흐름 구현 완료
- Paho MQTT: VERSION2 API 사용, DeprecationWarning 제거

## 다음 세션 참고사항

- CLASS_2 실험 결과 검증 필요 (route_class 수정 후 트라이얼 Pass 여부)
- `_await_caregiver_response` 내에서 `submit_selection()` 결과는 telemetry에 반영되지 않음 (이미 publish 완료 후 실행). 실험 로그/audit DB에서 확인 가능
- `session.status`가 `handle_timeout()` 호출로 `TIMED_OUT`으로 설정된 후 `submit_selection()`이 `SELECTED`로 덮어씀 — 기능상 문제없으나 다음 세션에서 세션 상태 관리 정리 가능
