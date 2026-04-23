# integration/scenarios

이 디렉터리는 **deterministic scenario, stress scenario, fault-injection scenario, reproducible evaluation package**를 두는 공간이다.

---

## 목적

이 디렉터리는 다음을 가능하게 해야 한다.

- deterministic scenario replay
- fault-injection case packaging
- expected safe outcome 정의
- reproducible paper-evaluation support
- canonical emergency family `E001`~`E005`와 정합적인 scenario 구성

---

## 개발자가 먼저 읽어야 하는 문서

JSON skeleton만 보면 의미를 빠르게 파악하기 어려울 수 있으므로, 실제 검토자는 먼저 아래 문서를 보는 것을 권장한다.

- `scenario_review_guide.md`

이 문서는 다음을 설명한다.
- 각 scenario가 실제로 무엇을 시험하는지
- 왜 필요한지
- 어떤 결과가 안전한지
- 어떤 결과가 위험 신호인지
- 실제 사용 맥락에서 어떻게 읽어야 하는지

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
- current implemented scope 기준의 low-risk autonomous actuation 범위는 `required_experiments.md`와 정렬되어야 한다.

---

## 다음 권장 작업

1. E002~E005 전용 payload fixture 추가
2. randomized stress metadata skeleton 추가
3. expected outcome comparator와 scenario 연동 adapter 추가
4. 실제 MQTT publish / audit observe adapter 추가
5. class-wise latency profile과 scenario 연결 문서화
