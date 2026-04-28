# 작업 계획 / Work Plan

**기준일**: 2026-04-28  
**현재 브랜치**: main (`ae86af6`)

---

## 전체 단계 개요

```
Phase 1 — 실행 준비 완성  (하드웨어 없이 가능)
Phase 2 — 하드웨어 연결 및 기본 동작 확인
Phase 3 — 실험 실행 (패키지 A/B/C)
Phase 4 — 논문 작성
```

---

## Phase 1 — 실행 준비 완성

> 하드웨어 없이 완료 가능. 우선 처리.

### 1-1. 의존성 파일 보완

**파일**: `requirements-rpi.txt`, `requirements-mac.txt`

현재 문제:
- `requirements-rpi.txt`: `fastapi`, `uvicorn`, `python-dotenv` 누락 → `rpi/code/main.py` 실행 불가
- `requirements-mac.txt`: `python-dotenv` 누락 → `.env` 자동 로딩 불가

작업:
- [ ] `requirements-rpi.txt`에 `fastapi>=0.115.0`, `uvicorn>=0.32.0`, `python-dotenv>=1.0.0` 추가
- [ ] `requirements-mac.txt`에 `python-dotenv>=1.0.0` 추가
- [ ] RPi 설치 스크립트(`rpi/scripts/install/30_install_python_deps_rpi.sh`)에서 신규 패키지 설치 확인 또는 추가

---

### 1-2. 시나리오 픽스처 파일 작성

**경로**: `integration/scenarios/` (현재 스켈레톤만 존재)

각 스켈레톤이 참조하는 `payload_fixture` 경로에 실제 발행 가능한 JSON 페이로드 파일이 없음.

작업:
- [ ] CLASS_1 기본 시나리오 픽스처 작성
  - 파일: `integration/tests/data/sample_policy_router_input_class1.json`
  - 내용: 유효한 `policy_router_input_schema.json` 준수 페이로드 (조명 요청)
- [ ] CLASS_0 긴급 시나리오 픽스처 작성 (가스, 낙상 등 각 트리거별)
  - 파일: `integration/tests/data/sample_policy_router_input_class0_e001.json` ~ `e005.json`
- [ ] CLASS_2 시나리오 픽스처 작성 (insufficient_context, staleness 등)
  - 파일: `integration/tests/data/sample_policy_router_input_class2_*.json`
- [ ] Fault injection 시나리오 픽스처 작성 (staleness, missing_state, conflict)
  - 파일: `integration/tests/data/sample_fault_*.json`
- [ ] `docs/setup/05_integration_run.md`에서 참조한 `sc01_light_on_request.json` 작성

참조 기준:
- `common/schemas/policy_router_input_schema.json`
- `common/schemas/context_schema.json`
- `common/policies/policy_table.json` (trigger 조건)
- `common/payloads/README.md`
- `integration/scenarios/*.json` 스켈레톤

---

### 1-3. 시스템 구조 다이어그램 수정

**참조**: `common/docs/architecture/08_system_structure_figure_revision_plan.md`

현재 상태: 개정 계획 존재, 실제 그림 미완성

작업:
- [ ] 개정 계획 검토
- [ ] 다이어그램 수정 (도구: draw.io, Mermaid, 또는 ASCII)
- [ ] `common/docs/architecture/figures/` 또는 `common/docs/architecture/figure_revision/` 저장

---

## Phase 2 — 하드웨어 연결 및 기본 동작 확인

> Mac mini + RPi 실물 연결 필요. ESP32는 Phase 3에서.

### 2-1. Mac mini 서비스 기동 확인

- [ ] Docker 서비스 기동: `docker compose up -d`
- [ ] 검증 스크립트 실행: `bash mac_mini/scripts/verify/80_verify_services.sh`
- [ ] Python 허브 앱 실행: `python mac_mini/code/main.py`
- [ ] `MQTT connected` 로그 확인

### 2-2. RPi 앱 기동 확인

