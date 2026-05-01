# Class 2 Caregiver Confirmation Doorlock-Sensitive Scenario User Story
## 방문자 상황에서 도어락 요청을 보호자 확인으로 넘기는 상황

## 1. 이 문서가 설명하는 JSON 파일

이 문서는 다음 scenario JSON 파일을 실제 사용환경에서 일어날 수 있는 상황으로 풀어 설명한다.

```text
integration/scenarios/class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json
```

이 JSON 파일은 방문자 또는 도어락 관련 요청이 들어왔을 때, 시스템이 이를 낮은 위험도의 Class 1 자동 실행으로 처리하지 않고 Class 2 caregiver confirmation 또는 별도 governed manual confirmation path로 넘기는지를 검토하기 위한 시나리오다.

---

## 2. 발생 상황

사용자는 집 안에 있고, 현관에서 초인종 또는 방문자 감지 이벤트가 발생한다.

동시에 사용자가 버튼을 누르거나, 제한된 입력을 통해 방문자에게 응답하려는 상황이 생길 수 있다.

예를 들어 사용자는 다음 중 하나를 원할 수 있다.

```text
방문자가 왔는지 확인하고 싶다.
보호자에게 방문자 상황을 알리고 싶다.
문을 열어달라는 의도를 표현하려고 했을 수 있다.
```

하지만 도어락 제어는 현재 Class 1 autonomous low-risk catalog에 포함되지 않는다.

`doorbell_detected=true`는 방문자 상황을 설명하는 context일 뿐, door unlock authorization이 아니다.

---

## 3. 시스템이 인식해야 하는 상황

시스템은 다음을 분명히 구분해야 한다.

```text
doorbell_detected=true
→ 최근 현관 호출 또는 방문자 도착 context가 있음

door unlock authorization
→ 아님
```

**중요: `doorbell_detected` 위치에 따른 라우팅 차이**

| 위치 | 의미 | Policy Router 결과 |
|---|---|---|
| `environmental_context.doorbell_detected=true` (+ button trigger) | 방문자 있는 상태에서 사용자 버튼 입력 | **CLASS_1** (lighting 등 저위험 동작 가능) |
| `trigger_event.event_type=sensor, event_code=doorbell_detected` | 초인종 자체가 트리거 이벤트 (C208) | **CLASS_2** → caregiver escalation |

즉, `environmental_context.doorbell_detected=true`만으로는 CLASS_2에 진입하지 않는다.
CLASS_2(C208)는 doorbell sensor 자체가 `trigger_event`로 올 때 발생한다.

따라서 방문자 상황이 있어도 시스템은 도어락을 자동으로 열면 안 된다.

도어락 관련 요청은 민감 액추에이션이므로 Class 2 notification, caregiver confirmation, 또는 별도 governed manual confirmation path로 넘어가야 한다.

---

## 4. 정보 출처 노드 및 상태 정보

| 항목 | 정보를 제공하는 노드/구성요소 | 제공되는 정보 | 시나리오 내 상태 |
|---|---|---|---|
| 방문자 context | Doorbell/Visitor Context Node | `doorbell_detected` 값 | true일 수 있음 |
| 사용자 입력 | Bounded Input Node 또는 Voice Input | 제한된 방문자 응답 입력 | 의미가 민감할 수 있음 |
| 정책 판단 | Policy Router | 도어락 관련 요청을 Class 2로 분류 | 자동 Class 1 차단 |
| Class 2 알림 | Mac mini Edge Hub | 보호자에게 전달할 상황 요약 | class2 notification 생성 |
| 보호자 확인 | Caregiver Confirmation Backend | confirm, deny, timeout 등 | 별도 governed manual path |
| clarification evidence | Class 2 Clarification Manager | 필요 시 후보/확인 evidence | 권한 아님 |
| ACK와 기록 | Audit Log, ACK Handler | 수동 경로의 확인과 결과 | audit-visible 필요 |

---

## 5. 노드별 개발 관점 정리

| 노드/구성요소 | 개발 시 필요한 기능 | 이 시나리오에서의 역할 |
|---|---|---|
| Doorbell/Visitor Context Node | 초인종 또는 방문자 도착 context 제공 | 방문자 상황을 알려줌 |
| Bounded Input Node | 사용자의 제한된 방문자 응답 입력 수집 | 모호하거나 민감한 요청의 시작점 |
| Policy Router | 도어락 관련 요청을 Class 2로 분류 | 자동 Class 1 실행 차단 |
| Class 2 Clarification Manager | 필요 시 bounded clarification evidence 생성 | 도어락 권한을 만들지 않음 |
| Caregiver Confirmation Backend | 보호자 확인, 거부, 무응답 처리 | 별도 수동 확인 경로 관리 |
| Doorlock Interface | 실험상 민감 액추에이션 대표 대상 | 현재 Class 1 자동 실행 대상 아님 |
| Audit Log | 알림, 확인, ACK, 거부, timeout 기록 | 민감 경로의 추적성 확보 |

---

## 6. 처리 과정

### 6.1 방문자 context가 들어온다

Doorbell/Visitor Context Node가 방문자 도착 context를 전달한다.

```text
doorbell_detected: true
```

이 값은 방문자 응답 해석에 도움을 주지만, 도어락을 열 권한은 아니다.

### 6.2 사용자의 제한된 입력이 들어온다

사용자가 버튼을 누르거나 짧은 음성 입력을 보낼 수 있다.

이 입력은 방문자에게 응답하려는 의도일 수 있지만, 도어락 실행으로 바로 연결되면 안 된다.

### 6.3 Policy Router가 Class 2로 분류한다

도어락 또는 문 열림과 연결될 수 있는 요청은 sensitive actuation으로 취급한다.

```text
Class 1 autonomous execution: 금지
Class 2 caregiver confirmation: 필요
```

### 6.4 보호자에게 상황을 알린다

시스템은 보호자에게 방문자 context와 사용자의 제한된 입력을 요약해 전달할 수 있다.

예를 들어 다음 정보가 포함될 수 있다.

```text
방문자 감지 여부
사용자 입력 발생 시각
요청이 도어락 관련 민감 액추에이션일 수 있다는 점
자동 실행하지 않았다는 점
```

### 6.5 보호자가 확인하거나 거부한다

보호자는 별도 governed manual confirmation path를 통해 확인 또는 거부할 수 있다.

보호자 확인은 Class 1 validator approval과 다르다. 이는 별도의 수동 확인 경로이며, 현재 autonomous low-risk catalog를 확장하지 않는다.

### 6.6 ACK와 audit가 남아야 한다

만약 별도 수동 경로에서 어떤 도어락 관련 조치가 수행된다면, ACK와 audit 기록이 필요하다.

응답이 없거나 거부되거나 검증할 수 없으면 시스템은 안전 보류 또는 caregiver confirmation 유지 상태로 남아야 한다.

---

## 7. 기대 결과

```text
초기 상태: 방문자 또는 도어락 관련 sensitive request
route_class: CLASS_2
자동 Class 1 doorlock 실행: 금지
doorbell_detected 기반 unlock authorization: 금지
후속 경로: Caregiver Confirmation 또는 Safe Deferral
```

---

## 8. 안전상 중요한 점

- `doorbell_detected`는 방문자 context이지 unlock authorization이 아니다.
- Doorlock은 현재 autonomous Class 1 low-risk catalog에 없다.
- Class 2 notification은 actuation authority가 아니다.
- Caregiver confirmation은 validator approval이 아니다.
- 수동 도어락 경로가 실험에 포함되더라도 ACK와 audit가 필요하다.

