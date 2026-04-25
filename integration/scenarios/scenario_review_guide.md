# scenario_review_guide.md

이 문서는 `integration/scenarios/`에 있는 scenario skeleton들을 **개발자가 실제 사용 맥락과 연결해서 검토하기 쉽게 설명**하기 위한 안내서다.

JSON 파일 자체는 loader, runner, comparator가 읽기 쉽게 구성되어 있지만, 실제 검토자는 다음이 더 중요하다.

- 이 시나리오가 무엇을 시험하는가
- 왜 필요한가
- 어떤 결과가 나오면 안전한가
- 어떤 결과가 나오면 문제가 있는가
- 장애인과 고령자의 실제 생활 맥락에서 어떤 의미가 있는가

이 문서는 그 질문에 답하기 위한 **developer-oriented review guide**다.

이 문서는 canonical policy truth를 재정의하지 않는다.  
정책/스키마/용어의 authoritative baseline은 `common/`의 frozen assets에 남는다.

---

## 0. 현재 architecture / policy / schema 기준으로 읽는 법

Scenario review는 다음 현재 기준을 전제로 해야 한다.

```text
Active policy baseline:
common/policies/policy_table_v1_2_0_FROZEN.json

Low-risk action catalog:
common/policies/low_risk_actions_v1_1_0_FROZEN.json

Pure context schema:
common/schemas/context_schema_v1_0_0_FROZEN.json

Class 2 notification schema:
common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json

Class 2 clarification interaction schema:
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json

MQTT topic registry:
common/mqtt/topic_registry_v1_0_0.json
```

기본 해석 원칙:

- scenario는 canonical truth가 아니라 integration/evaluation asset이다.
- scenario는 frozen policy, frozen schema, MQTT topic registry, interface matrix를 소비한다.
- scenario는 threshold, required key, trigger predicate, allowed action scope를 새로 정의하지 않는다.
- MQTT topic은 `safe_deferral/...` namespace를 따라야 한다.
- legacy `smarthome/...` topic은 신규 scenario 기준으로 사용하지 않는다.
- Class 0 emergency는 LLM을 primary decision path로 사용하지 않는다.
- Class 1 autonomous low-risk execution은 현재 frozen lighting catalog로 제한된다.
- Class 2는 terminal failure가 아니라 clarification / transition state이다.
- Class 2에서 LLM은 bounded candidate guidance만 생성할 수 있고 final decision, actuation authorization, emergency trigger 권한은 없다.
- doorlock-sensitive request는 Class 1 autonomous execution이 아니라 Class 2 clarification/escalation 또는 governed manual confirmation path로 해석해야 한다.
- `doorbell_detected`는 required visitor-response context field이지만 emergency evidence 또는 autonomous unlock authorization이 아니다.
- `llm_invocation_allowed`는 coarse legacy field일 수 있으므로, 가능하면 `llm_decision_invocation_allowed`와 `llm_guidance_generation_allowed`를 구분해 해석한다.

---

## 1. 이 시나리오 문서를 읽을 때 떠올려야 하는 실제 사용자

루트 `README.md`가 설명하듯, 이 시스템의 주요 대상은 다음과 같다.

- **중증 신체 장애인 및 운동 기능 저하 사용자**  
  예: 뇌성마비, 근육병, 척수 손상, 뇌졸중 등으로 손가락 미세 조작이나 이동이 어려운 사용자
- **언어 및 발화 제약이 있는 사용자**  
  예: 조음장애, 피로, 호흡 문제 등으로 일반 음성비서가 요구하는 또렷한 발화가 어려운 사용자
- **일상 기능 저하를 겪는 고령층**  
  예: 근력, 시력, 반응속도, 인지 기능 저하로 스마트홈 제어와 안전 관리가 어려운 사용자
- **보호자 및 활동지원사**  
  Safe Deferral 또는 Caregiver Confirmation 이후 제한적으로 개입하는 2차 사용자

