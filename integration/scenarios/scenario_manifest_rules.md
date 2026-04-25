# scenario_manifest_rules.md

이 문서는 `integration/scenarios/` 아래의 scenario JSON 파일이 따라야 하는 **공통 manifest 규칙**을 정의한다.

이 문서는 canonical policy truth를 재정의하지 않는다.  
정책/스키마/용어의 authoritative baseline은 `common/`의 frozen assets에 남는다.

---

## 1. 목적

scenario manifest 규칙은 다음을 위해 필요하다.

- scenario 파일 형식 일관성 확보
- scenario loader / comparator / test runner 작성 용이성 확보
- deterministic scenario와 fault scenario의 공통 구조 정리
- measurement profile과의 연결 용이성 확보
- reproducible evaluation package 구성 용이성 확보
- MQTT topic registry 및 interface matrix와의 정합성 확보
- frozen policy/schema/payload boundary를 침범하지 않는 scenario 구성
- Class 2 clarification / transition structure의 machine-readable 표현

즉, 이 문서는 **scenario JSON의 공통 메타구조**를 정의한다.

---

## 2. 기본 원칙

- scenario는 canonical truth가 아니다.
- scenario는 frozen assets를 소비하는 evaluation asset이다.
- scenario는 operational hub를 우회하는 제어 경로를 만들면 안 된다.
- threshold, required key, trigger predicate, routing truth를 scenario가 최종 정의하면 안 된다.
- scenario는 가능한 한 machine-readable 하면서도 사람이 읽기 쉬워야 한다.
- scenario topic은 `common/mqtt/topic_registry_v1_0_0.json` 및 `common/docs/architecture/15_interface_matrix.md`와 정렬되어야 한다.
- scenario fixture는 current schema boundary를 따라야 한다.
- scenario는 Class 1 autonomous low-risk scope를 frozen lighting catalog 밖으로 확장하면 안 된다.
- scenario는 doorlock-sensitive behavior를 autonomous Class 1 execution으로 표현하면 안 된다.
- Class 2 scenario는 terminal failure만 표현하면 안 되며, clarification / transition structure를 명시해야 한다.
- Class 2 candidate choices는 validator output, actuator command, emergency trigger, doorlock authorization이 아니다.

---

## 3. Current active baseline

Scenario manifest는 아래 active baseline과 정합적이어야 한다.

```text
Active policy baseline:
common/policies/policy_table_v1_2_0_FROZEN.json

Low-risk action catalog:
common/policies/low_risk_actions_v1_1_0_FROZEN.json

Fault injection rules:
common/policies/fault_injection_rules_v1_4_0_FROZEN.json

Pure context schema:
common/schemas/context_schema_v1_0_0_FROZEN.json

Policy router input schema:
common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json

Candidate action schema:
common/schemas/candidate_action_schema_v1_0_0_FROZEN.json

Validator output schema:
common/schemas/validator_output_schema_v1_1_0_FROZEN.json

Class 2 notification schema:
common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json

Class 2 clarification interaction schema:
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json

MQTT topic registry:
common/mqtt/topic_registry_v1_0_0.json

Interface matrix:
common/docs/architecture/15_interface_matrix.md

Payload registry:
common/docs/architecture/17_payload_contract_and_registry.md

Class 2 architecture alignment:
common/docs/architecture/19_class2_clarification_architecture_alignment.md
```

Historical baseline:

```text
common/policies/policy_table_v1_1_2_FROZEN.json
common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json
```

Historical baselines must not be used as the current scenario alignment authority when they conflict with Class 2 clarification / transition semantics.

---

## 4. 파일 위치 규칙

scenario manifest 파일은 다음 위치에 둔다.

```text
integration/scenarios/
```

파일명은 목적이 드러나게 작성하는 것을 권장한다.

예:

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

---

## 5. 공통 최상위 필드 규칙

모든 scenario manifest는 가능한 한 아래 최상위 필드를 공통으로 가진다.

### 필수 권장 필드

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

### Class 2 추가 권장 필드

