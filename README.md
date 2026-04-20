# 지체장애인을 위한 프라이버시 인지 엣지 스마트홈 시스템

This repository contains the frozen assets, scripts, schemas, policies, and future codebase for the safe deferral smart-home system.

## System Overview
 신체 및 언어적 제약 상황에서의 접근성 높은 상호작용을 위한 맥락 인지형 LLM 보조 기반 프라이버시 인지 엣지 스마트홈 시스템(A Privacy-Aware Edge Smart Home System with Context-Aware LLM Assistance for Accessible Interaction under Physical and Speech Limitations)

## Target User Group
본 시스템의 최우선 사용자 대상은 **신체적, 언어적 제약(Physical and Speech Limitations)을 복합적으로 겪고 있어 상용 스마트홈 기기(일반 음성 비서, 터치스크린 등)를 독자적으로 사용하기 어려운 취약 계층**
구체적인 타겟 사용자 그룹은 다음과 같이 분류

### 1. 중증 신체 장애인 및 운동 기능 저하 사용자
  * 뇌성마비(Cerebral Palsy), 근육병(Myopathy), 소아마비(Polio), 척수 손상이나 뇌졸중 등으로 인해 상/하지의 미세한 운동 제어나 이동이 어려운 사용자들.
  * 스마트폰 터치나 정교한 스위치 조작이 불가능하여, 주먹으로 내리치거나 발로 차는 형태의 **단일 물리 타격 버튼(Kick buttons)과 같이 극도로 제한된 입력 수단**에 의존해야 하는 그룹을 포함.
    
### 2. 언어 및 발화 제약이 있는 사용자 (조음장애 등)
  * 조음장애(Dysarthria)를 앓고 있거나 신체적 피로감 등으로 인해 명확한 발음이 어려운 사용자들.
  * 기존 상용 음성 비서(Google Home, Alexa 등)는 명확한 발음을 요구하기 때문에 이들의 명령을 제대로 인식하지 못하는 한계가 있으며, 심한 경우 신체적 장애와 발화 장애가 동반되어 나타나기 때문에 입력 수단이 극히 제한.
  * 본 시스템은 이러한 표준 밖의 입력 환경에서도 엣지 LLM을 활용해 사용자의 의도를 추론하여 이들을 지원.
    
### 3. 일상 기능 저하를 겪는 고령층 (Aging Population)
  * 노화로 인해 근력 및 시력이 떨어지거나 인지 기능이 저하되어 일상적인 가사 활동, 전자기기 조작, 안전 관리에 어려움을 겪는 노인들.
    
### 4. 보호자 및 활동지원사 (Caregivers and Support Staff)
  * 직접적인 1차 사용자는 아니지만, 시스템 생태계의 필수적인 2차 사용자.
  * 스마트홈 시스템이 입력의 모호성을 감지하여 '안전 보류(Safe Deferral)' 상태로 전환하거나 응급 상황(Class 0, Class 2)을 판단했을 때, **보안 처리된 아웃바운드 통신(Telegram 등)을 통해 상황 알림과 수동 제어 권한을 에스컬레이션(Escalation) 받는 주체**
   
자유로운 대화나 정교한 조작이 불가능한 복합 장애 당사자 및 고령자가 단일 타격 버튼과 같은 최소한의 입력만으로도 안전하게 자율 제어 혜택을 누릴 수 있도록 돕는 **포용적(Inclusive) 접근성 지원 시스템**


