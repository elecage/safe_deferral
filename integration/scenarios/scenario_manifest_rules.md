# scenario_manifest_rules.md

이 문서는 `integration/scenarios/` 아래의 scenario JSON 파일이 따라야 하는 공통 manifest 규칙을 정의한다.

이 문서는 canonical policy truth를 재정의하지 않는다. 정책/스키마/용어의 authoritative baseline은 `common/`의 canonical assets에 남는다.

---

## 1. 목적

scenario manifest 규칙은 다음을 위해 필요하다.

- scenario 파일 형식 일관성 확보
- scenario loader / comparator / test runner 작성 용이성 확보
- deterministic scenario와 fault scenario의 공통 구조 정리
- measurement profile과의 연결 용이성 확보
- reproducible evaluation package 구성 용이성 확보
- MQTT topic registry 및 active MQTT/payload contract 문서와의 정합성 확보
- canonical policy/schema/payload boundary를 침범하지 않는 scenario 구성
- Class 2 clarification / transition structure의 machine-readable 표현
- Class 2 clarification interaction evidence topic의 비권한성 보존

---

## 2. 기본 원칙

- scenario는 canonical truth가 아니다.
- scenario는 canonical assets를 소비하는 evaluation asset이다.
- scenario는 operational hub를 우회하는 제어 경로를 만들면 안 된다.
- threshold, required key, trigger predicate, routing truth를 scenario가 최종 정의하면 안 된다.
- scenario topic은 `common/mqtt/topic_registry.json` 및 `common/docs/architecture/03_payload_and_mqtt_contracts.md`와 정렬되어야 한다.
- `common/history/mqtt/topic_registry.json`은 historical baseline으로만 다룬다.
- scenario fixture는 current schema boundary를 따라야 한다.
- scenario는 Class 1 autonomous low-risk scope를 canonical lighting catalog 밖으로 확장하면 안 된다.
- scenario는 doorlock-sensitive behavior를 autonomous Class 1 execution으로 표현하면 안 된다.
- Class 2 scenario는 terminal failure만 표현하면 안 되며, clarification / transition structure를 명시해야 한다.
- Class 2 candidate choices는 validator output, actuator command, emergency trigger, doorlock authorization이 아니다.
- `safe_deferral/clarification/interaction`은 Class 2 clarification interaction evidence topic이며 authorization topic이 아니다.

---

## 3. Current active baseline

Scenario manifest는 아래 active baseline과 정합적이어야 한다.

```text
Active policy baseline:
common/policies/policy_table.json

Low-risk action catalog:
common/policies/low_risk_actions.json

Fault injection rules:
common/policies/fault_injection_rules.json

Pure context schema:
common/schemas/context_schema.json

Policy router input schema:
common/schemas/policy_router_input_schema.json

Candidate action schema:
common/schemas/candidate_action_schema.json

Validator output schema:
common/schemas/validator_output_schema.json

Class 2 notification schema:
common/schemas/class2_notification_payload_schema.json

Class 2 clarification interaction schema:
common/schemas/clarification_interaction_schema.json

Current MQTT topic registry:
common/mqtt/topic_registry.json

MQTT topic payload contracts:
common/mqtt/topic_payload_contracts.md

Representative Class 2 clarification interaction example:
common/payloads/examples/clarification_interaction_two_options_pending.json

Scenario/evaluation architecture:
common/docs/architecture/07_scenarios_and_evaluation.md

MQTT/payload contracts:
common/docs/architecture/03_payload_and_mqtt_contracts.md

Class 2 clarification:
common/docs/architecture/04_class2_clarification.md
```

Historical baselines:

```text
common/history/policies/policy_table.json
common/history/schemas/class2_notification_payload_schema.json
common/history/mqtt/topic_registry.json
```

Historical baselines must not be used as current scenario alignment authority when they conflict with Class 2 clarification / transition semantics.

---

## 4. 파일 위치 및 naming 규칙

Scenario manifest 파일은 다음 위치에 둔다.

```text
integration/scenarios/
```

파일명은 snake_case를 사용하고 가능하면 `_scenario_skeleton.json` suffix를 유지한다.

현재 대표 파일:

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

권장 추가 Class 2 skeleton:

- `class2_to_class1_low_risk_confirmation_scenario_skeleton.json`
- `class2_to_class0_emergency_confirmation_scenario_skeleton.json`
- `class2_timeout_no_response_safe_deferral_scenario_skeleton.json`
- `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json`

---

## 5. 공통 최상위 필드 규칙

모든 scenario manifest는 가능한 한 아래 최상위 필드를 공통으로 가진다.

필수 권장 필드:

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

Class 2 추가 권장 필드:

- `clarification_interaction`
- `class2_clarification_expectation`
- `transition_outcomes`
- step-level `candidate_choices`

