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

## 경계 원칙

- 운영 로직 구현 위치가 아니다.
- Mac mini operational code를 대체하지 않는다.
- Raspberry Pi simulation runtime을 대체하지 않는다.
- ESP32 firmware를 대체하지 않는다.

즉, 이 디렉터리는 **검증 harness 계층**이다.

---

## 다음 권장 작업

1. integration test runner skeleton 추가
2. expected outcome comparator 추가
3. scenario file loader test 추가
4. canonical consistency smoke test 추가
