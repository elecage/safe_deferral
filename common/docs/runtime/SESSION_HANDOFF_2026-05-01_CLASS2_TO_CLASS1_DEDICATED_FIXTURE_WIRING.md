# SESSION_HANDOFF — class2_to_class1 Scenario Skeleton Dedicated Fixture Wiring

**Date:** 2026-05-01
**Tests:** 435/435 mac_mini, 128/128 rpi (unchanged — fixture/scenario asset edits only)
**Schema validation:** 15/15 scenario skeletons + new dedicated input fixture validates against policy_router_input_schema; all fixture references resolve

---

## 이번 세션에서 수정한 내용

여러 직전 PR 핸드오프(#80/#81/#82/#83)에서 반복 권장된 **class2_to_class1 시나리오 dedicated fixture 연결** 작업. 직전까지 이 시나리오는 `class2_insufficient_context` 시나리오와 input fixture를 공유했고, expected outcome fixture와 selection fixture는 시나리오 단계에 연결되어 있지 않았다.

### Issue: class2_to_class1 시나리오가 일반 fixture를 공유, expected outcome 미연결

**증상:**
- step 1의 `payload_fixture`가 일반 `sample_policy_router_input_class2_insufficient_context.json`를 사용 → 시나리오 의도(CLASS_2 → CLASS_1 lighting transition)가 fixture 데이터로는 명확히 표현되지 않음. 특히 기존 fixture는 `living_room_light: "on"`이라 light_on dispatch의 narrative와 어긋남.
- step 4 (collect selection)에 fixture 미참조.
- step 5 (validator re-entry)에 expected outcome fixture 미참조.

### 수정

**신규 파일:** `integration/tests/data/sample_policy_router_input_class2_to_class1_low_risk_confirmation.json`

| 필드 | 값 | 의도 |
|---|---|---|
| `trigger_event.event_code` | `double_click` | `recognized_class1_button_event_codes`에 없으므로 PolicyRouter가 CLASS_2 / C206(insufficient_context)으로 라우팅 |
| `environmental_context.illuminance` | `50` | 저조도 → "조명 도움" 의도가 자연스러움 |
| `environmental_context.occupancy_detected` | `true` | 사용자가 거실에 있음 |
| `environmental_context.doorbell_detected` | `false` | C208 visitor 경로 회피 |
| `device_states.living_room_light` | `"off"` | C1_LIGHTING_ASSISTANCE → light_on living_room_light dispatch가 의미 있음 |
| `device_states.bedroom_light` | `"off"` | 동일 |
| temperature/smoke/gas | 정상 | CLASS_0 emergency 회피 |

**수정 파일:** `integration/scenarios/class2_to_class1_low_risk_confirmation_scenario_skeleton.json`

- step 1 `payload_fixture`: 공유 fixture → 신규 dedicated fixture.
- step 4 `payload_fixture` 추가: `integration/tests/data/sample_class2_user_selection_class1.json` (이미 존재). 사용자가 C1_LIGHTING_ASSISTANCE를 선택하는 clarification interaction evidence.
- step 5 `expected_fixture` 추가: `integration/tests/data/expected_class2_transition_class1.json` (이미 존재). validator approval + low-risk catalog 검증 + dispatcher ACK 기대 명세.
- step 1과 step 4 description을 fixture 의도에 맞게 보강 (double_click + low illuminance, C1_LIGHTING_ASSISTANCE 선택 명시).

### 라우팅 검증 (Mac mini PolicyRouter 기준)

신규 fixture가 의도대로 CLASS_2 / C206에 도달하는 경로:
1. Schema 검증 통과 (jsonschema 통과 확인됨).
2. Staleness: `1777200000000 - 1777199999900 = 100ms` < 3000ms → 통과.
3. Emergency 체크: temperature=22°C (E001), event_code=double_click (E002 triple_hit 아님), smoke=false (E003), gas=false (E004), event_type=button (E005 sensor/fall 아님) → 모두 미매칭.
4. C208 visitor: trigger event_type=button ≠ "sensor" → 미매칭.
5. C206 insufficient context: event_type=button + event_code=double_click ∉ {"single_click"} → **매칭** → CLASS_2 / C206.

### Runner 동작 (확인용)

`PackageRunner._match_observation`이 시나리오의 `expected_transition_target=CLASS_1`을 보고 자동으로 `single_click`을 발행 → Pipeline._try_handle_as_user_selection이 첫 후보(C1_LIGHTING_ASSISTANCE) 선택 → `_execute_class2_transition` validator/dispatcher → post-transition observation에 class2 + validation(approved) + ack 모두 채워짐 → `_is_pass`가 `requires_validator_reentry_when_class1=true` 계약(approved + ACK 모두 필요) 통과.

---

## 추가/변경된 테스트 요약

코드 변경 없음, fixture/scenario asset만 수정 → 단위 테스트 추가 없음. 검증은:
- 신규 input fixture가 `policy_router_input_schema.json` 통과
- 모든 시나리오 skeleton(15개)이 `scenario_manifest_schema.json` 통과
- 모든 시나리오의 `payload_fixture` / `expected_fixture` 참조 경로가 실제 파일에 매핑됨 (3개 모두)
- 기존 mac_mini 435/435, rpi 128/128 테스트 회귀 없음

---

## 주의사항

- **`sample_class2_user_selection_class1.json`** (step 4 fixture): 이전 세션의 "Policy Router re-entry → Validator re-entry" 정정에서 이미 `allowed_next_path: "bounded_low_risk_assistance_path"`로 정리된 상태. 추가 수정 불필요.
- **`expected_class2_transition_class1.json`** (step 5 fixture): `expected_validator_required_before_dispatch: true`, `expected_low_risk_catalog_ref` 등 이번 PR의 verdict 강화(approved + ACK)와 일관됨. 추가 수정 불필요.
- **하드웨어 미준비:** 본 세션은 "A안" (fixture 정리 우선)에 따라 진행. 실 하드웨어 E2E 실행은 준비 후 별도 세션에서 진행 권장.

---

## 다음 세션 권장 작업

1. **CLASS_2 → CLASS_1 / CLASS_0 E2E 실험 재실행** (하드웨어 준비 후) — 이번 dedicated fixture 연결 + 누적된 verdict 강화/렌더링 정정 효과를 실 trial로 확인.
2. **(선택) `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json` dedicated input fixture 추가** — Package E doorlock-sensitive 검증 정확도 향상. C208 notification fixture 정렬과 자연스럽게 이어짐.
3. **(선택) `class2_to_class0_emergency_confirmation_scenario_skeleton.json` dedicated input fixture 추가** — CLASS_2→CLASS_0 transition도 같은 패턴으로 정리.
4. **(선택) audit_logger에 `experiment_mode` 기록** — Package A Table 5 trace 편의.
5. **(선택) Package D vacuous-case (`notification_expected_count=0`) 표현 합의** — 0.0 유지 vs 1.0(vacuous true) 결정.
