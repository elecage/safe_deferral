# integration/scenarios

이 디렉터리는 deterministic scenario, stress scenario, fault-injection scenario, reproducible evaluation package를 두는 공간이다.

Scenario 파일은 canonical policy/schema truth가 아니다. Scenario는 `common/` 아래 canonical policy/schema assets, MQTT registry, payload contracts, and active architecture documents를 소비하는 integration-side evaluation asset이다.

---

## 목적

이 디렉터리는 다음을 가능하게 해야 한다.

- deterministic scenario replay
- fault-injection case packaging
- expected safe outcome 정의
- reproducible paper-evaluation support
- canonical emergency family `E001`~`E005`와 정합적인 scenario 구성
- `safe_deferral/...` MQTT namespace와 정합적인 scenario 구성
- canonical policy/schema/payload boundary를 변경하지 않는 integration evaluation 구성
- Class 2 clarification / transition interaction 검토
- conflict fault, missing-state fault, stale fault의 보수적 처리 검토

---

## 현재 active baseline

Scenario는 아래 active baseline을 소비한다.

```text
Policy baseline:
common/policies/policy_table.json

Low-risk action catalog:
common/policies/low_risk_actions.json

Fault injection rules:
common/policies/fault_injection_rules.json

Pure context schema:
common/schemas/context_schema.json

Policy-router input schema:
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

MQTT payload contracts:
common/mqtt/topic_payload_contracts.md

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

Historical baselines must not be used as the current scenario alignment authority when they conflict with Class 2 clarification / transition semantics.

---

## 개발자가 먼저 읽어야 하는 문서

JSON skeleton만 보면 의미를 빠르게 파악하기 어려울 수 있으므로, 실제 검토자는 먼저 아래 문서를 보는 것을 권장한다.

- `scenario_review_guide.md`
- `scenario_manifest_rules.md`
- `scenario_manifest_schema.json`
- `common/docs/architecture/00_architecture_index.md`
- `common/docs/architecture/03_payload_and_mqtt_contracts.md`
- `common/docs/architecture/04_class2_clarification.md`
- `common/docs/architecture/07_scenarios_and_evaluation.md`
- `common/mqtt/topic_registry.json`
- `common/mqtt/topic_payload_contracts.md`

---

## 현재 반영된 scenario skeleton

현재 다음 skeleton이 반영되어 있다.

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

### Recommended next Class 2 skeletons

The following skeletons should be added in the next scenario-expansion pass.

- `class2_to_class1_low_risk_confirmation_scenario_skeleton.json`
- `class2_to_class0_emergency_confirmation_scenario_skeleton.json`
- `class2_timeout_no_response_safe_deferral_scenario_skeleton.json`
- `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json`

---

## 공통 구조 원칙

현재 skeleton들은 가능한 한 공통 필드를 맞추도록 작성되어 있다.

Representative fields:

- `scenario_id`
- `title`
- `description`
- `category`
- `mode`
- `input_plane`
- `preconditions`
- `steps`
- `clarification_interaction`, for Class 2 scenarios
- `class2_clarification_expectation`, for Class 2 transition scenarios
- `transition_outcomes`, for Class 2 scenarios
- `expected_outcomes`
- `notes`

---

## MQTT topic boundary

Scenario skeletons must align with the current MQTT registry and interface matrix.

Current registry:

```text
common/mqtt/topic_registry.json
```

Historical registry baseline:

```text
common/history/mqtt/topic_registry.json
```

Default namespace:

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

Class 2 caregiver confirmation topic:

```text
safe_deferral/caregiver/confirmation
```

Audit observation topic:

```text
safe_deferral/audit/log
```

Legacy topics are not allowed in new or aligned scenarios:

```text
smarthome/context/raw
smarthome/audit/validator_output
```

---

## Class 2 clarification interaction topic

When Class 2 clarification interaction artifacts are published over MQTT, they should use:

```text
safe_deferral/clarification/interaction
```

Contract:

```text
payload_family: clarification_interaction_payload
schema: common/schemas/clarification_interaction_schema.json
example_payload: common/payloads/examples/clarification_interaction_two_options_pending.json
authority_level: class2_interaction_evidence_not_authority
```

This topic may carry:

- candidate choices
- presentation channel
- user/caregiver selection result
- timeout/no-response result
- transition target
- final safe outcome evidence

It must not be interpreted as:

- validator approval
- actuation command
- emergency trigger authority
- doorlock authorization

Required interpretation:

```text
selection results are confirmed-candidate evidence
Class 1 selections re-enter the Deterministic Validator with the bounded candidate and still require validator approval before any low-risk dispatch
Class 0 transition requires deterministic emergency evidence or explicit emergency confirmation
timeout/no-response must not infer user intent
```

---

## Class 0 emergency boundary

Class 0 is a life/safety emergency path.

Canonical emergency family:

```text
E001 high temperature
E002 triple-hit emergency input
E003 smoke detected
E004 gas detected
E005 fall detected
```

Class 0 must not use the LLM as the primary decision path. During Class 2 clarification, Class 0 may be reached only through explicit emergency confirmation, triple-hit input, or deterministic E001~E005 evidence. LLM candidate text alone is not emergency evidence.

---

## Class 1 low-risk boundary

Current Class 1 autonomous low-risk execution is limited to the canonical lighting catalog.

Authoritative reference:

```text
common/policies/low_risk_actions.json
```

Class 2 can transition to Class 1 only after the user/caregiver confirms a bounded candidate and the Deterministic Validator approves it (the runtime re-enters the validator with the confirmed candidate; it does not re-route through the Policy Router). Scenario files must not represent `door_unlock` or `front_door_lock` as Class 1 autonomous low-risk actions.

---

## Class 2 clarification / transition boundary

Current interpretation:

```text
Class 2 = clarification / transition state
```

Class 2 may be entered for:

- insufficient context
- ambiguous user intent
- unresolved candidate conflict
- missing policy input
- stale policy-relevant state
- missing critical state
- actuation ACK timeout
- caregiver-required sensitive path
- no response / timeout after candidate presentation

Class 2 allowed flow:

```text
ambiguous or insufficient input
→ bounded candidate choices
→ TTS/display/caregiver prompt
→ user/caregiver selection, timeout/no-response, or deterministic evidence
→ Deterministic Validator re-entry with confirmed bounded candidate (Class 1 only)
  | emergency announcement and caregiver notification (Class 0)
  | safe deferral / caregiver confirmation (timeout, no response, or ambiguous)
