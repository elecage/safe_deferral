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
│   └── data/
│      └── README.md
├── scenarios/
│   └── README.md
└── measurement/
    └── README.md
```

---

## 2. 하위 디렉터리 역할

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

## 3. 경계 원칙

- `integration/`은 **operational control plane**이 아니다.
- Mac mini hub-side policy truth를 재정의하지 않는다.
- Raspberry Pi evaluation path를 우회하는 별도 제어 경로를 만들지 않는다.
- ESP32 physical node behavior를 직접 대체하지 않는다.
- measurement support는 evaluation-only support path로 유지한다.

즉, `integration/`의 목적은 **검증, 재현성, 평가**이지, 운영 로직 대체가 아니다.

---

## 4. 참조해야 하는 canonical baseline

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

## 5. 현재 단계에서 권장되는 다음 작업

1. `integration/requirements.md`를 기준으로 요구사항 확정
2. `integration/scenarios/`에 deterministic scenario skeleton 추가
3. `integration/tests/data/`에 sample fixture package 추가
4. `integration/tests/`에 integration test runner skeleton 추가
5. 필요 시 `integration/measurement/`에 class-wise latency profile 문서 추가

이후에야 `integration/`이 문서 수준을 넘어 실제 검증 자산 계층으로 동작할 수 있다.
