# 25_architecture_handoff_status.md

## 1. 목적

이 문서는 현재까지 진행된 **논문용 시스템 구조도 정리 작업의 인수인계 문서**이다.
주요 목적은 다음과 같다.

- 현재 확정된 최종 구조도 상태를 기록
- 어떤 설계 판단이 내려졌는지 정리
- 어느 문서와 그림이 최종 기준인지 명시
- 다음 작업자가 이어서 검토해야 할 포인트를 남김

---

## 2. 현재 최종 기준 파일

현재 논문용 최종 구조도 기준은 아래 두 파일이다.

- 최종 그림: `common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg`
- 최종 설명 문서: `common/docs/architecture/24_final_paper_architecture_figure.md`

즉, 후속 수정이나 검토는 위 두 파일을 기준으로 해야 한다.

---

## 3. 현재 구조도의 핵심 해석

### 3.1 전체 구조

현재 구조도는 크게 다음 세 영역으로 해석된다.

- **ESP32 Device Layer**
- **Mac mini Edge Hub**
- **Raspberry Pi 5 support region**

### 3.2 ESP32 Device Layer

ESP32 쪽에는 다음 서브 블록이 포함되어 있다.

- `Bounded Input Node`
- `Context Nodes`
- `Emergency Nodes`
- `Actuator Interface Nodes`

이 영역은 현장 입력, 센싱, 긴급 감지, 액추에이터 인터페이스를 담당한다.

### 3.3 Mac mini Edge Hub

Mac mini는 현재 **L자형 외곽선**으로 표현되어 있으며, caregiver approval 처리 영역까지 같은 운영 호스트 경계 안에 포함되도록 정리되어 있다.

이 영역에는 다음 블록이 포함된다.

- `MQTT Ingestion / State Intake`
- `Context and Runtime State Aggregation`
- `Local LLM Reasoning Layer`
- `Policy Routing + Validation`
- `Approved Low-Risk Actuation Path`
- `Safe Deferral and Clarification Management`
- `Caregiver Escalation`
- `Caregiver Approval`
- `TTS Rendering / Voice Output`
- `Local ACK + Audit Logging`

### 3.4 Raspberry Pi 5 support region

Raspberry Pi 영역은 논문용 최종 구조도에서도 유지하기로 결정되었다.
이 영역은 제어의 핵심 권한보다는 **모니터링 / 실험 / 결과 가시화 계층**으로 해석한다.

현재 Raspberry Pi 내부 블록은 다음과 같다.

- `Monitoring / Experiment Dashboard`
- `Experiment Support`
- `Progress / Result Publication`

---

## 4. 이번까지 확정된 주요 설계 판단

### 4.1 Caregiver Approval의 위치

초기에는 caregiver approval을 Raspberry Pi 쪽에 둘지 Mac mini 쪽에 둘지 논의가 있었으나,
최종적으로는 **Caregiver Approval을 Mac mini 운영 경계 안에 포함**하는 방향으로 정리되었다.

즉, caregiver approval은 단순 외부 UI가 아니라,
정책 기반 제어 루프 안에서 민감 액션 승인을 담당하는 운영 구성요소로 해석한다.

### 4.2 Raspberry Pi의 역할

Raspberry Pi는 최종 구조도에서 제거하지 않고 유지한다.
다만 역할은 핵심 제어가 아니라 다음과 같이 정리한다.

- 모니터링
- 실험 시나리오 지원
- 진행상황 / 결과 가시화

따라서 Raspberry Pi는 **support / monitoring / experiment layer**로 해석한다.

### 4.3 대시보드의 위치

대시보드는 Mac mini가 아니라 Raspberry Pi 내부에 두는 것으로 결정되었다.
현재 채택된 블록명은 다음과 같다.

- `Monitoring / Experiment Dashboard`

이 블록은 caregiver state visibility, event view, runtime status, experiment monitoring을 나타내는 용도로 사용한다.

### 4.4 LLM과 TTS의 관계

구조도에는 직접적인 `Local LLM Reasoning Layer → TTS Rendering / Voice Output` 경로를 두지 않았다.
이는 LLM 출력이 곧바로 음성으로 나가는 것이 아니라,
반드시 `Policy Routing + Validation`을 거친 **policy-constrained spoken output**으로 해석되도록 하기 위한 것이다.

### 4.5 Safe Deferral의 위치와 역할

`Safe Deferral and Clarification Management`는 단순 예외처리가 아니라,
구조도상 독립된 정책 결과 상태로 유지한다.
즉, 이 시스템은 단순 실행/실패 이분법이 아니라,
**안전 보류(safe deferral)**를 1급 결과 상태로 가진다는 점을 구조도에 반영한다.

