# 지체장애인을 위한 프라이버시 인지 엣지 스마트홈 시스템

This repository contains the frozen assets, scripts, schemas, policies, experiment documents, and future codebase for a privacy-aware safe deferral smart-home system.

## System Overview

신체적·언어적 제약 상황에서의 접근성 높은 상호작용을 위한 **프라이버시 인지형 엣지 스마트홈 시스템**이다.  
본 시스템은 클라우드 의존 없이 로컬 엣지 허브에서 동작하며, 극도로 제한된 입력 환경에서도 사용자의 의도를 안전하게 처리할 수 있도록 설계된다.

영문 설명:  
**A Privacy-Aware Edge Smart Home System with Context-Aware LLM Assistance for Accessible Interaction under Physical and Speech Limitations**

---

## Target User Group

본 시스템의 최우선 사용자 대상은 **신체적, 언어적 제약(Physical and Speech Limitations)을 복합적으로 겪고 있어 상용 스마트홈 기기(일반 음성 비서, 터치스크린 등)를 독자적으로 사용하기 어려운 취약 계층**이다.

### 1. 중증 신체 장애인 및 운동 기능 저하 사용자
- 뇌성마비(Cerebral Palsy), 근육병(Myopathy), 소아마비(Polio), 척수 손상, 뇌졸중 등으로 인해 상·하지의 미세한 운동 제어나 이동이 어려운 사용자
- 스마트폰 터치나 정교한 스위치 조작이 어려워, 주먹으로 내리치거나 발로 차는 형태의 **단일 물리 타격 버튼(single-hit or kick-style bounded button input)** 같은 극도로 제한된 입력 수단에 의존하는 사용자

### 2. 언어 및 발화 제약이 있는 사용자
- 조음장애(Dysarthria) 또는 신체적 피로 등으로 인해 명확한 발음이 어려운 사용자
- 기존 상용 음성 비서가 요구하는 표준 발화 조건을 만족하기 어려운 사용자
- 본 시스템은 이러한 표준 밖 입력 환경에서도 **bounded LLM assistance**를 통해 의도 해석을 보조한다

### 3. 일상 기능 저하를 겪는 고령층
- 노화로 인해 근력, 시력, 반응 속도, 인지 기능이 저하되어 일상적인 가사 활동과 안전 관리에 어려움을 겪는 사용자

### 4. 보호자 및 활동지원사
- 직접적인 1차 사용자는 아니지만, 시스템 생태계의 필수적인 2차 사용자
- 시스템이 입력의 모호성, 컨텍스트 부족, 응급 판단 등을 감지해 **Safe Deferral** 또는 **Caregiver Escalation** 경로로 전환했을 때, 보안 처리된 아웃바운드 통신(Telegram 등)을 통해 상황 알림과 제한적 수동 개입 권한을 받는 주체

본 시스템은 자유로운 대화나 정교한 조작이 어려운 복합 장애 당사자 및 고령자가 **최소한의 bounded physical input**만으로도 안전하게 스마트홈 기능을 사용할 수 있도록 돕는 **포용적(inclusive) 접근성 지원 시스템**이다.

---

## Core Objectives

### 1. 포용적 접근성 제공 (Inclusive Accessibility)
- 단일 물리 타격 버튼과 같은 극도로 제한된 입력 수단만으로도 시스템과 상호작용할 수 있도록 지원
- 자유 대화형 AI가 아니라, 엄격한 정책 및 스키마 경계 내에서 동작하는 **context-aware edge LLM assistance**를 활용

### 2. 결정론적 안전 보장 (Deterministic Safety)과 Safe Deferral
- LLM의 환각이나 잘못된 해석이 위험한 물리 제어(unsafe actuation)로 이어지는 것을 원천 차단
- 입력이 모호하거나 문맥이 부족하거나 센서 간 충돌이 발생할 경우, 자율 제어를 즉시 중단하고 **context-integrity-based safe deferral stage**로 전환
- 필요한 경우 bounded clarification 또는 caregiver escalation로 넘어가며, 임의의 물리 제어는 허용하지 않음

### 3. 프라이버시 인지형 엣지 아키텍처 (Privacy-Aware Edge Architecture)
- 핵심 운영 경로에서 클라우드 의존성을 배제
- 센싱, 판단, 검증, 로깅, 보조 추론을 로컬망의 Mac mini 허브 내에서 처리
- 외부 인터넷으로부터의 인바운드 접근을 차단하고, Telegram 등 제한된 아웃바운드 통신만 허용

