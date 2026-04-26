# stm32_nucleo_h723zg_measurement_node.md

## 1. 목적

이 문서는 **STM32 Nucleo-H723ZG**를 이용한 out-of-band measurement node 설계 및 개발 방향을 정리한다.

이 노드는 다음 용도로 사용한다.

- physical node 간 시간 싱크 보조
- trigger / observe / actuation timing capture
- class-wise latency 실험 근거 데이터 수집
- CSV / timestamp export 생성 보조

이 노드는 operational control path에 속하지 않는다.
즉, 본 노드는 **evaluation-only measurement support node**다.

---

## 2. 역할과 경계

## 2.1 해야 하는 일
- 실험용 timing capture point에서 timestamp 수집
- 여러 capture channel 간 상대 시간 비교
- 측정 시작/종료 상태 보고
- 결과 export (CSV 또는 raw timestamp)
- measurement heartbeat/status 보고

## 2.2 하면 안 되는 일
- policy routing 개입
- validator 결과 결정
- actuator command 발행
- low-risk / high-risk actuation semantics 해석
- emergency/class semantics 재정의

즉, STM32 measurement node는 **정책/제어 노드가 아니라 증거 수집 노드**다.

---

## 3. 권장 위치

문서/설계상 이 노드는 다음 계층에 속한다.

- `integration/measurement/`

해석:
- `esp32/`와 같은 bounded physical node layer가 아님
- `mac_mini/` operational hub도 아님
- `rpi/` simulation/fault injection layer도 아님
- **optional out-of-band timing / latency evaluation support**

---

## 4. Nucleo-H723ZG를 쓰는 이유

STM32 Nucleo-H723ZG는 다음 이유로 measurement node 후보로 적합하다.

- 상대적으로 높은 성능과 안정적인 타이머 자원
- 다수 GPIO 입력 캡처 구성 가능
- 실험용 timestamp capture firmware 개발에 유리
- 재현성 있는 bare-metal / HAL 기반 구현 가능
- LAN/MQTT operational path와 분리된 out-of-band 계측 구조에 적합

본 프로젝트에서는 이 보드를 **measurement probe** 또는 **timing capture node**로 사용한다.

---

## 5. 권장 capability 정의

측정 노드는 capability를 명시적으로 선언하는 것이 좋다.

예:

- `time_sync_probe`
- `latency_capture`
- `edge_timestamp_capture`
- `timestamp_export`
- `measurement_status_report`

예시 상태 표현:

```json
{
  "node_id": "stm32_time_probe_01",
  "node_class": "measurement_node",
  "implementation": "stm32_nucleo_h723zg",
  "state": "ready",
  "capabilities": [
    "time_sync_probe",
    "latency_capture",
    "timestamp_export"
  ]
}
```

---

## 6. 추천 측정 시나리오

이 노드는 다음 실험에서 특히 유용하다.

### 6.1 class-wise latency profile
- CLASS_0 / CLASS_1 / CLASS_2 경로별 지연 계측
- repeated-run summary 생성

### 6.2 trigger-to-observe timing
- 센서 trigger 발생 시점
- hub-side observe 시점
- audit emission 시점 비교

### 6.3 observe-to-actuation timing
- validator/dispatcher 결과 이후
- bounded actuator interface ACK까지의 시간 비교

### 6.4 out-of-band delay measurement
- MQTT application layer 로그와 별도로
- hardware-visible timing evidence 확보

---

## 7. 권장 하드웨어/배선 개념

정확한 배선은 실험 설계에 따라 달라질 수 있으나, 개념적으로는 다음 capture point를 고려한다.

- `CAPTURE_A`: trigger source edge
- `CAPTURE_B`: hub/bridge observable event edge
- `CAPTURE_C`: actuator interface ACK edge

예시 해석:
- `CAPTURE_A -> CAPTURE_B` = ingest / observe delay
- `CAPTURE_B -> CAPTURE_C` = decision / actuation acknowledgment delay
- `CAPTURE_A -> CAPTURE_C` = end-to-end response delay

주의:
- measurement wiring은 operational control path와 분리되어야 한다.
- measurement probe가 actuator command를 주입하면 안 된다.

---

## 8. 권장 소프트웨어 구조

STM32 firmware는 최소 다음 모듈로 나누는 것이 좋다.

- `capture/`
  - timer input capture
  - edge timestamp collection
- `sync/`
  - measurement session sync / start marker handling
