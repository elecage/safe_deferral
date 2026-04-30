# SESSION_HANDOFF_2026-04-30_CLASS2_PHASE_TIMEOUT_AND_TTS_FIX.md

## Purpose

이전 세션(`SESSION_HANDOFF_2026-04-30_DASHBOARD_AND_CLASS2_BUGFIX.md`,
`SESSION_HANDOFF_2026-04-30_CLASS2_TELEGRAM_KEYBOARD_AND_TELEMETRY_FIX.md`)의
연속.  
이 문서가 기록하는 항목에서 위 문서들과 내용이 충돌하면 이 문서를 우선한다.

---

## 이번 세션에서 수정한 버그 (PR #73 ~ #75)

---

### PR #73 — NameError: `expected_route_class` is not defined

**파일:** `rpi/code/experiment_package/runner.py`

**증상:** CLASS_2 시나리오를 실행하면 대시보드에서 항상 타임아웃이 표시됨.
맥미니 로그에는 "caregiver selected C1_LIGHTING_ASSISTANCE"가 정상적으로
찍히는데 RPi 쪽에서 타임아웃 처리.

**근본 원인:** `_run_trial()` 내부에서 `expected_route_class`를 지역 변수처럼
사용했으나 실제로 해당 이름의 지역 변수는 없음.
올바른 접근 경로는 메서드 인자인 `trial: TrialResult`의 속성 `trial.expected_route_class`.
NameError가 CLASS_2 trial 백그라운드 스레드를 즉시 크래시시켜
`timeout_trial()`이 호출되었음.

**수정:**
```python
# 수정 전 (NameError 발생)
auto_class2_node = (
    node if expected_route_class == "CLASS_2" else None
)

# 수정 후
auto_class2_node = (
    node if trial.expected_route_class == "CLASS_2" else None
)
```

---

### PR #74 — PackageRunner auto-simulate가 카레기버 Telegram 경로 차단

**파일:** `rpi/code/experiment_package/runner.py`