## Core Objectives
  * **포용적 접근성 제공** (Inclusive Accessibility):
    * 신체적, 언어적 제약이 있는 사용자도 단일 물리 타격 버튼과 같이 극도로 제한된 입력 수단만으로 시스템과 원활하게 상호작용할 수 있도록 지원하는 것을 일차적 목적으로 함
    * 이를 위해 자유 대화형 AI가 아닌, 철저히 통제된 샌드박스 경계 내에서 동작하는 맥락 인지형(Context-Aware) 엣지 LLM 보조 모듈을 활용하여 사용자의 의도를 추론
   
  * **결정론적 안전 보장** (Deterministic Safety & Safe Deferral):
    * LLM의 환각(Hallucination)이나 잘못된 판단이 위험한 물리적 기기 제어(Unsafe Actuation)로 이어지는 것을 원천 차단하는 안전 보전형(Safety-Critical) 시스템을 구축
    * 입력이 모호하거나 문맥이 부족한 상황, 센서 데이터 간의 충돌이 발생하는 경우에는 자율 제어를 즉각 중단하고 '안전 보류(Safe Deferral)' 상태로 전환
    * 이후 점진적 명확화 요청(iCR)을 통해 모호성을 안전하게 해소하거나, 보호자에게 권한을 위임(Class 2 Caregiver Escalation)하여 사고를 방지
  * **완벽한 프라이버시 보호 및 엣지 독립성** (Privacy-Aware Edge Architecture):
    * 가장 민감한 개인 공간인 가정 내의 프라이버시를 완벽히 지키기 위해, 운영 핵심 아키텍처에서 클라우드 의존성을 전면 배제
    * 모든 센싱 데이터 수집, 판단, AI 추론 로직은 로컬망에 위치한 Mac mini 허브 내에서 독립적으로
    * 외부 인터넷으로부터의 인바운드 접근을 전면 차단하고 텔레그램 등을 이용한 아웃바운드 보안 통신만 허용하여 공격 표면(Attack Surface)을 실질적으로 축소
  * **장애 허용성 및 기계적 신뢰성 확보** (Fault Tolerance & Robustness):
    * 단순히 정상 작동을 지원하는 것을 넘어 센서 데이터 지연(Staleness), 상태 누락(Missing State), 통신 타임아웃, 예기치 못한 버튼 패턴 오류 등의 물리/네트워크 결함 조건에서도 보수적인 안전 정책이 흔들림 없이 유지됨을 증명
    * 이를 위해 결함 주입(Fault Injection)과 폐루프 자동 검증(Closed-loop Audit) 파이프라인을 구축하여 강건성을 기계적으로 보장한다
   
## Main Scenario
  * 본 시스템(프라이버시 인지 엣지 스마트홈)의 동작 시나리오는 신체적/언어적 제약을 가진 사용자의 극도로 제한된 물리적 입력(예: 단일 버튼 타격)을 바탕으로, 엣지 허브(Mac mini) 내에서 클라우드 의존 없이 100% 로컬로 처리되며, 철저한 안전 검증을 거쳐 동작.
  * 전체 동작 시나리오는 입력 발생부터 실행 및 보호자 개입까지 크게 5단계의 폐루프(Closed-loop) 파이프라인으로 진행

### 1단계: 이벤트 발생 및 순수 컨텍스트 수집 (Input & Context Gathering)
  * 사용자가 물리적 버튼을 조작하거나(예: 1회 타격, 연속 3회 타격, 길게 누르기) 환경 센서가 임계치를 초과하면 이벤트가 발생.
  * 이때 시스템은 네트워크 상태나 지연 시간 같은 시스템 내부 메타데이터를 배제하고, 오직 순수 물리 환경(온도, 조도, 연기/가스 등), 기기 상태, 그리고 트리거 이벤트만으로 구성된 pure_context_payload를 수집하여 래핑(Wrapping).
  * 이는 후속 단계에서 LLM이 시스템 데이터를 환경 데이터로 착각하여 환각(Hallucination)을 일으키는 것을 원천 차단.

### 2단계: 정책 라우터를 통한 위험도 기반 분기 (Policy Routing)
가장 먼저 'Policy Router'가 수집된 데이터를 분석하여 최상위 안전 규칙표(policy_table.json)에 따라 다음 세 가지 클래스 중 하나로 라우팅
  * **Class 0** (응급 상황 - Emergency Override):
    * 버튼의 3회 연속 타격(Triple-hit)이나 화재/가스 등 생명과 직결된 임계치 초과가 감지된 경우
    * LLM의 판단을 거치지 않고 결정론적으로 즉각적인 로컬 보호 조치(예: 모든 조명 켜기, 사이렌 작동)를 실행하며, 유예 시간(Grace period) 후 외부 보호자나 응급망으로 즉시 알림을 발송
  * **Class 1** (저위험 로컬 보조 - Low-Risk Local Assistance):
    * 일상적인 1회 버튼 클릭과 같은 일반 이벤트
    * 이 데이터는 로컬 LLM으로 전달되며, LLM은 자유 대화가 아닌 엄격한 샌드박스 규격(candidate_action_schema_v1_0_0_FROZEN.json) 내에서 조명 On/Off와 같은 '단일 저위험 액션' 또는 '안전 보류(Safe Deferral)' 중 하나만을 제안
  * **Class 2** (보호자 개입 - Caregiver Escalation):
    *  센서 데이터가 너무 오래되었거나(Staleness), 필수 데이터가 누락된 경우, 자율 제어를 포기하고 처음부터 4단계의 보호자 개입 경로로 직행