- [ ] `ping mac-mini.local` 응답 확인
- [ ] Python 실험 앱 실행: `python rpi/code/main.py`
- [ ] 대시보드 접근 확인: `http://<RPi_IP>:8888/preflight`
- [ ] 거버넌스 UI 접근 확인: `http://<RPi_IP>:8889`

### 2-3. 단위 파이프라인 동작 확인

- [ ] 테스트 CLASS_1 페이로드 발행 후 Mac mini 로그 확인
  ```bash
  mosquitto_pub -h localhost -p 1883 -t safe_deferral/context/input \
    -f integration/tests/data/sample_policy_router_input_class1.json
  ```
  예상 로그: `Route: CLASS_1` → `Validation: approved` → `Dispatched command_id=...`
- [ ] 테스트 CLASS_0 페이로드 발행 후 Telegram 알림 수신 확인
- [ ] ACK 왕복 확인: PN-07/08 노드 또는 mock ACK 발행

### 2-4. ESP32 노드 프로비저닝

- [ ] 각 ESP32 노드 전원 투입 및 SoftAP 프로비저닝 완료
  - WiFi SSID/PW, MQTT Broker URI (`mqtt://mac-mini.local:1883`)
- [ ] 각 노드 연결 후 토픽 수신 확인
  ```bash
  mosquitto_sub -h localhost -p 1883 -t "safe_deferral/#" -v
  ```

---

## Phase 3 — 실험 실행

> `common/docs/required_experiments.md` 기준.

### 3-1. 패키지 A — 정책 분기 정확성 및 안전성 검증

목표: CLASS_0 / CLASS_1 / CLASS_2 분기가 canonical policy에 따라 정확히 동작하는지 검증

- [ ] CLASS_1 정상 경로 시나리오 (N ≥ 30회) 실행 및 결과 기록
  - 검증 지표: CLASS_1 routing accuracy, false safe_deferral rate
- [ ] CLASS_0 긴급 경로 시나리오 (E001~E005 각각) 실행 및 결과 기록
  - 검증 지표: 0-miss emergency detection, 긴급 알림 전달 여부
- [ ] CLASS_2 진입 경로 시나리오 (C204 staleness, C206 insufficient_context 등) 실행
  - 검증 지표: Class 2 escalation 정확도
- [ ] Intent recovery 비교 (LLM-assisted vs. rule-only baseline) 결과 기록
  - `5.7 Contribution 1 보강용` 시나리오
- [ ] Doorlock sensitive-actuation 차단 검증 (CLASS_1 autonomous path에서 차단 확인)

### 3-2. 패키지 B — 클래스별 지연 시간 측정

목표: CLASS_0 / CLASS_1 / CLASS_2 각 경로의 end-to-end latency 측정

- [ ] STM32 또는 타임스탬프 기반 측정 설정
- [ ] 각 클래스별 N ≥ 30회 왕복 측정
  - CLASS_0: 컨텍스트 수신 → Telegram 알림 발송
  - CLASS_1: 컨텍스트 수신 → actuation command publish
  - CLASS_2: 컨텍스트 수신 → escalation publish
- [ ] 측정값 기록: median, 95th percentile, max
- [ ] 논문 Figure용 bar chart / CDF 데이터 저장

### 3-3. 패키지 C — Fault Injection 기반 강건성 검증

목표: canonical fault profile에 따른 시스템 반응이 예상과 일치하는지 검증

- [ ] `common/policies/fault_injection_rules.json` 기준 fault profile 확인
- [ ] Staleness fault (FAULT_STALENESS_01) 주입 후 C204 분기 확인
- [ ] Missing state fault 주입 후 C206 분기 확인
- [ ] Conflict fault 주입 후 처리 경로 확인
- [ ] Emergency pass-through 확인: fault 상황에서도 CLASS_0 차단 없음

### 3-4. (선택) 패키지 G — MQTT/Payload Contract 검증

- [ ] RPi `75_verify_rpi_mqtt_payload_alignment.sh` 실행 후 결과 기록
- [ ] Topic registry alignment report 생성
- [ ] Governance UI에서 payload 검증 결과 확인

