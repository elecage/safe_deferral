# 필수 실험 내용 및 검증 지표 정리
# Required Experiments and Verification Metrics

## 0. 문서의 역할과 적용 범위

본 문서는 제안 시스템의 실험 설계, 검증 대상, 평가 지표, 그리고 frozen asset 간의 연결 관계를 정의하는 **실험 기준 문서(experiment baseline manifest)**이다.  
본 문서는 단순 개념 설명이 아니라, 실제 실험 스크립트·결과 표·논문 본문과 정합성을 유지하기 위한 기준 문서로 사용한다.

본 문서의 목적은 다음과 같다.

1. 어떤 실험을 반드시 수행해야 하는지 정의한다.
2. 각 실험이 어떤 frozen policy/schema asset에 의존하는지 명시한다.
3. 현재 구현 범위(Current Implemented Scope)와 향후 확장 범위(Extended Experimental Scope)를 구분한다.
4. fault taxonomy와 실제 deterministic fault profile ID를 매핑한다.
5. 논문 표/그림에 직접 연결될 수 있는 평가 지표를 고정한다.

---

## 1. Canonical Frozen Asset Versions

본 문서는 아래 frozen asset version을 기준으로 해석한다.

- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

> 주의:
> frozen asset 간 버전이 변경되면, 본 문서도 함께 갱신되어야 한다.
> 특히 policy table, validator output schema, fault injection rules 간 trigger ID 집합의 정합성을 유지해야 한다.

---

## 2. 현재 구현 범위와 확장 범위

### 2.1 Current Implemented Scope

현재 검증의 우선 대상은 **Class 1 bounded low-risk assistance**의 최소 구현 범위이다.

#### 현재 공식 low-risk action 범위
- `light_on`
- `light_off`

#### 현재 공식 target device 범위
- `living_room_light`
- `bedroom_light`

#### 현재 Safe Deferral 후보 출력 범위
- `safe_deferral`
- `deferral_reason`:
  - `ambiguous_target`
  - `insufficient_context`
  - `policy_restriction`
  - `unresolved_multi_candidate`

따라서 현재 실험에서 **자율 low-risk actuation**은 조명 2개 on/off 경로를 기준으로 검증한다.

### 2.2 Extended Experimental Scope

다음 항목은 시스템의 확장 실험 범위로 간주한다.

- additional actuator nodes (예: blind, doorlock, siren/buzzer)
- richer device-state context
- larger multi-node simulation
- richer caregiver workflow
- additional low-risk action coverage beyond the current authoritative catalog

이 확장 범위는 별도 표기 없이 현재 구현 범위와 혼용해서 해석해서는 안 된다.

---

## 3. 실험 설계의 전체 원칙

본 연구의 실험은 시스템이 얼마나 “똑똑한가”보다, **얼마나 안전하게 분기하고, 멈추고, 위임하는가**를 검증하는 데 초점을 둔다.

필수 실험은 다음 세 가지 패키지로 구성한다.

- **패키지 A**: 정책 분기 정확성 및 안전성
- **패키지 B**: 클래스별 지연 시간
- **패키지 C**: Fault Injection 기반 강건성

필요 시 다음 선택 실험을 추가할 수 있다.

- **패키지 D (선택)**: Class 2 notification payload completeness
- **패키지 E (선택)**: Grace period cancellation / false dispatch suppression

---

## 4. 정책 및 스키마 해석 기준

### 4.1 Policy Router 입력 기준
Policy Router는 다음 정보를 입력으로 받는다.

- `source_node_id`
- `routing_metadata`
- `pure_context_payload`

이 중 LLM prompt 구성에 전달 가능한 것은 오직 `pure_context_payload`이다.  
`routing_metadata`의 ingest timestamp, network status, audit correlation 정보는 안전 fallback 및 감사 추적을 위한 정보이며, LLM 해석 입력으로 직접 혼합하지 않는다.

### 4.2 Context 해석 기준
실험 입력은 `context_schema_v1_0_0_FROZEN.json`을 만족해야 한다.  
즉, 다음 세 블록이 모두 존재해야 한다.

- `trigger_event`
- `environmental_context`
- `device_states`

### 4.3 Candidate Action 해석 기준
Class 1 low-risk path에서 LLM 또는 bounded assistance layer가 생성하는 후보는 `candidate_action_schema_v1_0_0_FROZEN.json`을 만족해야 한다.  
후보는 다음 두 부류만 허용한다.

1. 단일 저위험 액션 후보
2. `safe_deferral`

### 4.4 Deterministic Validator 해석 기준
후보 검증 결과는 `validator_output_schema_v1_1_0_FROZEN.json`을 만족해야 하며, 최종 결과는 다음 셋 중 하나다.

- `approved`
- `safe_deferral`
- `rejected_escalation`

### 4.5 Authoritative Emergency Interpretation
현재 authoritative emergency trigger 집합은 `policy_table_v1_1_2_FROZEN.json`의 `class_0_emergency.triggers`를 기준으로 해석한다.  
현재 canonical emergency trigger는 다음 다섯 개다.

