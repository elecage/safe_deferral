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
- Class 2 clarification / transition interaction 검토
- conflict fault, missing-state fault, stale fault의 보수적 처리 검토

---

## 현재 active baseline

Scenario는 아래 active baseline을 소비한다.

```text
Policy baseline:
common/policies/policy_table_v1_2_0_FROZEN.json

Low-risk action catalog:
common/policies/low_risk_actions_v1_1_0_FROZEN.json

Pure context schema:
common/schemas/context_schema_v1_0_0_FROZEN.json

Policy-router input schema:
common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json

Validator output schema:
common/schemas/validator_output_schema_v1_1_0_FROZEN.json

Class 2 notification schema:
common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json

Class 2 clarification interaction schema:
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json

MQTT topic registry:
common/mqtt/topic_registry_v1_0_0.json
```

Historical baseline:

```text
common/policies/policy_table_v1_1_2_FROZEN.json
```

`policy_table_v1_1_2_FROZEN.json`은 Class 2 clarification / transition 의미가 반영된 현재 기준이 아니며, 현재 scenario alignment 기준은 `policy_table_v1_2_0_FROZEN.json`이다.

---

## 개발자가 먼저 읽어야 하는 문서

JSON skeleton만 보면 의미를 빠르게 파악하기 어려울 수 있으므로, 실제 검토자는 먼저 아래 문서를 보는 것을 권장한다.

- `scenario_review_guide.md`
- `scenario_manifest_rules.md`
- `common/docs/architecture/19_class2_clarification_architecture_alignment.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

이 문서들은 다음을 설명한다.

- 각 scenario가 실제로 무엇을 시험하는지
- 왜 필요한지
- 어떤 결과가 안전한지
- 어떤 결과가 위험 신호인지
- 실제 사용 맥락에서 어떻게 읽어야 하는지
- scenario가 어떤 MQTT topic, policy, schema, fixture boundary를 따라야 하는지
- Class 2가 어떻게 후보 제시, 사용자/보호자 확인, Class 0/Class 1/Safe Deferral 전이로 이어지는지

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

---

## skeleton 분류

### Baseline / class-oriented

- `baseline_scenario_skeleton.json`
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

Class 2 clarification / transition scenario는 추가로 다음 필드를 사용할 수 있다.

- `clarification_interaction`
- `transition_outcomes`
- step-level `candidate_choices`
- `expected_outcomes.class2_role`
- `expected_outcomes.candidate_generation_allowed`
- `expected_outcomes.candidate_generation_authorizes_actuation`
- `expected_outcomes.confirmation_required_before_transition`
- `expected_outcomes.allowed_transition_targets`

추가 규칙 문서는 아래를 참조한다.

- `scenario_manifest_rules.md`
- `scenario_manifest_schema.json`

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

Class 2 clarification flow는 현재 별도 topic registry version 없이 기존 topic으로 표현한다.

```text
safe_deferral/context/input
safe_deferral/deferral/request
safe_deferral/escalation/class2
safe_deferral/caregiver/confirmation
safe_deferral/audit/log
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

## Class 0 emergency boundary

Class 0은 생명·안전 관련 즉시 대응 경로다.

Canonical emergency family:

```text
E001 high temperature
E002 triple-hit emergency input
E003 smoke detected
E004 gas detected
E005 fall detected
```

Class 0은 LLM을 primary decision path로 사용하면 안 된다.

Class 2 clarification 중에도 다음 조건이 발생하면 Class 0으로 전이할 수 있다.

```text
- 사용자가 긴급 도움 후보를 명확히 선택함
- 보호자가 emergency path를 확인함
- triple-hit pattern이 발생함
- E001~E005 deterministic emergency evidence가 도착함
```

이 경우에도 LLM은 emergency trigger 권한을 갖지 않는다.

---

## Class 1 low-risk boundary

현재 Class 1 autonomous low-risk execution은 frozen lighting catalog로 제한된다.

Authoritative reference:

```text
common/policies/low_risk_actions_v1_1_0_FROZEN.json
```

현재 baseline에서 허용되는 autonomous low-risk action은 조명 관련 action으로 제한된다.

