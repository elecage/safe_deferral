# SESSION_HANDOFF — Experiment Metrics Fixes, Package A Real Branching, Validator-Reentry Doc Alignment

**Date:** 2026-05-01
**Tests:** 427/427 mac_mini, 102/102 rpi (was 414/414, 91/91)
**Schema validation:** 15/15 scenario skeletons + clarification example payload + sample policy-router input

---

## 이번 세션에서 수정한 내용

이번 세션은 사용자가 보고한 실험 패키지/문서 정합성 문제 5건을 일괄 처리했다. 사용자는 또한 직전 핸드오프(`SESSION_HANDOFF_2026-05-01_CLASS2_TRANSITION_HANDLER_AND_TRIAL_VERDICT.md`)의 권장 작업을 우선 기록해 두라고 요청했고, 그중 문서 정정과 겹치는 부분(`class2_to_class1` skeleton)은 함께 처리했다. 나머지 권장 작업은 본 문서 마지막 절에 다시 기록한다.

### Issue 1: Package D `_metrics_d()`가 nested observation 구조를 못 읽음

**증상:**
- Mac mini는 `safe_deferral/dashboard/observation`에 `route.route_class`, `validation.validation_status`, `generated_at_ms`, `route.timestamp_ms`, `class2.transition_target` 같은 nested 구조의 `TelemetrySnapshot`을 발행한다.
- `_metrics_d()`는 flat top-level key (`route_class`, `validation_status`, `snapshot_ts_ms`, `ingest_timestamp_ms`)가 있다고 가정 → 정상적인 CLASS_2 observation도 `payload_completeness_rate=0.0`으로 계산.

**수정 파일:** `rpi/code/experiment_package/trial_store.py`

- `_REQUIRED_C2_PATHS` 튜플 도입: `route.route_class`, `validation.validation_status`, `audit_correlation_id`, `generated_at_ms`, `route.timestamp_ms`, `class2.transition_target`, `class2.unresolved_reason`.
- `_has_path()` 헬퍼 추가 — dot-notation으로 nested dict 안전 접근, None 값도 누락으로 간주.
- `_metrics_d()`가 path 단위로 누락 집계: `missing_by_field`도 path 키로 보고.

**테스트:** `rpi/code/tests/test_rpi_components.py::TestPackageMetricsD` (3개)

---

### Issue 2: Package E/F/G의 `required_metrics`가 실제 산출되지 않음

**증상:**
- `definitions.py`는 E에 `doorlock_safe_deferral_rate`/`unauthorized_doorlock_rate`, F에 `grace_period_cancellation_rate`/`false_dispatch_rate`, G에 `governance_pass_rate`/`topic_drift_detection_rate`를 선언.
- `compute_metrics()`는 E/F를 generic `_metrics_ef`로 묶어 `pass_rate`만 산출, G는 default branch에서 `pass_count`만 반환 → 모든 선언 지표 미계산.

**수정 파일:** `rpi/code/experiment_package/trial_store.py`

- `_metrics_ef()` 제거, `_metrics_e()`, `_metrics_f()`, `_metrics_g()` 신설.
- E: doorlock-sensitive (CLASS_2 expected) trial에서 `doorlock_safe_deferral_rate`(CLASS_2 + non-approved)와 `unauthorized_doorlock_rate`(CLASS_1 + approved) 산출.
- F: `grace_period_cancellation_rate`(CLASS_2 expected & observed CLASS_2 with safe_deferral/rejected_escalation), `false_dispatch_rate`(`_is_unsafe_actuation()` 재사용).
- G: `topic_drift_detection_rate`(FAULT_CONTRACT_DRIFT_01 trials 중 pass), `governance_pass_rate`(전체 pass 비율).
- `compute_metrics()` 디스패치 분기를 E/F/G 각각으로 수정.

**테스트:** `TestPackageMetricsE` (2개), `TestPackageMetricsF` (2개), `TestPackageMetricsG` (2개).

---

### Issue 3: Package A의 `comparison_condition`이 라벨만 기록되고 실제 경로가 안 바뀜

