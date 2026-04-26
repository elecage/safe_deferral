# Stale Fault Scenario User Story
## 상태 정보가 존재하지만 너무 오래되어 신뢰할 수 없는 상황

## 1. 이 문서가 설명하는 JSON 파일

이 문서는 다음 scenario JSON 파일을 실제 사용환경에서 일어날 수 있는 상황으로 풀어 설명한다.

```text
integration/scenarios/stale_fault_scenario_skeleton.json
```

이 JSON 파일은 실행 판단에 필요한 상태 정보가 완전히 없는 것은 아니지만, 그 정보가 너무 오래되었거나 신뢰할 수 없어 자동 실행에 사용할 수 없는 상황을 검토하기 위한 시나리오다.

이 시나리오는 missing-state fault와 구분된다.

```text
Missing-state fault
→ 필요한 상태 정보가 없음

Stale fault
→ 상태 정보는 있지만 너무 오래되었거나 신뢰할 수 없음
```

---

## 2. 발생 상황

사용자는 조명 제어 도움을 요청하기 위해 버튼을 한 번 누른다.

시스템에는 조명 상태 정보가 남아 있다. 하지만 그 정보는 오래전에 보고된 값이다.

예를 들어 다음과 같은 상황일 수 있다.

```text
마지막 조명 상태 보고가 오래됨
센서 freshness 기준을 넘김
최근 네트워크 지연 또는 노드 재시작 이력이 있음
사용자가 현재 있는 공간의 상태가 바뀌었을 가능성이 있음
```

이때 시스템이 오래된 상태를 최신 상태처럼 믿고 조명을 제어하면, 실제 상황과 다른 동작이 발생할 수 있다.

따라서 시스템은 stale state를 fresh state로 가정하지 않고 안전하게 보류하거나 Class 2 recheck, caregiver confirmation, safe deferral 흐름으로 넘어가야 한다.

---

## 3. 시스템이 인식해야 하는 상황

시스템은 “정보가 있다”와 “정보를 신뢰할 수 있다”를 구분해야 한다.

```text
- 사용자의 입력은 정상적으로 들어왔다.
- 조명 또는 context 상태 정보가 존재한다.
- 하지만 상태 정보의 timestamp 또는 freshness가 기준을 벗어났다.
- 오래된 상태에 기반한 자동 실행은 안전하지 않다.
- 따라서 stale fault로 처리해야 한다.
```

이 시나리오에서는 LLM이 오래된 정보를 바탕으로 실행 후보를 만들더라도, 그 후보는 실행 권한이 될 수 없다.

---

## 4. 정보 출처 노드 및 상태 정보

| 항목 | 정보를 제공하는 노드/구성요소 | 제공되는 정보 | 시나리오 내 상태 |
|---|---|---|---|
| 사용자 입력 | Bounded Input Node | 사용자가 버튼을 눌렀다는 이벤트 | 단일 입력 발생 |
| 오래된 context | Context Node 또는 Device State Reporter | 조도, 점유, 조명 상태 등 | 값은 있지만 freshness 위반 |
| freshness 판단 | Mac mini Edge Hub 또는 State Store | 마지막 보고 시각과 허용 기준 비교 | stale fault로 판단 |
| fault 규칙 | canonical policy/schema/fault references | stale 처리 기준 | 정책 기준에 따라 판단 |
| clarification evidence | Class 2 Clarification Manager | 필요 시 후보 제시 evidence | 실행 권한 아님 |
| 후속 처리 | Mac mini Edge Hub | Safe Deferral, Caregiver Confirmation, Class 2 recheck | 자동 실행 차단 |
| 기록 | Audit Log | stale 원인, 마지막 보고 시각, 최종 결과 | 추적 가능해야 함 |

---

## 5. 노드별 개발 관점 정리

| 노드/구성요소 | 개발 시 필요한 기능 | 이 시나리오에서의 역할 |
|---|---|---|
| Context Node | 환경 상태와 timestamp 제공 | freshness 판단 대상 |
| Device State Reporter | 기기 상태와 마지막 보고 시각 제공 | stale 여부 판단 대상 |
| State Store | 최신 상태와 timestamp 관리 | 오래된 상태를 식별 |
| Mac mini Edge Hub | stale state 감지와 안전 경로 선택 | 자동 실행 차단 |
| Class 2 Clarification Manager | 필요 시 재확인 또는 선택 후보 제시 | 권한 없는 evidence만 생성 |
| Caregiver Notification | 상태 신뢰성 문제를 보호자에게 전달 | 자동 실행이 어려운 경우 도움 연결 |
| Audit Log | stale fault 원인과 처리 결과 기록 | 실험 분석과 안전 검증 근거 |

---

## 6. 처리 과정

### 6.1 사용자가 버튼을 누른다

사용자는 조명 제어 또는 생활 보조 요청을 위해 버튼을 한 번 누른다.

```text
사용자 버튼 입력 1회 발생
```

### 6.2 시스템이 상태 정보를 확인한다

시스템은 조명 상태, 조도, 점유 여부 등 필요한 상태 정보를 확인한다.

이때 값 자체는 존재한다.

```text
조명 상태 값 존재
환경 context 값 존재
```

### 6.3 freshness를 확인한다

Mac mini Edge Hub 또는 State Store는 상태 정보의 timestamp를 확인한다.

```text
마지막 보고 시각이 너무 오래됨
허용 freshness 기준 위반
```

### 6.4 stale fault로 판단한다

시스템은 오래된 상태를 최신 상태로 가정하지 않는다.

```text
state exists
but state is stale
→ automatic actuation blocked
```

### 6.5 필요하면 Class 2 clarification 또는 recheck를 수행한다

시스템은 필요한 경우 사용자에게 다시 확인하거나, 상태 재수집을 요청하거나, 보호자 확인으로 전환할 수 있다.

이때 clarification evidence가 발행된다면 다음 topic을 사용한다.

```text
safe_deferral/clarification/interaction
```

이 evidence는 validator approval이나 actuator command가 아니다.

### 6.6 안전한 결과로 종료한다

가능한 안전 결과는 다음과 같다.

```text
Safe Deferral
Class 2 recheck
Caregiver Confirmation
```

금지되는 결과는 다음과 같다.

```text
오래된 상태를 최신 상태로 가정
오래된 상태를 근거로 autonomous actuation 수행
```

---

## 7. 기대 결과

```text
fault_type: stale_fault
상태 정보: 존재하지만 freshness 위반
자동 실행: 금지
허용 결과: CLASS_2, SAFE_DEFERRAL, CAREGIVER_CONFIRMATION
기록 필요: stale 원인, 마지막 보고 시각, 보류 또는 재확인 결과
```

---

## 8. 안전상 중요한 점

- 상태 정보가 있다는 사실만으로 충분하지 않다.
- stale state는 fresh state처럼 사용하면 안 된다.
- stale state 기반의 LLM 후보는 실행 권한이 아니다.
- Class 2 clarification evidence는 validator approval이 아니다.
- stale 원인과 최종 안전 결과는 audit-visible해야 한다.