Class 2 clarification 후에도 사용자가 조명 같은 low-risk assistance 후보를 확인하면 Class 1로 전이할 수 있다. 단, 다음 조건이 필요하다.

```text
- user/caregiver confirmation 존재
- candidate가 low-risk catalog 안에 있음
- Deterministic Validator가 정확히 하나의 admissible action을 승인함
- actuator dispatch 전 validator approval 필요
```

Scenario는 다음을 하면 안 된다.

- doorlock을 Class 1 autonomous low-risk action으로 표현
- `door_unlock`을 Class 1 expected action으로 표현
- `front_door_lock`을 Class 1 target device로 표현
- low-risk catalog를 scenario 안에서 확장

Doorlock-sensitive request는 Class 2 clarification/escalation 또는 별도 governed manual confirmation path로 해석해야 한다.

---

## Class 2 clarification / transition boundary

Class 2는 더 이상 단순 terminal failure 또는 caregiver escalation만을 의미하지 않는다.

현재 기준:

```text
Class 2 = clarification / transition state
```

Class 2는 다음 상황에서 진입할 수 있다.

- insufficient context
- ambiguous user intent
- unresolved candidate conflict
- missing policy input
- stale policy-relevant state
- missing critical state
- actuation ACK timeout
- caregiver-required sensitive path
- no response / timeout after candidate presentation

Class 2에서 허용되는 흐름:

```text
ambiguous or insufficient input
→ bounded candidate choices
→ TTS/display/caregiver prompt
→ user/caregiver selection or deterministic evidence
→ CLASS_1 / CLASS_0 / SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
```

Class 2에서 LLM은 다음을 할 수 있다.

```text
- bounded candidate choice generation
- user-facing guidance text generation
- ambiguity explanation
- waiting-for-confirmation explanation
```

Class 2에서 LLM은 다음을 할 수 없다.

```text
- final class decision
- actuator authorization
- emergency trigger
- sensitive actuation approval
- Policy Router override
- Deterministic Validator bypass
```

---

## Fault scenario boundary

Fault scenario는 단순히 실패를 뜻하지 않는다. 각 fault는 서로 다른 안전 처리 이유를 가진다.

| Fault | 의미 | 안전 처리 |
|---|---|---|
| stale fault | policy-relevant state가 오래되어 신뢰할 수 없음 | safe deferral 또는 Class 2 clarification / caregiver confirmation |
| conflict fault | 여러 후보가 동시에 가능해 임의 선택이 위험함 | 후보 확인 또는 safe deferral |
| missing-state fault | 필요한 상태 보고가 누락됨 | 상태 재확인, safe deferral, caregiver confirmation |

Conflict fault와 missing-state fault는 Class 2-like clarification flow로 이어질 수 있지만, audit과 scenario 설명에서는 원인 구분을 유지해야 한다.

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
- Class 2의 candidate generation은 clarification interaction일 뿐 validator output이나 actuator command가 아니다.

---

## Payload boundary

Class 2 clarification data는 pure context payload가 아니다.

다음은 `pure_context_payload`에 넣지 않는다.

```text
candidate_choices
selection_result
transition_target
timeout_result
LLM-generated prompt text
```

Class 2 clarification interaction payload는 다음 schema를 따른다.

```text
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
```

Class 2 notification payload는 다음 schema를 따른다.

```text
common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json
```

---

## 포함 가능한 대상

- normal-context scenarios
- emergency-trigger scenarios
- Class 2 clarification/transition scenarios
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
- Class 2 clarification interaction은 `common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json`과 `common/policies/policy_table_v1_2_0_FROZEN.json`을 따라야 한다.

---

## 다음 권장 작업

1. Scenario skeleton JSON의 remaining legacy topic / wording 정렬
2. Class 2 candidate prompt / Class 2→Class 1 / Class 2→Class 0 / timeout fixture 추가
3. conflict fault 및 missing-state fault expected fixture 분리
4. fixture reference existence verifier 강화
5. scenario topic alignment verifier 강화
6. policy/schema alignment verifier 추가 보강
7. expected outcome comparator와 scenario 연동 adapter 추가
8. 실제 MQTT publish / audit observe adapter 추가
9. class-wise latency profile과 scenario 연결 문서화