- `export/`
  - UART/USB CDC 또는 other export path
- `status/`
  - heartbeat / health / metadata reporting
- `main/`
  - safe startup / main loop / error handling

권장 특성:
- deterministic startup
- conservative boot behavior
- explicit session start/stop
- bounded memory usage
- reproducibility-oriented log format

---

## 9. 통신/출력 방식 추천

measurement node는 operational MQTT plane에 직접 개입하지 않아도 된다.

권장 출력 방식 예:

### 방식 A. USB CDC / UART export
- 가장 단순하고 디버깅이 쉬움
- raw timestamp export 적합

### 방식 B. 별도 measurement collector로 serial ingest
- Mac mini 또는 measurement collector가 수집
- CSV/JSON 변환 가능

### 방식 C. 제한적 status heartbeat
- measurement readiness만 MQTT 또는 bridge를 통해 보고
- 단, measurement node가 operational control semantics를 발행하지 않도록 주의

권장 방향:
- **timestamp/raw data export는 serial/USB 우선**
- **readiness/heartbeat는 필요 시 bridge를 통해 상위 시스템에 전달**

---

## 10. Home Assistant 대시보드와의 연결 방식

대시보드에서 STM32 measurement node는 다음 용도로 표시된다.

- 연결 상태
- 마지막 heartbeat
- 마지막 capture 성공 여부
- 마지막 export 성공 여부
- 최근 CSV/plot 생성 상태

예:
- `STM32 Probe A: online`
- `STM32 Probe B: online`
- `Last session sync: OK`
- `Latest latency CSV: ready`
- `Latest plot: ready`

중요:
- 대시보드는 measurement node를 **실험 readiness / 결과 신뢰성 표시** 용도로 사용한다.
- operational command UI로 쓰면 안 된다.

---

## 11. preflight readiness에서의 해석

STM32 measurement node는 일반 required node와 별도로 본다.

### 예 1. EXP_FAULT_STALENESS_01
- edge_controller_app 없음 → `BLOCKED`
- STM32 probe 없음 → 실험은 가능하나 정밀 timing evidence 없음 → `DEGRADED`

### 예 2. EXP_CLASSWISE_LATENCY_PROFILE
- STM32 probe 없음 → `BLOCKED`

즉, 측정 노드는 **실험 종류에 따라 optional / required가 달라진다.**

---

## 12. 개발 권장 흐름

### 12.1 1단계: measurement firmware 최소 골격
- boot
- board init
- timer init
- capture channel init
- UART/USB export
- startup self-test log

### 12.2 2단계: single-channel capture
- 하나의 입력 edge timestamp 수집
- raw log export

### 12.3 3단계: multi-channel relative timing
- 2개 이상의 capture channel
- relative delta 계산
- CSV export format 정리

### 12.4 4단계: session control / readiness reporting
- measurement session start/stop
- capture armed/disarmed state
- heartbeat/status metadata

### 12.5 5단계: integration/measurement 문서와 결과 포맷 정렬
- latency.csv
- summary.json
- plot generation input format 정렬

---

## 13. 최소 결과물 권장안

STM32 측정 노드 개발의 최소 산출물은 다음이 바람직하다.

- firmware source
- build instructions
- pin/capture mapping notes
- export format spec
- sample capture output
- validation checklist

예시 결과 파일:
- `raw_timestamps.csv`
- `session_metadata.json`
- `latency_summary.csv`

---

## 14. 권장 검증 항목

- board boot success
- timer initialization success
- capture input edge detection success
- repeated-run timestamp reproducibility
- export path success
- no unintended operational command behavior

즉, 이 노드는 **정확히 측정만 하고**, operational side effect는 없어야 한다.

---

## 15. 향후 연결 권장안

향후에는 아래 자산과 연결되는 것이 바람직하다.

- `integration/measurement/class_wise_latency_profiles.md`
- `integration/measurement/experiment_preflight_readiness_design.md`
- Home Assistant experiment dashboard
- experiment runner result exporter

---

## 16. 요약

STM32 Nucleo-H723ZG는 본 프로젝트에서 **out-of-band measurement node**로 취급하는 것이 맞다.

핵심 정리:
- operational control path에 넣지 않는다.
- policy/validator authority와 분리한다.
- 실험 전 readiness 확인과 실험 후 결과 신뢰성 표시에서 중요한 역할을 한다.
- 일부 실험에서는 optional, 정밀 latency 실험에서는 required measurement node가 된다.
