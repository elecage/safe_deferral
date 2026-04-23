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
- experiment preflight readiness에서 measurement dependency 분리 설명

---

## 포함 가능한 대상

- latency experiment profiles
- timing capture notes
- wiring references
- result templates
- reproducibility-oriented measurement summaries
- timing node support notes
- experiment preflight readiness design docs
- out-of-band measurement node development guides

---

## 현재 포함 문서

### `class_wise_latency_profiles.md`
- Class 0 / Class 1 / Class 2 경로별 latency profile 정리

### `experiment_preflight_readiness_design.md`
- 실험별 required node / required measurement node 분리 설계
- READY / DEGRADED / BLOCKED / UNKNOWN 판정 구조
- Home Assistant experiment dashboard와 연결 가능한 preflight readiness 설계

### `stm32_nucleo_h723zg_measurement_node.md`
- STM32 Nucleo-H723ZG 기반 out-of-band measurement node의 역할과 경계
- timing capture / export / dashboard readiness 연계 방향
- operational control path와 분리된 측정 노드 개발 가이드

---

## 경계 원칙

- operational decision path에 개입하지 않는다.
- Mac mini hub-side runtime authority를 대체하지 않는다.
- measurement support는 평가를 위한 보조 경로일 뿐이다.
- STM32 timing node는 actuator/sensor operational node가 아니라 **out-of-band evidence collection node**다.

---

## 다음 권장 작업

1. result template 추가
2. timestamp export contract 정리
3. STM32 measurement node heartbeat/status contract 정리
4. experiment registry와 measurement dependency 연결
5. Home Assistant 실험 대시보드 readiness panel 설계와 연결