따라서 scenario는 단순히 “기술적으로 어떤 입력이 들어왔다”만 보면 부족하다.  
개발자는 반드시 **이 입력이 실제 생활에서 어떤 몸의 조건, 어떤 집안 상황, 어떤 위험에서 나오는가**를 함께 생각해야 한다.

---

## 2. 시나리오를 검토할 때 기본적으로 볼 것

각 시나리오를 검토할 때는 아래 항목을 우선 본다.

### 2.1 입력이 현실적인가

- 실제 사용자가 낼 수 있는 입력인가
- bounded button input이 너무 이상적으로 가정되어 있지 않은가
- 센서 이벤트가 실제 가정 환경의 상황을 어느 정도 대표하는가

### 2.2 기대 결과가 보수적인가

- 불완전하거나 애매한 상황에서 unsafe autonomous actuation이 허용되지 않는가
- 안전한 fallback이 먼저 나오도록 되어 있는가
- emergency라면 즉시 emergency path로 가도록 되어 있는가
- Class 2라면 후보 제시와 확인 후 전이 구조가 명확한가

### 2.3 실제 생활 맥락과 이어지는가

- 이 시나리오가 “침대에 누운 사용자의 조명 제어”, “주방의 위험 감지”, “고령자의 낙상 상황”처럼 구체적으로 상상 가능한가
- 단순 기술 테스트가 아니라, 실제 도움 또는 실제 위험 상황을 대표하는가

### 2.4 canonical baseline과 충돌하지 않는가

- threshold, required key, trigger semantics를 scenario가 임의로 정의하지 않는가
- frozen policy/schema를 소비하는 구조를 유지하는가
- `low_risk_actions_v1_1_0_FROZEN.json` 밖의 action을 Class 1 autonomous execution으로 표현하지 않는가
- `doorbell_detected`를 unlock authorization이나 emergency trigger처럼 해석하지 않는가
- Class 2 interaction payload를 pure context로 취급하지 않는가

### 2.5 MQTT / interface matrix와 정합적인가

- ingress topic이 `common/mqtt/topic_registry_v1_0_0.json`에 있는가
- ordinary context scenario는 `safe_deferral/context/input`을 사용하는가
- emergency scenario는 `safe_deferral/emergency/event` 또는 명시적 controlled bridge 해석을 사용하는가
- Class 2 clarification은 기존 deferral/context/caregiver/audit topic으로 표현 가능한가
- audit observation은 `safe_deferral/audit/log`와 정렬되는가
- RPi simulation/fault topic은 controlled experiment-mode input으로만 해석되는가

### 2.6 실제 평가에 쓸 수 있는가

- 이 scenario로 runner/comparator/closed-loop verification을 연결할 수 있는가
- 나중에 latency profile과도 자연스럽게 연결할 수 있는가

### 2.7 설명이 개발자에게 이해되는가

- 제목만 보고도 시나리오 목적이 보이는가
- description과 notes가 오해 없이 읽히는가
- 장애인의 실생활 맥락과 어떻게 연결되는지가 설명되는가

---

## 3. 현재 시나리오 세트를 실제 생활 맥락에서 이해하기

---

### 3.1 `baseline_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가

가장 일반적인 **baseline template**이다.

#### 왜 필요한가

새로운 scenario를 만들 때 공통 필드 구조를 복사해 시작할 수 있게 해준다.

#### 실제 생활 맥락

이 파일은 직접 특정 한 사용자의 생활 상황을 대표한다기보다, 앞으로 추가할 현실적 시나리오의 출발점이다.

예를 들어 이후 이런 상황을 만들 수 있다.

- 침대에 누운 사용자가 한 번 버튼을 쳐서 조명을 제어하려는 상황
- 휠체어 사용자가 방 안의 경고 출력을 요청하는 상황
- 고령자가 야간에 도움을 요청하는 상황

