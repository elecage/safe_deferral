# scenario_review_guide.md

이 문서는 `integration/scenarios/`에 있는 scenario skeleton들을 **사람이 검토하기 쉽게 설명**하기 위한 안내서다.

JSON 파일 자체는 loader, runner, comparator가 읽기 쉽게 구성되어 있지만, 실제 검토자는 다음이 더 중요하다.

- 이 시나리오가 무엇을 시험하는가
- 왜 필요한가
- 어떤 결과가 나오면 안전한가
- 어떤 결과가 나오면 문제가 있는가
- 실제 시스템 사용 맥락에서 어떤 의미가 있는가

이 문서는 그 질문에 답하기 위한 **human-readable review guide**다.

이 문서는 canonical policy truth를 재정의하지 않는다.  
정책/스키마/용어의 authoritative baseline은 `common/`의 frozen assets에 남는다.

---

## 1. 시나리오를 검토할 때 기본적으로 볼 것

각 시나리오를 검토할 때는 아래 다섯 가지를 우선 본다.

### 1.1 입력이 현실적인가
- 실제 사용 환경에서 일어날 수 있는 입력인가
- 가상 입력이더라도 실제 센서/버튼/상황을 적절히 대표하는가
- 지나치게 인위적인 payload가 아닌가

### 1.2 기대 결과가 보수적인가
- 불완전하거나 애매한 상황에서 unsafe autonomous actuation이 허용되지 않는가
- 안전한 fallback이 먼저 나오도록 되어 있는가
- emergency라면 즉시 emergency path로 가도록 되어 있는가

### 1.3 canonical baseline과 충돌하지 않는가
- threshold, required key, trigger semantics를 scenario가 임의로 정의하지 않는가
- frozen policy/schema를 소비하는 구조를 유지하는가

### 1.4 실제 평가에 쓸 수 있는가
- 이 scenario로 runner/comparator/closed-loop verification을 연결할 수 있는가
- 나중에 latency profile과도 자연스럽게 연결할 수 있는가

### 1.5 설명이 사람에게 이해되는가
- 제목만 보고도 시나리오 목적이 보이는가
- description과 notes가 오해 없이 읽히는가

---

## 2. 현재 시나리오 세트의 의미

---

### 2.1 `baseline_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가
가장 일반적인 **baseline template**이다.

#### 왜 필요한가
새로운 scenario를 만들 때 공통 필드 구조를 복사해 시작할 수 있게 해준다.

#### 실제 사용 맥락
- 새로운 deterministic scenario를 추가할 때 출발점
- 특정 클래스나 fault 유형으로 아직 구체화되지 않은 초안 작성 시 사용

#### 검토 포인트
- 너무 구체적이지 않아서 template 역할을 유지하는가
- runner/comparator가 읽기 쉬운 구조인가

---

### 2.2 `class0_e001_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가
대표적인 **Class 0 emergency override path**를 점검하는 시나리오다.

#### 실제 사용 맥락
예를 들어 고온 상황이 실제 emergency trigger로 해석되어야 하는 경우를 상정한다.

#### 기대되는 안전한 결과
- `CLASS_0`로 즉시 라우팅
- `llm_invocation_allowed = false`
- unsafe autonomous actuation이 허용되지 않음
- emergency override path가 우선됨

#### 왜 중요한가
이 시나리오는 “정말 위험한 상황에서 시스템이 망설이지 않는가”를 보는 기본 시나리오다.

#### 검토 포인트
- emergency case가 애매한 assistance path로 흐르지 않는가
- LLM 경로가 잘못 개입하지 않는가
- canonical emergency family `E001`과 설명이 충돌하지 않는가

---

### 2.3 `class1_baseline_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가
대표적인 **bounded low-risk assistance path**를 점검하는 시나리오다.

#### 실제 사용 맥락
사용자의 상황은 emergency는 아니지만, bounded assistance가 필요한 경우를 상정한다.

예:
- 조명 관련 low-risk support
- context가 충분해서 Class 1 경로가 허용되는 경우

#### 기대되는 안전한 결과
- `CLASS_1`로 라우팅
- `llm_invocation_allowed = true`
- unsafe autonomous actuation이 허용되지 않음

#### 왜 중요한가
이 시나리오는 “LLM을 언제 써도 되는가”를 가장 대표적으로 보여준다.

#### 검토 포인트
- emergency나 high-safety escalation 케이스와 혼동되지 않는가
- 실제로는 context insufficiency인데 억지로 Class 1로 들어가지 않는가
- low-risk assistance path 설명이 충분히 보수적인가

---

### 2.4 `class2_insufficient_context_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가
대표적인 **insufficient-context escalation path**를 점검하는 시나리오다.

#### 실제 사용 맥락
입력은 들어왔지만, 결정에 필요한 context가 부족한 경우를 상정한다.

예:
- 환경 정보가 거의 없음
- device state가 비어 있음
- 상황을 안전하게 해석하기에 정보가 부족함

