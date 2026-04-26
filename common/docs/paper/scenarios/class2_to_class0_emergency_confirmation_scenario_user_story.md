# Class 2 To Class 0 Emergency Confirmation Scenario User Story
## 불명확한 도움 요청이 긴급상황으로 확인되는 상황

## 1. 이 문서가 설명하는 JSON 파일

이 문서는 다음 scenario JSON 파일을 실제 사용환경에서 일어날 수 있는 상황으로 풀어 설명한다.

```text
integration/scenarios/class2_to_class0_emergency_confirmation_scenario_skeleton.json
```

이 JSON 파일은 처음에는 사용자의 의도가 불명확해 Class 2 clarification으로 들어갔지만, 이후 명시적 긴급 확인이나 결정론적 긴급 증거가 들어오면 Class 0 긴급 대응으로 전이할 수 있는지를 검토하기 위한 시나리오다.

핵심은 다음과 같다.

```text
LLM이 만든 “긴급상황인가요?” 같은 후보 문장은 긴급 트리거 권한이 아니다.
Class 0 전이는 명시적 긴급 확인, triple-hit 입력, 또는 E001-E005 계열의 결정론적 긴급 증거가 있을 때만 가능하다.
```

---

## 2. 발생 상황

사용자는 집 안에서 불편함이나 위험을 느끼지만, 처음 입력만으로는 단순한 생활 보조 요청인지 긴급 도움 요청인지 확정하기 어렵다.

예를 들어 사용자가 버튼을 한 번 눌렀고, 시스템은 다음과 같은 후보를 생각할 수 있다.

```text
조명을 켜고 싶은 것일 수 있다.
보호자에게 도움을 요청하려는 것일 수 있다.
긴급상황일 수도 있다.
```

초기 입력만으로는 Class 0로 바로 전환할 결정론적 증거가 없다. 따라서 시스템은 Class 2 clarification 상태로 진입한다.

그 후 사용자가 추가 입력으로 긴급 도움을 명확히 선택하거나, 짧은 시간 안에 triple-hit 입력이 발생하거나, 연기·가스·고온·낙상 같은 결정론적 긴급 이벤트가 감지될 수 있다.

---

## 3. 시스템이 인식해야 하는 상황

시스템은 두 단계를 구분해야 한다.

첫 번째 단계는 불명확한 상태다.

```text
- 사용자의 입력이 있다.
- 생활 보조 요청일 수도 있고 긴급 도움 요청일 수도 있다.
- 결정론적 긴급 증거는 아직 없다.
- 따라서 Class 2 clarification으로 들어간다.
```

두 번째 단계는 긴급 확인 또는 긴급 증거가 생긴 상태다.

```text
- 사용자가 긴급 도움 후보를 명확히 선택했다.
- 또는 triple-hit 입력이 발생했다.
- 또는 E001-E005 계열의 긴급 센서 증거가 들어왔다.
- 이 경우 Policy Router 재진입 후 Class 0 전이를 검토한다.
```

---

## 4. 정보 출처 노드 및 상태 정보

| 항목 | 정보를 제공하는 노드/구성요소 | 제공되는 정보 | 시나리오 내 상태 |
|---|---|---|---|
| 최초 사용자 입력 | Bounded Input Node | 불명확한 버튼 입력 | 단일 입력 또는 모호한 입력 |
| 후보 생성 | LLM Guidance Layer 또는 Input Context Mapper | 가능한 도움 후보 | 안내 후보만 생성 |
| 후보 제시 | Class 2 Clarification Manager | `safe_deferral/clarification/interaction` payload | 긴급 후보를 포함할 수 있음 |
| 긴급 확인 | Bounded Input Node, Voice Input, Caregiver Confirmation | 사용자의 명시적 긴급 선택 | Class 0 전이 근거가 될 수 있음 |
| 결정론적 긴급 증거 | Emergency Node | triple-hit, smoke, gas, high temperature, fall 등 | Class 0 전이 근거 |
| 정책 재진입 | Mac mini Edge Hub | 확인 또는 증거를 Policy Router로 다시 전달 | 재분류 필요 |
| 긴급 처리 | Warning Output, Caregiver Notification | 사용자 경고와 보호자 알림 | Class 0 전이 후 수행 |
| 처리 기록 | Audit Log | clarification, 긴급 확인, 전이 근거 기록 | 전 과정 기록 |