**증상:**
- `definitions.py`는 A에 `["direct_mapping", "rule_only", "llm_assisted"]` 비교 조건을 선언, `required_experiments.md`도 Intent Recovery Comparison(Table 5) 결과를 필수 실험에 포함.
- `PackageRunner`는 `TrialResult.comparison_condition`만 기록하고 Mac mini runtime mode/LLM 사용 여부/라우팅 전략은 전혀 바꾸지 않음 → 모든 condition이 같은 LLM 경로를 통과.

**수정 (canonical schema 추가 포함):**

| 파일 | 변경 |
|---|---|
| `common/schemas/policy_router_input_schema.json` | `routing_metadata.experiment_mode` optional 필드 추가 (enum: `direct_mapping`, `rule_only`, `llm_assisted`). LLM prompt에 노출되지 않으며 Class 0/Class 2 경로에는 영향 없음. |
| `mac_mini/code/policy_router/models.py` | `PolicyRouterResult.experiment_mode: Optional[str] = None` 추가. |
| `mac_mini/code/policy_router/router.py` | `routing_metadata.experiment_mode`를 모든 분기 결과에 통과 (CLASS_0/CLASS_1/CLASS_2 + `_class2()` helper). |
| `mac_mini/code/main.py` | `Pipeline._handle_class1()`이 `experiment_mode`로 분기: `direct_mapping`/`rule_only`는 LLM 호출 우회, `llm_assisted`(또는 None)는 기존 LLM 경로. 두 경로 모두 후속 Validator 게이트는 그대로 통과. |
| `mac_mini/code/main.py` | 모듈 레벨 헬퍼 `_DIRECT_MAPPING_TABLE`, `_direct_mapping_candidate()`, `_rule_only_candidate()` 추가. direct=button event_code → 고정 액션 매핑, rule=환경 컨텍스트(illuminance/occupancy/현재 상태)에 의한 결정론적 규칙. |
| `rpi/code/experiment_package/runner.py` | `trial.comparison_condition`을 `routing_metadata.experiment_mode`로 자동 주입. |

**테스트:** `mac_mini/code/tests/test_policy_router.py::TestExperimentModePassthrough` (5개), `mac_mini/code/tests/test_pipeline_ack_escalation.py::TestIntentRecoveryHelpers` (5개), `TestHandleClass1ExperimentMode` (3개), `rpi/code/tests/test_rpi_components.py::TestExperimentModePropagation` (1개).

**경계 유지:**
- `experiment_mode`는 `routing_metadata` 필드. `pure_context_payload`에는 들어가지 않음 → LLM prompt에는 노출되지 않음.
- 모든 경로(direct/rule/llm)는 동일한 `DeterministicValidator` 게이트를 통과. validator authority bypass 없음.
- Class 0 emergency 라우팅은 `experiment_mode`와 무관하게 결정론적으로 유지.
- 잘못된 enum 값은 `policy_router_input_schema` 검증 실패 → C202 CLASS_2.

---

### Issue 4: Package C의 `topic_drift_detection_rate` 누락

**증상:**
- `required_experiments.md` §7.6은 Package C 필수 지표에 `Topic/Payload Drift Detection Rate` 포함, deterministic fault table에도 `FAULT_CONTRACT_DRIFT_01` 존재.
- 코드의 Package C `recommended_fault_profiles`에 `FAULT_CONTRACT_DRIFT_01`은 들어 있으나 `_metrics_c()`와 `required_metrics`에는 명시 산출 없음.

**수정 파일:** `rpi/code/experiment_package/trial_store.py`, `rpi/code/experiment_package/definitions.py`

- `_metrics_c()`에 `topic_drift_detection_rate` 추가 (FAULT_CONTRACT_DRIFT_01 trials 중 pass 비율).
- `definitions.py`의 Package C `required_metrics`에 `topic_drift_detection_rate` 추가.

**테스트:** `TestPackageMetricsCDriftRate` (1개).

---

### Issue 5: 일부 문서가 여전히 "Policy Router re-entry"를 필수로 기술

**증상:**
- 직전 세션에서 `_execute_class2_transition()`은 Policy Router 재호출 없이 `DeterministicValidator.validate()`를 직접 호출하도록 정리됨 (main.py:769-845).
- 그러나 다수의 시나리오·MQTT·아키텍처·페이퍼 문서가 여전히 "Policy Router re-entry"를 Class 2 → Class 1 전이 필수 단계로 기술.
- 이전 핸드오프 문구상 04 문서는 이미 정리됐다고 했으나 실제로는 §3, §6에 잔존.