### 3단계: 결정론적 안전 검증 및 안전 보류 (Deterministic Validation & Safe Deferral)
Class 1 경로에서 LLM이 제안한 액션은 곧바로 실행되지 않고 **결정론적 검증기(Deterministic Validator)**를 거쳐 실행. 
검증기는 LLM의 출력을 평가하여 다음 3가지 중 단 하나의 결과만 승인.
  * **실행 승인** (Approved): 제안된 액션이 안전하다고 판단되면 실행기(actuator_dispatcher)로 전달되어 스마트홈 기기(예: 거실 조명)를 제어
  * **안전 보류** (Safe Deferral):
    * 만약 타겟 기기가 모호하거나(Ambiguous target), 다중 후보가 경합하거나, 센서 문맥이 불충분한 경우, **시스템은 물리적 실행을 즉시 중단(Safe Deferral)**
    * 이후 iCR Handler(점진적 명확화 핸들러)로 넘어가 버튼 기반의 추가 입력을 요구하여 모호성을 스스로 해소하려고 시도
  * **거부 및 에스컬레이션** (Rejected Escalation): 보안/안전 정책을 명백히 위반한 LLM의 제안이거나 액추에이터 고장이 의심되는 하드 실패(Hard failure) 상황일 경우, 제어를 즉각 차단하고 Class 2 에스컬레이션으로 넘김

### 4단계: 보호자 권한 위임 및 알림 (Caregiver Escalation)
  * Class 2 경로로 에스컬레이션되거나 iCR 시도 후에도 모호성이 해결되지 않은 경우, 시스템은 인바운드가 전면 차단된 안전한 아웃바운드 통신(Telegram 등)을 통해 **보호자에게 권한을 안전하게 위임(Handoff)**
  * 전송되는 알림 페이로드에는 이벤트 요약, 현재 환경/기기 컨텍스트, 제어 보류 사유(Unresolved Reason), 그리고 보호자가 직접 제어할 수 있는 수동 승인 경로(Manual confirmation path)가 모두 포함되어 보호자가 상황을 완벽히 인지하고 대처할 수 있도록 도와줌

### 5단계: 폐루프 피드백 및 로컬 감사 로깅 (Closed-loop Feedback & Audit Logging)
기기 제어 명령이 전달된 후에는 단순 발송으로 끝나지 않음
  * 상태 ACK 확인:
    * 시스템은 반드시 물리적 기기의 상태가 성공적으로 변경되었는지(ACK) 확인.
    * 정해진 시간 내에 ACK가 오지 않으면 기기 고장으로 간주하여 실행 실패 처리 후 Class 2로 에스컬레이션.
  * 프라이버시 인지 로컬 로깅:
    * 모든 라우팅 이벤트, Validator의 승인/거부 판정, 안전 보류 사유 등은 클라우드로 전송되지 않고 Mac mini 내부의 SQLite 단일 작성자(Single-writer) DB에 감사 로그(Audit Log)로 안전하게 격리 저장
    * 이러한 다단계 시나리오를 통해, 본 시스템은 사용자 편의를 제공하면서도 "**모호하거나 정보가 부족할 때는 절대 임의로 물리적 기기를 제어하지 않고 멈춘다**"는 결정론적 안전성(Deterministic Safety)을 보장

## System Verification Scenario    
### 1. 정책 분기 정확성 및 안전성 검증 (Policy Routing Correctness & Safety)
정상적인 환경 및 모호한 상황에서 입력 이벤트와 센서 컨텍스트가 의도한 Class 0, 1, 2로 올바르게 라우팅되는지 확인하는 시나리오
  * **입력 이벤트 조건**: 버튼 1회 타격, 응급 연속 타격(triple-hit), 길게 누르기(long-press), 센서 임계치 초과.
  * **환경 컨텍스트 조건**: 온도, 조도, 기기 상태, 센서 최신화(freshness), 통신 상태.
  * **기대 동작 시나리오**:
    * **Class 0** (응급): 생명 위협 시 LLM을 거치지 않고 즉각적인 로컬 보호 조치 실행.
    * **Class 1** (저위험 보조): 단일 저위험 액션(low-risk local assistance) 승인 및 실행.
    * **Class 2** (보호자 개입) 및 안전 보류: 컨텍스트가 부족하거나 대상이 모호할 경우, 자율 실행(Unsafe Actuation)을 즉시 차단하고 안전 보류(Safe Deferral + iCR) 상태로 전환하거나 보호자에게 에스컬레이션.
      
