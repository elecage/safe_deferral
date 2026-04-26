# experiment_preflight_readiness_design.md

## 1. 목적

이 문서는 **실험별 required node / preflight readiness** 설계안을 정리한다.

목표는 다음과 같다.

- 실험 실행 전에 어떤 노드/서비스/자산이 필요한지 선언한다.
- 현재 시스템 상태를 바탕으로 **READY / DEGRADED / BLOCKED / UNKNOWN** 판정을 수행한다.
- Home Assistant 대시보드 또는 다른 실험 제어 UI에서 **실험 시작 가능 여부**를 설명 가능하게 만든다.
- 실험 실행 경로와 out-of-band measurement 경로를 분리한다.

이 문서는 canonical policy/schema truth를 재정의하지 않는다.
이 문서의 역할은 **운영/평가용 preflight 계층 설계**다.

---

## 2. 핵심 원칙

### 2.1 preflight readiness는 정책 authority가 아니다
이 설계는 다음만 담당한다.

- 실험별 의존성 선언
- 상태 수집
- 사전조건 검사
- 최종 readiness 판정
- blocked reason 설명

이 설계는 다음을 하지 않는다.

- policy semantics 변경
- validator 판단 대체
- canonical trigger family 재정의
- low-risk catalog 확장

### 2.2 operational node와 measurement node를 분리한다
본 프로젝트에서 out-of-band measurement node는 일반 physical node와 별도로 취급한다.

예:
- operational / physical node:
  - Mac mini
  - Mosquitto
  - Home Assistant
  - Raspberry Pi simulator/evaluation node
  - ESP32 bounded physical nodes
- measurement node:
  - STM32 time probe / timestamp capture node

STM32 Nucleo-H723ZG 기반 시간계측 노드는 **integration/measurement/ layer**에 속하며, operational control path에 개입하지 않는다.

### 2.3 실험별 required dependency는 역할 중심으로 선언한다
특정 보드명 그 자체보다, 실험에 필요한 역할을 기준으로 선언한다.

예:
- `mosquitto`
- `edge_controller_app`
- `rpi`
- `button_input_node`
- `measurement_time_probe_a`
- `measurement_time_probe_b`

구현 metadata로 `esp32`, `stm32`, `rpi_simulator` 같은 세부 구현체를 구분할 수 있다.

---

## 3. 상태 판정 레벨

각 preflight 항목은 아래 4단계로 판정한다.

### READY
실험 실행에 필요한 조건이 충족됨.

### DEGRADED
실험은 실행 가능하나 품질, 정밀도, 또는 결과 완전성이 저하될 수 있음.

예:
- optional plot exporter 없음
- measurement node 일부 부재
- time sync margin이 권장치에 비해 좁음

### BLOCKED
실험 실행 자체가 불가능함.

예:
- required node offline
- required service unavailable
- required asset missing
- experiment runner busy

### UNKNOWN
상태를 판정할 근거가 부족함.

예:
- heartbeat 없음
- checker timeout
- health endpoint 미구현

---

## 4. 기본 개체 모델

## 4.1 Experiment Registry
각 실험의 메타데이터 정의.

권장 필드:
- `experiment_id`
- `display_name`
- `description`
- `required_nodes`
- `required_services`
- `required_topics`
- `required_assets`
- `required_runtime_conditions`
- `required_measurement_nodes`
- `expected_result_artifacts`
- `blocked_if_missing`

예시:

```json
{
  "experiment_id": "EXP_FAULT_STALENESS_01",
  "display_name": "Fault Staleness Closed-Loop Audit",
  "required_nodes": [
    "mac_mini",
    "mosquitto",
    "rpi",
    "edge_controller_app"
  ],
  "required_services": [
    "mqtt_broker",
    "audit_pipeline"
  ],
  "required_topics": [
    "safe_deferral/context/input",
    "safe_deferral/validator/output"
  ],
  "required_assets": [
    "policy_table.json",
    "fault_injection_rules.json"
  ],
  "required_runtime_conditions": [
    "artifact_sync_complete",
    "mqtt_reachable"
  ],
  "required_measurement_nodes": [
    "stm32_time_probe_01",
    "stm32_time_probe_02"
  ],
  "expected_result_artifacts": [
    "summary.json",
    "raw_audit.log",
    "latency.csv",
    "latency_plot.png"
  ],
  "blocked_if_missing": true
}
```

## 4.2 Node Registry
각 node/service의 상태와 capability를 관리한다.