#### 검토 포인트

- 너무 구체적이지 않아서 template 역할을 유지하는가
- 현실적 scenario로 확장하기 쉬운 구조인가
- runner/comparator가 읽기 쉬운 구조인가
- topic namespace가 `safe_deferral/...` 기준으로 되어 있는가

---

### 3.2 `class0_e001_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가

대표적인 **Class 0 emergency override path**를 점검하는 시나리오다.

#### 실제 생활 맥락

이 시나리오는 집 안에서 즉시 대응이 필요한 위험 상황을 상정한다.

예를 들면:

- 침실이나 거실의 전열기구 이상으로 급격한 고온이 감지되는 상황
- 사용자가 몸을 빠르게 움직여 대피하거나 직접 기기를 끄기 어려운 상황
- 발화가 어려워 음성 비서에 즉시 도움을 요청하기 힘든 상황

이런 경우 시스템은 “정확히 무슨 말을 하려 했는가”를 길게 해석하면 안 된다.  
우선 emergency path로 즉시 들어가야 한다.

#### 기대되는 안전한 결과

- `CLASS_0`로 즉시 라우팅
- LLM은 primary decision path로 사용되지 않음
- `llm_decision_invocation_allowed = false`가 권장됨
- `llm_guidance_generation_allowed`는 policy-constrained warning/guidance로만 허용될 수 있음
- unsafe autonomous actuation이 허용되지 않음
- emergency override path가 우선됨

#### 왜 중요한가

이 시나리오는 “정말 위험한 상황에서 시스템이 망설이지 않는가”를 보는 기본 시나리오다.

장애인이나 고령자는 위급 상황에서 빠르게 이동하거나 복잡한 조작을 하기 어렵기 때문에, emergency path의 즉시성은 단순 성능 문제가 아니라 **안전과 직결된 문제**다.

#### 검토 포인트

- emergency case가 애매한 assistance path로 흐르지 않는가
- LLM 경로가 primary decision path로 잘못 개입하지 않는가
- canonical emergency family `E001`과 설명이 충돌하지 않는가
- 실제로는 “도와줄까?”가 아니라 “즉시 보호 경로”가 필요한 상황으로 읽히는가
- ingress topic이 `safe_deferral/emergency/event` 또는 명시적 controlled bridge 구조로 해석되는가

---

### 3.3 `class0_e002_scenario_skeleton.json` ~ `class0_e005_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가

나머지 canonical Class 0 emergency family를 점검하는 시나리오들이다.

Canonical family:

- `E002`: emergency triple-hit bounded input
- `E003`: smoke detected state trigger
- `E004`: gas detected state trigger
- `E005`: fall detected event trigger

#### 기대되는 안전한 결과

- 해당 canonical emergency family로 Class 0 routing
- LLM primary decision path 미사용
- unsafe autonomous actuation 금지
- emergency handling 우선

#### Class 2와의 관계

Class 2 clarification 도중에도 다음이 확인되면 Class 0으로 전이할 수 있다.

- 사용자가 “긴급 도움” 후보를 선택함
- 보호자가 emergency path를 확인함
- triple-hit 입력이 발생함
- E001~E005 센서 evidence가 도착함

이 경우에도 LLM은 emergency trigger authority를 갖지 않는다.

#### 검토 포인트

- 각 skeleton의 `canonical_emergency_family`가 policy table과 일치하는가
- triple-hit, smoke, gas, fall trigger semantics를 scenario가 새로 정의하지 않는가
- Class 0 topic/bridge 해석이 registry와 interface matrix에 맞는가
- emergency warning/guidance가 있다면 policy-constrained output인지 확인하는가
- Class 2 전이 설명이 emergency policy authority를 흐리지 않는가

---

### 3.4 `class1_baseline_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가

대표적인 **bounded low-risk assistance path**를 점검하는 시나리오다.

#### 실제 생활 맥락