`scenario_manifest_schema.json`는 these fields를 documentation schema로 표현한다. It does not become policy authority.

---

## 6. MQTT topic 규칙

Scenario는 current MQTT registry와 active MQTT/payload contract rules를 따라야 한다.

Authoritative current references:

- `common/mqtt/topic_registry.json`
- `common/docs/architecture/03_payload_and_mqtt_contracts.md`
- `common/mqtt/topic_payload_contracts.md`

Historical reference:

- `common/history/mqtt/topic_registry.json`

기본 namespace:

```text
safe_deferral/...
```

Ordinary context/input scenario ingress topic:

```text
safe_deferral/context/input
```

Class 0 emergency scenario ingress topic:

```text
safe_deferral/emergency/event
```

Class 2 notification topic:

```text
safe_deferral/escalation/class2
```

Class 2 clarification interaction evidence topic:

```text
safe_deferral/clarification/interaction
```

Caregiver confirmation topic:

```text
safe_deferral/caregiver/confirmation
```

Audit observation topic:

```text
safe_deferral/audit/log
```

Legacy topics are not allowed in new or aligned scenarios:

```text
safe_deferral/context/input
safe_deferral/validator/output
```

---

## 7. Class 2 clarification / transition 필드 규칙

Class 2는 다음 의미로 사용한다.

```text
Class 2 = clarification / transition state
```

Class 2는 terminal failure 또는 caregiver escalation만을 의미하지 않는다.

### 7.1 `clarification_interaction`

Class 2 scenario는 다음 구조를 권장한다.

