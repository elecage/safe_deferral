# integration

이 디렉터리는 **Mac mini / Raspberry Pi / ESP32를 가로지르는 cross-device integration, scenario execution, evaluation, measurement 지원 자산**을 두는 공간이다.

`integration/`은 특정 단일 디바이스의 구현 폴더가 아니다.  
대신 다음 역할을 담당한다.

- end-to-end integration test
- reproducible scenario definition
- fault-injection and closed-loop evaluation support
- optional out-of-band timing / latency measurement support
- reusable test-data and expected-outcome assets
- experiment preflight readiness 설계 및 measurement-node readiness 지원

즉, `integration/`은 **시스템 전체를 검증하고 재현성을 확보하기 위한 cross-device layer**다.

---

## 1. 현재 하위 구조

```text
integration/
├── README.md
├── requirements.md
├── tests/
│   ├── README.md
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
    ├── class_wise_latency_profiles.md
    ├── experiment_preflight_readiness_design.md
    └── stm32_nucleo_h723zg_measurement_node.md
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

### Python runner status

Python runner/comparator code has been removed during the current documentation
and contract cleanup phase. `integration/tests/data/` and `integration/scenarios/`
remain as active contract and fixture assets. A runner may be reintroduced only
after the canonical architecture, scenario, policy, schema, MQTT, and payload
baseline is stable.

### `integration/measurement/class_wise_latency_profiles.md`
역할:
- Class 0 / Class 1 / Class 2 경로별 latency measurement 목적 정의
- capture point 개념 정리
- repeated-run summary 지향 원칙 정리
- measurement profile 문서화 예시 제공

### `integration/measurement/experiment_preflight_readiness_design.md`
역할:
- 실험별 required node / service / asset / measurement dependency 설계
- READY / DEGRADED / BLOCKED / UNKNOWN 판정 모델 정리
- Home Assistant 실험 대시보드와 연결 가능한 preflight readiness 설계 정리
- operational node와 out-of-band measurement node 분리 원칙 정리

### `integration/measurement/stm32_nucleo_h723zg_measurement_node.md`
역할:
- STM32 Nucleo-H723ZG를 out-of-band measurement node로 해석하는 기준 정리
- timing capture / latency evidence / export 역할 정의
- operational control path와 분리된 계측 노드 개발 방향 정리

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
- experiment preflight readiness design
- dedicated measurement node support notes

---

## 4. 경계 원칙

- `integration/`은 **operational control plane**이 아니다.
- Mac mini hub-side policy truth를 재정의하지 않는다.
- Raspberry Pi evaluation path를 우회하는 별도 제어 경로를 만들지 않는다.
- ESP32 physical node behavior를 직접 대체하지 않는다.
- measurement support는 evaluation-only support path로 유지한다.
- STM32 timing/measurement node는 operational actuator/sensor node가 아니라 **out-of-band evidence collection node**로 유지한다.

즉, `integration/`의 목적은 **검증, 재현성, 평가**이지, 운영 로직 대체가 아니다.

---

## 5. 참조해야 하는 canonical baseline

`integration/`에서 사용하는 정책/스키마/용어 기준은 모두 `common/`의 frozen assets를 따른다.

대표 기준:
- `common/policies/policy_table.json`
- `common/policies/low_risk_actions.json`
- `common/policies/fault_injection_rules.json`
- `common/schemas/context_schema.json`
- `common/schemas/candidate_action_schema.json`
- `common/schemas/policy_router_input_schema.json`
- `common/schemas/validator_output_schema.json`
- `common/schemas/class2_notification_payload_schema.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

---

## 6. 기본 사용 흐름

현재 상태에서 가능한 최소 흐름은 다음과 같다.

1. scenario skeleton 작성 또는 복제
2. `integration/tests/data/`의 fixture 참조
3. JSON syntax와 fixture reference를 문서/리뷰 기준으로 확인
4. 필요 시 `integration/measurement/experiment_preflight_readiness_design.md`를 바탕으로 실험 전 readiness 조건 정의
5. timing/latency 실험이 필요한 경우 `integration/measurement/stm32_nucleo_h723zg_measurement_node.md`를 참고하여 measurement node 요구사항 정리
6. 이후 runner / expected outcome comparator / MQTT adapter / audit observer를 재도입

---

## 7. 현재 단계에서 권장되는 다음 작업

1. non-Python 또는 추후 재도입 runner 검증 방식 결정
2. expected outcome comparator 설계 재정의
3. scenario loader validation rule 문서화
4. canonical consistency smoke test 설계
5. `integration/measurement/`에 result template 문서 추가
6. experiment registry / node registry 설계 자산 추가
7. Home Assistant 실험 대시보드와 연결될 preflight readiness panel 설계
8. STM32 measurement node heartbeat / export contract 구체화
9. 이후 실제 MQTT publish / audit observe adapter 추가

이후에야 `integration/`이 문서 수준을 넘어 **실제 cross-device evaluation asset layer**로 동작하게 된다.