→ CLASS_1 / CLASS_0 / SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
```

Class 2 candidate generation is guidance only. It is not validator output, actuator command, emergency trigger authority, or doorlock authorization.

---

## Recommended `class2_clarification_expectation` block

Class 2 transition scenarios should include a block like this:

```json
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
```

---

## Fault scenario boundary

Fault scenario is not just a failure label. Each fault has a distinct safety reason.

| Fault | Meaning | Safe handling |
|---|---|---|
| stale fault | policy-relevant state is too old to trust | safe deferral or Class 2 clarification / caregiver confirmation |
| conflict fault | multiple plausible candidates make arbitrary selection unsafe | bounded clarification or safe deferral |
| missing-state fault | required state report is missing | state recheck, safe deferral, or caregiver confirmation |

Fault scenarios may use Class 2-like clarification, but the fault cause identity must remain explicit.

---

## `doorbell_detected` boundary

`environmental_context.doorbell_detected` is required in schema-governed context payloads.

Rules:

- non-visitor scenario: normally `doorbell_detected=false`
- visitor-response scenario: may set `doorbell_detected=true`
- `doorbell_detected=true` is not emergency evidence
- `doorbell_detected=true` is not autonomous door unlock authorization

---

## Payload boundary

Class 2 clarification data is not pure context payload.

Do not put the following into `pure_context_payload`:

```text
candidate_choices
selection_result
transition_target
timeout_result
LLM-generated prompt text
```

Use `clarification_interaction_payload` governed by:

```text
common/schemas/clarification_interaction_schema.json
```

Class 2 notification payload is governed by:

```text
common/schemas/class2_notification_payload_schema.json
```

---

## 경계 원칙

- scenario는 canonical policy truth를 재정의하지 않는다.
- scenario는 canonical assets를 소비하는 evaluation asset이다.
- scenario는 operational hub를 우회하는 control path를 만들지 않는다.
- threshold, required key, trigger semantics는 `common/` canonical assets에서 최종적으로 해석되어야 한다.
- scenario topic은 `common/mqtt/topic_registry.json` 및 `common/docs/architecture/03_payload_and_mqtt_contracts.md`와 정렬되어야 한다.
- scenario fixture는 current schema boundary를 따르고, `doorbell_detected` required field와 doorlock state boundary를 위반하면 안 된다.
- Class 2 clarification interaction은 `common/schemas/clarification_interaction_schema.json`, `common/policies/policy_table.json`, and `safe_deferral/clarification/interaction`을 따라야 한다.

---

## 다음 권장 작업

1. Existing Class 2 / fault skeleton에 `class2_clarification_expectation` 추가
2. Class 2 transition skeleton 4개 추가
3. conflict fault 및 missing-state fault expected fixture 분리
4. fixture reference existence verifier 강화
5. scenario topic alignment verifier 강화
6. policy/schema alignment verifier 추가 보강
7. expected outcome comparator와 scenario 연동 adapter 추가
8. 실제 MQTT publish / audit observe adapter 추가
9. class-wise latency profile과 scenario 연결 문서화
