# Session Handoff — 2026-04-30
## Dashboard JS Parse Failure, Fetch Timeout, CLASS_2 Phase Guard, Runner Auto-Interact

---

## 작업 범위

이전 세션(SESSION_HANDOFF_2026-04-30_CLASS2_TELEGRAM_KEYBOARD_AND_TELEMETRY_FIX.md)의 연속.  
이번 세션에서 완료한 작업 (PR #67~#71):

1. 대시보드 fetch 타임아웃 추가 (무한 로딩 방지)
2. 대시보드 JS 파싱 실패 수정 (`DEVICE_LABELS` 중복 선언)
3. 대시보드 서버 오프라인 즉시 감지 (`/health` 엔드포인트 + `_boot()`)
4. CLASS_2 Phase 2 파이프라인 우회 버그 수정 (보호자 대기 중 비버튼 이벤트 → CLASS_1 dispatch 방지)
5. PackageRunner CLASS_2 사용자 버튼 자동 시뮬레이션

---

## 변경 파일 목록

| 파일 | PR | 변경 내용 |
|------|-----|----------|
| `rpi/code/dashboard/static/index.html` | #67, #68, #69 | `fetchT()`, `_boot()`, `DEVICE_LABELS` 중복 제거 |
| `rpi/code/dashboard/app.py` | #68 | `GET /health` 엔드포인트 추가 |
| `mac_mini/code/main.py` | #70 | `_await_user_then_caregiver()` Phase 2 가드, `_try_handle_as_user_selection()` Phase 1/2 통합 |
| `rpi/code/experiment_package/runner.py` | #71 | `_simulate_class2_button()`, `_match_observation(auto_class2_node=)` |

---

## 수정 1: 대시보드 fetch 타임아웃 (PR #67)

### 문제
브라우저 `fetch()`는 서버가 TCP 연결을 명시적으로 거부하지 않으면 OS TCP 타임아웃(~90초)까지 무한 대기.  
페이지 로드 시 6개 API 요청이 동시에 발행 → 서버가 없으면 모두 동시에 멈춤.

```
MQTT 확인 중…   ← 영원히 변화 없음
시스템 확인 중…
패키지를 불러오는 중…
시나리오를 불러오는 중…
```

### 해결

```javascript
function fetchT(url, options = {}, timeoutMs = 8000) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), timeoutMs);
  return fetch(url, { ...options, signal: ctrl.signal })
    .finally(() => clearTimeout(id));
}
```

`checkMqtt()`, `checkPreflight()`, `loadPackages()`, `loadFaultProfiles()`, `loadScenarios()`, `loadSimState()`, `updateTopoMqtt()` 모두 `fetchT()` 사용으로 교체. 8초 후 기존 catch 블록이 오류 상태 표시.

---

## 수정 2: 대시보드 JS 파싱 실패 (PR #69)

### 문제 (근본 원인)

```
SyntaxError: Identifier 'DEVICE_LABELS' has already been declared
```

`const DEVICE_LABELS`가 스크립트 내에 두 번 선언:
- 1차: 노드 섹션 (~line 1495)
- 2차: 시뮬레이션 상태 섹션 (이전 세션 추가)

브라우저는 중복 `const` 선언을 `SyntaxError`로 처리 → **`<script>` 블록 전체 파싱 포기** → JS 한 줄도 실행 안 됨.

**증상**: 대시보드 HTML은 로드되지만 텍스트가 전혀 바뀌지 않음. 강력 새로고침(Ctrl+Shift+R)해도 동일.

### 해결

시뮬레이션 섹션의 중복 `const DEVICE_LABELS` 선언 제거. `DEVICE_STATES` const는 유지.

### 진단 명령

```bash
python3 -c "
import re
with open('rpi/code/dashboard/static/index.html') as f:
    content = f.read()
m = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
with open('/tmp/check.js', 'w') as out:
    out.write(m.group(1))
"
node --check /tmp/check.js
```

---

## 수정 3: 서버 오프라인 즉시 감지 (PR #68)

### 문제

JS가 실행은 되지만 서버가 응답하지 않을 때 사용자가 원인을 알 수 없음.

### 해결

**`GET /health` 엔드포인트** (app.py):
```python
@app.get("/health", include_in_schema=False)
def health():
    return {"ok": True}
```

**`_boot()` 함수** (index.html):
```javascript
async function _boot() {
  // 1) 즉시 텍스트 변경 → JS 실행 여부 즉시 확인
  document.getElementById('lbl-mqtt').textContent = 'MQTT 서버 연결 중…';
  document.getElementById('lbl-system').textContent = '시스템 연결 중…';

  // 2) 2초 타임아웃으로 /health 호출 → 서버 연결 여부 판단
  let serverOk = false;
  try {
    const r = await fetchT('/health', {}, 2000);
    serverOk = r.ok;
  } catch (_) {}

  if (!serverOk) {
    // 3) 오프라인: 에러 메시지 표시, 5초 후 자동 재시도
    document.getElementById('lbl-mqtt').textContent = 'MQTT — 서버 오프라인';
    document.getElementById('lbl-system').textContent = '시스템 — 서버 오프라인';
    document.getElementById('pkg-grid').innerHTML =
      '<div class="empty">⚠️ RPi 서버(포트 8888)에 연결할 수 없습니다.</div>';
    setTimeout(_boot, 5000);
    return;
  }

  // 4) 온라인: 정상 로드
  refreshAll(); loadPackages(); loadScenarios(); loadSimState();
  setInterval(refreshAll, 10000);
  ...
}
window.addEventListener('DOMContentLoaded', _boot);
```

**진단 포인트**:
- 페이지 로드 후 즉시 텍스트가 "MQTT 서버 연결 중…"으로 바뀌면 → JS 정상 실행
- 텍스트가 전혀 안 바뀌면 → JS 파싱 오류 (브라우저 콘솔 확인)
- "서버 오프라인" 메시지가 뜨면 → RPi `main.py` 미실행 또는 포트 접근 불가

---

## 수정 4: CLASS_2 Phase 2 파이프라인 우회 버그 (PR #70)

### 문제

```
[CLASS_2 시작]
  Phase 1 (15초 사용자 대기)
    → _pending_user_class2에서 세션 제거  ← 가드 사라짐!
  Phase 2 (보호자 Telegram 대기)
    → 실험 runner가 /interact로 single_click 발행
    → _try_handle_as_user_selection(): _pending_user_class2 비어 있음 → False
    → 일반 CLASS_1 파이프라인 진행
    → LLM: light_on → Validator: APPROVED → Dispatcher → 거실 조명 ON  ← 버그
```

또한 Phase 1/2 모두에서 비버튼(non-button) 이벤트가 일반 파이프라인으로 흘러들어 갔음.

### 해결

**`_await_user_then_caregiver()` 변경**:

```python
# Phase 1 전: caregiver_event를 미리 생성해 entry에 저장
caregiver_event = threading.Event()
entry = {
    "session": session,
    "event": user_event,
    "caregiver_event": caregiver_event,  # Phase 2 중 늦은 사용자 버튼이 이것을 깨움
    "trigger_id": trigger_id,
    "audit_id": audit_correlation_id,
    "selection": None,
    "phase": 1,
}
with self._user_class2_lock:
    self._pending_user_class2[cid] = entry  # ← 전체 세션 동안 유지

# Phase 1 끝 후: user_selected_id가 있으면 처리 후 pop, 없으면 phase=2로 업데이트
# Phase 2 중: entry가 _pending_user_class2에 유지됨 (가드 활성)
# Phase 2 끝: with self._user_class2_lock: self._pending_user_class2.pop(cid)
```

**`_try_handle_as_user_selection()` 변경**:

```python
if event_type != "button":
    # CLASS_2 활성 중 비버튼 이벤트: 파이프라인 차단
    return True  # 소비, 정상 파이프라인 미진행

# Phase 1 버튼: live_entry["event"].set()
# Phase 2 버튼: live_entry["caregiver_event"].set()  ← 늦은 사용자 선택
```

**Phase 2 늦은 사용자 선택 처리** (late_user_selected_id):

Phase 2 중 사용자가 버튼을 누르면:
1. `caregiver_event.set()` → Phase 2 대기 해제
2. `entry["selection"]` = selected_id (늦은 사용자 선택)
3. `late_user_selected_id` 확인 → `submit_selection(..., source="user_mqtt_button_late")`
4. 보호자 선택보다 우선 (사용자가 직접 응답)

### 권한 경계 확인

CLASS_2 선택 결과(`Class2Result`)는 **실험 텔레메트리 기록 전용**. 사용자·보호자 선택 어느 쪽도 자율 액추에이션(dispatch)을 유발하지 않음. 이 코드는 의도된 설계를 구현한 것임.

---

## 수정 5: PackageRunner CLASS_2 자동 사용자 버튼 시뮬레이션 (PR #71)

### 문제

CLASS_2 trial에서 수동 상호작용이 필요했음:
- "📤 1회 발행": 원본 템플릿(voice_command 등) 발행 → event_type != "button" → Phase 1/2 가드가 차단 → 선택 미기록
- "🎯 인터랙션": `/interact` 엔드포인트 → `event_type=button, event_code=single_click` → 정상 인터셉트
- 15초 내에 수동으로 "🎯 인터랙션"을 눌러야 했으며, 실패 시 Phase 1 timeout → SAFE_DEFERRAL 결과

### 해결

**`PackageRunner._simulate_class2_button(node, correlation_id)`**:

```python
def _simulate_class2_button(self, node, correlation_id):
    patched = copy.deepcopy(node.profile.payload_template)
    patched["pure_context_payload"]["trigger_event"]["event_type"] = "button"
    patched["pure_context_payload"]["trigger_event"]["event_code"] = "single_click"
    patched["pure_context_payload"]["trigger_event"]["timestamp_ms"] = now_ms
    patched["routing_metadata"]["audit_correlation_id"] = correlation_id
    # 임시로 RUNNING 상태 + patched 템플릿으로 publish_once() 호출
    # finally: 원본 복원
```

**`PackageRunner._match_observation(auto_class2_node=None)`**:

```python
# CLASS_2 관찰(class2 block 없음)을 처음 발견하면:
if not class2_button_sent and auto_class2_node is not None:
    class2_button_sent = True
    time.sleep(1.0)  # Phase 1 가드 등록 대기
    self._simulate_class2_button(auto_class2_node, correlation_id)
```

**`_run_trial()`**:

```python
auto_class2_node = node if expected_route_class == "CLASS_2" else None
observation = self._match_observation(
    correlation_id, _TRIAL_TIMEOUT_S,
    auto_class2_node=auto_class2_node,
)
```

### 결과

| 항목 | 이전 | 이후 |
|------|------|------|
| 완료 시간 | Phase 1 timeout 15s + α | 관찰 도착 후 ~2-3s |
| selection_source | timeout_or_no_response | user_mqtt_button |
| transition_target | SAFE_DEFERRAL | CLASS_1 |
| 수동 개입 | 필요 (15초 이내 클릭) | 불필요 |

---

## CLASS_2 선택과 액추에이션 관계 (중요 아키텍처 메모)

현재 구현에서 CLASS_2 선택 결과(`transition_target=CLASS_1`)는 **텔레메트리 기록 전용**이며, 실제 액추에이션(거실 조명 ON 등)으로 이어지지 않음. 이것은 의도된 설계:

- 안전 경계: CLASS_2 결과는 "사용자 의도 확인 증거"에 불과, 자율 dispatch 권한 없음
- 선택 결과를 바탕으로 실제 행동하려면 Policy Router 재진입 + Validator 승인 필요
- 실험에서 CLASS_2 trail의 pass 기준은 route_class=CLASS_2 관찰 + class2 block 존재 여부

CLASS_2 → CLASS_1 재진입 실행 흐름은 현재 미구현 상태. 필요 시 별도 설계 필요.

---

## 현재 시스템 상태

### 대시보드 (RPi, 포트 8888)
- JS 파싱 오류 해결 → 모든 UI 기능 정상
- 서버 오프라인 시 2초 내 "서버 오프라인" 표시, 5초마다 자동 재시도
- fetch 타임아웃 8초 → 서버 응답 없으면 오류 상태 표시

### CLASS_2 파이프라인 (Mac mini)
- Phase 1 + Phase 2 전체 기간에 걸쳐 가드 활성 (`_pending_user_class2` 세션 유지)
- 비버튼 이벤트: Phase 1/2 모두에서 파이프라인 차단 (True 반환, 소비)
- Phase 2 중 늦은 사용자 버튼 → `caregiver_event.set()` → 보호자보다 우선 처리
- 보호자 응답 없이 Phase 2 timeout → `handle_timeout()` → 에스컬레이션 알림

### PackageRunner (RPi)
- CLASS_2 trial: 자동으로 `single_click` 버튼 시뮬레이션
- 비 CLASS_2 trial: 영향 없음

---

## 다음 세션 참고사항

1. **CLASS_2 → CLASS_1 재실행 미구현**: 사용자/보호자가 CLASS_1 후보를 선택해도 실제 액추에이션이 일어나지 않음. 실험 목적(텔레메트리/관찰)에는 충분하나, 실제 사용 환경에서는 재진입 흐름 구현 필요.

2. **"거실 조명을 켭니다만" TTS**: Trial 완료 후 사용자가 "1회 발행"을 다시 누르면 새 CLASS_2 세션이 시작되며 `announce_class2()` TTS가 재생됨. 버그 아님, 사용자 workflow 주의사항.

3. **Telegram 미설정 시 Phase 2 즉시 스킵**: `TELEGRAM_TOKEN` 없으면 `NoOpTelegramSender.send_message_with_buttons()` → `None` 반환 → Phase 2 대기 없이 즉시 `handle_timeout()`. Trial 약 15s 내 완료.

4. **CLASS_2 trial timeout**: `_TRIAL_TIMEOUT_S = 30.0`. Phase 1(15s) + Phase 2(최대 300s) 전체를 기다리면 trial timeout. Telegram 설정 시 자동 버튼 시뮬레이션으로 Phase 1에서 처리되므로 timeout 없이 완료.

5. **시뮬레이션 아키텍처**: SimStateStore (공유 상태) + ENV_SENSOR_NODE / DEVICE_STATE_NODE (개별 가상 노드) + CONTEXT_NODE (발행 시 SimStateStore 스냅샷 주입) 구조 완성. 이전 세션 대비 추가 변경 없음.
