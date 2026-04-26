# Class 2 Timeout No-Response Safe Deferral Scenario User Story
## 후보를 제시했지만 사용자가 응답하지 않아 안전 보류하는 상황

## 1. 이 문서가 설명하는 JSON 파일

이 문서는 다음 scenario JSON 파일을 실제 사용환경에서 일어날 수 있는 상황으로 풀어 설명한다.

```text
integration/scenarios/class2_timeout_no_response_safe_deferral_scenario_skeleton.json
```

이 JSON 파일은 Class 2 clarification 상태에서 사용자가 후보를 선택하지 않거나 시간 안에 응답하지 않을 때, 시스템이 사용자의 의도를 임의로 추정하지 않고 Safe Deferral 또는 Caregiver Confirmation으로 전환하는지를 검토하기 위한 시나리오다.

---

## 2. 발생 상황

사용자가 버튼을 한 번 눌렀다. 시스템은 이 입력을 조명 제어, 보호자 호출, 긴급 도움 요청 등 여러 가능성으로 해석할 수 있다.

하지만 어떤 후보가 맞는지 확정할 수 없기 때문에 Class 2 clarification 상태로 진입한다.

시스템은 사용자에게 후보를 제시한다.

```text
1번: 조명을 켤까요?
2번: 보호자에게 도움을 요청할까요?
3번: 긴급상황인가요?
4번: 취소하고 대기할까요?
```

그러나 사용자는 응답하지 못한다.

그 이유는 다양할 수 있다.

```text
사용자가 버튼을 다시 누르기 어려움
음성 응답이 불명확함
사용자가 피로하거나 주의를 기울이기 어려움
출력 안내를 듣거나 보지 못함
네트워크 또는 입력 노드 문제가 있음
```

---

## 3. 시스템이 인식해야 하는 상황

시스템은 timeout과 no-response를 사용자 선택으로 해석하면 안 된다.

```text
응답 없음은 “조명을 켜라”가 아니다.
응답 없음은 “긴급상황이다”도 아니다.
응답 없음은 “문을 열어도 된다”는 뜻도 아니다.
```

따라서 시스템은 candidate 중 하나를 임의로 선택하지 않고 안전하게 멈추거나 보호자 확인으로 넘어가야 한다.

---

## 4. 정보 출처 노드 및 상태 정보

| 항목 | 정보를 제공하는 노드/구성요소 | 제공되는 정보 | 시나리오 내 상태 |
|---|---|---|---|
| 최초 입력 | Bounded Input Node | 사용자의 버튼 입력 | 불명확한 요청 |
| 후보 제시 | Class 2 Clarification Manager | `safe_deferral/clarification/interaction` payload | 후보 제시됨 |
| 출력 채널 | TTS/Voice Output 또는 Display Output | 사용자에게 후보 안내 | 안내 출력됨 |
| 응답 수집 | Bounded Input Node, Voice Input | 사용자 선택 응답 | timeout 또는 no-response |
| timeout 판정 | Class 2 Clarification Manager | 응답 제한 시간 초과 | 의도 추정 금지 |
| 후속 처리 | Mac mini Edge Hub | Safe Deferral 또는 Caregiver Confirmation | 자동 실행 차단 |
| 기록 | Audit Log | 후보 제시와 timeout 결과 | 전 과정 기록 |

---

## 5. 노드별 개발 관점 정리

| 노드/구성요소 | 개발 시 필요한 기능 | 이 시나리오에서의 역할 |
|---|---|---|
| Class 2 Clarification Manager | 후보 제시, 응답 대기, timeout 판정 | 응답 없음 처리의 핵심 |
| Bounded Input Node | 선택 입력 수집 | 응답이 없음을 확인 |
| Voice Input | 짧은 음성 선택 수집 | 음성 응답이 없거나 불명확할 수 있음 |
| TTS/Display Output | 후보 안내 출력 | 사용자가 이해할 수 있는 선택지 제공 |
| Mac mini Edge Hub | timeout 후 안전 경로 선택 | 자동 실행을 막고 보류 또는 보호자 확인으로 전환 |
| Caregiver Notification | 필요 시 보호자에게 확인 요청 | 사용자가 응답하지 못할 때 도움 연결 |
| Audit Log | timeout, no-response, 보류 사유 기록 | 왜 실행하지 않았는지 추적 |

---

## 6. 처리 과정

### 6.1 시스템이 Class 2 clarification으로 진입한다

입력이 불명확해 바로 실행하지 않고 Class 2 clarification 상태로 들어간다.

### 6.2 후보를 제시한다

후보 제시는 다음 topic의 evidence로 기록될 수 있다.

```text
safe_deferral/clarification/interaction
```

이 payload는 후보 제시 증거일 뿐 실행 권한이 아니다.

### 6.3 사용자의 응답을 기다린다

시스템은 버튼, 음성, 보호자 확인 등으로 선택이 들어오는지 기다린다.

### 6.4 timeout 또는 no-response를 기록한다

정해진 시간 안에 선택이 들어오지 않으면 시스템은 timeout 또는 no-response로 기록한다.

```text
응답 없음
선택 없음
의도 추정 금지
```

### 6.5 자동 실행하지 않는다

시스템은 후보 중 하나를 임의로 실행하지 않는다.

특히 조명 제어, 긴급 전이, doorlock 같은 민감 액추에이션은 응답 없음만으로 선택될 수 없다.

### 6.6 Safe Deferral 또는 Caregiver Confirmation으로 전환한다

시스템은 다음 중 안전한 경로로 넘어간다.

```text
아무 동작도 실행하지 않고 안전 보류
사용자에게 다시 안내
보호자에게 확인 요청
상태를 audit log에 기록
```

---

## 7. 기대 결과

```text
초기 상태: Class 2 clarification
사용자 응답: timeout 또는 no-response
금지 결과: 자동 Class 1 실행
금지 결과: 자동 Class 0 전이
금지 결과: doorlock authorization
최종 결과: Safe Deferral 또는 Caregiver Confirmation
```

---

## 8. 안전상 중요한 점

- 무응답은 선택이 아니다.
- timeout은 사용자 의도 증거가 아니다.
- candidate presentation은 validator approval이 아니다.
- 자동 실행 대신 안전 보류 또는 보호자 확인으로 넘어가야 한다.
- timeout/no-response는 audit-visible해야 한다.

