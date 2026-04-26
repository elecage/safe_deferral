# Class 2 To Class 1 Low-Risk Confirmation Scenario User Story
## 불명확한 요청을 확인한 뒤 조명 제어로 전이하는 상황

## 1. 이 문서가 설명하는 JSON 파일

이 문서는 다음 scenario JSON 파일을 실제 사용환경에서 일어날 수 있는 상황으로 풀어 설명한다.

```text
integration/scenarios/class2_to_class1_low_risk_confirmation_scenario_skeleton.json
```

이 JSON 파일은 사용자의 입력만으로는 실행 대상을 바로 확정할 수 없지만, 사용자 또는 보호자가 낮은 위험도의 조명 후보를 명확히 선택하면 시스템이 다시 정책 라우터로 진입한 뒤 Class 1 조명 제어로 전이할 수 있는지를 검토하기 위한 시나리오다.

핵심은 다음과 같다.

```text
Class 2에서 후보를 보여주는 것만으로는 실행 권한이 생기지 않는다.
사용자 또는 보호자의 선택 이후에도 Policy Router 재진입과 Deterministic Validator 검증이 필요하다.
최종 실행 가능 대상은 canonical low-risk lighting catalog 안의 조명 제어에 한정된다.
```

---

## 2. 발생 상황

사용자는 침대에 누워 있거나 휠체어에 앉아 있다.

사용자는 집 안의 조명을 켜고 싶어 버튼을 한 번 누른다. 하지만 현재 상황만으로는 어느 조명을 켜야 하는지 확정하기 어렵다.

예를 들어 다음과 같은 상황일 수 있다.

```text
사용자가 버튼을 한 번 눌렀다.
거실 조명과 침실 조명 모두 꺼져 있다.
사용자 위치 정보가 충분히 명확하지 않다.
긴급상황은 감지되지 않았다.
방문자 또는 도어락 관련 상황도 아니다.
```

이때 시스템이 임의로 거실 조명 또는 침실 조명을 선택하면 사용자의 실제 의도와 다른 동작이 발생할 수 있다.

따라서 시스템은 바로 실행하지 않고 Class 2 clarification 상태로 진입해 사용자에게 bounded candidate를 제시한다.

---

## 3. 시스템이 인식해야 하는 상황

시스템은 이 상황을 단순한 Class 1 실행으로 처리하지 않는다.

처음에는 다음과 같이 판단한다.

```text
- 사용자의 입력은 생활 보조 요청일 가능성이 있다.
- 조명 제어 후보가 존재한다.
- 하지만 실행 대상을 하나로 확정할 수 없다.
- 긴급상황으로 볼 결정론적 증거는 없다.
- 민감 액추에이션 요청도 아니다.
- 따라서 Class 2 clarification이 필요하다.
```

이후 사용자가 “침실 조명” 또는 “거실 조명” 같은 낮은 위험도 후보를 선택하면, 시스템은 그 선택을 곧바로 actuator 명령으로 바꾸지 않는다.

선택 결과는 다시 Policy Router로 들어가야 하며, Class 1로 전이되더라도 Deterministic Validator가 `common/policies/low_risk_actions.json` 기준으로 승인해야 한다.

---

## 4. 정보 출처 노드 및 상태 정보

| 항목 | 정보를 제공하는 노드/구성요소 | 제공되는 정보 | 시나리오 내 상태 |
|---|---|---|---|
| 사용자 입력 | Bounded Input Node | 사용자가 버튼을 눌렀다는 이벤트 | 단일 입력 발생 |
| 환경 정보 | Context Node | 조도, 점유 여부, 위치 추정 | 실행 후보를 하나로 좁히기에는 불충분 |
| 조명 상태 | Lighting Actuator Node 또는 Device State Reporter | 거실/침실 조명 상태 | 둘 다 실행 후보가 될 수 있음 |
| 후보 생성 | LLM Guidance Layer 또는 Input Context Mapper | 사용자에게 제시할 bounded candidate | 후보 안내만 가능 |
| 후보 제시 | TTS/Voice Output 또는 Display Output | 사용자가 고를 수 있는 짧은 선택지 | 조명 후보를 안내 |
| 사용자 선택 | Bounded Input Node, Voice Input, Caregiver Confirmation | 선택된 낮은 위험도 후보 | Class 1 전이 후보 |
| 정책 재진입 | Mac mini Edge Hub | 선택 결과를 Policy Router로 다시 전달 | 재분류 필요 |
| 안전 검증 | Deterministic Validator | low-risk catalog 기반 승인 여부 | 승인 후에만 실행 가능 |
| 조명 실행 | Lighting Actuator Node | 승인된 조명 제어 수행 및 ACK | 승인된 경우에만 수행 |
| 처리 기록 | Audit Log | 후보 제시, 선택, 재진입, 검증, 실행 결과 | 전 과정 기록 |