---

## 5. 선(경로) 관련 최종 반영 사항

### 5.1 Policy branching

현재 최종 구조도에서 `Policy Routing + Validation`은 다음 세 방향으로 분기한다.

- `Approved Low-Risk Actuation Path`
- `Safe Deferral and Clarification Management`
- `Caregiver Escalation`

### 5.2 Caregiver Approval → Actuator 경로

이 경로는 사용자 피드백을 반영해 최종적으로 **직교 경로(orthogonal path)** 형태로 조정되었다.
최종 해석은 다음과 같다.

- `Caregiver Approval`에서 시작
- 약간 왼쪽으로 진행
- 아래로 꺾임
- 같은 높이에서 다시 왼쪽으로 진행
- `Approved Low-Risk → Actuator` 경로의 외곽 꺾임 x축 위치에서 위로 꺾임
- 마지막으로 오른쪽으로 꺾여 actuator 경로 쪽으로 연결

즉, caregiver-mediated execution path가 low-risk execution path와 시각적으로 구분되면서도,
결국 actuator 쪽 인터페이스로 합류하는 구조를 보이도록 조정되었다.

### 5.3 Approved Low-Risk → Actuator 경로

이 경로 역시 외곽 꺾임점이 ESP32와 Mac mini 사이의 공간에서 균형 있게 보이도록 조정되었다.

---

## 6. 레이아웃 관련 최종 반영 사항

### 6.1 Raspberry Pi 내부 레이아웃

Raspberry Pi 내부는 현재 위에서 아래 순서로 다음과 같이 배치된다.

1. `Monitoring / Experiment Dashboard`
2. `Experiment Support`
3. `Progress / Result Publication`

또한 다음 사항이 반영되었다.

- Dashboard의 윗변은 `Policy Routing + Validation`의 윗변과 맞춤
- `Progress / Result Publication` 블록은 텍스트가 밖으로 나오지 않도록 높이를 증대
- Raspberry Pi 오른쪽 변은 상단 caregiver actor 및 caregiver approval 관련 배치와 정렬되도록 조정

### 6.2 Caregiver 관련 블록 정렬

- `Caregiver Escalation`과 `Caregiver Approval`의 밑변은 `TTS Rendering / Voice Output`의 밑변과 정렬되도록 조정
- 상단 `Caregiver` actor의 오른쪽 변은 Raspberry Pi 오른쪽 변과 정렬
- `Caregiver Approval` 블록은 Mac mini 오른쪽 경계와 붙지 않도록 너비를 약간 축소

### 6.3 Mac mini 외곽선

Mac mini 외곽선은 현재 **아래 오른쪽이 돌출된 L자형**이다.
이 형태는 caregiver approval을 동일 운영 경계 안에 넣기 위한 의도적 선택이다.

---

## 7. 이미 반영된 GitHub 파일 상태

현재 다음 파일들이 이미 GitHub에 반영되어 있다.

- `common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg`
- `common/docs/architecture/24_final_paper_architecture_figure.md`

이 두 파일은 현 시점의 논문용 최종 구조도 기준으로 간주한다.

---

## 8. 다음 작업자가 검토하면 좋은 항목

다음 단계에서는 아래 문서들이 현재 최종 구조도와 일치하는지 검토하는 것이 좋다.

- `14_system_components_outline_v2.md`
- `15_interface_matrix.md`
- 이후 장별 설계 설명 문서들

특히 확인할 항목은 다음과 같다.

- caregiver approval의 호스트 위치 해석이 여전히 Raspberry Pi 쪽으로 남아 있지 않은지
- Raspberry Pi 내부 대시보드 반영이 문서에도 반영되어 있는지
- safe deferral이 독립 결과 상태로 문서에 일관되게 남아 있는지
- LLM과 TTS 사이 직접 경로가 있다고 오해하게 쓰인 부분이 없는지

---

## 9. 요약

현재 논문용 구조도는 다음과 같이 확정된 상태다.

- Mac mini는 L자형 운영 경계
- caregiver approval은 Mac mini 경계 안
- Raspberry Pi는 support / dashboard / experiment layer
- dashboard는 Raspberry Pi 내부 최상단
- safe deferral은 독립 정책 결과 상태
- caregiver approval execution path는 요청에 따라 직교 경로로 정리

따라서 후속 작업은 **새 구조도를 다시 설계하는 것**이 아니라,
**기존 문서들이 이 최종 구조도를 정확히 따라오도록 정합성 검토**하는 방향으로 진행하면 된다.