### 2. 클래스별 지연 시간 검증 (Class-wise Latency)
제안한 아키텍처가 엣지(Edge) 환경에서 실용적인 반응 속도를 보장하는지 경로별로 분리하여 계측하는 시나리오
  * **Class 0 지연 시간**: 응급 트리거 발생부터 로컬 보호 액션 실행 및 외부 알림망(Dispatch) 전송까지의 시간.
  * **Class 1 지연 시간**: 버튼 이벤트 발생부터 LLM 추론을 거쳐 저위험 로컬 액션이 승인되거나, 안전 보류(Safe Deferral)가 결정되기까지의 시간.
  * **Class 2 지연 시간**: 버튼 이벤트 발생 후 모호성을 감지하고 보호자에게 알림(Notification)이 발송되기까지의 시간.
  * 측정 지표: p50(중간값), p95(Tail Latency), p99 등 지연 시간 분포.
    
### 3. 결함 주입 기반 강건성 검증 (Robustness under Fault Injection)
네트워크나 센서 상태가 정상적이지 않은 장애 조건 하에서 보수적인 안전 정책이 흔들림 없이 유지되는지 Raspberry Pi 5를 통해 검증하는 시나리오. 
하드코딩 없이 사전 동결된 스키마와 정책표(policy_table.json, context_schema.json)를 동적으로 파싱하여 결함을 생성.

  * **임계치 초과 응급 주입** (Threshold-crossing emergency): 정책표의 최소 트리거 조건을 명시적으로 초과하여 생명 위협 이벤트가 Class 0으로 즉각 라우팅되는지 확인.
  * **문맥 상충 주입** (Context conflict): 상충하는 제어 근거가 동시에 존재하도록 주입하여, 물리적 자율 제어(Actuation)를 멈추고 Safe Deferral이나 Class 2로 전환되는지 확인.
  * **센서/상태 데이터 지연 주입** (Sensor/State staleness): 신선도(freshness limit) 한계를 초과한 과거의 타임스탬프를 주입하여 오래된 데이터에 대한 Fail-safe 동작을 확인.
  * **상태 누락 주입** (Missing state): 필수 키(Required keys)를 의도적으로 누락시켜, 불완전한 상태 정보 하에서 즉시 Class 2로 빠지거나 실행을 차단하는지 확인.

### 4. 폐루프 자동 검증 (Closed-loop Automated Verification)
Raspberry Pi 5 노드를 통해 주입된 결함 시나리오 결과가 사람의 수동 개입 없이 시스템 내부에서 기계적으로 판정되는 시나리오.

  * **자동 판정 흐름**: Pi 5의 검증 스크립트가 결함 페이로드를 Publish함과 동시에 Mac mini의 **'검증용 감사 스트림(verification-safe audit MQTT stream)'**을 백그라운드에서 구독.
  * **단언(Assert) 기준**: Mac mini의 최종 라우팅 및 로깅 결과가 기대되는 안전 귀결(Safe Outcome: Safe Deferral, Class 2, Class 0)과 일치하는지 비교하여 자동으로 Pass/Fail을 판정. 특히 결함 주입 상황에서 **Unsafe Actuation Rate(위험 작동률)가 0%**로 완벽하게 억제되는지가 핵심 합격 기준
    
## Repository Structure

- `common/`: shared frozen assets such as policies, schemas, documentation, and terminology
- `mac_mini/`: Mac mini installation, configuration, verification scripts, runtime files, and future code
- `rpi/`: Raspberry Pi installation, configuration, verification scripts, and future code
- `integration/`: end-to-end tests, scenarios, and experiment assets

## Current Scope

This repository is being initialized with:
- frozen policy assets
- frozen schema assets
- installation/configuration/verification scripts
- terminology freeze records

## Canonical Term

**context-integrity-based safe deferral stage**