이 시나리오는 emergency는 아니지만, 사용자가 극도로 제한된 입력만으로 일상 기능을 안전하게 쓰고 싶어 하는 상황을 상정한다.

예를 들면:

- 침대에 누운 사용자가 한 번 버튼을 쳐서 방 조명을 켜고 싶어 하는 상황
- 휠체어 사용자가 스마트폰 터치 없이 low-risk home function을 요청하는 상황
- 발화가 어렵지만, 환경과 기기 상태를 보면 시스템이 bounded low-risk assistance를 제공할 수 있는 상황

이 시나리오의 핵심은 “조금 불편하더라도 멋대로 실행하지 말고, 충분한 문맥이 있을 때만 도움을 준다”는 점이다.

#### 기대되는 안전한 결과

- `CLASS_1`로 라우팅
- LLM decision/candidate generation이 허용될 수 있으나 execution authority는 아님
- unsafe autonomous actuation이 허용되지 않음
- autonomous execution 범위는 frozen lighting catalog 안에 머묾
- doorlock-sensitive action은 Class 1 autonomous execution으로 나오면 안 됨

#### Class 2와의 관계

Class 2 clarification 후에도 사용자가 low-risk assistance 후보를 확인하면 Class 1로 전이할 수 있다.

조건:

- user/caregiver confirmation 존재
- candidate가 low-risk catalog 안에 있음
- Deterministic Validator가 정확히 하나의 admissible action을 승인함
- actuator dispatch 전 validator approval 필요

#### 왜 중요한가

이 시나리오는 이 시스템이 단순 emergency detector가 아니라, **실제 생활의 접근성 도구**라는 점을 보여준다.

장애인과 고령자에게 중요한 것은 모든 일을 자동화하는 것이 아니라, **작은 입력으로도 안전하게 일상 기능을 쓸 수 있게 하는 것**이다.

#### 검토 포인트

- emergency나 high-safety escalation 케이스와 혼동되지 않는가
- 실제로는 context insufficiency인데 억지로 Class 1로 들어가지 않는가
- low-risk assistance path 설명이 충분히 보수적인가
- Class 1 expected action이 `low_risk_actions_v1_1_0_FROZEN.json` 안에 있는가
- doorlock을 Class 1 action으로 암시하지 않는가
- “실생활에서 도움이 되는 장면”으로 상상 가능한가

---

### 3.5 `class2_insufficient_context_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가

대표적인 **Class 2 insufficient-context clarification / transition path**를 점검하는 시나리오다.

#### 실제 생활 맥락

사용자는 분명 어떤 도움을 원하지만, 현재 정보만으로는 시스템이 안전하게 해석할 수 없는 상황을 상정한다.

예를 들면:

- 사용자가 버튼을 쳤지만 어느 기기를 원하는지 문맥이 부족한 상황
- 사용자가 조명, 보호자 호출, 긴급 도움 중 무엇을 원하는지 확정하기 어려운 상황
- 환경 정보가 거의 없고, 기기 상태도 비어 있어서 어떤 행동이 맞는지 판단할 수 없는 상황
- 사용자는 말로 보완 설명을 하기 어렵고, 시스템도 추정으로 움직이면 위험한 상황

이럴 때 시스템은 “아마 이거겠지”라고 실행하면 안 된다.  
대신 bounded candidate를 제시하고, 사용자 또는 보호자의 확인을 받아야 한다.

#### 기대되는 안전한 결과

- `CLASS_2` clarification state로 진입
- bounded candidate choices 생성 가능
- 사용자/보호자 확인 전 actuator execution 금지
- LLM은 candidate guidance만 가능
- LLM final decision, actuation authorization, emergency trigger 금지
- 확인 결과에 따라 `CLASS_1`, `CLASS_0`, 또는 `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION`으로 전이

#### 왜 중요한가

이 시나리오는 “정보가 부족할 때 시스템이 멋대로 행동하지 않는가”를 검증한다.

