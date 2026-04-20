# 필수 실험 내용 및 검증 지표 정리

## 1. 실험 설계의 전체 원칙

본 논문의 실험은 시스템이 얼마나 “똑똑한가”보다, **얼마나 안전하게 분기하고, 멈추고, 위임하는가**를 검증하는 데 초점을 두어야 한다. 따라서 실험은 다음 네 가지 축을 중심으로 최소 구성으로 압축하는 것이 적절하다.

  1. 정책 분기 정확성(Policy Routing Correctness)
  1. 안전성(Safety under Ambiguity and Insufficient Context)
  1. 지연 시간(Class-wise Latency)
  1. 강건성(Robustness under Fault Injection)

필수 실험은 아래 3개 패키지로 묶어 제시하는 것이 가장 적절하다.

* **패키지 A**: 정책 분기 정확성 + 안전성
* **패키지 B**: 클래스별 지연 시간
* **패키지 C**: Fault injection 기반 강건성

## 2. 필수 실험 1: 정책 분기 정확성 및 안전성 검증

### 2.1 목적

입력 이벤트와 센서 컨텍스트가 의도한 **Class 0 / Class 1 / Class 2**로 올바르게 라우팅되는지 확인하고, 특히 모호하거나 문맥이 부족한 상황에서 **unsafe actuation** 없이 **Safe Deferral** 또는 **Caregiver Escalation**으로 안전하게 처리되는지 검증한다.

### 2.2 실험 시나리오 구성
시나리오 기반 테스트셋을 구축한다. 각 시나리오는 다음 요소를 포함한다.

* 입력 이벤트
  * 버튼 1회 타격
  * emergency triple-hit
  * long-press
  * 센서 임계치 초과
* 컨텍스트
  * 온도
  * 조도
  * 기기 상태
  * 센서 freshness
  * 통신 상태
* 기대 클래스
  * Class 0
  * Class 1
  * Class 2
* 기대 동작
  * 즉시 로컬 보호조치
  * low-risk local assistance
  * Safe Deferral + iCR
  * caregiver escalation

### 2.3 시나리오 최소 권장 수

* Class 0 관련: 15~20개
* Class 1 관련: 20~25개
* Class 2 관련: 20~25개
* 총합: 최소 50~70개

### 2.4 필수 검증 지표
* Class Routing Accuracy
* Emergency Miss Rate
* Unsafe Actuation Rate (UAR)
* Safe Deferral Rate (SDR)
* Class 2 Handoff Correctness

## 3. 필수 실험 2: 클래스별 지연 시간 검증

### 3.1 목적

제안한 architecture가 실제 edge 환경에서 충분히 빠르게 작동하는지 검증한다. 특히 **Class 0, Class 1, Class 2**는 서로 다른 동작 경로를 가지므로, 지연 시간도 **경로별로 분리하여 측정**해야 한다.

### 3.2 권장 계측 방식

가능하면 **Out-of-band hardware measurement network**를 사용한다. 예를 들어 STM32 또는 별도 계측 노드를 이용하여 서비스망과 분리된 상태에서 GPIO/interrupt 기반 timestamp를 수집하는 방식이 바람직하다.

### 3.3 필수 측정 경로

* Class 0: emergency trigger → local protective action / external dispatch
* Class 1: button event → validated low-risk local action / Safe Deferral decision / iCR output
* Class 2: button event → caregiver notification dispatch

### 3.4 필수 검증 지표

* p50 latency
* p95 latency
* p99 latency (선택)
* Deferral decision latency
* Notification dispatch latency

## 4. 필수 실험 3: Fault Injection 기반 강건성 검증

### 4.1 목적

정상 상황이 아니라 **센서 오류, 통신 지연, stale context, 버튼 패턴 오류** 같은 장애 조건에서도 안전 정책이 유지되는지 검증한다.

### 4.2 Fault injection 구현 원칙