```json
{
  "clarification_interaction": {
    "class2_role": "clarification_transition_state",
    "clarification_topic": "safe_deferral/clarification/interaction",
    "clarification_schema_ref": "common/schemas/clarification_interaction_schema.json",
    "example_payload_ref": "common/payloads/examples/clarification_interaction_two_options_pending.json",
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
- clarification interaction artifacts가 MQTT로 발행되는 경우 `safe_deferral/clarification/interaction`을 사용한다.

### 7.2 `class2_clarification_expectation`

Class 2 transition scenario는 다음 block을 권장한다.

```json
{
  "class2_clarification_expectation": {
    "enabled": true,
    "clarification_topic": "safe_deferral/clarification/interaction",
    "clarification_schema_ref": "common/schemas/clarification_interaction_schema.json",
    "example_payload_ref": "common/payloads/examples/clarification_interaction_two_options_pending.json",
    "expected_transition_target": "CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
    "requires_validator_reentry_when_class1": true,
    "requires_validator_when_class1": true,
    "timeout_must_not_infer_intent": true,
    "clarification_payload_is_not_authorization": true,
    "forbidden_interpretations": [
      "validator_approval",
      "actuation_command",
      "emergency_trigger_authority",
      "doorlock_authorization"
    ]
  }
}
```

This block is evidence/verification expectation only. It does not authorize execution.

### 7.3 `candidate_choices`

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

Rules:

- 후보는 bounded candidate여야 한다.
- 후보 수는 최대 4개 이하를 권장한다.
- `candidate_transition_target`은 `CLASS_1`, `CLASS_0`, `SAFE_DEFERRAL`, `CAREGIVER_CONFIRMATION`, `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION` 중 하나여야 한다.
- 후보가 있다고 해서 actuation authority가 생기지 않는다.

### 7.4 `transition_outcomes`

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

Rules:

- `CLASS_1` 전이는 low-risk catalog와 Deterministic Validator 조건을 가져야 한다.
- `CLASS_0` 전이는 emergency confirmation, triple-hit, E001~E005 deterministic evidence 조건을 가져야 한다.
- no response 또는 persistent ambiguity는 Safe Deferral 또는 Caregiver Confirmation으로 이어져야 한다.

---

## 8. expected_outcomes 필드 규칙

### deterministic single-outcome style

Class 0 또는 Class 1처럼 단일 route/class expectation이 명확할 때 사용한다.

### Class 2 clarification/transition style

Class 2 clarification state와 후속 전이를 표현할 때 사용한다.

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

### allowed/prohibited outcome style

Fault scenario처럼 conservative safe outcome 집합이 허용될 수 있을 때 사용한다.

---

## 9. Class 1 low-risk boundary 규칙

Class 1 autonomous execution은 현재 canonical low-risk lighting catalog로 제한된다.

Authoritative reference:

```text
common/policies/low_risk_actions.json
```

Scenario는 다음을 하면 안 된다.

- low-risk action catalog를 scenario 안에서 확장
- `door_unlock`을 Class 1 candidate action으로 표현
- `front_door_lock`을 Class 1 target device로 표현
- doorlock-sensitive request를 Class 1 autonomous execution expected outcome으로 표현

Class 2에서 Class 1로 전이되는 경우에도 같은 low-risk catalog와 Deterministic Validator boundary가 적용된다.

---

## 10. Class 0 emergency boundary 규칙

Class 0은 E001~E005 deterministic emergency family와 정합적이어야 한다.

Class 2에서 Class 0으로 전이되는 경우에도 다음 중 하나가 필요하다.

```text
- user/caregiver confirms emergency help
- triple-hit input occurs
- deterministic E001-E005 emergency evidence arrives
```

LLM candidate text alone must not trigger Class 0.

---

## 11. `doorbell_detected` 규칙

Schema-governed context fixture는 current context schema와 맞아야 한다.

`environmental_context.doorbell_detected`는 required field다.

Rules:

- non-visitor scenario에서는 일반적으로 `doorbell_detected=false`
- visitor-response scenario에서는 적절한 경우에만 `doorbell_detected=true`
- `doorbell_detected=true`는 emergency evidence가 아니다
- `doorbell_detected=true`는 autonomous door unlock authorization이 아니다

### trigger_event vs environmental_context 구분

`doorbell_detected`는 두 가지 다른 위치에서 사용되며 혼동해서는 안 된다:

| 위치 | 필드 | 역할 | Policy Router 결과 |
|---|---|---|---|
| `environmental_context.doorbell_detected` | boolean context field | 방문자 도착 상황 context signal | **CLASS_1** (button trigger와 함께 사용 시) |
| `trigger_event.event_type=sensor` + `event_code=doorbell_detected` | trigger event | 도어벨 센서 이벤트 자체 | **CLASS_2 (C208)** |

- `environmental_context.doorbell_detected=true`만으로는 CLASS_2가 되지 않는다.
  button trigger와 함께라면 CLASS_1 pipeline을 따른다.
- `trigger_event.event_type=sensor, event_code=doorbell_detected`일 때만 C208로
  CLASS_2에 진입한다. 이는 도어락 민감 경로이므로 보호자 확인이 필요하다.
- 두 경우 모두 `doorbell_detected`는 doorlock 자동 개방 권한이 아니다.

---

## 12. fixture 참조 규칙

Scenario는 fixture를 직접 내장하기보다 참조하는 방식을 권장한다.

권장 위치:

```text
integration/tests/data/
```

Verifier는 다음을 확인해야 한다.

- referenced file exists
- JSON parse OK
- schema-governed fixture includes required fields
- `doorbell_detected` required field is present where applicable
- current `device_states` does not include doorlock state
- Class 1 fixture does not imply doorlock autonomous execution
- Class 2 clarification fixture does not encode actuator command or validator approval in candidate text
- Class 2 clarification fixture uses `safe_deferral/clarification/interaction` when published as interaction evidence

---

## 13. canonical alignment 규칙

Scenario는 다음 canonical assets 및 registry/active architecture references와 정합적이어야 한다.

- `common/policies/policy_table.json`
- `common/policies/low_risk_actions.json`
- `common/policies/fault_injection_rules.json`
- `common/schemas/context_schema.json`
- `common/schemas/candidate_action_schema.json`
- `common/schemas/policy_router_input_schema.json`
- `common/schemas/validator_output_schema.json`
- `common/schemas/class2_notification_payload_schema.json`
- `common/schemas/clarification_interaction_schema.json`
- `common/mqtt/topic_registry.json`
- `common/mqtt/topic_payload_contracts.md`
- `common/docs/architecture/03_payload_and_mqtt_contracts.md`
- `common/docs/architecture/04_class2_clarification.md`
- `common/docs/architecture/07_scenarios_and_evaluation.md`
- `common/terminology/`

주의:

- scenario는 threshold를 확정하지 않는다.
- scenario는 trigger semantics를 새로 정의하지 않는다.
- scenario는 required keys를 새로 정의하지 않는다.
- scenario는 current MQTT topic registry에 없는 topic을 임의로 만들지 않는다.
- scenario는 policy/schema/registry drift를 숨기지 않는다.
- scenario는 historical policy/schema/MQTT baseline을 current active baseline처럼 참조하지 않는다.

---

## 14. measurement 연결 규칙

Scenario는 이후 class-wise latency profile과 연결될 수 있어야 한다.

- scenario는 무엇을 평가할지 정의한다.
- measurement profile은 어떻게 측정할지 정의한다.
- `scenario_id`를 measurement profile에서 참조한다.

---

## 15. 다음 권장 작업

1. Existing Class 2 / fault skeleton에 `class2_clarification_expectation` 추가
2. Class 2 transition fixture 추가
3. Class 2 transition skeleton 4개 추가
4. scenario loader validation rule 문서화
5. expected outcome comparator 설계 재정의
6. topic alignment 검증 방식 재정의
7. fixture reference 검증 방식 재정의
8. policy/schema alignment 검증 방식 재정의
9. randomized stress metadata 규칙 문서화
10. measurement profile과 scenario 매핑 문서화