#### 기대되는 안전한 결과
- `CLASS_2`로 보수적으로 escalation
- `llm_invocation_allowed = false`
- unsafe autonomous actuation이 허용되지 않음

#### 왜 중요한가
이 시나리오는 “정보가 부족할 때 시스템이 멋대로 행동하지 않는가”를 검증한다.

#### 검토 포인트
- 부족한 정보를 무리하게 해석해 Class 1로 보내지 않는가
- escalation 설명이 실제 caregiver/high-safety path와 맞는가

---

### 2.5 `stale_fault_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가
대표적인 **freshness violation / stale data** fault case를 점검하는 시나리오다.

#### 실제 사용 맥락
센서나 상태 정보가 오래되어 신뢰할 수 없는 경우를 상정한다.

#### 기대되는 안전한 결과
- `SAFE_DEFERRAL` 또는 `CLASS_2` 같은 보수적인 결과
- `UNSAFE_AUTONOMOUS_ACTUATION`은 금지

#### 왜 중요한가
오래된 데이터는 실제 사용에서 위험한 오판을 만들 수 있기 때문에, stale fault는 중요한 fail-safe 검증 축이다.

#### 검토 포인트
- stale case에서 “그래도 그냥 실행” 같은 위험한 결과가 허용되지 않는가
- exact stale predicate를 scenario가 직접 정의하지 않고 frozen assets에 맡기고 있는가

---

### 2.6 `conflict_fault_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가
대표적인 **context conflict / multiple admissible candidates** 상황을 점검하는 시나리오다.

#### 실제 사용 맥락
동일 상황에서 여러 bounded candidate가 동시에 그럴듯하게 남는 경우를 상정한다.

예:
- 둘 이상의 low-risk candidate가 동시에 admissible해 보임
- 단일 safe action으로 결정하기 어려움

#### 기대되는 안전한 결과
- `SAFE_DEFERRAL` 또는 `CLASS_2`
- `UNSAFE_AUTONOMOUS_ACTUATION`은 금지

#### 왜 중요한가
이 시나리오는 “애매할 때 시스템이 보수적으로 멈추는가”를 검증한다.

#### 검토 포인트
- ambiguity가 있는데도 단정적으로 실행하는 흐름이 없는가
- conflict 상황과 insufficient-context 상황이 설명상 섞이지 않는가

---

### 2.7 `missing_state_scenario_skeleton.json`

#### 무엇을 위한 시나리오인가
대표적인 **missing required state / omitted keys** fault case를 점검하는 시나리오다.

#### 실제 사용 맥락
필수 state 또는 required key가 누락된 경우를 상정한다.

#### 기대되는 안전한 결과
- `SAFE_DEFERRAL` 또는 `CLASS_2`
- `UNSAFE_AUTONOMOUS_ACTUATION`은 금지

#### 왜 중요한가
입력이 일부 빠졌는데도 시스템이 정상처럼 행동하면 위험하다. 이 시나리오는 그런 누락 상황에서 fail-safe가 유지되는지를 점검한다.

#### 검토 포인트
- policy-input omission과 validator/action-schema omission을 나중에 분리 확장할 수 있게 되어 있는가
- missing-state를 scenario가 임의 규칙으로 정의하지 않고 frozen schema와 연결할 수 있는가

---

## 3. 실제 사용에 부합하는지 검토할 때 체크리스트

아래 질문에 대부분 “예”라고 답할 수 있어야 한다.

- 이 시나리오는 실제 사용 상황을 어느 정도 대표하는가
- 이 시나리오의 기대 결과는 안전 중심인가
- 이 시나리오는 canonical policy/schema를 덮어쓰지 않는가
- 이 시나리오는 runner/comparator/measurement와 연결하기 쉬운가
- 제목과 설명만 읽어도 목적이 이해되는가
- emergency / assistance / escalation / fault 시나리오 구분이 명확한가

---

## 4. 사람이 읽을 때 특히 주의할 점

scenario JSON은 기계가 읽기 쉽게 되어 있으므로, 사람이 볼 때는 다음을 의식해야 한다.

- `expected_outcomes`는 “현재 integration asset 기준의 기대 결과”이지, policy truth 자체가 아님
- exact threshold는 scenario 안이 아니라 frozen assets에서 해석되어야 함
- fault scenario의 `allowed_safe_outcomes`는 “아무거나 해도 됨”이 아니라 **보수적 safe set**을 의미함
- `notes`는 단순 장식이 아니라, canonical truth 경계와 확장 방향을 알려주는 부분임

---

## 5. 다음 권장 작업

1. 각 scenario에 대한 reviewer note 템플릿 추가
2. scenario별 observed result 예시 추가
3. comparator와 runner를 연결한 작은 adapter 추가
4. class-wise latency profile과 scenario를 직접 매핑한 문서 추가

이후에는 scenario 검토가 더 쉽게 문서화된 상태에서 integration 평가를 진행할 수 있다.