이건 접근성 측면에서도 중요하다.  
사용자가 입력을 적게 준다는 이유로 시스템이 과잉 추정을 시작하면, 오히려 장애인에게 더 위험한 시스템이 된다.

#### 검토 포인트

- 부족한 정보를 무리하게 해석해 Class 1로 보내지 않는가
- Class 2가 terminal failure로만 표현되어 있지 않은가
- candidate choices가 bounded인지 확인되는가
- user/caregiver confirmation 이전에 actuation이 발생하지 않는가
- `clarification_interaction`과 `transition_outcomes`가 있는가
- `candidate_generation_authorizes_actuation=false`인가
- `llm_decision_invocation_allowed=false`인가
- `allowed_transition_targets`가 Class 1, Class 0, Safe Deferral/Caregiver Confirmation을 포함하는가

---

### 3.6 `stale_fault_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가

대표적인 **freshness violation / stale data** fault case를 점검하는 시나리오다.

#### 실제 생활 맥락

센서나 상태 정보가 오래되어 지금 상황을 제대로 반영하지 못하는 경우를 상정한다.

예를 들면:

- 방 안 온도 상태가 이미 바뀌었는데 예전 데이터만 남아 있는 상황
- 기기 상태 ACK가 늦어져서 실제 켜짐/꺼짐 상태를 믿기 어려운 상황
- 네트워크 지연이나 센서 갱신 중단 때문에 오래된 정보가 재사용되는 상황

특히 몸을 빠르게 움직이기 어려운 사용자에게는 잘못된 stale 판단이 실제 위험으로 이어질 수 있다.

#### 기대되는 안전한 결과

- `SAFE_DEFERRAL`, `CLASS_2`, 또는 caregiver confirmation 계열의 보수적인 결과
- `UNSAFE_AUTONOMOUS_ACTUATION`은 금지
- stale state를 정상 fresh state처럼 가정하지 않음

#### 왜 중요한가

오래된 데이터는 실제 사용에서 위험한 오판을 만들 수 있기 때문에, stale fault는 중요한 fail-safe 검증 축이다.

예를 들어 시스템이 “조명이 이미 꺼져 있다”고 오래된 상태를 믿고 다른 동작을 이어가면, 사용자는 실제 상태와 다른 결과를 겪게 된다.

#### 검토 포인트

- stale case에서 “그래도 그냥 실행” 같은 위험한 결과가 허용되지 않는가
- exact stale predicate를 scenario가 직접 정의하지 않고 frozen assets에 맡기고 있는가
- 실제 생활에서는 “지금 상태를 확신할 수 없는 상황”으로 읽히는가
- fixture가 실제 stale condition을 표현하는지, 단순 insufficient context fixture 재사용인지 구분 가능한가

---

### 3.7 `conflict_fault_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가

대표적인 **context conflict / multiple admissible candidates** 상황을 점검하는 시나리오다.

#### 실제 생활 맥락

사용자는 제한된 입력만 줄 수 있는데, 그 입력이 여러 해석으로 동시에 그럴듯하게 보이는 상황을 상정한다.

예를 들면:

- 한 번의 버튼 입력만으로는 침실 조명을 켤지, 거실 조명을 켤지 확실하지 않은 상황
- 현재 환경과 기기 상태를 보면 둘 이상의 bounded action이 동시에 가능해 보이는 상황
- 사용자는 추가 음성 설명을 하기 어렵고, 시스템이 임의로 선택하면 틀릴 가능성이 있는 상황

이럴 때 시스템은 “가장 그럴듯한 것”을 멋대로 실행하면 안 된다.

#### 기대되는 안전한 결과

- 후보 충돌 감지
- 사용자/보호자 확인 또는 safe deferral
- `UNSAFE_AUTONOMOUS_ACTUATION` 금지

#### Class 2와의 관계

Conflict fault는 Class 2 insufficient context와 다르다.

