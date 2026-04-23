# integration

이 디렉터리는 **Mac mini / Raspberry Pi / ESP32를 가로지르는 cross-device integration, scenario execution, evaluation, measurement 지원 자산**을 두는 공간이다.

`integration/`은 특정 단일 디바이스의 구현 폴더가 아니다.  
대신 다음 역할을 담당한다.

- end-to-end integration test
- reproducible scenario definition
- fault-injection and closed-loop evaluation support
- optional out-of-band timing / latency measurement support
- reusable test-data and expected-outcome assets

즉, `integration/`은 **시스템 전체를 검증하고 재현성을 확보하기 위한 cross-device layer**다.

---

## 1. 현재 하위 구조

```text
integration/
├── README.md
├── requirements.md
├── tests/
│   ├── README.md
│   ├── integration_test_runner_skeleton.py
│   └── data/
│      ├── README.md
│      ├── sample_policy_router_input_class1.json
│      ├── sample_policy_router_input_class2_insufficient_context.json
│      ├── sample_policy_router_input_class0_e001.json
│      ├── expected_routing_class1.json
│      ├── expected_routing_class2.json
│      └── expected_routing_class0_e001.json
├── scenarios/
│   ├── README.md
│   └── baseline_scenario_skeleton.json
└── measurement/
    ├── README.md
    └── class_wise_latency_profiles.md
```

---

## 2. 현재 반영된 핵심 자산

### `integration/scenarios/baseline_scenario_skeleton.json`
- deterministic baseline scenario 골격
- ingress topic / audit topic / preconditions / steps / expected outcomes 포함
- fixture 파일 참조 구조 포함

### `integration/tests/data/*.json`
현재 포함된 예시:
- representative Class 1 input fixture
- representative Class 2 insufficient-context fixture
- representative Class 0 E001 emergency fixture
- expected routing result fixtures

이 파일들은 canonical truth가 아니라 **integration-side sample fixture**다.

### `integration/tests/integration_test_runner_skeleton.py`
역할:
- scenario JSON 로드
- scenario가 참조하는 fixture JSON 로드
- fixture path 누락/오타/JSON syntax 오류 fail-fast 검출
- machine-readable summary 출력

현재 단계에서는 **scenario / fixture loading skeleton**이다.

### `integration/measurement/class_wise_latency_profiles.md`
역할:
- Class 0 / Class 1 / Class 2 경로별 latency measurement 목적 정의
- capture point 개념 정리
- repeated-run summary 지향 원칙 정리
- measurement profile 문서화 예시 제공

---

## 3. 하위 디렉터리 역할

### `integration/tests/`
- end-to-end integration test harness
- expected outcome comparison logic
- canonical asset consistency test support
- cross-device behavioral validation

### `integration/tests/data/`
- reusable test fixtures
- sample contexts / expected outputs / payload examples
- consistency fixtures for policy/schema/rules validation

### `integration/scenarios/`
- deterministic scenarios
- stress scenarios
- fault-injection scenario definitions
- reproducible evaluation case packages

### `integration/measurement/`
- optional out-of-band latency evaluation support
- timing capture notes
- measurement profiles
- result templates and export references

---

## 4. 경계 원칙

- `integration/`은 **operational control plane**이 아니다.
- Mac mini hub-side policy truth를 재정의하지 않는다.
- Raspberry Pi evaluation path를 우회하는 별도 제어 경로를 만들지 않는다.
- ESP32 physical node behavior를 직접 대체하지 않는다.
- measurement support는 evaluation-only support path로 유지한다.

즉, `integration/`의 목적은 **검증, 재현성, 평가**이지, 운영 로직 대체가 아니다.

---

## 5. 참조해야 하는 canonical baseline

`integration/`에서 사용하는 정책/스키마/용어 기준은 모두 `common/`의 frozen assets를 따른다.

대표 기준:
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

---

## 6. 기본 사용 흐름

현재 상태에서 가능한 최소 흐름은 다음과 같다.

1. scenario skeleton 작성 또는 복제
2. `integration/tests/data/`의 fixture 참조
3. `integration_test_runner_skeleton.py`로 scenario + fixture loading 검증
4. 이후 expected outcome comparator / MQTT adapter / audit observer 추가

예:

```bash
python3 integration/tests/integration_test_runner_skeleton.py --pretty
```

특정 scenario 지정 예:

```bash
python3 integration/tests/integration_test_runner_skeleton.py \
  --scenario integration/scenarios/baseline_scenario_skeleton.json \
  --pretty
```

---

## 7. 현재 단계에서 권장되는 다음 작업

1. expected outcome comparator 추가
2. scenario loader unit test 추가
3. canonical consistency smoke test 추가
4. `integration/measurement/`에 result template 문서 추가
5. `integration/scenarios/`에 Class 0 / Class 2 / stale / conflict skeleton 추가
6. 이후 실제 MQTT publish / audit observe adapter 추가

이후에야 `integration/`이 문서 수준을 넘어 **실제 cross-device evaluation asset layer**로 동작하게 된다.