Class 2 insufficient-context scenario 또는 Class 2-like clarification flow를 표현하는 scenario는 다음 필드를 추가할 수 있다.

- `clarification_interaction`
- `transition_outcomes`
- step-level `candidate_choices`

`expected_outcomes`에는 다음 필드를 사용할 수 있다.

- `class2_role`
- `candidate_generation_allowed`
- `candidate_generation_authorizes_actuation`
- `confirmation_required_before_transition`
- `allowed_transition_targets`

### 필드 설명

#### `scenario_id`

- 문자열
- 저장소 내에서 사람이 식별 가능한 ID
- 공백 없는 식별자 권장

예:

- `SCN_CLASS0_E001_BASELINE`
- `SCN_CLASS0_E002_BASELINE`
- `SCN_CLASS0_E003_BASELINE`
- `SCN_CLASS0_E004_BASELINE`
- `SCN_CLASS0_E005_BASELINE`
- `SCN_CLASS2_INSUFFICIENT_CONTEXT`
- `SCN_FAULT_CONFLICT_BASELINE`

#### `title`

- 문자열
- 사람이 읽기 쉬운 짧은 제목

#### `description`

- 문자열
- scenario 목적과 성격 설명
- canonical truth가 아니라 integration asset임을 드러내는 문구 권장

#### `category`

- 문자열
- scenario 분류

권장 category 예시:

- `baseline`
- `class0_emergency`
- `class1_baseline`
- `class2_insufficient_context`
- `fault_stale`
- `fault_conflict`
- `fault_missing_state`

#### `mode`

- 문자열
- 현재는 `deterministic`를 기본 권장
- 이후 필요 시 `randomized_stress` 확장 가능

#### `input_plane`

- 객체
- scenario가 어떤 ingress plane을 전제로 하는지 표현

권장 하위 필드:

- `protocol`
- `ingress_topic`
- `audit_topic`

Class 0 emergency scenario에서 emergency event ingress와 normalized policy-input bridge를 구분해야 할 경우 다음 필드를 추가할 수 있다.

- `normalized_policy_input_topic`
- `bridge_mode`

예:

```json
{
  "protocol": "mqtt",
  "ingress_topic": "safe_deferral/emergency/event",
  "normalized_policy_input_topic": "safe_deferral/context/input",
  "bridge_mode": "controlled_runtime_or_experiment_bridge",
  "audit_topic": "safe_deferral/audit/log"
}
```

#### `preconditions`

- 객체
- scenario 실행 전 만족되어야 할 환경 가정

예:

- `requires_mac_mini_runtime`
- `requires_rpi_evaluation_runtime`
- `requires_synced_phase0_assets`
- `requires_time_sync_healthy`
- `requires_fault_profile_alignment`
- `requires_mqtt_registry_alignment`
- `requires_policy_schema_alignment`
- `requires_class2_clarification_manager`
- `requires_user_feedback_output`
- `requires_bounded_selection_input`

#### `steps`

- 배열
- scenario 실행 절차
- 최소 1개 이상의 step 필요

#### `expected_outcomes`

- 객체
- expected safe outcome 또는 allowed/prohibited outcome 집합

#### `notes`

- 배열
- 해석 주의점, canonical truth 경계, 추후 확장 포인트 등을 기록

---

## 6. Class 2 clarification / transition 필드 규칙

Class 2는 다음 의미로 사용한다.

```text
Class 2 = clarification / transition state
```

Class 2는 terminal failure 또는 caregiver escalation만을 의미하지 않는다.

### 6.1 `clarification_interaction`

Class 2 scenario는 다음 구조를 권장한다.

```json
{
  "clarification_interaction": {
    "class2_role": "clarification_transition_state",
    "candidate_generation_actor": "LLM_GUIDANCE_LAYER_OR_INPUT_CONTEXT_MAPPER",
    "candidate_generation_boundary": "candidate_generation_only_no_final_decision_no_actuation_authority",
    "presentation_channels": ["TTS_OR_VOICE_OUTPUT", "DISPLAY_OUTPUT"],
    "selection_inputs": ["BOUNDED_INPUT_NODE", "VOICE_INPUT", "CAREGIVER_CONFIRMATION", "TIMEOUT_OR_NO_RESPONSE"],
    "confirmation_required_before_transition": true,
    "timeout_behavior": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"
  }
}
```