**수정한 active 문서 (전부):**

| 파일 | 변경 요지 |
|---|---|
| `common/docs/architecture/04_class2_clarification.md` | §3 "Policy Router re-entry when appropriate" → "Deterministic Validator re-entry on the confirmed bounded candidate when the selected transition is Class 1". §6 단계3 재기술. |
| `common/docs/architecture/03_payload_and_mqtt_contracts.md` | clarification 토픽 설명을 "confirmed-candidate evidence; Class 1 selections re-enter the Deterministic Validator with the bounded candidate"로. |
| `common/mqtt/topic_payload_contracts.md` | 동일 정정. |
| `common/mqtt/publisher_subscriber_matrix.md` | 동일 정정. |
| `common/mqtt/topic_registry.json` | clarification topic `notes` 정정. |
| `common/payloads/examples/clarification_interaction_two_options_pending.json` | `allowed_next_path` → `validator_reentry_with_confirmed_candidate`. notes 정정. |
| `integration/scenarios/README.md` | 토픽 해석 규칙, Class 2 transition 경계, allowed flow diagram, recommended `class2_clarification_expectation` 블록 모두 정정. |
| `integration/scenarios/scenario_manifest_schema.json` | `requires_policy_router_reentry` → `requires_validator_reentry_when_class1` (rename, additionalProperties:true 블록이라 호환). |
| `integration/scenarios/scenario_manifest_rules.md` | 동일 rename. |
| `integration/scenarios/docs/scenario_review_class2.md` | Class 2 flow 다이어그램, transition rules, review checklist, Class 2→Class 1/Class 0 must-verify 모두 정정. |
| `integration/scenarios/docs/scenario_review_class0_class1.md` | Class 2 → Class 1 조건 기술 정정. |
| `integration/scenarios/docs/scenario_review_faults.md` | fault checklist 항목 rename. |
| `integration/scenarios/class2_insufficient_context_scenario_skeleton.json` | step 6/7 description, expectation 필드 rename, transition_outcomes `allowed_next_path`, notes. |
| `integration/scenarios/class2_to_class1_low_risk_confirmation_scenario_skeleton.json` | description, step 5/6 action rename, expectation 필드 rename, transition_outcomes. |
| `integration/scenarios/class2_to_class0_emergency_confirmation_scenario_skeleton.json` | step 5/6 description, expectation 필드 rename, allowed_next_path. |
| `integration/scenarios/class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json` | expectation 필드 rename. |
| `integration/scenarios/class2_timeout_no_response_safe_deferral_scenario_skeleton.json` | expectation 필드 rename. |
| `integration/scenarios/stale_fault_scenario_skeleton.json` | expectation 필드 rename. |
| `integration/scenarios/conflict_fault_scenario_skeleton.json` | expectation 필드 rename. |
| `integration/scenarios/missing_state_scenario_skeleton.json` | expectation 필드 rename. |
| `common/payloads/templates/scenario_fixture_template.json` | 템플릿 필드 rename. |
| `common/docs/paper/scenarios/class2_to_class1_low_risk_confirmation_scenario_user_story.md` | §1, §3, §4 표, §5 표, §6.6/6.8, §7, §8 모두 정정. |
| `common/docs/paper/scenarios/class2_to_class0_emergency_confirmation_scenario_user_story.md` | §3, §4 표, §5 표, §6.5/6.6, §7 정정. |
| `mac_mini/code/safe_deferral_handler/handler.py` | 모듈 docstring 정정 (CLASS_1 transition은 Validator 재진입). |
| `mac_mini/code/class2_clarification_manager/manager.py` | 모듈 docstring 정정 (동일). |

**의도적으로 유지한 표현 (모두 "Policy Router 재호출이 필요 없다"는 정정 컨텍스트):**

- `mac_mini/code/main.py:788` — `_execute_class2_transition` docstring "Policy Router re-entry is not needed".
- `common/docs/architecture/12_prompts_mac_mini_components.md:144` — "Policy Router re-entry is not required when candidate is...".
- `integration/scenarios/scenario_manifest_schema.json:235` — 새 필드 description 안에서 legacy 이름 언급.

---

## 추가된 테스트 요약

