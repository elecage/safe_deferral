# SESSION_HANDOFF — CLASS_2→CLASS_1 Dispatch Fix & Validator Evidence Tracking

**Date:** 2026-05-01
**Branch:** claude/strange-engelbart-bd3430 → PR #78 to main
**Tests:** 421/421 mac_mini, 103/103 rpi

---

## 이번 세션에서 수정한 내용

### Issue 1: C1_LIGHTING_ASSISTANCE target_hint 누락 → CLASS_2→CLASS_1 디스패치 미실행

**증상:**
- `_DEFAULT_CANDIDATES["insufficient_context"]` 및 `["missing_policy_input"]`의 `C1_LIGHTING_ASSISTANCE`가 `target_hint=None`
- `Class2Result.is_class1_ready` = False → `_execute_class2_transition()` 에서 dispatcher 호출 불가

**수정:** `mac_mini/code/class2_clarification_manager/manager.py`

- `insufficient_context`와 `missing_policy_input`의 `C1_LIGHTING_ASSISTANCE` → `target_hint="living_room_light"` 추가
- `unresolved_context_conflict`의 `OPT_LIVING_ROOM`/`OPT_BEDROOM` → `action_hint="light_on"` 추가 (두 hint 모두 필요해야 `is_class1_ready=True`)

---

### Issue 2: TrialStore — CLASS_2→CLASS_1 전이 후 Validator 증거 검증 미구현

**증상:**
- CLASS_2 시나리오의 `requires_validator_when_class1: true` 설정이 trial verdict에 반영되지 않음
- `_match_observation()`이 `class2` 블록만 있으면 즉시 반환 → post-transition validator 결과 대기 없음

**수정 파일:** `mac_mini/code/telemetry_adapter/models.py`

```python
@dataclass
class Class2Telemetry:
    ...
    post_transition_validator_status: Optional[str] = None  # "approved"|"safe_deferral"|"rejected_escalation"|"not_ready"
    post_transition_dispatched: Optional[bool] = None
```

**수정 파일:** `mac_mini/code/telemetry_adapter/adapter.py`

`publish_class2_transition_result(audit_id, class2_result, post_transition_validator_status, post_transition_dispatched)` 추가:
- `publish_class2_update()` 이후, `_execute_class2_transition()`이 CLASS_1 경로 실행 완료 후 호출
- `observation_topic`에 별도 snapshot 발행 (동일 `audit_correlation_id`)
- `class2.post_transition_validator_status` + `class2.post_transition_dispatched` 포함

**수정 파일:** `mac_mini/code/main.py`

`_execute_class2_transition()` CLASS_1 경로 3곳에 `publish_class2_transition_result()` 호출 추가:
| 경로 | post_transition_validator_status | post_transition_dispatched |
|---|---|---|
| is_class1_ready=True + APPROVED | "approved" | True |
| is_class1_ready=True + not approved | val_result.validation_status.value | False |
| is_class1_ready=False | "not_ready" | False |

**수정 파일:** `rpi/code/experiment_package/trial_store.py`

- `TrialResult`에 `requires_validator_when_class1: Optional[bool] = None` 추가
- `to_dict()`에 포함
- `create_trial()` 파라미터 추가
- `_is_pass()` CLASS_2 블록: `expected_transition_target == "CLASS_1"` and `requires_validator_when_class1` → `class2_tel.get("post_transition_validator_status") != "approved"` 이면 실패

**수정 파일:** `rpi/code/experiment_package/runner.py`

- `start_trial_async()`: 시나리오에서 `requires_validator_when_class1` 로드 → `create_trial()` 전달
- `_run_trial()`: `requires_post = (trial.expected_transition_target == "CLASS_1" and trial.requires_validator_when_class1)` → `_match_observation(requires_post_transition_snapshot=requires_post)` 전달
- `_match_observation()`: `requires_post_transition_snapshot=True`이면 `class2.post_transition_validator_status is not None`까지 폴링

---

### Issue 3: expected_transition_target 정규화 — CAREGIVER_CONFIRMATION 및 복합 _OR_ 값

**수정 파일:** `rpi/code/experiment_package/runner.py`

`_normalize_expected_transition_target(raw)` 함수 추가:
- `None`/빈 문자열 → `None`
- `"CAREGIVER_CONFIRMATION"` → `"SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"` (runtime canonical 값)
- canonical 값 집합 (`CLASS_1`, `CLASS_0`, `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION`) → 그대로 통과
- `_OR_` 포함 (복합 다중 타겟) → `None` (strict check 없음)

