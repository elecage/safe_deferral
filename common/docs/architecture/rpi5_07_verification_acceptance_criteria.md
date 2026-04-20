# Raspberry Pi 5 Verification / Acceptance Criteria

## 목적
Raspberry Pi 5가 Track B의 시뮬레이션 및 결함 주입 노드로서 안정적으로 동작하고, Mac mini의 안전 결정 결과를 **자동 폐루프 방식**으로 검증할 수 있는지 확인한다.

## 1. Broker Connectivity

### 기준

* Mac mini Mosquitto broker에 LAN을 통해 연결 가능
* `.env` 기반 broker host/port/credentials 반영 성공
* publish 테스트 성공
* topic namespace가 예상대로 반영됨

## 2. Throughput and Publish Stability

### 기준

* 30~40개 virtual nodes 동시 publish 시 크래시 없음
* publish loop가 설정된 interval 범위 내에서 유지됨
* deterministic scenario 실행 중 메시지 발행이 누락되지 않음

## 3. Reproducibility

### 기준

* deterministic fault scenario를 동일 설정으로 재실행했을 때 동일한 fault metadata 생성
* scenario orchestrator의 run summary가 반복 실행 간 일관됨

## 4. Correct Fault Generation

### 기준

* 모든 fault는 `policy_table.json`, `context_schema.json`, `fault_injection_rules.json`에서 파싱한 값으로 생성됨
* Threshold-crossing emergency injection은 minimal triggering predicate를 만족함
* Context conflict injection은 expected safe outcome label을 포함함
* Missing state injection은 policy-input omission과 validator/action omission을 구분함

## 5. Artifact Sync Correctness

### 기준

* Pi 5 로컬의 정책/스키마 파일 해시 또는 버전이 Mac mini source와 일치
* 런타임 모듈이 로컬 synced artifact만 참조함
* unattended sync 방식으로 자동화가 중단되지 않음

## 6. Time Sync Accuracy / Validity

### 기준

* Mac mini를 authoritative local time source로 사용
* 외부 WAN NTP 서버를 사용하지 않음
* 실험 전 clock offset 측정 및 로그 저장
* offset이 사전에 정의한 target bound 이내인지 확인
* stale fault injection margin이 measured offset + jitter보다 충분히 큼

주의: “절대 10ms 보장”이 아니라, **측정·기록·검증 가능한 target bound 기반**으로 관리한다.

## 7. Closed-loop Automated Verification

### 기준

* Pi 5 verification script가 fault/test payload를 publish함과 동시에 **verification-safe audit MQTT stream**을 구독함
* Mac mini의 observed routing/logging outcome이 expected safe outcome과 자동 비교됨
* Safe Deferral / Class 2 / Class 0 결과가 자동 assert됨
* 수동 화면 확인 없이 pass/fail 판정 가능

## 8. Security / Config Hygiene

### 기준

* broker credentials 하드코딩 금지
* `.env` 또는 외부 설정 파일 사용
* topic namespace 분리 유지
* 로컬 인증이 활성화된 경우 인증 성공/실패 동작 검증

## 9. 최종 합격 조건

다음이 모두 만족되면 Pi 5 개발 산출물을 합격으로 본다.

  1. MQTT connectivity PASS
  1. artifact sync PASS
  1. time sync check PASS
  1. deterministic scenario reproducibility PASS
  1. fault generation correctness PASS
  1. publish stability PASS
  1. closed-loop verification PASS