### 3-5. 실험 결과 정리

- [ ] `integration/results/` 디렉터리에 결과 JSON / CSV 저장
- [ ] RPi 대시보드에서 Markdown 리포트 export
- [ ] 논문 표/그림 데이터 추출

---

## Phase 4 — 논문 작성

> 실험 결과 확보 후 진행. `common/docs/paper/` 참조.

**목표 저널**: ICT Express  
**논문 제목**: *Local LLM-Assisted Intent Recovery With Policy-Constrained Sensitive-Actuation Control for Assistive Smart Homes*

### 4-1. 섹션별 작성

| 섹션 | 참조 문서 | 상태 |
|------|-----------|------|
| Abstract | `01_paper_contributions.md` | ⬜ |
| 1. Introduction | `03_title_keywords_and_introduction_outline.md` | ⬜ |
| 2. System Design | `04_section2_system_design_outline.md` | ⬜ |
| 3. Implementation | 아키텍처 문서 전반 | ⬜ |
| 4. Experiments | Phase 3 결과 | ⬜ |
| 5. Discussion | `01_paper_contributions.md` §Limitations | ⬜ |
| 6. Conclusion | — | ⬜ |

### 4-2. 필수 표/그림

`required_experiments.md §12~13` 기준:

- [ ] Table 1: 실험 노드 구성 (물리 + 가상)
- [ ] Table 2: 정책 분기 정확성 결과 (CLASS_0/1/2 routing accuracy)
- [ ] Table 3: Fault injection 강건성 결과
- [ ] Table 4: Intent recovery 비교 (LLM-assisted vs. baseline)
- [ ] Figure 1: 시스템 구조 다이어그램 (Phase 1-3에서 완성)
- [ ] Figure 2: 클래스별 지연 시간 bar chart / CDF

### 4-3. 제출 전 체크리스트

- [ ] 페이지 수 확인 (ICT Express 단문 4페이지 기준)
- [ ] canonical asset 인용 일관성 검토
- [ ] Safety boundary 서술 검토 (`02_safety_and_authority_boundaries.md` 기준)
- [ ] 그림/표 해상도 및 포맷 확인

---

## 작업 의존성 요약

```
1-1 (의존성) ──→ 2-1 (Mac mini 기동)
1-2 (픽스처) ──→ 2-3 (파이프라인 확인) ──→ 3-1~3-3 (실험)
1-3 (다이어그램) ─────────────────────────→ 4-2 Figure 1

2-1 + 2-2 + 2-4 ──→ 3-1~3-4 (실험 실행)
3-1~3-4 ────────────────────────────────→ 4-1~4-3 (논문)
```

---

## 진행 상태 요약 (2026-04-28 기준)

| 항목 | 상태 |
|------|------|
| Mac mini 라이브러리 코드 (MM-01~10) | ✅ 완료 |
| Mac mini 진입점 (`main.py`) | ✅ 완료 |
| RPi 라이브러리 코드 (RPI-01~10) | ✅ 완료 |
| RPi 진입점 (`main.py`) | ✅ 완료 |
| ESP32 노드 펌웨어 (PN-01~08) | ✅ 완료 (하드웨어 검증 대기) |
| STM32 타이밍 펌웨어 | ✅ 스켈레톤 완료 (하드웨어 검증 대기) |
| 설치 문서 (01~04) | ✅ 완료 |
| 통합 실행 문서 (05) | ✅ 완료 |
| requirements 의존성 보완 (1-1) | ✅ 완료 |
| 시나리오 픽스처 파일 (1-2) | ✅ 완료 |
| 시스템 구조 다이어그램 (1-3) | ✅ 완료 |
| 하드웨어 기동 확인 (Phase 2) | ⬜ 미시작 |
| 실험 실행 A/B/C (Phase 3) | ⬜ 미시작 |
| 논문 작성 (Phase 4) | ⬜ 미시작 |
