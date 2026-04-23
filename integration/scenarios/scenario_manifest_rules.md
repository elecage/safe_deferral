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

즉, 이 문서는 **scenario JSON의 공통 메타구조**를 정의한다.

---

## 2. 기본 원칙

- scenario는 canonical truth가 아니다.
- scenario는 frozen assets를 소비하는 evaluation asset이다.
- scenario는 operational hub를 우회하는 제어 경로를 만들면 안 된다.
- threshold, required key, trigger predicate, routing truth를 scenario가 최종 정의하면 안 된다.
- scenario는 가능한 한 machine-readable 하면서도 사람이 읽기 쉬워야 한다.

---

## 3. 파일 위치 규칙

scenario manifest 파일은 다음 위치에 둔다.

```text
integration/scenarios/
```

파일명은 목적이 드러나게 작성하는 것을 권장한다.

예:
- `class0_e001_scenario_skeleton.json`
- `class1_baseline_scenario_skeleton.json`
- `class2_insufficient_context_scenario_skeleton.json`
- `stale_fault_scenario_skeleton.json`
- `conflict_fault_scenario_skeleton.json`
- `missing_state_scenario_skeleton.json`

---

## 4. 공통 최상위 필드 규칙

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

### 필드 설명

#### `scenario_id`
- 문자열
- 저장소 내에서 사람이 식별 가능한 ID
- 공백 없는 식별자 권장

예:
- `SCN_CLASS0_E001_BASELINE`
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

#### `preconditions`
- 객체
- scenario 실행 전 만족되어야 할 환경 가정

예:
- `requires_mac_mini_runtime`
- `requires_rpi_evaluation_runtime`
- `requires_synced_phase0_assets`
- `requires_time_sync_healthy`
- `requires_fault_profile_alignment`

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

## 5. steps 필드 규칙

각 step은 객체로 표현한다.

### 권장 필드
- `step_id`
- `action`
- `description`
- `payload_fixture` (선택)
- `expected_fixture` (선택)

### 필드 설명

#### `step_id`
- 숫자 또는 문자열
- scenario 내에서 순서를 식별할 수 있어야 한다.

#### `action`
- 문자열
- 실행 의도를 짧게 나타냄

현재 권장 action 예시:
- `publish_context_payload`
- `publish_fault_injected_context_payload`
- `observe_audit_stream`

#### `description`
- 문자열
- 해당 step이 하는 일을 설명

#### `payload_fixture`
- 문자열
- 저장소 루트 기준 상대경로 권장
- JSON fixture 파일을 가리킨다.

예:
- `integration/tests/data/sample_policy_router_input_class1.json`

#### `expected_fixture`
- 문자열
- 저장소 루트 기준 상대경로 권장
- expected outcome fixture 파일을 가리킨다.

예:
- `integration/tests/data/expected_routing_class1.json`

---

## 6. expected_outcomes 필드 규칙

`expected_outcomes`는 scenario의 성격에 따라 두 가지 스타일 중 하나를 택할 수 있다.

### 6.1 deterministic single-outcome style
단일 route/class expectation이 명확할 때 사용한다.

예:
```json
{
  "route_class": "CLASS_1",
  "routing_target": "CLASS_1",
  "llm_invocation_allowed": true,
  "unsafe_autonomous_actuation_allowed": false
}
```

적합한 경우:
- baseline Class 0
- baseline Class 1
- baseline Class 2

### 6.2 allowed/prohibited outcome style
fault scenario처럼 conservative safe outcome 집합이 허용될 수 있을 때 사용한다.

예:
```json
{
  "allowed_safe_outcomes": ["SAFE_DEFERRAL", "CLASS_2"],
  "prohibited_outcomes": ["UNSAFE_AUTONOMOUS_ACTUATION"],
  "unsafe_autonomous_actuation_allowed": false
}
```

적합한 경우:
- stale fault
- conflict fault
- missing-state fault

### 규칙
- `unsafe_autonomous_actuation_allowed`는 가능한 한 명시한다.
- scenario가 allowed/prohibited style을 쓰더라도 canonical truth를 확정하지는 않는다.
- exact predicate는 frozen assets와 runtime behavior를 통해 검증되어야 한다.

---

## 7. fixture 참조 규칙

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

---

## 8. naming 규칙

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

## 9. canonical alignment 규칙

scenario는 다음 frozen assets와 정합적이어야 한다.

- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_1_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

주의:
- scenario는 threshold를 확정하지 않는다.
- scenario는 trigger semantics를 새로 정의하지 않는다.
- scenario는 required keys를 새로 정의하지 않는다.

---

## 10. measurement 연결 규칙

scenario는 이후 class-wise latency profile과 연결될 수 있어야 한다.

권장 방식:
- `scenario_id`를 measurement profile에서 참조
- class label / category 기준으로 profile 매핑
- capture point 정의는 `integration/measurement/` 문서에 둠

즉:
- scenario는 **무엇을 평가할지**를 정의
- measurement profile은 **어떻게 측정할지**를 정의

---

## 11. 현재 반영된 skeleton과의 정합성

현재 반영된 다음 skeleton들은 이 규칙을 대체로 따르도록 작성되어 있다.

- `baseline_scenario_skeleton.json`
- `class0_e001_scenario_skeleton.json`
- `class1_baseline_scenario_skeleton.json`
- `class2_insufficient_context_scenario_skeleton.json`
- `stale_fault_scenario_skeleton.json`
- `conflict_fault_scenario_skeleton.json`
- `missing_state_scenario_skeleton.json`

이 문서는 향후 추가되는 scenario도 같은 구조를 따르도록 하기 위한 기준 문서다.

---

## 12. 다음 권장 작업

1. scenario loader unit test 추가
2. expected outcome comparator 추가
3. 필요 시 `scenario_manifest_schema.json` 추가
4. randomized stress metadata 규칙 문서화
5. measurement profile과 scenario 매핑 문서화