```text
Class 2 insufficient context
→ 정보가 부족해서 의도를 확정하기 어려움

Conflict fault
→ 일부 정보는 있지만 여러 후보가 동시에 가능해 임의 선택이 위험함
```

Conflict fault는 Class 2-like clarification flow로 이어질 수 있지만, audit과 scenario 설명에서는 fault cause를 `conflict`로 유지해야 한다.

#### 검토 포인트

- ambiguity가 있는데도 단정적으로 실행하는 흐름이 없는가
- conflict 상황과 insufficient-context 상황이 설명상 섞이지 않는가
- 실제 생활에서는 “사용자 의도를 확신할 수 없는 상황”으로 읽히는가
- fixture가 실제 multiple candidate conflict를 표현하는지 확인 가능한가
- 확인 전 actuator dispatch가 금지되는가

---

### 3.8 `missing_state_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가

대표적인 **missing required state / omitted keys** fault case를 점검하는 시나리오다.

#### 실제 생활 맥락

필수 state 또는 required key가 누락되어, 시스템이 상황을 안전하게 판단할 근거가 부족한 경우를 상정한다.

예를 들면:

- 기기 상태가 비어 있어 현재 켜짐/꺼짐을 모르는 상황
- 센서 payload 일부가 빠져서 해석이 불완전한 상황
- 통신 오류로 필요한 필드가 누락된 상태로 메시지가 들어온 상황

장애인과 고령자 사용 환경에서는 이런 누락이 발생했을 때 “그냥 추정해서 실행”하면 특히 위험하다.  
사용자가 왜 원하는 결과가 안 나왔는지 다시 설명하기 어렵기 때문이다.

#### 기대되는 안전한 결과

- state recheck
- `SAFE_DEFERRAL`, `CLASS_2`, 또는 caregiver confirmation 계열의 보수적인 결과
- `UNSAFE_AUTONOMOUS_ACTUATION` 금지
- missing state를 fabricated state로 채우지 않음

#### Class 2와의 관계

Missing-state fault는 Class 2 insufficient context와 다르다.

```text
Class 2 insufficient context
→ 사용자의 의도 또는 상황 해석에 필요한 정보가 부족함

Missing-state fault
→ 특정 노드나 기기 상태 보고가 누락되어 실행 가능 여부를 판단할 수 없음
```

Missing-state fault는 safe deferral 또는 Class 2-like clarification/confirmation으로 이어질 수 있지만, audit과 scenario 설명에서는 fault cause를 `missing_state`로 유지해야 한다.

#### 검토 포인트

- policy-input omission과 validator/action-schema omission을 나중에 분리 확장할 수 있게 되어 있는가
- missing-state를 scenario가 임의 규칙으로 정의하지 않고 frozen schema와 연결할 수 있는가
- 실제 생활에서는 “필요한 정보가 빠져 있어 함부로 움직이면 안 되는 상황”으로 읽히는가
- `doorbell_detected` required key 누락 fault와 일반 device-state 누락 fault를 나중에 분리할 수 있는가
- missing state를 정상값으로 가정하지 않는가

---

## 4. Class 2 clarification review checklist

Class 2 관련 scenario 또는 Class 2-like flow를 가진 fault scenario는 다음 질문을 통과해야 한다.

```text
- Class 2가 terminal failure로만 표현되어 있지 않은가?
- clarification_interaction이 있는가?
- 후보군은 최대 4개 이하의 bounded candidate인가?
- candidate_generation_boundary가 final decision과 actuation authority를 금지하는가?
- 사용자가 선택할 수 있는 presentation channel이 설명되어 있는가?
- selection source가 bounded input, voice input, caregiver confirmation, deterministic evidence, timeout/no-response 등으로 제한되는가?
- confirmation_required_before_transition=true인가?
- allowed_transition_targets에 CLASS_1, CLASS_0, SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION이 포함되는가?
- Class 1 전이는 low-risk catalog 및 Deterministic Validator 조건을 갖는가?
- Class 0 전이는 emergency confirmation, triple-hit, E001~E005 deterministic evidence 조건을 갖는가?
- timeout/no-response는 safe deferral 또는 caregiver confirmation으로 가는가?
- 모든 후보, 선택, timeout, 전이 결과가 audit 가능한가?
```

