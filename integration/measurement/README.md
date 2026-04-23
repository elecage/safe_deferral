# integration/measurement

이 디렉터리는 **optional out-of-band timing / latency evaluation support assets**를 둔다.

이 영역은 operational control path가 아니라 **evaluation-only support path**다.

---

## 목적

다음을 지원한다.

- class-wise latency evaluation
- timing capture point 설명
- measurement profile 관리
- result template / export format 관리
- optional STM32 timing node 또는 dedicated measurement node 관련 문서화

---

## 포함 가능한 대상

- latency experiment profiles
- timing capture notes
- wiring references
- result templates
- reproducibility-oriented measurement summaries
- timing node support notes

---

## 경계 원칙

- operational decision path에 개입하지 않는다.
- Mac mini hub-side runtime authority를 대체하지 않는다.
- measurement support는 평가를 위한 보조 경로일 뿐이다.

---

## 다음 권장 작업

1. class-wise latency profile 문서 추가
2. timing capture point 문서 추가
3. result template 추가
4. optional timing node support note 추가
