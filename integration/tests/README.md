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

## 현재 반영된 자산

현재 cleanup phase에서는 Python runner/comparator code가 제거되어 있다.

남아 있는 active 자산:

- `integration/tests/data/`
- scenario input fixtures
- expected routing / clarification / fault outcome fixtures
- fixture documentation

향후 runner를 재도입할 때의 역할:

- scenario JSON 로드
- scenario가 참조하는 fixture JSON 로드
- fixture path 누락/오타/JSON syntax 오류 fail-fast 검출
- observed result와 expected fixture 비교
- machine-readable summary 출력

재도입되는 runner/comparator는 canonical truth를 재정의하지 않고
integration-side expected fixture와 observed result를 비교하는 검증 계층이어야 한다.

---

## 경계 원칙

- 운영 로직 구현 위치가 아니다.
- Mac mini operational code를 대체하지 않는다.
- Raspberry Pi simulation runtime을 대체하지 않는다.
- ESP32 firmware를 대체하지 않는다.

즉, 이 디렉터리는 **검증 harness 계층**이다.

---

## 다음 권장 작업

1. runner 재도입 방식 결정
2. canonical consistency smoke test 설계
3. comparator와 runner 연결 방식 재정의
4. 실제 MQTT publish / audit observe adapter 설계