`start_trial_async()`에서 `c2_exp.get("expected_transition_target")`에 적용.

**수정 파일:** 시나리오 스켈레톤

| 파일 | 변경 전 | 변경 후 |
|---|---|---|
| `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json` | `"CAREGIVER_CONFIRMATION"` | `"SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"` |
| `class2_insufficient_context_scenario_skeleton.json` | `"CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"` | `null` |

---

### Issue 4: 문서 — Policy Router re-entry 불일치 수정

**수정 파일:** `common/docs/architecture/04_class2_clarification.md`

Section 6 item 3:
- 변경 전: `3. Policy Router re-entry occurs,`
- 변경 후: `3. Deterministic Validator re-entry validates the bounded candidate (Policy Router re-entry is not required when the bounded candidate is explicitly selected through clarification — the Validator is the safety gate for the confirmed candidate),`

**수정 파일:** 시나리오 스켈레톤 (4개 모두)

`class2_clarification_expectation.requires_policy_router_reentry`: `true` → `false`
- `class2_to_class1_low_risk_confirmation_scenario_skeleton.json`
- `class2_to_class0_emergency_confirmation_scenario_skeleton.json`
- `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json`
- `class2_insufficient_context_scenario_skeleton.json`

**수정 파일:** `mac_mini/code/class2_clarification_manager/manager.py` docstring

- 변경 전: `CLASS_1 transition still requires Policy Router re-entry + Validator approval.`
- 변경 후: `CLASS_1 transition requires Deterministic Validator approval on the confirmed bounded candidate (Policy Router re-entry is not required for explicitly selected bounded candidates).`

---

### Issue 5: 논문 문서 — doorbell trigger_event vs environmental_context 구분

**수정 파일:** `common/docs/paper/scenarios/class2_caregiver_confirmation_doorlock_sensitive_scenario_user_story.md`

Section 3에 표 추가:

| 위치 | 의미 | Policy Router 결과 |
|---|---|---|
| `environmental_context.doorbell_detected=true` (+ button trigger) | 방문자 있는 상태에서 사용자 버튼 입력 | **CLASS_1** 가능 |
| `trigger_event.event_type=sensor, event_code=doorbell_detected` | 초인종 자체가 트리거 (C208) | **CLASS_2** → caregiver escalation |

**수정 파일:** `common/docs/paper/scenarios/README.md`

동일 구분 설명 추가.

---

## 추가된 테스트

**`mac_mini/code/tests/test_pipeline_ack_escalation.py`** (7개 추가):
- `TestPublishClass2TransitionResult` (3개): `approved` 필드 포함 snapshot 발행, `not_ready` 필드, `audit_correlation_id` 포함
- `TestDefaultCandidatesTargetHint` (4개): `C1_LIGHTING_ASSISTANCE` target_hint=living_room_light 확인 (insufficient_context, missing_policy_input), OPT_LIVING_ROOM/OPT_BEDROOM action_hint 확인

**`rpi/code/tests/test_rpi_components.py`** (12개 추가):
- `TestTrialStoreRequiresValidatorWhenClass1` (5개): approved 통과, not_ready 실패, flag=False 무시, flag=None 무시, to_dict 포함
- `TestNormalizeExpectedTransitionTarget` (7개): None, 빈문자열, CAREGIVER_CONFIRMATION 매핑, 복합 _OR_, CLASS_1/CLASS_0/SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION pass-through

---

## 주의사항

- `publish_class2_transition_result()`는 background thread에서 fire-and-forget으로 호출됨
- `_match_observation(requires_post_transition_snapshot=True)`를 사용하면 CLASS_1 trial timeout이 `_TRIAL_TIMEOUT_CLASS2_S=360s`로 더 길어짐 (CLASS_1 transition이어도 2-phase wait 전체 대기 가능)
- `_CANONICAL_TRANSITION_TARGETS` 집합이 `_normalize_expected_transition_target()`에서 `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION`의 `_OR_` 오탐을 방지

---

## 다음 세션 권장 작업

1. **end-to-end 실험 재실행** — C1_LIGHTING_ASSISTANCE target_hint 추가 후 CLASS_2→CLASS_1 전이 경로 E2E 검증
2. **`class2_to_class1` 시나리오 step 5 설명 업데이트** — "Policy Router re-entry" 문구 제거 (Validator-only 반영)
3. **transition_outcomes의 `allowed_next_path`** — `class2_to_class1_low_risk_confirmation_scenario_skeleton.json`의 `policy_router_reentry_then_validator_...` → `validator_then_bounded_low_risk_assistance_path`로 수정
