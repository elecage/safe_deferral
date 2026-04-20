# 필수 실험 내용 및 검증 지표 정리

## 1. 실험 설계의 전체 원칙

본 논문의 실험은 시스템이 얼마나 “똑똑한가”보다, **얼마나 안전하게 분기하고, 멈추고, 위임하는가**를 검증하는 데 초점을 두어야 한다.  
따라서 실험은 다음 네 가지 축을 중심으로 구성하는 것이 적절하다.

1. 정책 분기 정확성 (Policy Routing Correctness)
2. 안전성 (Safety under Ambiguity and Insufficient Context)
3. 지연 시간 (Class-wise Latency)
4. 강건성 (Robustness under Fault Injection)

필수 실험은 아래 3개 패키지로 묶어 제시하는 것이 가장 적절하다.

- **패키지 A**: 정책 분기 정확성 + 안전성
- **패키지 B**: 클래스별 지연 시간
- **패키지 C**: Fault Injection 기반 강건성

---

## 2. 실험 노드 구성 원칙

본 연구의 실험 노드는 다음 세 계층으로 구분한다.

### 2.1 ESP32 실물 노드
ESP32 기반 실물 노드는 실제 물리 입력 및 출력 경로를 검증하기 위해 사용한다.

#### 대표 입력 실물 노드
- bounded button touch / kick-style button node
- 온습도 센서 노드
- 가스 센서 노드
- 화재 감지 센서 노드

#### 대표 출력 실물 노드
- 전등 on/off 노드
- 도어락 노드
- 필요 시 경고 부저 또는 사이렌 노드

### 2.2 Raspberry Pi 기반 가상 노드
Raspberry Pi 5 기반 가상 노드는 다음과 같은 실험에 사용한다.

- 다중 노드 시나리오
- 대량 센서/상태 시뮬레이션
- fault injection
- stale / missing / conflict 조건 검증
- fail-safe 및 closed-loop automated verification

실물 ESP32 노드를 다수 제작하는 것은 비용과 관리 측면에서 비효율적이므로, 다중 노드 및 결함 주입 실험은 Raspberry Pi 가상 노드 계층이 담당하는 것이 적절하다.

### 2.3 Optional STM32 Timing Node
클래스별 지연 시간은 가능하면 서비스망과 분리된 **out-of-band hardware measurement network**에서 측정한다.

이를 위해 다음과 같은 별도 계측 노드를 사용할 수 있다.

- STM32 기반 timing node
- 또는 별도의 dedicated timing / measurement node

이 노드는 trigger-to-action 경로를 운영 트래픽과 독립적으로 계측하기 위한 실험용 계측 인프라이다.

---

## 3. 실험 패키지 A: 정책 분기 정확성 및 안전성 검증

### 3.1 목적
입력 이벤트와 센서 컨텍스트가 의도한 **Class 0 / Class 1 / Class 2**로 올바르게 라우팅되는지 확인하고, 특히 모호하거나 문맥이 부족한 상황에서 **unsafe actuation** 없이 **Safe Deferral** 또는 **Caregiver Escalation**으로 안전하게 처리되는지 검증한다.

### 3.2 권장 노드 구성
이 패키지는 **실물 노드 중심**으로 구성하는 것이 적절하다.

#### 권장 최소 구성
- **ESP32 실물 입력 노드: 4개**
  - bounded button node 1개
  - 온습도 센서 노드 1개
  - 가스 센서 노드 1개
  - 화재 감지 센서 노드 1개
- **ESP32 실물 출력 노드: 2개**
  - 전등 on/off 노드 1개
  - 도어락 또는 경고 출력 노드 1개
- **Raspberry Pi 가상 노드: 0~2개**
  - 필요 시 보조 컨텍스트 제공용
- **Timing node: 0개**
  - 필수 아님

#### 권장 표준 구성
- ESP32 실물 노드 총 **6개**
- Raspberry Pi 가상 노드 **0~4개**
- STM32 timing node **0개**

### 3.3 실험 시나리오 구성
시나리오 기반 테스트셋을 구축한다. 각 시나리오는 다음 요소를 포함한다.

#### 입력 이벤트
- 버튼 1회 타격
- emergency triple-hit
- long-press
- 센서 임계치 초과

#### 컨텍스트
- 온도
- 조도
- 기기 상태
- 센서 freshness
- 통신 상태

#### 기대 클래스
- Class 0
- Class 1
- Class 2