| 테스트 클래스 | 위치 | 개수 |
|---|---|---|
| `TestPackageMetricsD` | `rpi/code/tests/test_rpi_components.py` | 3 |
| `TestPackageMetricsE` | `rpi/code/tests/test_rpi_components.py` | 2 |
| `TestPackageMetricsF` | `rpi/code/tests/test_rpi_components.py` | 2 |
| `TestPackageMetricsG` | `rpi/code/tests/test_rpi_components.py` | 2 |
| `TestPackageMetricsCDriftRate` | `rpi/code/tests/test_rpi_components.py` | 1 |
| `TestExperimentModePropagation` | `rpi/code/tests/test_rpi_components.py` | 1 |
| `TestExperimentModePassthrough` | `mac_mini/code/tests/test_policy_router.py` | 5 |
| `TestIntentRecoveryHelpers` | `mac_mini/code/tests/test_pipeline_ack_escalation.py` | 5 |
| `TestHandleClass1ExperimentMode` | `mac_mini/code/tests/test_pipeline_ack_escalation.py` | 3 |

총 +24 테스트 추가, mac_mini 414→427, rpi 91→102. 모두 통과.

---

## 주의사항

- **canonical schema 편집 정당화:** `policy_router_input_schema.json`에 `experiment_mode` (optional) 필드를 추가했다. 이는 `additionalProperties: false`인 `routing_metadata` 블록의 정합성을 유지하면서 Package A 비교 실험을 실제로 수행 가능하게 만들기 위한 최소 변경이다. 기존 fixture는 이 필드가 없어도 그대로 검증 통과한다.
- **scenario_manifest_schema 필드 rename:** `requires_policy_router_reentry` → `requires_validator_reentry_when_class1`. 어떠한 Python 코드도 이 필드를 읽지 않는다 (verifier 부재). 모든 scenario skeleton을 동시에 rename 했고 jsonschema 검증 15/15 통과.
- **direct_mapping/rule_only 베이스라인은 의도적으로 단순:** `direct_mapping`은 button event_code → 고정 (action, target) 매핑, `rule_only`은 illuminance<200 + occupancy + 현재 living_room_light=off일 때만 light_on 제안. 모두 바깥 catalog는 시도하지 않으며 validator gate는 동일.
- **TelemetryAdapter는 변경 없음.** `_handle_class1`이 LLM 우회 경로일 때 `publish_llm_candidate()`를 호출하지 않으므로, direct/rule trial에서는 `safe_deferral/llm/candidate_action` 토픽이 비어 있다. dashboard observation의 `route`/`validation`/`class2` 블록은 그대로 채워진다.
- **`audit_logger`에 `experiment_mode` 기록 없음:** 본 세션에서는 추가하지 않았다. 필요 시 후속 작업에서 audit 메타에 기입 가능 (canonical audit schema 수정 필요).

---

## 다음 세션 권장 작업 (직전 핸드오프 + 본 세션에서 미처리)

1. **CLASS_1 후보 `target_hint` 추가** — `class2_clarification_manager/manager.py`의 `_DEFAULT_CANDIDATES`에서 `C1_LIGHTING_ASSISTANCE`에 `"target_hint": "living_room_light"` 추가 (또는 context 기반 동적 설정). 현재는 `target_hint=None`이라 `is_class1_ready=False` → CLASS_2→CLASS_1 디스패치가 실제로 일어나지 않는다.
2. **CLASS_2 → CLASS_1 전이 포함 E2E 실험 재실행** — 위 (1) 적용 후. `_metrics_d` nested 수정으로 이번 라운드부터는 정상적인 CLASS_2 observation이 `payload_completeness_rate=1.0`으로 집계된다.
3. **`class2_to_class1_low_risk_confirmation_scenario_skeleton.json`을 dedicated input/expected fixture와 연결** — 현재는 `sample_policy_router_input_class2_insufficient_context.json`을 공유 사용 중. 별도 입력 fixture와 `expected_class2_transition_class1.json` 연동.
4. **(선택) Package A 결과 분석 시 audit_logger에 `experiment_mode` 기록 추가** — Table 5 분석 편의를 위해.
5. **(선택) Package E doorlock 시나리오 fixture 보강** — `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json` 전용 input fixture 추가.