---

## 5. 노드별 개발 관점 정리

| 노드/구성요소 | 개발 시 필요한 기능 | 이 시나리오에서의 역할 |
|---|---|---|
| Bounded Input Node | 단일 입력, 선택 입력, triple-hit 입력 감지 | 초기 입력과 긴급 확인 입력 제공 |
| Emergency Node | 화재, 가스, 고온, 낙상 등 결정론적 긴급 이벤트 생성 | Class 0 전이 근거 제공 |
| Class 2 Clarification Manager | 후보 제시 및 응답 수집 | 불명확한 요청을 bounded clarification으로 처리 |
| LLM Guidance Layer | 사용자에게 이해 가능한 후보 문장 생성 | 후보 안내만 수행 |
| Policy Router | 긴급 확인 또는 증거를 다시 분류 | Class 0 전이 여부 판단 |
| Warning Output Node | 사용자에게 위험 또는 긴급 접수 안내 | Class 0 전이 후 경고 |
| Caregiver Notification | 보호자에게 긴급 알림 전달 | 긴급상황 공유 |
| Audit Log | 긴급 전이 근거와 처리 결과 기록 | 후보 문장과 실제 긴급 근거를 구분 |

---

## 6. 처리 과정

### 6.1 불명확한 입력이 들어온다

사용자는 버튼을 한 번 누르거나 짧은 입력을 보낸다.

```text
사용자 입력 발생
하지만 긴급상황인지 생활 보조인지 확정할 수 없음
```

### 6.2 Class 2 clarification 상태로 들어간다

시스템은 바로 Class 0로 전환하지 않는다. 결정론적 긴급 증거가 아직 없기 때문이다.

### 6.3 긴급 후보를 포함한 선택지를 제시한다

시스템은 접근 가능한 출력으로 후보를 안내할 수 있다.

```text
1번: 조명을 켤까요?
2번: 보호자에게 도움을 요청할까요?
3번: 긴급상황인가요?
```

이 문장은 긴급상황을 선언하는 것이 아니다. 사용자가 이해하기 쉽게 확인 질문을 만든 것이다.

### 6.4 긴급 확인 또는 긴급 증거가 들어온다

Class 0 전이는 다음 중 하나가 있을 때만 가능하다.

```text
사용자 또는 보호자가 긴급 도움을 명시적으로 확인함
짧은 시간 안에 triple-hit 입력이 발생함
Emergency Node가 E001-E005 계열 긴급 증거를 감지함
```

### 6.5 Policy Router로 다시 들어간다

긴급 확인 또는 결정론적 증거는 Policy Router로 다시 들어간다.

이 단계에서 시스템은 긴급 전이가 후보 문장 때문인지, 실제 확인 또는 증거 때문인지 구분해야 한다.

### 6.6 Class 0 긴급 흐름으로 전환한다

Policy Router가 Class 0 조건을 만족한다고 판단하면 시스템은 긴급 대응 흐름으로 전환한다.

예를 들어 다음을 수행할 수 있다.

```text
사용자에게 긴급 요청 접수 안내
경고 출력
보호자 또는 관리자에게 알림
긴급 처리 결과 기록
```

---

## 7. 기대 결과

```text
초기 상태: Class 2 clarification
전이 조건: 명시적 긴급 확인 또는 결정론적 긴급 증거
필수 조건: Policy Router 재진입
최종 결과: Class 0 긴급 대응 흐름
```

---

## 8. 안전상 중요한 점

- LLM candidate text는 긴급 트리거가 아니다.
- “긴급상황인가요?”라는 질문 자체가 Class 0 전이를 만들 수 없다.
- timeout 또는 무응답만으로 긴급상황을 추정하지 않는다.
- Class 0 전이는 명시적 확인, triple-hit, 또는 결정론적 긴급 증거가 필요하다.
- 전이 근거는 audit log에 남아야 한다.

