# integration/scenarios

이 디렉터리는 **deterministic scenario, stress scenario, fault-injection scenario, reproducible evaluation package**를 두는 공간이다.

이 디렉터리의 파일은 canonical policy/schema truth가 아니다. Scenario는 `common/` 아래 frozen policy, frozen schema, MQTT registry, interface matrix를 소비하는 **integration-side evaluation asset**이다.

---

## 목적

이 디렉터리는 다음을 가능하게 해야 한다.

- deterministic scenario replay
- fault-injection case packaging
- expected safe outcome 정의
- reproducible paper-evaluation support
- canonical emergency family `E001`~`E005`와 정합적인 scenario 구성
- `safe_deferral/...` MQTT namespace와 정합적인 scenario 구성
- frozen policy/schema/payload boundary를 변경하지 않는 integration evaluation 구성

---

## 개발자가 먼저 읽어야 하는 문서

JSON skeleton만 보면 의미를 빠르게 파악하기 어려울 수 있으므로, 실제 검토자는 먼저 아래 문서를 보는 것을 권장한다.

- `scenario_review_guide.md`
- `scenario_manifest_rules.md`

이 문서들은 다음을 설명한다.

- 각 scenario가 실제로 무엇을 시험하는지
- 왜 필요한지
- 어떤 결과가 안전한지
- 어떤 결과가 위험 신호인지
- 실제 사용 맥락에서 어떻게 읽어야 하는지
- scenario가 어떤 MQTT topic, policy, schema, fixture boundary를 따라야 하는지

그 다음에 JSON skeleton과 fixture를 보는 것이 자연스럽다.

---

## 현재 반영된 scenario skeleton

현재 다음 skeleton이 반영되어 있다.

- `baseline_scenario_skeleton.json`
- `class0_e001_scenario_skeleton.json`
- `class0_e002_scenario_skeleton.json`
- `class0_e003_scenario_skeleton.json`
- `class0_e004_scenario_skeleton.json`
- `class0_e005_scenario_skeleton.json`
- `class1_baseline_scenario_skeleton.json`
- `class2_insufficient_context_scenario_skeleton.json`
- `stale_fault_scenario_skeleton.json`
- `conflict_fault_scenario_skeleton.json`
- `missing_state_scenario_skeleton.json`

이 파일들은 canonical truth가 아니라 **integration-side scenario assets**다.

주의: 일부 skeleton JSON은 아직 legacy `smarthome/...` topic을 포함할 수 있다. 이는 다음 JSON alignment 단계에서 `safe_deferral/...` namespace로 수정되어야 한다.

---

## skeleton 분류

### Baseline / class-oriented
- `class0_e001_scenario_skeleton.json`
- `class0_e002_scenario_skeleton.json`
- `class0_e003_scenario_skeleton.json`
- `class0_e004_scenario_skeleton.json`
- `class0_e005_scenario_skeleton.json`
- `class1_baseline_scenario_skeleton.json`
- `class2_insufficient_context_scenario_skeleton.json`

### Fault-oriented
- `stale_fault_scenario_skeleton.json`
- `conflict_fault_scenario_skeleton.json`
- `missing_state_scenario_skeleton.json`

### Generic template
- `baseline_scenario_skeleton.json`

---

## 공통 구조 원칙

현재 skeleton들은 가능한 한 공통 필드를 맞추도록 작성되어 있다.

대표 필드:
- `scenario_id`
- `title`
- `description`
- `category`
- `mode`
- `input_plane`
- `preconditions`
- `steps`
- `expected_outcomes`
- `notes`

이 구조는 이후 scenario manifest 규칙이나 loader/unit test 작성 시 공통 골격으로 쓰기 쉽도록 의도한 것이다.

추가 규칙 문서는 아래를 참조한다.

- `scenario_manifest_rules.md`

---

## MQTT topic boundary

Scenario skeleton은 현재 MQTT registry와 interface matrix에 맞춰야 한다.

기본 namespace는 다음이다.

```text
safe_deferral/...
```

ordinary context/input scenario의 기본 ingress topic은 다음이어야 한다.

```text
safe_deferral/context/input
```