- `E001`: high temperature threshold crossing
- `E002`: emergency triple-hit pattern
- `E003`: smoke detected state trigger
- `E004`: gas detected state trigger
- `E005`: fall detected event trigger

---

## 5. 실험 패키지 A: 정책 분기 정확성 및 안전성 검증

### 5.1 목적
입력 이벤트와 센서/상태 컨텍스트가 의도한 **Class 0 / Class 1 / Class 2** 또는 **Safe Deferral**로 올바르게 처리되는지 검증한다.

### 5.2 현재 구현 범위에서의 핵심 질문
- current policy table 기준 emergency event는 올바르게 Class 0으로 라우팅되는가?
- current low-risk action catalog 범위 내에서 단일 admissible action만 승인되는가?
- ambiguity 또는 insufficient context 상황에서 unsafe actuation 없이 `safe_deferral` 또는 `class_2_escalation`으로 전환되는가?

### 5.3 권장 노드 구성
#### 최소 구성
- ESP32 실물 입력 노드: 2~4개
  - bounded button node
  - representative environmental sensor node
  - optional emergency representative node
- ESP32 실물 출력 노드: 1~2개
  - living_room_light representative output
  - bedroom_light representative output or warning output
- Raspberry Pi virtual node: 0~2개
- STM32 timing node: 필수 아님

### 5.4 시나리오 구성 요소
#### 입력 이벤트
- single click / bounded button trigger
- triple-hit emergency trigger
- threshold-crossing emergency trigger
- state-trigger emergency (`smoke_detected`, `gas_detected`)
- event-trigger emergency (`fall_detected`)
- long-press

#### 컨텍스트
- temperature
- illuminance
- occupancy_detected
- smoke_detected
- gas_detected
- living_room_light
- bedroom_light
- other device states if included in the current experiment profile

### 5.5 기대 결과 분류
- Class 0 emergency
- Class 1 validated low-risk action
- Safe Deferral
- Class 2 escalation

### 5.6 필수 검증 지표
- Class Routing Accuracy
- Emergency Miss Rate
- Unsafe Actuation Rate (UAR)
- Safe Deferral Rate (SDR)
- Class 2 Handoff Correctness

---

## 6. 실험 패키지 B: 클래스별 지연 시간 검증

### 6.1 목적
Class 0, Class 1, Class 2가 서로 다른 경로를 가지므로, 경로별 지연 시간을 분리 계측한다.

### 6.2 권장 구성
#### 최소 구성
- ESP32 입력 노드: 2개
- ESP32 출력 노드: 1~2개
- STM32 timing node: 1개 권장
- Raspberry Pi virtual node: 0개

### 6.3 필수 측정 경로
- Class 0: emergency trigger → local protective action / external dispatch
- Class 1: button trigger → validated low-risk action OR safe deferral decision
- Class 2: button or policy failure event → caregiver notification dispatch

### 6.4 필수 측정 지표
- p50 latency
- p95 latency
- p99 latency (optional)
- deferral decision latency
- notification dispatch latency

### 6.5 계측 원칙
가능하면 서비스망과 분리된 **out-of-band hardware measurement network**를 사용한다.  
GPIO/interrupt 기반 timestamp를 통해 trigger-to-action 경로를 독립 측정하는 것이 바람직하다.

---

## 7. 실험 패키지 C: Fault Injection 기반 강건성 검증

### 7.1 목적
정상 상황이 아니라 stale context, missing state, ambiguity, 통신 지연 등 장애 조건에서도 안전 정책이 유지되는지 검증한다.

### 7.2 authoritative generation principle
Fault injection 수치는 임의 하드코딩하지 않는다.  
반드시 다음 frozen asset을 파싱하여 동적으로 생성한다.

- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`

### 7.3 fault taxonomy
본 문서의 fault taxonomy는 다음 네 부류로 구성한다.

#### (A) Policy-declared emergency injection
- 목적: declared emergency predicate가 policy-consistent class 0 path로 라우팅되는지 검증

#### (B) Context conflict injection
- 목적: low-risk path에서 ambiguity 발생 시 unsafe actuation 없이 safe fallback으로 전환되는지 검증

#### (C) Sensor/State staleness injection
- 목적: freshness limit 초과 시 fail-safe escalation이 이루어지는지 검증

#### (D) Missing state injection
- 목적: required input/context 누락 시 보수적 fallback이 발생하는지 검증

### 7.4 deterministic fault profile mapping table

| Fault Taxonomy | Deterministic Profile ID | Expected Safe Outcome |
|---|---|---|
| A1. Temperature emergency | `FAULT_EMERGENCY_01_TEMP` | `class_0_emergency` |
| A2. Button triple-hit emergency | `FAULT_EMERGENCY_02_BUTTON_TRIPLE_HIT` | `class_0_emergency` |
| A3. Smoke emergency | `FAULT_EMERGENCY_03_SMOKE` | `class_0_emergency` |
| A4. Gas emergency | `FAULT_EMERGENCY_04_GAS` | `class_0_emergency` |
| A5. Fall emergency | `FAULT_EMERGENCY_05_FALL` | `class_0_emergency` |
| B1. Context conflict | `FAULT_CONFLICT_01_GHOST_PRESS` | `safe_deferral` or `class_2_escalation` |
| C1. Staleness | `FAULT_STALENESS_01` | `class_2_escalation` |
| D1. Missing context | `FAULT_MISSING_CONTEXT_01` | `class_2_escalation` |

> 주의:
> fault profile ID는 frozen rules file을 기준으로 유지한다.
> 새로운 deterministic profile을 추가할 경우 본 표도 함께 갱신해야 한다.

### 7.5 emergency pass/fail interpretation
Emergency-focused fault injection 결과는 반드시 canonical policy table에 정의된 trigger ID와 일치해야 한다.  
즉,
- `FAULT_EMERGENCY_01_TEMP`는 `E001`,
- `FAULT_EMERGENCY_02_BUTTON_TRIPLE_HIT`는 `E002`,
- `FAULT_EMERGENCY_03_SMOKE`는 `E003`,
- `FAULT_EMERGENCY_04_GAS`는 `E004`,
- `FAULT_EMERGENCY_05_FALL`은 `E005`
의 policy-consistent class 0 outcome으로 평가되어야 한다.

### 7.6 필수 검증 지표
- Safe Fallback Rate
- UAR under Faults
- Misrouting under Faults
- Emergency Protection Preservation

---

## 8. 선택 실험 패키지 D: Class 2 Payload Completeness

### 8.1 목적
Class 2 escalation이 발생했을 때 caregiver notification payload가 필요한 필드를 빠짐없이 포함하는지 검증한다.

### 8.2 필수 포함 항목
- `event_summary`
- `context_summary`
- `unresolved_reason`
- `manual_confirmation_path`

### 8.3 권장 추가 항목
- `audit_correlation_id`
- `timestamp_ms`
- `notification_channel`
- `source_layer`

### 8.4 검증 지표
- Payload Completeness Rate
- Missing Field Rate
- Notification Readiness Rate

### 8.5 검증 기준 스키마
본 실험은 `class_2_notification_payload_schema_v1_0_0_FROZEN.json`을 기준으로 검증한다.

---

## 9. 선택 실험 패키지 E: Grace Period Cancellation / False Dispatch Suppression

### 9.1 목적
external dispatch grace period가 존재하는 emergency path에서 false dispatch suppression이 적절히 작동하는지 확인한다.

### 9.2 검증 지표
- cancellation success rate
- false dispatch suppression rate
- emergency preservation correctness

---

## 10. 논문에 반드시 들어가야 할 핵심 지표

- Class Routing Accuracy
- Emergency Miss Rate
- Unsafe Actuation Rate (UAR)
- Safe Deferral Rate (SDR)
- Class 2 Handoff Correctness
- Class-wise Latency (p50 / p95 / optional p99)
- UAR under Fault Injection
- Misrouting under Faults

---

## 11. 논문 표/그림 추천 구성

### Figure 1. Class-wise latency distribution
- Class 0
- Class 1
- Class 2
- p50 / p95 / optional p99

### Table 1. Policy-routing and safety results
- scenario ID
- expected class
- observed class
- unsafe actuation occurrence
- deferral occurrence
- pass/fail

### Table 2. Fault injection results
- fault taxonomy
- deterministic profile ID
- expected safe behavior
- observed behavior
- UAR under fault
- routing correctness
- pass/fail

### Table 3. Experimental node composition
- package
- physical ESP32 input nodes
- physical ESP32 output nodes
- Raspberry Pi virtual nodes
- STM32 timing nodes
- purpose

### Table 4. Current implemented scope vs extended scope
- category
- current authoritative scope
- extended scope
- included in main paper results (Y/N)

---

## 12. 논문용 최소 실험 세트

### 필수
- 정책 분기 정확성 + 안전성 결과 표 1개
- Class-wise latency figure 1개
- Fault injection 결과 표 1개
- Experimental node composition 표 1개

### 권장 추가
- Class 2 payload completeness 결과 1개
- false dispatch suppression 결과 1개

---

## 13. 최종 실험 설계 원칙

1. 실험은 “똑똑함”보다 **안전한 분기, 보류, 위임**을 검증해야 한다.
2. 현재 구현 범위와 확장 범위를 혼용하지 않는다.
3. emergency 판정은 반드시 current canonical policy table을 기준으로 한다.
4. fault injection은 frozen policy/schema/rules를 파싱하여 동적으로 생성한다.
5. 논문 표/그림의 모든 결과는 deterministic profile 또는 canonical scenario ID와 연결 가능해야 한다.
6. frozen asset version이 변경되면 본 문서도 함께 갱신한다.