규칙:

- `confirmation_required_before_transition`은 true여야 한다.
- `candidate_generation_boundary`는 final decision과 actuation authority 금지를 표현해야 한다.
- 후보 제시는 user-facing guidance이지 validator output이 아니다.
- 후보 제시는 actuator command가 아니다.

### 6.2 `candidate_choices`

Class 2 candidate choices는 step-level에 둘 수 있다.

```json
{
  "candidate_choices": [
    {
      "candidate_id": "C1_LIGHTING_ASSISTANCE",
      "user_prompt": "조명을 켤까요?",
      "candidate_transition_target": "CLASS_1",
      "requires_user_or_caregiver_confirmation": true
    }
  ]
}
```

규칙:

- 후보는 bounded candidate여야 한다.
- 후보 수는 정책 기준상 최대 4개 이하를 권장한다.
- `candidate_transition_target`은 `CLASS_1`, `CLASS_0`, `SAFE_DEFERRAL`, `CAREGIVER_CONFIRMATION`, `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION` 중 하나여야 한다.
- 후보가 있다고 해서 actuation authority가 생기지 않는다.

### 6.3 `transition_outcomes`

Class 2 scenario는 가능한 transition outcome을 명시해야 한다.

```json
{
  "transition_outcomes": [
    {
      "transition_target": "CLASS_1",
      "condition": "User or caregiver confirms a bounded low-risk assistance request."
    },
    {
      "transition_target": "CLASS_0",
      "condition": "User confirms emergency help or deterministic emergency evidence arrives."
    },
    {
      "transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
      "condition": "User response is absent or ambiguity remains unresolved."
    }
  ]
}
```

규칙:

- `CLASS_1` 전이는 low-risk catalog와 Deterministic Validator 조건을 가져야 한다.
- `CLASS_0` 전이는 emergency confirmation, triple-hit, E001~E005 deterministic evidence 조건을 가져야 한다.
- no response 또는 persistent ambiguity는 Safe Deferral 또는 Caregiver Confirmation으로 이어져야 한다.

### 6.4 `expected_outcomes` Class 2 필드

Class 2 expected outcomes에는 다음을 권장한다.

```json
{
  "route_class": "CLASS_2",
  "routing_target": "CLASS_2",
  "class2_role": "clarification_transition_state",
  "llm_decision_invocation_allowed": false,
  "llm_guidance_generation_allowed": "policy_constrained_only",
  "candidate_generation_allowed": true,
  "candidate_generation_authorizes_actuation": false,
  "confirmation_required_before_transition": true,
  "allowed_transition_targets": [
    "CLASS_1",
    "CLASS_0",
    "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"
  ],
  "unsafe_autonomous_actuation_allowed": false,
  "doorlock_autonomous_execution_allowed": false
}
```

---

## 7. MQTT topic 규칙

Scenario는 current MQTT registry와 interface matrix를 따라야 한다.

Authoritative references:

- `common/mqtt/topic_registry_v1_0_0.json`
- `common/docs/architecture/15_interface_matrix.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`

기본 namespace:

```text
safe_deferral/...
```

### 7.1 Ordinary context/input scenario

ordinary context/input scenario의 기본 ingress topic:

```text
safe_deferral/context/input
```

예:

```json
"input_plane": {
  "protocol": "mqtt",
  "ingress_topic": "safe_deferral/context/input",
  "audit_topic": "safe_deferral/audit/log"
}
```

### 7.2 Class 0 emergency scenario

Class 0 emergency scenario의 기본 ingress topic:

```text
safe_deferral/emergency/event
```

예:

