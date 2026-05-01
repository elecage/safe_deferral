# SESSION_HANDOFF — Doorlock-Sensitive and CLASS_2→CLASS_0 Scenario Skeletons Dedicated Fixture Wiring

**Date:** 2026-05-01
**Tests:** 435/435 mac_mini, 128/128 rpi (unchanged — fixture/scenario asset edits only)
**Schema validation:** 15/15 scenario skeletons + 2 new dedicated input fixtures pass; all `payload_fixture` / `expected_fixture` references resolve

---

## 이번 세션에서 수정한 내용

직전 PR #84의 `class2_to_class1` dedicated fixture 패턴을 sibling 시나리오 두 개에 동일하게 적용. 이전 권장작업 목록의 "선택" 항목 두 건을 함께 처리.

### Issue 1: `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json` dedicated fixture 미연결

**증상:**
- step 1의 `payload_fixture`가 `common/payloads/examples/policy_router_input_visitor_doorbell.json`(generic example)을 사용 — 시나리오 의도(C208 doorlock-sensitive caregiver confirmation)와 audit_correlation_id 트레이싱이 분리.
- step 5 (collect_caregiver_confirmation)에 `expected_fixture` 미연결 → caregiver/lighting 후보 차단·notification 검증 등 핵심 안전 invariant이 시나리오 자산으로 표현되지 않음.

**수정:**

신규 파일 `integration/tests/data/sample_policy_router_input_class2_caregiver_confirmation_doorlock_sensitive.json`:

| 필드 | 값 | 의도 |
|---|---|---|
| `trigger_event.event_type` / `event_code` | `sensor` / `doorbell_detected` | PolicyRouter의 C208 visitor-context 분기로 직행 |
| `environmental_context.doorbell_detected` | `true` | visitor-response context |
| `device_states.living_room_blind` | `closed` | 방문자 도착 narrative와 정합 |
| `audit_correlation_id` | `sample_class2_caregiver_doorlock_sensitive_001` | 시나리오 전용 트레이스 ID |
| smoke/gas/triple_hit | 정상 | CLASS_0 emergency 회피, 순수 visitor → C208 경로 보장 |