#### 기대 동작
- 즉시 로컬 보호조치
- low-risk local assistance
- Safe Deferral + context-integrity-based safe deferral stage
- caregiver escalation

### 3.4 시나리오 최소 권장 수
- Class 0 관련: 15~20개
- Class 1 관련: 20~25개
- Class 2 관련: 20~25개
- 총합: 최소 50~70개

### 3.5 필수 검증 지표
- Class Routing Accuracy
- Emergency Miss Rate
- Unsafe Actuation Rate (UAR)
- Safe Deferral Rate (SDR)
- Class 2 Handoff Correctness

---

## 4. 실험 패키지 B: 클래스별 지연 시간 검증

### 4.1 목적
제안한 아키텍처가 실제 edge 환경에서 충분히 빠르게 작동하는지 검증한다.  
특히 **Class 0, Class 1, Class 2**는 서로 다른 동작 경로를 가지므로, 지연 시간도 **경로별로 분리하여 측정**해야 한다.

### 4.2 권장 노드 구성
이 패키지는 **실물 노드 + timing node** 조합이 핵심이다.

#### 권장 최소 구성
- **ESP32 실물 입력 노드: 2개**
  - bounded button node 1개
  - emergency representative input node 1개
- **ESP32 실물 출력 노드: 2개**
  - 전등/릴레이 계열 노드 1개
  - 도어락 또는 경고 출력 노드 1개
- **Raspberry Pi 가상 노드: 0개**
- **STM32 timing node: 1개 필수**

#### 권장 표준 구성
- ESP32 실물 노드 총 **4~5개**
- STM32 timing node **1개**
- 여유가 있으면 STM32 timing node **2개**
  - 1개: 입력 기준 타이밍
  - 1개: 출력/ACK 기준 타이밍

### 4.3 권장 계측 방식
가능하면 **Out-of-band hardware measurement network**를 사용한다.

예를 들어 STM32 또는 별도 계측 노드를 이용해 서비스망과 분리된 상태에서 GPIO / interrupt 기반 timestamp를 수집하는 방식이 바람직하다.

### 4.4 필수 측정 경로
- Class 0: emergency trigger → local protective action / external dispatch
- Class 1: button event → validated low-risk local action / Safe Deferral decision
- Class 2: button event → caregiver notification dispatch

### 4.5 필수 검증 지표
- p50 latency
- p95 latency
- p99 latency (선택)
- Deferral decision latency
- Notification dispatch latency

---

## 5. 실험 패키지 C: Fault Injection 기반 강건성 검증

### 5.1 목적
정상 상황이 아니라 **센서 오류, 통신 지연, stale context, 버튼 패턴 오류** 같은 장애 조건에서도 안전 정책이 유지되는지 검증한다.

### 5.2 권장 노드 구성
이 패키지는 **Raspberry Pi 기반 가상 노드 중심**으로 구성하는 것이 적절하다.

#### 권장 최소 구성
- **ESP32 실물 입력 노드: 1~2개**
  - bounded button node 1개
  - 필요 시 representative physical sensor node 1개
- **ESP32 실물 출력 노드: 1개**
  - representative actuator or warning output node 1개
- **Raspberry Pi 가상 노드: 20개**
- **Timing node: 0개**

#### 권장 표준 구성
- ESP32 실물 노드 총 **2~3개**
- Raspberry Pi 가상 노드 **30개**
- 확장 실험 시 Raspberry Pi 가상 노드 **40개**까지 가능

### 5.3 Fault Injection 구현 원칙
결함 주입 수치는 스크립트에 임의로 하드코딩하지 않는다. 반드시 다음 frozen artifacts에서 규칙과 임계치를 파싱하여 동적으로 생성한다.

- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`

### 5.4 필수 fault 유형

#### (A) Threshold-crossing emergency injection
- 목적: 생명 위협 이벤트가 Class 0으로 즉각 라우팅되는지 검증
- 생성 규칙:
  - routing policy artifact에서 각 emergency rule의 minimal triggering predicate를 파싱
  - 단일 임계치 기반이면 해당 threshold를 명시적으로 초과
  - 복합 조건이면 정책을 만족시키는 최소 센서 조합 생성

#### (B) Context conflict injection
- 목적: 상충하는 저위험 제어 근거가 동시에 존재할 때, 시스템이 Unsafe Actuation 없이 Safe Deferral 또는 Class 2로 전환하는지 검증
- 생성 규칙:
  - 동일 액추에이터에 대해 둘 이상의 bounded low-risk candidate가 동시에 admissible하게 남도록 주입
  - 기대 안전 귀결은 정책표에서 도출
    - clarification 가능 시: SAFE_DEFERRAL + context-integrity-based safe deferral stage
    - 필수 문맥이 여전히 부족할 시: CLASS_2 escalation
  - 어떤 경우에도 autonomous physical actuation이 발생하면 안 된다

#### (C) Sensor/State staleness injection
- 목적: 오래된 데이터에 대한 fail-safe 동작 검증
- 생성 규칙:
  - routing policy artifact에 정의된 freshness limit를 초과하는 타임스탬프를 freshness-critical sensor field 또는 device-state field에 주입

#### (D) Missing state injection
- 목적: 불완전한 상태 정보 하에서의 보수적 안전 동작 검증
- 생성 규칙:
  - frozen context schema에 정의된 required keys를 의도적으로 누락
  - 다음 두 종류를 구분
    1. **policy-input omissions**: Class 1 진입을 막고 즉시 Class 2로 전환
    2. **validator/action-schema omissions**: 실행을 막고 Safe Deferral 또는 Class 2로 이어져야 함

### 5.5 필수 검증 지표
- Safe Fallback Rate
- UAR under Faults
- Misrouting under Faults
- Emergency Protection Preservation

---

## 6. 선택 실험

### 6.1 Class 2 Payload Completeness
- Event Summary
- Context Summary
- Unresolved Reason
- Manual Confirmation Path

### 6.2 Grace Period Cancellation Success
- cancellation success rate
- false dispatch suppression rate

---

## 7. 논문에 반드시 넣어야 할 핵심 지표 요약
- Class Routing Accuracy
- Emergency Miss Rate
- Unsafe Actuation Rate (UAR)
- Safe Deferral Rate (SDR)
- Class 2 Handoff Correctness
- Class-wise Latency (p50 / p95, 가능하면 p99)
- UAR under Fault Injection

---

## 8. 논문에 넣기 좋은 결과 표/그림 구성

### Figure 1. Class-wise latency distribution
- Class 0
- Class 1
- Class 2
- p50 / p95 (가능하면 p99)

### Table 1. Policy-routing and safety results
- Class routing accuracy
- Emergency miss rate
- UAR
- SDR
- Class 2 handoff correctness

### Table 2. Fault injection results
- fault type
- expected safe behavior
- observed behavior
- UAR under fault
- routing correctness under fault

### Table 3. Experimental node composition
- package
- physical ESP32 input nodes
- physical ESP32 output nodes
- Raspberry Pi virtual nodes
- STM32 timing nodes
- purpose

---

## 9. 논문용 최소 실험 세트 제안

### 필수 세트
- 정책 분기 정확성 + 안전성 결과 표 1개
- Class별 지연 시간 그림 1개
- Fault Injection 결과 표 1개
- Experimental node composition 표 1개

### 가능하면 포함
- grace period cancellation 또는 payload completeness 중 하나

---

## 10. 권장 실험 구성 요약

### 패키지 A: 정책 분기 정확성 + 안전성
- ESP32 실물 입력 노드: 4개
- ESP32 실물 출력 노드: 2개
- Raspberry Pi 가상 노드: 0~4개
- STM32 timing node: 0개

### 패키지 B: 클래스별 지연 시간
- ESP32 실물 노드: 4~5개
- Raspberry Pi 가상 노드: 0개
- STM32 timing node: 1개 권장, 2개면 이상적

### 패키지 C: Fault Injection 기반 강건성
- ESP32 실물 노드: 2~3개
- Raspberry Pi 가상 노드: 20개 최소, 30개 권장, 40개 확장 가능
- STM32 timing node: 0개

---

## 11. 최종 실험 설계 원칙

- 실물 물리 경로 검증은 **ESP32 실물 노드** 중심으로 수행한다.
- 다중 노드, 대규모 시나리오, stale/missing/conflict, fail-safe 검증은 **Raspberry Pi 기반 가상 노드** 중심으로 수행한다.
- 클래스별 지연 시간은 가능하면 **STM32 기반 out-of-band timing node**를 이용해 서비스망과 분리하여 계측한다.
- 모든 실험은 “얼마나 똑똑한가”보다 **얼마나 안전하게 분기하고, 멈추고, 위임하는가**를 검증해야 한다.