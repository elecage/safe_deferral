# integration/tests/data

이 디렉터리는 **reusable integration test fixtures**를 둔다.

대표 예시:
- sample events
- sample contexts
- expected routing results
- expected validator outputs
- representative fault cases
- representative safe deferral cases
- representative escalation cases
- representative notification payload examples
- canonical consistency fixtures

---

## 목적

테스트마다 fixture를 중복 생성하지 않고, 재사용 가능한 입력/기대결과 세트를 유지한다.

이 디렉터리의 자산은 다음과 정합적이어야 한다.
- `common/policies/`
- `common/schemas/`
- `common/terminology/`

---

## 다음 권장 작업

1. sample context fixture 추가
2. expected routing result fixture 추가
3. fault case fixture 추가
4. notification payload example fixture 추가