예시:

```json
{
  "node_id": "stm32_time_probe_01",
  "node_class": "measurement_node",
  "implementation": "stm32_nucleo_h723zg",
  "state": "ready",
  "last_heartbeat": "2026-04-23T16:10:00+09:00",
  "capabilities": [
    "time_sync_probe",
    "latency_capture",
    "timestamp_export"
  ]
}
```

---

## 5. required dependency 분류

실험 의존성은 다음 3층으로 나누는 것을 권장한다.

### 5.1 Operational dependencies
실험 자체가 성립하기 위한 노드/서비스.

예:
- Mac mini
- Mosquitto
- Home Assistant
- Raspberry Pi
- edge_controller_app
- ESP32 physical node

이 계층이 실패하면 보통 **BLOCKED**다.

### 5.2 Measurement dependencies
정밀 계측, out-of-band timing capture, 결과 근거 확보를 위한 노드.

예:
- STM32 Nucleo-H723ZG time probe A
- STM32 Nucleo-H723ZG time probe B

이 계층은 실험 종류에 따라 의미가 다르다.

- 일부 실험에서는 measurement node 부재가 **DEGRADED**
- 정밀 latency 실험에서는 **BLOCKED**

### 5.3 Artifact / runtime dependencies
노드는 아니지만 readiness에 필수적인 자산.

예:
- policy/schema asset deployed
- RPi sync completed
- result directory writable
- active fault profile available
- required experiment fixture present

---

## 6. STM32 measurement node의 위치

STM32 Nucleo-H723ZG 기반 측정 노드는 본 설계에서 **out-of-band measurement node**다.

### 6.1 역할
- physical node 간 시간 동기화 보조
- trigger-to-observe / observe-to-actuate 지연 계측
- class-wise latency 실험의 timestamp 근거 수집
- exportable timestamp/CSV 생성 보조

### 6.2 비역할
- policy routing 참여 안 함
- validator decision 참여 안 함
- actuator control path 참여 안 함
- operational control authority 아님

### 6.3 문서상 위치
- `integration/measurement/`
- optional out-of-band timing / latency evaluation support

즉 STM32는 ESP32 bounded physical node와 같은 층이 아니라, measurement support 계층에 속한다.

---

## 7. readiness 판정 항목

## 7.1 Node connectivity
예:
- ping reachable
- heartbeat fresh
- container running
- serial/USB reachable
- API health reachable

## 7.2 Functional service health
예:
- Mosquitto publish 가능
- edge_controller_app subscribe/publish 가능
- Ollama inference 응답 가능
- Home Assistant UI/API reachable

## 7.3 Asset readiness
예:
- required JSON asset 존재
- JSON parse 가능
- RPi artifact sync 완료
- active fault profile 존재
- result storage writable

## 7.4 Measurement readiness
예:
- STM32 probe online
- measurement arming complete
- time capture path healthy
- timestamp export available
- measurement output directory writable

## 7.5 Experiment-specific conditions
예:
- runner idle
- test fixture exists
- audit topic configured
- required namespace available

---

## 8. blocked reason 표준 코드

대시보드/로그/요약에서 일관되게 쓰기 위해 blocked reason 코드를 표준화한다.

예시:
- `NODE_OFFLINE`
- `SERVICE_UNREACHABLE`
- `ASSET_MISSING`
- `ASSET_INVALID`
- `MQTT_UNREACHABLE`
- `RUNNER_BUSY`
- `AUDIT_PIPELINE_UNAVAILABLE`
- `EDGE_CONTROLLER_APP_UNAVAILABLE`
- `RESULT_STORE_NOT_WRITABLE`
- `SSH_SYNC_INCOMPLETE`
- `MEASUREMENT_NODE_UNAVAILABLE`
- `MEASUREMENT_EXPORT_UNAVAILABLE`
- `TIME_PROBE_HEARTBEAT_STALE`

예:

```json
{
  "final_state": "BLOCKED",
  "reasons": [
    {
      "code": "EDGE_CONTROLLER_APP_UNAVAILABLE",
      "message": "edge_controller_app is not running"
    }
  ]
}
```

---

## 9. 실험별 required dependency 초안

## 9.1 EXP_MQTT_PUBSUB_VERIFY
필수:
- `mac_mini`
- `mosquitto`

권장:
- `rpi`

measurement node:
- 없음

blocked 조건:
- mosquitto offline