신규 파일 `integration/tests/data/expected_class2_caregiver_confirmation_doorlock_sensitive.json` — 다음 invariant을 명시적으로 캡처:
- `expected_route_trigger_id="C208"`
- `expected_unresolved_reason="caregiver_required_sensitive_path"`
- `expected_first_candidate_id="C2_CAREGIVER_HELP"` (lighting candidate가 첫 후보로 등장하면 즉시 위반)
- `expected_lighting_candidate_blocked=true`
- `expected_caregiver_notification_published=true` + `expected_exception_trigger_id="C208"` (직전 PR #81의 schema enum + omission 일관성)
- `expected_doorbell_detected_authorizes_unlock=false`
- `expected_caregiver_confirmation_equals_validator_approval=false`

skeleton 업데이트:
- step 1 `payload_fixture` → 신규 dedicated input fixture.
- step 3/4 description에 `safe_deferral/escalation/class2`와 `exception_trigger_id=C208` 명시 (이미 fixture는 정렬됨, 표현만 보강).
- step 5에 `expected_fixture` 추가.

### Issue 2: `class2_to_class0_emergency_confirmation_scenario_skeleton.json` dedicated fixture 미연결

**증상:**
- step 1의 `payload_fixture`가 공유 `sample_policy_router_input_class2_insufficient_context.json`을 사용 — 시나리오별 audit_correlation_id 분리 안 됨.
- step 4 (collect_emergency_confirmation)에 fixture 미참조.
- step 5 (transition_to_class0)에 `expected_fixture` 미연결.

**수정:**

신규 파일 `integration/tests/data/sample_policy_router_input_class2_to_class0_emergency_confirmation.json`:
- `event_type=button`, `event_code=double_click` → C206 insufficient_context로 진입 (Class 2 clarification 도달).
- 정상 환경 컨텍스트(temperature 24°C, illuminance 200, smoke/gas/doorbell 모두 false) → CLASS_0 자동 라우팅 회피. CLASS_0 전이는 step 4의 `triple_hit` auto-drive 또는 emergency 후보 선택으로 닫힘.
- `audit_correlation_id`: `sample_class2_to_class0_emergency_confirmation_001` (시나리오 전용 트레이스).

skeleton 업데이트:
- step 1 `payload_fixture` → 신규 dedicated input fixture.
- step 4 `payload_fixture` → 기존 `sample_class2_user_selection_class0.json` (사용자가 C3_EMERGENCY_HELP 선택). description에 runner의 `triple_hit` auto-drive 동작도 명시.
- step 5 `expected_fixture` → 기존 `expected_class2_transition_class0.json`. description에 "post-transition observation must carry the escalation block" 추가 (PR #81의 verdict 강화 결과 명시화).

---

## 추가/변경된 파일 요약

| 파일 | 변경 |
|---|---|
| `integration/tests/data/sample_policy_router_input_class2_caregiver_confirmation_doorlock_sensitive.json` | 신규 (C208 dedicated input) |
| `integration/tests/data/expected_class2_caregiver_confirmation_doorlock_sensitive.json` | 신규 (doorlock-sensitive expected outcome) |
| `integration/tests/data/sample_policy_router_input_class2_to_class0_emergency_confirmation.json` | 신규 (C206→C0 dedicated input) |
| `integration/scenarios/class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json` | step 1 dedicated fixture, step 3/4 description 보강, step 5 expected_fixture 추가 |
| `integration/scenarios/class2_to_class0_emergency_confirmation_scenario_skeleton.json` | step 1 dedicated fixture, step 4 selection fixture, step 5 expected_fixture 추가 |

코드 변경 없음 → 단위 테스트 추가 없음. 검증:
- 신규 input fixture 2개 모두 `policy_router_input_schema.json` 통과.
- 신규 expected fixture는 manifest schema 외부 자유형 JSON (제약 없음).
- 모든 시나리오 skeleton 15/15 schema 통과.
- 모든 시나리오의 `payload_fixture`/`expected_fixture` 참조 경로가 실제 파일에 매핑됨.
- mac_mini 435/435, rpi 128/128 회귀 없음.

---

## 주의사항

- **Doorlock 시나리오 verdict 동작:** `expected_transition_target=CAREGIVER_CONFIRMATION` → `_expected_transition_targets()`에 의해 `{SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION}`으로 canonicalize. Runner는 단일 CLASS_1/CLASS_0 기대일 때만 auto-drive하므로 이 시나리오는 자동 selection 없이 caregiver Telegram 또는 timeout(360s) 까지 대기. 실 환경에서는 caregiver 응답이 시간 내 도착해야 하며, 응답 없으면 safe_deferral로 자연 종료.
- **CLASS_2→CLASS_0 시나리오 verdict 동작:** `expected_transition_target=CLASS_0` → 단일 CLASS_0 → runner가 `triple_hit` auto-drive → Pipeline._try_handle_as_user_selection이 첫 CLASS_0-targeted 후보(C3_EMERGENCY_HELP) 선택 → `_execute_class2_transition` CLASS_0 분기가 announce_emergency + send_notification + `publish_class2_to_class0_outcome`(escalation 블록 포함) 실행 → `_is_pass`가 `escalation.escalation_status` 존재 검증.
- **doorlock notification fixture와의 일관성:** 직전 PR #82에서 `class_2_notification_doorlock_sensitive.json`을 C208 + class2_clarification_manager로 정렬한 효과가 이번 expected fixture(`expected_exception_trigger_id="C208"`)와 직접 정합.

---

## 다음 세션 권장 작업

1. **CLASS_2 → CLASS_1 / CLASS_0 / Caregiver-confirmation E2E 실험 재실행** (하드웨어 준비 후) — 누적된 verdict 강화/dashboard 정정/dedicated fixture 정리 효과를 실 trial로 검증. 본 세션으로 fixture-side 정리는 사실상 마무리.
2. **(선택) `class2_timeout_no_response_safe_deferral_scenario_skeleton.json`도 같은 패턴으로 정리** — 현재 `payload_fixture`는 별도 timeout sample을 사용 중인지 확인 후 필요 시 dedicated 정리.
3. **(선택) `audit_logger`에 `experiment_mode` 기록** — Package A Table 5 trace 편의.
4. **(선택) Package D vacuous-case (`notification_expected_count=0`) 표현 합의** — 0.0 유지 vs 1.0(vacuous true) 결정.
