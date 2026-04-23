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

---

## 다음 권장 작업

1. deterministic baseline scenario 추가
2. canonical emergency family aligned scenario 추가
3. conflict / stale / missing-state scenario 추가
4. scenario metadata schema 또는 manifest 규칙 문서화