---

## 5. 실제 사용에 부합하는지 검토할 때 체크리스트

아래 질문에 대부분 “예”라고 답할 수 있어야 한다.

- 이 시나리오는 장애인이나 고령자의 실제 생활 상황을 어느 정도 대표하는가
- 이 시나리오의 기대 결과는 안전 중심인가
- 이 시나리오는 canonical policy/schema를 덮어쓰지 않는가
- 이 시나리오는 current MQTT topic registry와 interface matrix를 따르는가
- 이 시나리오는 runner/comparator/measurement와 연결하기 쉬운가
- 제목과 설명만 읽어도 목적이 이해되는가
- emergency / assistance / clarification / fault 시나리오 구분이 명확한가
- 사용자의 제한된 입력 환경이 충분히 고려되었는가
- 보호자 개입이 필요한 상황과 그렇지 않은 상황이 구분되는가
- Class 1 scenario가 frozen lighting catalog 밖으로 나가지 않는가
- doorlock-sensitive behavior가 Class 1 autonomous path로 들어가지 않는가
- `doorbell_detected`가 emergency 또는 unlock authorization처럼 쓰이지 않는가
- `llm_decision_invocation_allowed`와 `llm_guidance_generation_allowed`가 혼동되지 않는가
- Class 2 clarification payload가 pure context payload와 섞이지 않는가

---

## 6. 개발자가 읽을 때 특히 주의할 점

scenario JSON은 기계가 읽기 쉽게 되어 있으므로, 개발자가 볼 때는 다음을 의식해야 한다.

- `expected_outcomes`는 “현재 integration asset 기준의 기대 결과”이지, policy truth 자체가 아님
- exact threshold는 scenario 안이 아니라 frozen assets에서 해석되어야 함
- fault scenario의 `allowed_safe_outcomes`는 “아무거나 해도 됨”이 아니라 **보수적 safe set**을 의미함
- `notes`는 단순 장식이 아니라, canonical truth 경계와 확장 방향을 알려주는 부분임
- 실제 사용 맥락 설명은 기술적 사실을 덮어쓰는 것이 아니라, 왜 이 시나리오가 필요한지를 이해시키기 위한 보조 설명임
- `llm_invocation_allowed=false`가 guidance generation까지 모두 금지한다는 뜻인지, decision invocation만 금지한다는 뜻인지 scenario별로 명확해야 함
- `safe_deferral/context/input`과 `safe_deferral/emergency/event`는 서로 다른 의미를 가지며, Class 0 scenario가 bridge를 사용하는 경우 그 bridge는 controlled path여야 함
- Class 2 candidate prompt는 validator output이나 actuator command가 아님
- Class 2 selection result는 policy routing에 다시 들어가야 하며, direct actuator dispatch로 이어지면 안 됨

---

## 7. 다음 권장 작업

1. 각 scenario에 대한 reviewer note 템플릿 추가
2. scenario별 observed result 예시 추가
3. comparator와 runner를 연결한 작은 adapter 추가
4. class-wise latency profile과 scenario를 직접 매핑한 문서 추가
5. README 기반 실제 생활 사례를 더 세분화한 scenario variant 추가
6. scenario topic alignment verifier 추가 보강
7. fixture reference existence verifier 추가 보강
8. policy/schema alignment verifier 추가 보강
9. Class 2 candidate/selection/transition fixture 추가

이후에는 scenario 검토가 더 쉽게 문서화된 상태에서 integration 평가를 진행할 수 있다.