```json
"input_plane": {
  "protocol": "mqtt",
  "ingress_topic": "safe_deferral/emergency/event",
  "audit_topic": "safe_deferral/audit/log"
}
```

Class 0 fixture가 `policy_router_input` wrapper 형태라면, scenario는 emergency event ingress와 normalized input bridge를 명확히 구분해야 한다.

### 7.3 Class 2 clarification scenario

Class 2 clarification은 현재 별도 topic registry version 없이 기존 topic으로 표현한다.

```text
safe_deferral/context/input
safe_deferral/deferral/request
safe_deferral/escalation/class2
safe_deferral/caregiver/confirmation
safe_deferral/audit/log
```

규칙:

- prompt/candidate generation은 execution topic이 아니다.
- user selection은 bounded input/context input plane으로 다시 들어가야 한다.
- caregiver confirmation은 `safe_deferral/caregiver/confirmation` path를 사용한다.
- all candidate, selection, timeout, transition outcomes must be audit logged.

### 7.4 Audit observation

Audit observation은 다음 topic과 정렬되어야 한다.

```text
safe_deferral/audit/log
```

### 7.5 Legacy topic 금지

신규 또는 정합화된 scenario는 다음 legacy topic을 사용하지 않는다.

```text
smarthome/context/raw
smarthome/audit/validator_output
```

기존 skeleton에 이 값이 남아 있다면 JSON alignment 단계에서 수정해야 한다.

---

## 8. steps 필드 규칙

각 step은 객체로 표현한다.

### 권장 필드

- `step_id`
- `action`
- `description`
- `payload_fixture` 선택
- `expected_fixture` 선택
- `candidate_choices` Class 2 candidate step에서 선택

### 현재 권장 action 예시

- `publish_context_payload`
- `publish_emergency_event_payload`
- `publish_fault_injected_context_payload`
- `enter_class2_clarification_state`
- `generate_bounded_candidate_choices`
- `present_candidate_choices`
- `collect_confirmation_or_timeout`
- `transition_after_confirmation`
- `observe_audit_stream`

---

## 9. expected_outcomes 필드 규칙

`expected_outcomes`는 scenario의 성격에 따라 세 가지 스타일 중 하나를 택할 수 있다.

### 9.1 deterministic single-outcome style

단일 route/class expectation이 명확할 때 사용한다.

예:

```json
{
  "route_class": "CLASS_1",
  "routing_target": "CLASS_1",
  "llm_invocation_allowed": true,
  "llm_decision_invocation_allowed": true,
  "llm_guidance_generation_allowed": true,
  "unsafe_autonomous_actuation_allowed": false,
  "allowed_action_catalog_ref": "common/policies/low_risk_actions_v1_1_0_FROZEN.json",
  "doorlock_autonomous_execution_allowed": false
}
```

적합한 경우:

- baseline Class 0
- baseline Class 1

### 9.2 Class 2 clarification/transition style

Class 2 clarification state와 후속 전이를 표현할 때 사용한다.

예:

```json
{
  "route_class": "CLASS_2",
  "routing_target": "CLASS_2",
  "class2_role": "clarification_transition_state",
  "llm_decision_invocation_allowed": false,
  "llm_guidance_generation_allowed": "policy_constrained_only",
  "candidate_generation_allowed": true,
  "candidate_generation_authorizes_actuation": false,
  "confirmation_required_before_transition": true,
  "allowed_transition_targets": [
    "CLASS_1",
    "CLASS_0",
    "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"
  ],
  "unsafe_autonomous_actuation_allowed": false,
  "doorlock_autonomous_execution_allowed": false
}
```

적합한 경우:

- `class2_insufficient_context_scenario_skeleton.json`
- Class 2-like clarification flow를 포함하는 conflict/missing-state variants

### 9.3 allowed/prohibited outcome style

fault scenario처럼 conservative safe outcome 집합이 허용될 수 있을 때 사용한다.

예:

