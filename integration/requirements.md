# integration requirements

이 문서는 `integration/` 계층이 충족해야 하는 **cross-device integration / scenario / evaluation / measurement 요구사항**을 정리한다.

이 문서는 정책 truth를 재정의하지 않는다.  
정책/스키마/용어의 authoritative baseline은 `common/`의 frozen assets다.

---

## 1. 목적 요구사항

`integration/` 계층은 다음을 가능하게 해야 한다.

- cross-device integration validation
- deterministic scenario replay
- fault-injection outcome verification
- expected safe outcome comparison
- reproducible experiment packaging
- optional class-wise latency evaluation support

---

## 2. 구조 요구사항

최소 구조는 다음을 포함해야 한다.

```text
integration/
├── README.md
├── requirements.md
├── tests/
├── scenarios/
└── measurement/
```

추가적으로 reusable fixture 관리를 위해 다음 구조를 권장한다.

```text
integration/tests/data/
```

---

## 3. tests 요구사항

`integration/tests/`는 다음 요구사항을 만족해야 한다.

- end-to-end integration test를 둘 수 있어야 한다.
- expected outcome 비교 로직을 둘 수 있어야 한다.
- canonical policy/schema/rules consistency fixture를 소비할 수 있어야 한다.
- Mac mini / RPi / ESP32를 가로지르는 behavior assertion을 표현할 수 있어야 한다.
- closed-loop outcome verification과 연계될 수 있어야 한다.

---

## 4. scenarios 요구사항

`integration/scenarios/`는 다음 요구사항을 만족해야 한다.

- deterministic scenario를 정의할 수 있어야 한다.
- randomized or stress scenario metadata를 둘 수 있어야 한다.
- fault-injection profile과 expected safe outcome을 함께 표현할 수 있어야 한다.
- canonical emergency family `E001`~`E005`와 정합적인 scenario를 포함할 수 있어야 한다.
- reproducible paper-evaluation package로 확장 가능해야 한다.

---

## 5. measurement 요구사항

`integration/measurement/`는 optional path이지만, 사용 시 다음 요구사항을 만족해야 한다.

- operational control path와 분리되어야 한다.
- class-wise latency evaluation 지원이 가능해야 한다.
- timing capture point 설명을 둘 수 있어야 한다.
- measurement profile / result template / export format reference를 둘 수 있어야 한다.
- optional STM32 timing node 또는 dedicated measurement node 관련 문서를 둘 수 있어야 한다.

---

## 6. test data 요구사항

`integration/tests/data/`는 다음 요구사항을 만족해야 한다.

- sample events
- sample contexts
- expected routing results
- expected validator outcomes
- representative fault cases
- representative safe deferral cases
- representative escalation cases
- representative notification payload examples
- canonical consistency fixtures

이런 reusable fixture를 담을 수 있어야 한다.

---

## 7. 경계 요구사항

- `integration/`은 Mac mini operational hub를 대체하지 않는다.
- `integration/`은 Raspberry Pi evaluation path를 우회하는 control path를 만들지 않는다.
- `integration/`은 ESP32 bounded node를 추상적으로 검증할 수는 있지만, 그 자체가 physical node firmware를 대체하지 않는다.
- `integration/measurement/`는 evaluation-only support path로 유지되어야 한다.

---

## 8. 정합성 요구사항

`integration/`의 모든 scenario, test, measurement support는 다음 frozen assets와 정합적이어야 한다.

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

## 9. 완료 기준

`integration/` 계층은 최소한 다음이 만족될 때 구조적으로 준비된 것으로 본다.

- 폴더 구조가 존재한다.
- 각 하위 디렉터리의 README 또는 역할 문서가 존재한다.
- 요구사항 문서가 존재한다.
- tests / scenarios / measurement의 역할 구분이 명확하다.
- canonical baseline과의 정합성 원칙이 문서화되어 있다.