결함 주입 수치는 스크립트에 임의로 하드코딩하지 않는다. 반드시 다음 아티팩트에서 규칙과 임계치를 파싱하여 동적으로 생성한다.

* policy_table.json
* context_schema.json
* fault_injection_rules.json

### 4.3 필수 fault 유형

#### (A) Threshold-crossing emergency injection

* 목적: 생명 위협 이벤트가 Class 0으로 즉각 라우팅되는지 검증
* 생성 규칙:
  * policy_table.json에서 각 emergency rule의 minimal triggering predicate를 파싱한다.
  * rule이 단일 임계치 기반이면 그 threshold를 명시적으로 초과한다.
  * rule이 복합 조건이면 해당 정책을 만족시키는 최소 센서 조합을 생성한다.

#### (B) Context conflict injection

* 목적: 상충하는 저위험 제어 근거가 동시에 존재할 때, 시스템이 Unsafe Actuation 없이 Safe Deferral 또는 Class 2로 전환하는지 검증
* 생성 규칙:
  * 동일 액추에이터에 대해 둘 이상의 bounded low-risk candidate가 동시에 admissible하게 남도록 주입한다.
  * 기대 안전 귀결(expected safe outcome)은 정책표에서 도출한다:
    * clarification 가능 시: SAFE_DEFERRAL + iCR
    * 필수 문맥이 여전히 부족할 시: CLASS_2 escalation
  * 어떤 경우에도 autonomous physical actuation이 발생하면 안 된다.

#### (C) Sensor/State staleness injection

* 목적: 오래된 데이터에 대한 fail-safe 동작 검증
* 생성 규칙:
  * policy_table.json에 정의된 freshness limit를 초과하는 타임스탬프를 freshness-critical sensor field 또는 device-state field에 주입한다.

#### (D) Missing state injection

* 목적: 불완전한 상태 정보 하에서의 보수적 안전 동작 검증
* 생성 규칙:
  * context_schema.json에 정의된 required keys를 의도적으로 누락한다.
  * 다음 두 종류를 구분한다:
    1. **policy-input omission**s: Class 1 진입을 막고 즉시 Class 2로 전환해야 함
    1. **validator/action-schema omissions**: 실행을 막고 Safe Deferral 또는 Class 2로 이어져야 함

### 4.4 필수 검증 지표

* Safe Fallback Rate
* UAR under Faults
* Misrouting under Faults
* Emergency Protection Preservation

## 5. 선택 실험

### 5.1 Class 2 Payload Completeness
* Event Summary
* Context Summary
* Unresolved Reason
* Manual Confirmation Path
### 5.2 Grace Period Cancellation Success
* cancellation success rate
* false dispatch suppression rate

## 6. 논문에 반드시 넣어야 할 핵심 지표 요약
* Class Routing Accuracy
* Emergency Miss Rate
* Unsafe Actuation Rate (UAR)
* Safe Deferral Rate (SDR)
* Class 2 Handoff Correctness
* Class-wise Latency (p50 / p95, 가능하면 p99)
* UAR under Fault Injection

## 7. 논문에 넣기 좋은 결과 표/그림 구성

* Figure 1. Class-wise latency distribution
  * Class 0
  * Class 1
  * Class 2
  * p50/p95 (가능하면 p99)
* Table 1. Policy-routing and safety results
  * Class routing accuracy
  * Emergency miss rate
  * UAR
  *  SDR
  * Class 2 handoff correctness
* Table 2. Fault injection results
  * fault type
  * expected safe behavior
  * observed behavior
  * UAR under fault
  * routing correctness under fault

## 8. 논문용 용 최소 실험 세트 제안

### 필수 세트
* 정책 분기 정확성 + 안전성 결과 표 1개
* Class별 지연 시간 그림 1개
* Fault injection 결과 표 1개

### 가능하면 포함
* grace period cancellation 또는 payload completeness 중 하나