Class 0 emergency scenario의 기본 ingress topic은 다음이어야 한다.

```text
safe_deferral/emergency/event
```

단, Class 0 fixture가 아직 `policy_router_input` wrapper 형태인 경우에는 scenario가 다음을 명확히 구분해야 한다.

- emergency event ingress topic: `safe_deferral/emergency/event`
- normalized policy-input bridge, if used: controlled experiment/runtime bridge
- audit observation topic: `safe_deferral/audit/log`

Legacy topic인 다음 값은 신규 scenario 기준으로 사용하지 않는다.

```text
smarthome/context/raw
smarthome/audit/validator_output
```

---

## Class 1 low-risk boundary

현재 Class 1 autonomous low-risk execution은 frozen lighting catalog로 제한된다.

Authoritative reference:

```text
common/policies/low_risk_actions_v1_1_0_FROZEN.json
```

현재 baseline에서 허용되는 autonomous low-risk action은 조명 관련 action으로 제한된다.

Scenario는 다음을 하면 안 된다.

- doorlock을 Class 1 autonomous low-risk action으로 표현
- `door_unlock`을 Class 1 expected action으로 표현
- `front_door_lock`을 Class 1 target device로 표현
- low-risk catalog를 scenario 안에서 확장

Doorlock-sensitive request는 Class 2 escalation 또는 별도 governed manual confirmation path로 해석해야 한다.

---

## `doorbell_detected` boundary

현재 context schema에서 `environmental_context.doorbell_detected`는 required field다.

Scenario fixture가 schema-governed context payload를 참조하는 경우 다음을 지켜야 한다.

- non-visitor scenario에서는 일반적으로 `doorbell_detected=false`
- visitor-response scenario에서는 적절한 경우에만 `doorbell_detected=true`
- `doorbell_detected=true`는 emergency evidence가 아님
- `doorbell_detected=true`는 autonomous door unlock authorization이 아님

---

## LLM invocation boundary

기존 skeleton의 `llm_invocation_allowed`는 coarse legacy-style field로 볼 수 있다.

향후 scenario는 가능하면 다음을 구분해야 한다.

- `llm_decision_invocation_allowed`
- `llm_guidance_generation_allowed`

해석:

- LLM decision/candidate generation은 execution authority가 아니다.
- Class 0 emergency는 LLM을 primary decision path로 사용하면 안 된다.
- safe deferral, clarification, caregiver waiting, ACK result 설명은 policy-constrained guidance generation으로 허용될 수 있다.
- guidance generation 허용은 actuation authorization이 아니다.

---

## 포함 가능한 대상

- normal-context scenarios
- emergency-trigger scenarios
- conflict / stale / missing-state scenarios
- randomized stress metadata
- expected outcome summary files
- scenario manifest or profile files

---

## 경계 원칙

- scenario는 canonical policy truth를 재정의하지 않는다.
- scenario는 frozen assets를 소비하는 evaluation asset이다.
- scenario는 operational hub를 우회하는 control path를 만들지 않는다.
- threshold, required key, trigger semantics는 `common/` frozen assets에서 최종적으로 해석되어야 한다.
- current implemented scope 기준의 low-risk autonomous actuation 범위는 `common/policies/low_risk_actions_v1_1_0_FROZEN.json` 및 `required_experiments.md`와 정렬되어야 한다.
- scenario topic은 `common/mqtt/topic_registry_v1_0_0.json` 및 `common/docs/architecture/15_interface_matrix.md`와 정렬되어야 한다.
- scenario fixture는 current schema boundary를 따르고, `doorbell_detected` required field와 doorlock state boundary를 위반하면 안 된다.

---

## 다음 권장 작업

1. Scenario skeleton JSON의 legacy `smarthome/...` topic을 `safe_deferral/...` namespace로 수정
2. E002~E005 전용 payload fixture 추가 또는 기존 fixture bridge 해석 명확화
3. fixture reference existence verifier 추가
4. scenario topic alignment verifier 추가
5. policy/schema alignment verifier 추가
6. expected outcome comparator와 scenario 연동 adapter 추가
7. 실제 MQTT publish / audit observe adapter 추가
8. class-wise latency profile과 scenario 연결 문서화