---

## 5. 노드별 개발 관점 정리

| 노드/구성요소 | 개발 시 필요한 기능 | 이 시나리오에서의 역할 |
|---|---|---|
| Bounded Input Node | 최초 입력과 후보 선택 입력 감지 | 사용자의 제한된 입력을 이벤트로 전달 |
| Context Node | 조도, 점유, 위치 등 환경 정보 제공 | 후보 구성에 필요한 맥락 제공 |
| Lighting Actuator Node | 조명 상태 보고, 조명 제어, ACK 반환 | 최종 승인된 조명 제어만 수행 |
| Class 2 Clarification Manager | 후보 제시, 선택 수집, timeout 처리 | Class 2 clarification 흐름 관리 |
| LLM Guidance Layer | 후보를 사용자가 이해하기 쉬운 표현으로 정리 | 후보 안내만 수행하고 실행 권한은 없음 |
| Policy Router | 선택 결과를 다시 분류 | Class 1 전이 가능 여부 판단 |
| Deterministic Validator | canonical low-risk catalog 기준 검증 | Class 1 실행 승인 또는 거부 |
| TTS/Display Output | 후보를 접근 가능한 방식으로 제시 | 사용자가 선택할 수 있도록 안내 |
| Audit Log | 각 단계의 근거와 결과 기록 | 후보 제시가 실행 권한이 아니었음을 추적 |

---

## 6. 처리 과정

### 6.1 사용자가 버튼을 누른다

사용자는 조명 제어 도움을 요청하려고 버튼을 한 번 누른다.

```text
사용자 버튼 입력 1회 발생
```

### 6.2 시스템이 바로 실행하지 않는다

Mac mini Edge Hub는 현재 context를 확인하지만, 실행할 조명을 하나로 확정할 수 없다.

```text
조명 제어 후보는 존재함
하지만 거실 조명인지 침실 조명인지 불명확함
```

### 6.3 Class 2 clarification 상태로 진입한다

시스템은 사용자의 의도를 임의로 추정하지 않고 Class 2 clarification 상태로 들어간다.

이때 사용하는 clarification topic은 다음과 같다.

```text
safe_deferral/clarification/interaction
```

### 6.4 사용자에게 bounded candidate를 제시한다

TTS 또는 화면 출력은 사용자가 고를 수 있는 짧은 후보를 제시한다.

```text
1번: 거실 조명을 켤까요?
2번: 침실 조명을 켤까요?
3번: 취소하고 대기할까요?
```

이 후보는 안내일 뿐이다. 후보 문장 자체는 validator output도 아니고 actuator command도 아니다.

### 6.5 사용자 또는 보호자가 낮은 위험도 후보를 선택한다

사용자가 “침실 조명”을 선택하거나, 보호자가 같은 후보를 확인할 수 있다.

```text
선택 결과: 침실 조명 켜기
```

### 6.6 선택 결과가 Policy Router로 다시 들어간다

선택 결과는 곧바로 조명 명령으로 바뀌지 않는다.

Mac mini Edge Hub는 선택 결과를 Policy Router에 다시 넣어 현재 요청이 Class 1로 전이될 수 있는지 확인한다.

### 6.7 Deterministic Validator가 최종 승인한다

Class 1 후보가 되더라도 validator가 canonical low-risk catalog를 확인한다.

```text
action: light_on
target: bedroom_light
catalog: common/policies/low_risk_actions.json
```

catalog에 포함된 단일 낮은 위험도 조명 제어로 확인되면 실행이 가능하다.

### 6.8 조명 제어와 ACK가 기록된다

Lighting Actuator Node가 승인된 조명 제어만 수행하고 ACK를 반환한다.

Audit Log에는 후보 제시, 사용자 선택, Policy Router 재진입, validator 승인, actuator ACK가 함께 기록된다.

---

## 7. 기대 결과

```text
초기 상태: Class 2 clarification
사용자/보호자 선택: 낮은 위험도 조명 후보
필수 조건: Policy Router 재진입
필수 조건: Deterministic Validator 승인
최종 결과: 승인된 경우에만 Class 1 조명 제어 수행
```

---

## 8. 안전상 중요한 점

- Class 2 후보 제시는 실행 권한이 아니다.
- 사용자 선택도 actuator 명령이 아니다.
- Class 1 전이는 반드시 Policy Router 재진입 이후에만 가능하다.
- 조명 제어는 `common/policies/low_risk_actions.json`에 포함된 범위로 제한된다.
- Doorlock은 이 시나리오의 Class 1 전이 대상이 아니다.

