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

---

## 실행 예시

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

---

## 경계 원칙

- 운영 로직 구현 위치가 아니다.
- Mac mini operational code를 대체하지 않는다.
- Raspberry Pi simulation runtime을 대체하지 않는다.
- ESP32 firmware를 대체하지 않는다.

즉, 이 디렉터리는 **검증 harness 계층**이다.

---

## 다음 권장 작업

1. expected outcome comparator 추가
2. scenario file loader unit test 추가
3. canonical consistency smoke test 추가
4. 실제 MQTT publish / audit observe adapter는 별도 단계에서 추가