```json
{
  "allowed_safe_outcomes": ["SAFE_DEFERRAL", "CLASS_2"],
  "prohibited_outcomes": ["UNSAFE_AUTONOMOUS_ACTUATION"],
  "unsafe_autonomous_actuation_allowed": false,
  "doorlock_autonomous_execution_allowed": false
}
```

적합한 경우:

- stale fault
- conflict fault
- missing-state fault

### 9.4 LLM invocation field interpretation

기존 field:

```json
"llm_invocation_allowed": false
```

은 coarse legacy-style field로 남아 있을 수 있다.

향후 scenario에서는 가능하면 다음을 구분한다.

```json
"llm_decision_invocation_allowed": false,
"llm_guidance_generation_allowed": "policy_constrained_only"
```

해석:

- `llm_decision_invocation_allowed`는 LLM이 decision/candidate action generation path에 참여할 수 있는지를 뜻한다.
- `llm_guidance_generation_allowed`는 safe deferral, clarification, escalation waiting, ACK result 설명 등 user-facing guidance generation을 뜻한다.
- guidance generation 허용은 actuation authorization이 아니다.
- Class 0 emergency는 LLM을 primary decision path로 사용하면 안 된다.
- Class 2의 candidate generation은 clarification interaction일 뿐 validator output이나 actuator command가 아니다.

### 규칙

- `unsafe_autonomous_actuation_allowed`는 가능한 한 명시한다.
- `doorlock_autonomous_execution_allowed`는 doorlock-sensitive boundary가 관련되는 scenario에서 반드시 false로 명시하는 것을 권장한다.
- scenario가 allowed/prohibited style을 쓰더라도 canonical truth를 확정하지는 않는다.
- exact predicate는 frozen assets와 runtime behavior를 통해 검증되어야 한다.

---

## 10. Class 1 low-risk boundary 규칙

Class 1 autonomous execution은 현재 frozen low-risk lighting catalog로 제한된다.

Authoritative reference:

```text
common/policies/low_risk_actions_v1_1_0_FROZEN.json
```

Scenario는 다음을 하면 안 된다.

- low-risk action catalog를 scenario 안에서 확장
- `door_unlock`을 Class 1 candidate action으로 표현
- `front_door_lock`을 Class 1 target device로 표현
- doorlock-sensitive request를 Class 1 autonomous execution expected outcome으로 표현

Class 1 scenario에는 다음과 같은 expected outcome field를 넣는 것을 권장한다.

```json
"allowed_action_catalog_ref": "common/policies/low_risk_actions_v1_1_0_FROZEN.json",
"doorlock_autonomous_execution_allowed": false
```

Class 2에서 Class 1로 전이되는 경우에도 같은 low-risk catalog와 Deterministic Validator boundary가 적용된다.

---

## 11. Class 0 emergency boundary 규칙

Class 0은 E001~E005 deterministic emergency family와 정합적이어야 한다.

Class 2에서 Class 0으로 전이되는 경우에도 다음 중 하나가 필요하다.

```text
- user/caregiver confirms emergency help
- triple-hit input occurs
- deterministic E001-E005 emergency evidence arrives
```

LLM candidate text alone must not trigger Class 0.

---

## 12. `doorbell_detected` 규칙

Schema-governed context fixture는 현재 context schema와 맞아야 한다.

`environmental_context.doorbell_detected`는 required field다.

규칙:

- non-visitor scenario에서는 일반적으로 `doorbell_detected=false`
- visitor-response scenario에서는 적절한 경우에만 `doorbell_detected=true`
- `doorbell_detected=true`는 emergency evidence가 아니다
- `doorbell_detected=true`는 autonomous door unlock authorization이 아니다
- missing-state fault fixture에서는 `doorbell_detected` required key 누락 케이스와 일반 device-state 누락 케이스를 분리하는 것을 권장한다

---

## 13. fixture 참조 규칙

scenario는 fixture를 직접 내장하기보다 참조하는 방식을 권장한다.

권장 이유:

- 재사용 가능
- runner/comparator 구현 단순화
- 동일 입력을 여러 scenario에서 공유 가능

권장 위치:

