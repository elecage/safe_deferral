# SESSION_HANDOFF — CLASS_2 Transition Handler, TrialStore Verdict, Doc Clarity

**Date:** 2026-05-01
**Branch:** claude/strange-engelbart-bd3430 → PR to main
**Tests:** 414/414 mac_mini, 91/91 rpi

---

## 이번 세션에서 수정한 내용

### Issue 1 & 2: CLASS_2 선택 후 전이 핸들러 미구현

**증상:**
- CLASS_2 세션에서 사용자/보호자가 후보를 선택해도 Pipeline은 telemetry만 발행하고 종료
- `transition_target=CLASS_1`이어도 DeterministicValidator 재진입 없음
- `transition_target=CLASS_0`이어도 emergency handler 호출 없음
- `triple_hit` → CLASS_0 후보 선택 → CLASS_0 경로 미진입 (Issue 2와 동일 근본 원인)

**수정 파일:** `mac_mini/code/main.py`

`_execute_class2_transition(class2_result, audit_correlation_id, trigger_id)` 메서드 추가:

| 전이 대상 | 동작 |
|---|---|
| `CLASS_1` + `is_class1_ready=True` | `DeterministicValidator.validate()` → `publish_validator_output()` → APPROVED이면 `LowRiskDispatcher.dispatch()` → ACK 등록 → TTS announce |
| `CLASS_1` + `is_class1_ready=False` | 경고 로그 (target_hint 없음 — 후보 정의 업데이트 필요) |
| `CLASS_0` | `announce_emergency()` → `_caregiver.send_notification()` |
| `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION` | 자율 동작 없음 (기존 동작 유지) |

호출 위치: `_await_user_then_caregiver()` 내 모든 selection-based `publish_class2_update()` 직후
(user phase-1 선택, late-user phase-2 선택, caregiver phase-2 선택 — timeout 경로 제외)

---

### Issue 5: TrialStore CLASS_2 판정 — transition_target 검증 미비

**증상:**
- `_is_pass()` CLASS_2 블록이 `class2_tel` 존재 여부만 확인하고 `transition_target` 불일치를 통과시킴

**수정 파일:** `rpi/code/experiment_package/trial_store.py`

- `TrialResult`에 `expected_transition_target: Optional[str] = None` 필드 추가
- `to_dict()`에 포함
- `create_trial()`에 파라미터 추가
- `_is_pass()` CLASS_2 블록: `expected_transition_target`이 설정된 경우 `class2_tel.get("transition_target") == trial.expected_transition_target` 검증

**수정 파일:** `rpi/code/experiment_package/runner.py`

- `start_trial_async()`: `expected_route_class == "CLASS_2"`일 때 `loader.load_scenario()` 호출하여 `class2_clarification_expectation.expected_transition_target` 로드 → `create_trial()`에 전달

---

### Issue 3: 문서 — doorbell trigger_event vs environmental_context 혼동

**수정 파일:** `integration/scenarios/scenario_manifest_rules.md`

섹션 11에 표 추가:

| 위치 | 역할 | Policy Router 결과 |
|---|---|---|
| `environmental_context.doorbell_detected=true` | context signal | **CLASS_1** (button trigger 시) |
| `trigger_event.event_type=sensor, event_code=doorbell_detected` | trigger 이벤트 | **CLASS_2 (C208)** |

---

### Issue 4: 문서 — clarification/interaction "publish and consume" 오류

**수정 파일:** `common/docs/architecture/12_prompts_mac_mini_components.md`

Prompt MM-06:
- 변경 전: "publish **and consume** Class 2 interaction evidence"
- 변경 후: "publish Class 2 interaction evidence (publish-only; runtime receives CLASS_2 selections via context/input button press or Telegram callback)"

**수정 파일:** `common/docs/architecture/04_class2_clarification.md`

섹션 5에 publish-only 명시 추가:
"This topic is publish-only evidence. The runtime publishes interaction snapshots here for audit and experiment observation. It does not subscribe to this topic to receive CLASS_2 selections."

---

## 추가된 테스트

**`mac_mini/code/tests/test_pipeline_ack_escalation.py`** — `TestExecuteClass2Transition` (5개):
1. `test_class1_is_class1_ready_dispatches` — CLASS_1 + is_class1_ready → dispatcher 호출, ACK 등록
2. `test_class1_not_ready_no_dispatch` — CLASS_1 + target_hint 없음 → dispatch 없음
3. `test_class0_sends_caregiver_notification` — CLASS_0 → caregiver.send_notification 호출
4. `test_class0_trigger_id_in_summary` — CLASS_0 알림에 trigger_id 포함
5. `test_safe_deferral_no_dispatch_no_notify` — SAFE_DEFERRAL → 자율 동작 없음

**`rpi/code/tests/test_rpi_components.py`** — `TestTrialStoreTransitionTarget` (6개):
1. `test_no_expected_target_always_passes` — expected=None이면 어떤 observed_target도 통과
2. `test_matching_target_passes` — expected=CLASS_1, observed=CLASS_1 → pass
3. `test_mismatched_target_fails` — expected=CLASS_1, observed=CLASS_0 → fail
4. `test_class0_expected_target_passes` — expected=CLASS_0, observed=CLASS_0 → pass
5. `test_expected_target_in_to_dict` — to_dict()에 포함
6. `test_none_expected_target_in_to_dict` — None도 직렬화

---

## 주의사항

- `_execute_class2_transition()`은 background thread(`_await_user_then_caregiver`)에서 호출됨
  - `update_ack()`는 호출하지 않음 (shared state race 방지)
  - `publish_validator_output()`은 fire-and-forget이므로 안전
- CLASS_1 디스패치는 `is_class1_ready` (action_hint + target_hint 모두 설정)가 True일 때만 실행됨
  - 현재 `_DEFAULT_CANDIDATES`의 CLASS_1 후보(`C1_LIGHTING_ASSISTANCE`)는 `action_hint="light_on"`만 있고 `target_hint` 없음 → 실험에서 실제 디스패치를 테스트하려면 후보 정의에 `target_hint` 추가 필요
- `expected_transition_target`은 CLASS_2 시나리오의 `class2_clarification_expectation.expected_transition_target`에서 자동 로드
  - 필드가 없거나 scenario 로드 실패 시 None으로 fallback → 기존 pass/fail 로직 그대로

---

## 다음 세션 권장 작업

1. **CLASS_1 후보에 target_hint 추가** — `_DEFAULT_CANDIDATES`의 `C1_LIGHTING_ASSISTANCE`에 `"target_hint": "living_room_light"` 또는 context 기반 동적 설정 → `is_class1_ready=True`가 되어 실제 디스패치 가능
2. **end-to-end 실험 재실행** — CLASS_2 → CLASS_1 전이 경로 포함 E2E 검증
3. **class2_to_class1 시나리오 스켈레톤 연결** — `class2_to_class1_low_risk_confirmation_scenario_skeleton.json`을 실제 fixture와 연결