### 4. 장애 허용성과 기계적 신뢰성 확보 (Fault Tolerance & Robustness)
- 정상 상황뿐 아니라 stale context, missing state, timeout, 버튼 패턴 오류, 센서 충돌 같은 결함 조건에서도 보수적 안전 정책이 유지되어야 함
- 이를 위해 fault injection과 closed-loop audit verification 기반의 실험 체계를 사용

---

## Current Safety Boundary

현재 frozen baseline에서 **Class 1 autonomous low-risk action**은 다음 조명 제어에 한정된다.

- `light_on` → `living_room_light`
- `light_on` → `bedroom_light`
- `light_off` → `living_room_light`
- `light_off` → `bedroom_light`

Doorlock control, door opening, blinds, TV, gas valve, stove, medication device, mobility device, and other sensitive or non-catalog actions are **not** part of the current Class 1 autonomous low-risk scope.

Doorlock may be used as a representative sensitive-actuation evaluation case, but it must not be emitted as a Class 1 LLM candidate action or approved as a validator executable payload. Sensitive actuation requests must be handled through Class 2 escalation or a separately governed manual confirmation path.

`doorbell_detected` is a required boolean field in `environmental_context`. It represents a recent doorbell or visitor-arrival signal for visitor-response interpretation. It does **not** authorize autonomous doorlock control.

Current `context_schema.device_states` does not include doorlock state. Doorlock state, manual approval state, and ACK state should be represented through experiment annotations, mock approval state, dashboard-side observation, audit artifacts, manual-confirmation-path internal state, or a future schema revision.

The authoritative low-risk action source is:

- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`

The authoritative context schema source is:

- `common/schemas/context_schema_v1_0_0_FROZEN.json`

---

## Main Scenario

본 시스템은 사용자의 제한된 물리 입력과 환경 센서 이벤트를 바탕으로, 로컬 엣지 허브(Mac mini) 내에서 클라우드 의존 없이 처리되며, 철저한 정책 기반 검증을 거쳐 동작한다.

전체 동작은 다음의 5단계 폐루프 파이프라인으로 구성된다.

### 1단계: 이벤트 발생 및 순수 컨텍스트 수집 (Input & Context Gathering)
- 사용자가 bounded physical button을 조작하거나 환경 센서가 임계치를 초과하면 이벤트가 발생
- 시스템은 네트워크 상태, 내부 지연 시간 등 운영 메타데이터를 LLM 입력에 직접 섞지 않고, 오직 순수 물리 환경 정보와 기기 상태, 트리거 이벤트 중심의 **pure context payload**를 구성
- 모든 valid context payload는 `environmental_context.doorbell_detected`를 포함해야 하며, non-visitor scenario의 기본값은 `false`이다
- visitor-response 또는 doorlock-sensitive scenario에서는 `doorbell_detected=true/false`를 통해 최근 도어벨/방문자 도착 context 유무를 표현할 수 있다
- `doorbell_detected=true`는 방문자 응답 의도 해석을 보조하는 context signal일 뿐, door unlock authorization이 아니다
- 이를 통해 LLM이 시스템 메타데이터를 환경 데이터로 오인하는 것을 방지하고, visitor-response 상황에서도 민감 액추에이션 경계를 유지한다

### 2단계: 정책 라우터 기반 위험도 분기 (Policy Routing)
가장 먼저 **Policy Router**가 입력과 컨텍스트를 분석해 최상위 정책표에 따라 다음 세 클래스 중 하나로 라우팅한다.

- **Class 0 (Emergency Override)**  
  생명 위협 가능성이 있는 응급 상황  
  예: emergency triple-hit, 화재/가스 임계치 초과  
  → LLM을 거치지 않고 결정론적으로 즉시 로컬 보호 조치를 수행하고, 이후 외부 알림 경로를 사용할 수 있음

- **Class 1 (Low-Risk Local Assistance)**  
  현재 frozen low-risk catalog에 포함된 bounded low-risk action 후보만 허용할 수 있는 상황  
  → 로컬 LLM은 자유 대화가 아니라, 엄격한 candidate action schema 안에서만 제한된 제안을 수행  
  → 현재 autonomous execution scope는 `light_on` / `light_off` 조명 제어에 한정됨

- **Class 2 (Caregiver Escalation)**  
  stale context, missing state, 필수 입력 부족, 모호성 지속, sensitive actuation request 등으로 자율 경로를 포기해야 하는 상황  
  → 처음부터 보호자 개입 또는 별도 governed manual confirmation path로 전환

### 3단계: 결정론적 안전 검증 및 Safe Deferral
Class 1 경로에서 LLM이 제안한 액션은 곧바로 실행되지 않고, **Deterministic Validator**를 통해 검증된다.

Validator는 다음 세 가지 중 하나만 허용한다.

- **실행 승인 (Approved)**  
  제안된 단일 저위험 액션이 authoritative low-risk catalog 안에서 안전하다고 판단되면 dispatcher / actuator interface로 전달

- **안전 보류 (Safe Deferral)**  
  타겟이 모호하거나, 후보가 둘 이상 남거나, 문맥이 불충분한 경우  
  → 시스템은 물리 실행을 즉시 중단하고 **context-integrity-based safe deferral stage**로 전환  
  → 이후 bounded button-based clarification 또는 제한적 확인 절차를 통해 모호성 해소를 시도

- **거부 및 에스컬레이션 (Rejected Escalation)**  
  정책을 명백히 위반하거나 실행 실패, 상태 ACK 불일치, 하드 실패, sensitive actuation request가 의심되면 제어를 차단하고 Class 2로 전환

### 4단계: 보호자 권한 위임 및 알림 (Caregiver Escalation)
Class 2 경로로 전환되거나 Safe Deferral 이후에도 모호성이 해소되지 않으면, 시스템은 안전한 아웃바운드 통신(Telegram 등)을 통해 보호자에게 제한적 권한을 위임한다.

알림 페이로드에는 다음이 포함될 수 있다.
- 이벤트 요약
- 현재 환경/기기 컨텍스트 요약
- visitor-response context summary, including `doorbell_detected` when relevant
- unresolved reason
- 수동 확인 또는 제한적 승인 경로

이때 `manual_confirmation_path`는 보호자의 review, confirm, deny, intervene 경로를 설명하는 필드이며, 그 자체가 autonomous low-risk execution이나 sensitive actuation을 승인하는 권한 필드는 아니다.

### 5단계: 폐루프 피드백 및 로컬 감사 로깅 (Closed-loop Feedback & Audit Logging)
- 제어 명령 이후에는 반드시 **상태 ACK**를 확인
- ACK가 정해진 시간 안에 도착하지 않으면 실행 실패로 간주하고 보수적으로 처리
- 모든 라우팅 결과, 검증 결과, Safe Deferral 사유, escalation 이벤트, ACK 이벤트는 클라우드가 아니라 **Mac mini 내부의 SQLite single-writer audit pipeline**에 저장

이 구조를 통해 본 시스템은 다음 원칙을 지킨다.

> **모호하거나 정보가 부족한 경우, 시스템은 임의로 물리 제어하지 않고 멈추거나 위임한다.**

---

## System Verification Scenario

### 1. 정책 분기 정확성 및 안전성 검증 (Policy Routing Correctness & Safety)
입력 이벤트와 센서 컨텍스트가 의도한 **Class 0 / Class 1 / Class 2**로 올바르게 라우팅되는지 확인한다.

- 입력 이벤트 조건
  - 버튼 1회 타격
  - emergency triple-hit
  - long-press
  - 센서 임계치 초과
  - doorbell / visitor-arrival event via `doorbell_detected`
- 환경 컨텍스트 조건
  - 온도
  - 조도
  - 점유 상태
  - smoke_detected
  - gas_detected
  - doorbell_detected
  - 기기 상태
  - 센서 freshness
  - 통신 상태

기대 동작:
- **Class 0**: 즉시 로컬 보호 조치
- **Class 1**: bounded low-risk local assistance under the authoritative light-control catalog
- **Class 2** 또는 **Safe Deferral**: 자율 실행 차단 후 caregiver escalation 또는 bounded clarification
- **Sensitive actuation request**: autonomous execution 차단 후 Class 2 escalation 또는 별도 governed manual confirmation path
- **Doorlock-sensitive visitor-response**: `doorbell_detected` may affect interpretation or explanation, but autonomous unlock remains blocked

### 2. 클래스별 지연 시간 검증 (Class-wise Latency)
각 클래스는 서로 다른 경로를 가지므로 지연 시간도 경로별로 측정한다.

- **Class 0**: emergency trigger → local protective action / external dispatch
- **Class 1**: button event → validated low-risk action / Safe Deferral decision
- **Class 2**: button event or visitor-response sensitive request → caregiver notification dispatch

측정 지표:
- p50 latency
- p95 latency
- p99 latency (optional)
- deferral decision latency
- notification dispatch latency

실험 신뢰도를 높이기 위해, 가능하면 **서비스망과 분리된 out-of-band hardware measurement network**를 사용한다.  
예를 들어 STM32 기반 timing node 또는 별도 계측 노드를 이용해 GPIO / interrupt 기반 timestamp를 수집하면, 운영 트래픽과 독립적으로 trigger-to-action 경로를 정밀 계측할 수 있다.

### 3. Fault Injection 기반 강건성 검증 (Robustness under Fault Injection)
정상 상황이 아니라 stale context, missing state, 통신 지연, 버튼 패턴 오류 등 장애 조건에서도 안전 정책이 유지되는지 검증한다.

대표 fault 유형:
- threshold-crossing emergency injection
- context conflict injection
- sensor/state staleness injection
- missing state injection
- missing `doorbell_detected` context for strict visitor-response payload validation

핵심 기준:
- **Unsafe Actuation Rate (UAR) = 0%**
- expected safe outcome과 observed behavior의 일치
- emergency protection preservation

### 4. 폐루프 자동 검증 (Closed-loop Automated Verification)
Raspberry Pi 5 기반 fault injection과 Mac mini의 verification-safe audit stream을 이용해, 사람이 수동으로 보지 않아도 기대되는 safe outcome과 실제 결과를 비교해 Pass/Fail을 자동 판정한다.

---

## Experimental Validation Infrastructure

실험 인프라는 다음처럼 역할 분리된다.

- **Mac mini**: safety-critical operational edge hub, including policy routing, local LLM reasoning, deterministic validation, safe deferral, caregiver escalation/approval handling, ACK, and audit logging
- **Raspberry Pi 5**: experiment-side support region, including Monitoring / Experiment Dashboard, simulation, replay, fault injection, closed-loop experiment orchestration, progress/status publication, result summary, graph/CSV export, and evaluation artifact generation
- **ESP32**: bounded physical node layer (button, sensor, actuator/warning interface)
- **Optional STM32 or dedicated timing node**: out-of-band latency measurement infrastructure

Raspberry Pi 5 hosts the experiment and monitoring dashboard. The dashboard is a support-side visibility and experiment-operations console; it is not the policy authority, validator authority, caregiver approval authority, or primary operational hub. Mac mini may expose telemetry, audit summaries, and control-state topics consumed by the Raspberry Pi 5 dashboard.

For visitor-response and doorlock-sensitive experiments, Raspberry Pi 5 orchestration and dashboard layers should expose `doorbell_detected` state, autonomous-unlock-blocked status, caregiver escalation state, manual approval state, ACK state, and audit completeness. Doorlock state is not currently part of the official `device_states` context contract and should be handled through experiment annotations, dashboard-side observation, audit artifacts, manual-confirmation-path internal state, or a future schema revision.

이 분리는 운영 경로와 실험/계측 경로를 구분하여 재현성과 계측 신뢰도를 높이기 위한 것이다.

---

## Repository Structure

- `common/`: shared frozen assets such as policies, schemas, documentation, and terminology
- `mac_mini/`: Mac mini installation, configuration, verification scripts, runtime files, and future code
- `rpi/`: Raspberry Pi installation, configuration, verification scripts, experiment/dashboard runtime, and future experiment code
- `esp32/`: embedded firmware, device-specific implementation assets, and bounded physical node code
- `integration/`: end-to-end tests, scenarios, and experiment assets

---

## Current Scope

This repository is being initialized with:
- frozen policy assets
- frozen schema assets
- installation/configuration/verification scripts
- terminology freeze records
- architecture and experiment documents

---

## Canonical Term

**context-integrity-based safe deferral stage**