```text
integration/tests/data/
```

대표 예시:

- `sample_policy_router_input_class1.json`
- `sample_policy_router_input_class2_insufficient_context.json`
- `sample_policy_router_input_class0_e001.json`
- `expected_routing_class1.json`
- `expected_routing_class2.json`
- `expected_routing_class0_e001.json`

향후 권장 Class 2 fixtures:

- `expected_class2_candidate_prompt.json`
- `sample_class2_user_selection_class1.json`
- `expected_class2_transition_class1.json`
- `sample_class2_user_selection_class0.json`
- `expected_class2_transition_class0.json`
- `sample_class2_timeout_no_response.json`
- `expected_class2_timeout_safe_deferral.json`

향후 권장 fault-specific fixtures:

- `sample_policy_router_input_fault_stale.json`
- `sample_policy_router_input_fault_conflict_multiple_candidates.json`
- `sample_policy_router_input_fault_missing_doorbell_detected.json`
- `sample_policy_router_input_fault_missing_device_state.json`
- `expected_fault_conflict_safe_deferral.json`
- `expected_fault_missing_state_safe_deferral.json`

Fixture reference는 verifier에서 다음을 확인해야 한다.

- referenced file exists
- JSON parse OK
- schema-governed fixture includes required fields
- `doorbell_detected` required field is present where applicable
- current `device_states` does not include doorlock state
- Class 1 fixture does not imply doorlock autonomous execution
- Class 2 clarification fixture does not encode actuator command or validator approval in candidate text

---

## 14. naming 규칙

### scenario_id 권장 규칙

다음 패턴 중 하나를 권장한다.

- `SCN_CLASS0_*`
- `SCN_CLASS1_*`
- `SCN_CLASS2_*`
- `SCN_FAULT_*`

### 파일명 권장 규칙

- snake_case 사용
- suffix는 가능하면 `_scenario_skeleton.json`

---

## 15. canonical alignment 규칙

scenario는 다음 frozen assets 및 registry/interface references와 정합적이어야 한다.

- `common/policies/policy_table_v1_2_0_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json`
- `common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/19_class2_clarification_architecture_alignment.md`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

주의:

- scenario는 threshold를 확정하지 않는다.
- scenario는 trigger semantics를 새로 정의하지 않는다.
- scenario는 required keys를 새로 정의하지 않는다.
- scenario는 MQTT topic registry에 없는 topic을 임의로 만들지 않는다.
- scenario는 policy/schema/registry drift를 숨기지 않는다.
- scenario는 historical policy/schema baseline을 current active baseline처럼 참조하지 않는다.

---

## 16. measurement 연결 규칙

scenario는 이후 class-wise latency profile과 연결될 수 있어야 한다.

권장 방식:

- `scenario_id`를 measurement profile에서 참조
- class label / category 기준으로 profile 매핑
- capture point 정의는 `integration/measurement/` 문서에 둠

즉:

- scenario는 **무엇을 평가할지**를 정의
- measurement profile은 **어떻게 측정할지**를 정의

---

## 17. 현재 반영된 skeleton과의 정합성

현재 반영된 다음 skeleton들은 이 규칙에 맞춰 정합화되어야 한다.

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

Known current alignment issue:

- Some skeletons may still require Class 2 transition cross-reference notes or expected fixture expansion in the JSON alignment phase.
- Class 2 transition-specific fixtures are not yet fully added.

이 문서는 향후 추가되는 scenario도 같은 구조를 따르도록 하기 위한 기준 문서다.

---

## 18. 다음 권장 작업

1. scenario skeleton JSON semantic alignment
2. Class 2 transition fixture 추가
3. scenario loader unit test 추가
4. expected outcome comparator 추가
5. `verify_scenario_topic_alignment.py` 추가 보강
6. `verify_scenario_fixture_refs.py` 추가 보강
7. `verify_scenario_policy_schema_alignment.py` 추가 보강
8. randomized stress metadata 규칙 문서화
9. measurement profile과 scenario 매핑 문서화
