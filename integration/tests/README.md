# integration/tests

이 디렉터리는 **cross-device integration test harness와 system-level behavior verification 자산**을 둔다.

주요 목적:
- end-to-end integration test
- expected outcome assertion
- canonical asset consistency check support
- closed-loop behavior validation

---

## 포함 가능한 대상

- integration test runner
- scenario-based assertion logic
- expected routing / validator / escalation result checks
- canonical policy/schema/rules consistency test support
- ESP32 linked bounded input/output integration checks
- optional measurement-linked validation support

---

## 현재 반영된 skeleton

### `integration_test_runner_skeleton.py`
역할:
- scenario JSON 로드
- scenario가 참조하는 fixture JSON 로드
- fixture path 누락/오타/JSON syntax 오류를 fail-fast로 검출
- machine-readable summary 출력

현재 단계에서 이 runner는 **scenario / fixture loading skeleton**이다.
즉, 실제 MQTT publish, audit subscription, expected outcome assertion까지는 아직 하지 않는다.

### `expected_outcome_comparator.py`
역할:
- observed result JSON 로드
- expected outcome fixture JSON 로드
- 현재 supported field에 대해 pass/fail 비교
- machine-readable comparison summary 출력

현재 comparator가 비교하는 대표 필드:
- `expected_route_class` ↔ `route_class`
- `expected_routing_target` ↔ `routing_target`
- `expected_llm_invocation_allowed` ↔ `llm_invocation_allowed`
- `expected_safe_outcome` ↔ `safe_outcome`
- `canonical_emergency_family` ↔ `canonical_emergency_family`

현재 단계에서는 **bounded field comparator skeleton**이다.
즉, canonical truth를 재정의하지 않고 integration-side expected fixture와 observed result를 비교하는 최소 골격이다.

---

## 실행 예시

### 1. scenario / fixture loading skeleton 실행
저장소 루트에서:

```bash
python3 integration/tests/integration_test_runner_skeleton.py --pretty
```

특정 scenario를 지정하려면:

```bash
python3 integration/tests/integration_test_runner_skeleton.py \
  --scenario integration/scenarios/baseline_scenario_skeleton.json \
  --pretty
```

예상 결과:
- scenario id
- scenario path
- step count
- resolved payload fixture paths
- resolved expected fixture paths

이 JSON summary가 출력된다.

### 2. expected outcome comparator 실행
예시 observed file이 있다고 가정하면:

```bash
python3 integration/tests/expected_outcome_comparator.py \
  --observed path/to/observed_result.json \
  --expected integration/tests/data/expected_routing_class1.json \
  --pretty
```

예상 결과:
- pass/fail
- compared fields
- mismatch list
- observed path
- expected path

이 JSON summary가 출력된다.

---

## 경계 원칙

- 운영 로직 구현 위치가 아니다.
- Mac mini operational code를 대체하지 않는다.
- Raspberry Pi simulation runtime을 대체하지 않는다.
- ESP32 firmware를 대체하지 않는다.

즉, 이 디렉터리는 **검증 harness 계층**이다.

---

## 다음 권장 작업

1. scenario file loader unit test 추가
2. canonical consistency smoke test 추가
3. comparator를 runner와 연결하는 adapter 추가
4. 실제 MQTT publish / audit observe adapter는 별도 단계에서 추가