## 9.2 EXP_NOTIFICATION_VERIFY
필수:
- `mac_mini`
- `notification_backend`

measurement node:
- 없음

## 9.3 EXP_TIME_SYNC_MARGIN
필수:
- `mac_mini`
- `rpi`

권장:
- chrony / timesync healthy

measurement node:
- optional

## 9.4 EXP_FAULT_STALENESS_01
필수:
- `mac_mini`
- `mosquitto`
- `rpi`
- `edge_controller_app`

필수 자산:
- `policy_table.json`
- `fault_injection_rules.json`

measurement node:
- optional for precise timing evidence
  - `stm32_time_probe_01`
  - `stm32_time_probe_02`

판정 예:
- edge_controller_app 없음 → `BLOCKED`
- STM32 probe 없음 → 실험은 가능하나 정밀 측정은 `DEGRADED`

## 9.5 EXP_CLASSWISE_LATENCY_PROFILE
필수:
- `mac_mini`
- `mosquitto`
- `rpi`
- experiment runner

필수 measurement node:
- `stm32_time_probe_01`
- `stm32_time_probe_02`

blocked 조건:
- measurement node unavailable
- timestamp export path unavailable

## 9.6 EXP_TRIGGER_TO_ACTUATION_TIMING
필수:
- `mac_mini`
- `mosquitto`
- `edge_controller_app`
- relevant physical/simulated source node

필수 measurement node:
- `stm32_time_probe_01`
- `stm32_time_probe_02`

blocked 조건:
- measurement path unavailable

---

## 10. preflight 알고리즘 초안

실험 선택 시 아래 순서로 판정한다.

### Step 1
Experiment Registry에서 실험 메타데이터를 로드한다.

### Step 2
required operational node 상태를 수집한다.

### Step 3
required service / topic readiness를 수집한다.

### Step 4
required asset / runtime condition을 검사한다.

### Step 5
required_measurement_nodes 및 measurement export 조건을 검사한다.

### Step 6
최종 상태를 계산한다.

권장 규칙:
- required operational dependency에 blocked가 하나라도 있으면 `BLOCKED`
- measurement dependency만 문제이고 실험 자체는 가능하면 `DEGRADED`
- 전부 준비되면 `READY`
- 핵심 상태 판단이 불가하면 `UNKNOWN`

---

## 11. Home Assistant dashboard와의 연결

대시보드에서 실험 선택 시 아래를 보여주는 것을 권장한다.

- selected experiment
- required operational nodes
- required measurement nodes
- node state table
- required assets
- measurement readiness
- final readiness
- blocking reasons
- start button enabled / disabled

### Start button 규칙
- `READY` → enabled
- `DEGRADED` → enabled with warning
- `BLOCKED` → disabled
- `UNKNOWN` → disabled or manual override only

---

## 12. MQTT topic 예시

Preflight and monitoring examples should stay within the active
`safe_deferral/...` namespace unless the topic registry is intentionally updated.

### dashboard / node observation
- `safe_deferral/dashboard/observation`

### experiment progress and result
- `safe_deferral/experiment/progress`
- `safe_deferral/experiment/result`

---

## 13. expected result artifacts 예시

측정/분석이 필요한 실험은 최소 아래 결과물 중 일부를 기대할 수 있다.

- `summary.json`
- `raw_timestamps.csv`
- `latency.csv`
- `latency_plot.png`
- `run_metadata.json`
- `raw_log.txt`

STM32 measurement node가 포함되는 실험은 `timestamp export`와 `CSV/graph availability`를 readiness와 결과 양쪽에서 고려하는 것이 좋다.

---

## 14. 현재 프로젝트에 대한 현실적 해석

현재 known blocked example:

- `EXP_FAULT_STALENESS_01`
  - current likely blocked reason:
    - `EDGE_CONTROLLER_APP_UNAVAILABLE`

즉, preflight 계층은 실험이 왜 막히는지 솔직하게 보여줘야 한다.
이 설계는 단순 online/offline 표기가 아니라, **experiment-ready / blocked-by / measurement-degraded**를 설명 가능하게 만드는 것이 핵심이다.

---

## 15. 후속 구현 권장안

1. experiment registry file 추가
2. node registry / heartbeat format 정의
3. preflight readiness aggregator 구현
4. Home Assistant dashboard prototype에 readiness panel 반영
5. STM32 measurement node heartbeat / export contract 정의
6. result artifact naming 규칙 문서화