**증상 (PR #73 적용 후 새로 발생):**
- Telegram 메시지가 오지 않음
- "상태가 완료되었다"는 TTS가 선택하기 전에 울림
- 사용자 선택 없이 trial이 즉시 completed

**근본 원인:**
PR #73으로 NameError가 수정되자 `auto_class2_node`가 정상 설정됨.
`_match_observation()`이 첫 번째 CLASS_2 관찰(class2 블록 없음)을 보는 즉시
1초 대기 후 `single_click` 버튼 MQTT 이벤트를 자동 발행.
→ Phase 1 사용자 선택 즉시 완료 → Phase 2(카레기버 Telegram)가 절대 시작 안 됨.

**수정:**
`_match_observation()`에서 auto-simulate 로직 전체 제거.
러너는 맥미니가 최종 `class2` 블록이 포함된 관찰을 발행할 때까지 수동 대기.

CLASS_2 trial 전용 타임아웃 상수 추가:
```python
_TRIAL_TIMEOUT_S = 30.0          # CLASS_0 / CLASS_1
_TRIAL_TIMEOUT_CLASS2_S = 360.0  # CLASS_2: Phase1(≤30s) + Phase2(≤300s) + 여유
```

`_run_trial()` 내 타임아웃 선택:
```python
trial_timeout = (
    _TRIAL_TIMEOUT_CLASS2_S
    if trial.expected_route_class == "CLASS_2"
    else _TRIAL_TIMEOUT_S
)
observation = self._match_observation(correlation_id, trial_timeout)
```

`_match_observation()` 시그니처 단순화:
```python
# 수정 전
def _match_observation(self, correlation_id, timeout_s, auto_class2_node=None):

# 수정 후
def _match_observation(self, correlation_id: str, timeout_s: float) -> Optional[dict]:
```

**CLASS_2 관찰 폴링 로직 (변경 후):**
```python
route_class = (obs.get("route") or {}).get("route_class", "")
if route_class != "CLASS_2":
    return obs          # CLASS_0/1: 첫 번째 매치로 즉시 반환
if obs.get("class2"):
    return obs          # CLASS_2 + class2 블록: 최종 관찰 → 반환
# class2 블록 없음: Phase 1 또는 2 진행 중 → 계속 폴링
```

---

### PR #75 — Phase-1 사용자 타임아웃 15s 너무 짧음 + 선택 후 TTS 없음

**파일:**
- `common/policies/policy_table.json`
- `mac_mini/code/tts/speaker.py`
- `mac_mini/code/main.py`

#### 문제 1: Phase-1 타임아웃 15s → 30s

**증상:** 사용자가 버추얼 노드 버튼을 누르기 전에 Phase-1이 타임아웃되어
카레기버에게 즉시 에스컬레이션됨.

**수정:**
```json
// common/policies/policy_table.json
"class2_clarification_timeout_ms": 30000
```
(15000 ms → 30000 ms)

맥미니는 시작 시 `AssetLoader`로 정책 파일을 읽으므로 재시작 필요.

#### 문제 2: 사용자/카레기버 선택 후 TTS 안내 없음

**증상:**
- 카레기버가 Telegram에서 선택하면 맥미니 로그에 "caregiver selected C1_LIGHTING_ASSISTANCE"는 뜨지만 TTS 안내 없이 상태만 completed
- 사용자가 Phase-1에서 버튼을 눌러도 마찬가지로 조용함

**근본 원인:** `submit_selection()` 후 `publish_class2_update()`만 호출하고
TTS 피드백이 없었음.

**신규 TTS 헬퍼 (`tts/speaker.py`):**
```python
def announce_class2_selection(
    speaker: TtsSpeaker,
    selection_source: str,
    chosen_prompt: str,
) -> None:
    prefix = "보호자가" if "caregiver" in selection_source else "사용자가"
    text = f"{prefix} '{chosen_prompt}'을(를) 선택했습니다."
    speaker.speak(text)
```

**`main.py` 변경:**
`announce_class2_selection` import 추가 후
`_await_user_then_caregiver()` 내 세 경로 모두에 호출 추가:

| 경로 | selection_source |
|------|-----------------|
| Phase-1 사용자 버튼 | `"user_mqtt_button"` |
| Phase-2 늦은 사용자 버튼 | `"user_mqtt_button_late"` |
| Phase-2 카레기버 Telegram | `"caregiver_telegram_inline_keyboard"` |

각 경로에서 `session.candidate_choices`에서 선택된 candidate의 `prompt`를
가져와서 TTS 텍스트로 사용:
```python
chosen = next(
    (c for c in session.candidate_choices if c.candidate_id == selected_id),
    None,
)
announce_class2_selection(
    self._tts, selection_source, chosen.prompt if chosen else selected_id
)
```

---

## 수정 후 전체 CLASS_2 흐름

```
1. 컨텍스트 발행 → CLASS_2 라우팅
2. TTS: "보호자 확인이 필요합니다. 다음 중 선택해 주세요. 1번, 조명 도움이 필요하신가요?..."
3. Phase-1 (30초 대기):
   └─ 버튼 누름 → TTS "사용자가 '조명 도움이 필요하신가요?'을(를) 선택했습니다."
                  → publish_class2_update() → trial completed ✓
4. Phase-1 타임아웃 → Phase-2 (300초 대기):
   └─ Telegram 인라인 키보드 전송
   └─ 카레기버 응답 → TTS "보호자가 '...'을(를) 선택했습니다."
                      → publish_class2_update() → trial completed ✓
   └─ 300초 타임아웃 → 에스컬레이션 알림 → trial completed
5. RPi 러너: 최대 360초 대기, class2 블록 포함 관찰 수신 → complete_trial()
```

---

## PR 목록

| PR | 제목 | 변경 파일 |
|----|------|-----------|
| #73 | Fix NameError: use `trial.expected_route_class` in `_run_trial()` | `rpi/code/experiment_package/runner.py` |
| #74 | Remove CLASS_2 auto-simulate; extend timeout to 360s for caregiver path | `rpi/code/experiment_package/runner.py` |
| #75 | Fix CLASS_2 Phase-1 timeout (30s) and add TTS after selection | `common/policies/policy_table.json`, `mac_mini/code/tts/speaker.py`, `mac_mini/code/main.py` |

---

## 배포 체크리스트

**맥미니 (`git pull` + `main.py` 재시작):**
- [ ] `class2_clarification_timeout_ms` 30000ms 적용 확인 (로그에 "Phase-1 user wait 30s" 표시)
- [ ] Phase-1/2 선택 후 TTS 안내 확인

**RPi (`git pull` + 대시보드/러너 재시작):**
- [ ] CLASS_2 trial이 타임아웃 대신 completed로 표시되는지 확인
- [ ] CLASS_2 trial 타임아웃이 360초임을 확인

---

## 잔존 미확인 사항

- `_simulate_class2_button()` 메서드가 `runner.py`에 남아 있으나 미사용 상태.
  다음 세션에서 제거 가능.
- `trial.pass_` 정확성: 카레기버 선택 후 `expected_outcome`과의 매칭 로직이
  `trial_store.py`에서 올바르게 평가되는지 실 하드웨어에서 검증 필요.
- Phase-1 중 사용자가 버튼을 눌러 선택하는 경로(물리 버튼 또는 버추얼 노드)
  완전 end-to-end 검증 필요.
