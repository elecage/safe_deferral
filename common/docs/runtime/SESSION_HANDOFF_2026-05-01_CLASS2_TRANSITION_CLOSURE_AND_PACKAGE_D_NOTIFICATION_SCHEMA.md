# SESSION_HANDOFF — CLASS_2 Transition Closure, Auto-Drive, Validator Re-entry Verdict, Package D Notification-Schema Switch

**Date:** 2026-05-01
**Tests:** 429/429 mac_mini, 112/112 rpi (was 427/427, 102/102; +2 mac_mini, +10 rpi)
**Schema validation:** 15/15 scenario skeletons + clarification example payload still pass

---

## 이번 세션에서 수정한 내용

이번 세션은 사용자가 보고한 5개 follow-up 이슈를 처리했고, 그중 일부는 `SESSION_HANDOFF_2026-05-01_EXPERIMENT_METRICS_AND_VALIDATOR_REENTRY_DOC_ALIGNMENT.md`에 기록했던 권장 작업과 그대로 겹쳐서 함께 처리했다.

### Issue 1: CLASS_2→CLASS_1 기본 후보가 target_hint 없이 남아 dispatch 불가

**(직전 세션 권장 작업 #1과 동일)**

**증상:** `_DEFAULT_CANDIDATES["insufficient_context"]`/`["missing_policy_input"]`의 `C1_LIGHTING_ASSISTANCE`는 `action_hint="light_on"`이지만 `target_hint=None`. 따라서 `_execute_class2_transition()`이 `is_class1_ready=False`로 분기해 validator/dispatcher를 호출하지 않음.

**수정 파일:** `mac_mini/code/class2_clarification_manager/manager.py`

- 두 후보 세트의 `C1_LIGHTING_ASSISTANCE.target_hint`를 `"living_room_light"`로 설정 (canonical low-risk catalog 내 안전 기본값).
- 거실 vs 침실 모호성은 별도 `_DEFAULT_CANDIDATES["unresolved_context_conflict"]`의 `OPT_LIVING_ROOM`/`OPT_BEDROOM` 후보가 처리.

### Issue 2: `requires_validator_reentry_when_class1`가 runner/verdict에서 무시됨

**증상:** 직전 세션에서 scenario 필드를 `requires_policy_router_reentry` → `requires_validator_reentry_when_class1`로 rename했지만, `TrialResult`/`PackageRunner`는 이 필드를 저장조차 하지 않았고 `_is_pass()`도 검증하지 않았다.

**수정 파일:** `rpi/code/experiment_package/trial_store.py`, `rpi/code/experiment_package/runner.py`

- `TrialResult`에 `requires_validator_reentry_when_class1: bool = False` 필드 추가 + `to_dict()` 포함.
- `TrialStore.create_trial()` signature 확장.
- `PackageRunner.start_trial_async()`가 scenario의 `class2_clarification_expectation.requires_validator_reentry_when_class1`을 로드.
- `_is_pass()` CLASS_2 블록 재구조화:
  - `expected_transition_target=CLASS_1` + `requires_validator_reentry_when_class1=True` → 관측에 `validation.validation_status` 필요.
  - `expected_transition_target=CLASS_0` → 관측에 `escalation.escalation_status` 필요 (Issue #4 검증 보장).
  - 그 외(safe deferral) → 종전대로 `obs_val == "approved"` 차단 검사.

### Issue 3: CLASS_2→CLASS_1/CLASS_0 시나리오가 입력 자동 구동 미수행

**(직전 세션 권장 작업 #2와 동일 — E2E 재실행 선결조건)**

**증상:** `PackageRunner._match_observation()`이 passive wait만 수행해서, 사용자 선택 또는 응급 확인 없이 CLASS_2가 CLASS_1/CLASS_0로 전이되지 않음. `_simulate_class2_button` 헬퍼는 존재하지만 호출되지 않음.

**수정 파일:** `rpi/code/experiment_package/runner.py`

- `_simulate_class2_button(node, correlation_id, event_code="single_click")`로 매개변수화.
- `_match_observation()` signature 확장: `trial`, `node` 받음. 초기 CLASS_2 routing snapshot이 도착하면 (그러나 `class2` block이 아직 없으면) 자동 selection 주입:
  - `expected_transition_target=CLASS_1` → `single_click` 발행 (Pipeline._try_handle_as_user_selection 매핑상 첫 후보 = `C1_LIGHTING_ASSISTANCE`).
  - `expected_transition_target=CLASS_0` → `triple_hit` 발행 (첫 CLASS_0-targeted 후보).
  - `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION` → 자동 구동 안 함 (timeout/caregiver Telegram 경로를 그대로 검증).
- 종료 조건도 강화:
  - CLASS_1 expected → `class2 + validation` 둘 다 도착해야 final.
  - CLASS_0 expected → `class2 + escalation` 둘 다 도착해야 final.
- `start_trial_async()`에 `expected_transition_target_override: Optional[str]` 파라미터 추가 (테스트와 fixture 미사용 호출자 지원).

### Issue 4: CLASS_2→CLASS_0 emergency 후속 escalation evidence가 observation으로 안 닫힘

**증상:** `_execute_class2_transition`의 CLASS_0 분기는 `update_escalation()`만 호출하고 `publish()`는 안 했음. 따라서 dashboard/observation 상에 escalation_status가 절대 안 실리고, runner도 기다리지 않았음.

**수정 파일:** `mac_mini/code/telemetry_adapter/adapter.py`, `mac_mini/code/main.py`

- `TelemetryAdapter.publish_class2_to_class1_outcome(audit_correlation_id, class2_result, val_result, dispatch_record=None)` 신설: 격리 스냅샷 (route + class2 + validation + ack)를 dashboard/observation에 발행. 백그라운드 스레드에서 호출 안전.
- `TelemetryAdapter.publish_class2_to_class0_outcome(audit_correlation_id, class2_result, esc_result, trigger_id)` 신설: 격리 스냅샷 (route + class2 + escalation)을 dashboard/observation에 발행.
- `Pipeline._execute_class2_transition()`이 두 분기 모두 끝에서 해당 outcome publish 호출.

### Issue 5: Package D가 dashboard observation completeness를 측정함 (notification payload 아님)

**증상:** `required_experiments.md` §8.5는 Package D가 caregiver notification payload를 `class2_notification_payload_schema.json` 기준으로 검증한다고 명시. 그러나 `_metrics_d`는 `safe_deferral/dashboard/observation`의 nested 경로(route.route_class, validation.validation_status, class2.* 등)를 검사하고 있었음. 측정 대상이 다름.

**수정:**

- 새 파일 `rpi/code/notification_store.py` — `safe_deferral/escalation/class2` 토픽의 caregiver notification payload 링버퍼 (ObservationStore와 동일 패턴, `find_by_correlation_id` 지원).
- `rpi/code/main.py` — `_MONITOR_TOPICS`에 `safe_deferral/escalation/class2` 추가, `NotificationStore` 인스턴스 생성, 메시지 디스패치 분기 추가, `PackageRunner` 생성자에 전달.
- `rpi/code/experiment_package/runner.py` — `__init__`에 `notification_store=None` 파라미터 추가, `_run_trial`이 trial 완료 시 `notification_store.find_by_correlation_id(correlation_id)`로 notification을 조회해 `complete_trial(..., notification_payload=notif)`에 전달.
- `rpi/code/experiment_package/trial_store.py`:
  - `TrialResult.notification_payload: Optional[dict]` 추가.
  - `complete_trial()`/`timeout_trial()` signature 확장.
  - `_metrics_d()` 전면 재작성: `class2_notification_payload_schema.json`을 lazy-load한 jsonschema validator로 trial별 notification payload를 검증. 보고 metric:
    - `payload_completeness_rate`: 필수 4개 필드 모두 비어있지 않고 schema 위반도 없는 trial 비율.
    - `missing_field_rate`: 필수 필드 누락 비율.
    - `missing_by_field`: `event_summary`/`context_summary`/`unresolved_reason`/`manual_confirmation_path`별 누락 카운트.
    - `no_notification_count`: notification이 아예 안 온 CLASS_2 trial 수.
    - `schema_violation_count`: 필수는 채워졌으나 스키마 위반(예: additionalProperties)이 있는 trial 수.

---

## 추가/수정된 테스트 요약

| 파일 | 클래스 | 개수 | 비고 |
|---|---|---|---|
| `rpi/code/tests/test_rpi_components.py` | `TestPackageMetricsD` (재작성) | 4 | notification 기반 검증 (이전 dashboard observation 기반 3개 대체) |
| `rpi/code/tests/test_rpi_components.py` | `TestClass2SelectionAutoDrive` | 3 | single_click/triple_hit 자동 주입, SAFE_DEFERRAL은 미주입 |
| `rpi/code/tests/test_rpi_components.py` | `TestRequiresValidatorReentry` | 4 | flag=True 시 validation 필요, CLASS_0은 escalation 필요 |
| `rpi/code/tests/test_rpi_components.py` | `TestNotificationStore` | 2 | 기본 ring-buffer + most-recent 매칭 |
| `rpi/code/tests/test_rpi_components.py` | `TestTrialStoreTransitionTarget` (헬퍼 갱신) | 0 (재구조화) | `_complete_with_target`이 transition별로 validation/escalation block 자동 추가 |
| `mac_mini/code/tests/test_pipeline_ack_escalation.py` | `TestPostTransitionOutcomePublish` | 2 | CLASS_1 outcome=class2+validation, CLASS_0 outcome=class2+escalation |

총 mac_mini +2, rpi +10 (재작성 1 net 포함). mac_mini 427→429, rpi 102→112. 모두 통과.

---

## 주의사항

- **canonical schema 변경 없음.** `class2_notification_payload_schema.json`은 그대로 사용. `policy_router_input_schema.json`도 그대로 (이전 세션의 `experiment_mode` 추가는 유지).
- **Mac mini→RPi 신규 토픽 dependency:** RPi가 이제 `safe_deferral/escalation/class2`를 구독한다. Mac mini가 이미 이 토픽에 publish 중이므로(`caregiver_escalation/backend.py:119`) 추가 작업 불필요.
- **Auto-drive timing:** `_CLASS2_SELECTION_DRIVE_DELAY_S = 0.5`로 publish 후 selection 주입 전 짧은 대기. Pipeline가 CLASS_2 세션을 등록하기 전 selection이 도착하면 무시되므로 약간의 여유가 필요. 실 환경 latency가 더 길면 이 값을 늘릴 것.
- **CLASS_2 verdict 강화의 영향:** 기존에는 CLASS_2 trial이 단순히 `class2` block 존재만 확인했다. 이제는:
  - `expected_transition_target=CLASS_1` + `requires_validator_reentry_when_class1=True` → validation 블록도 필요. scenario에서 flag가 true이고 transition이 CLASS_1이면 더 엄격한 검증.
  - `expected_transition_target=CLASS_0` → 항상 escalation 블록 필요. 기존 dashboard obs 패턴이 escalation 없이 닫혔다면 fail. 새 `publish_class2_to_class0_outcome`가 escalation을 항상 채워주므로 정상 흐름은 통과.
- **Package D 측정 대상 전환:** 이전 dashboard-based 측정과 결과가 다르게 나올 수 있음. notification이 발행되지 않은 CLASS_2 trial은 `no_notification_count`로 별도 보고. 운영 환경에서 escalation 토픽 publish가 누락되면 즉시 0% completeness로 표시됨.

---

## 다음 세션 권장 작업

1. **CLASS_2→CLASS_1 E2E 실험 재실행** — target_hint 적용 + auto-drive + post-transition publish + validator re-entry verdict가 모두 자리 잡았으므로 실 환경에서 통과 여부 확인.
2. **CLASS_2→CLASS_0 E2E 실험 재실행** — triple_hit auto-drive와 escalation outcome publish가 결합된 첫 사이클.
3. **Package D 결과 검증** — 실제 caregiver notification payload가 `class2_notification_payload_schema`를 통과하는지 운영 trial 결과로 확인 (특히 `notification_channel` enum 일치).
4. **`class2_to_class1_low_risk_confirmation_scenario_skeleton.json` dedicated fixture 연결** — 직전 세션에서도 권장됨. 현재는 `sample_policy_router_input_class2_insufficient_context.json`을 공유 사용 중.
5. **(선택) `class2_caregiver_confirmation_doorlock_sensitive` scenario fixture 보강** — Package E 도어락 검증 정확도 향상.
6. **(선택) audit_logger에 `experiment_mode` 기록** — Package A 결과 분석 시 Table 5 결과 trace 편의를 위해.
