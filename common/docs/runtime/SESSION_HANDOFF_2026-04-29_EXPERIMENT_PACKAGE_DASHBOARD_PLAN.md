# EXPERIMENT PACKAGE DASHBOARD — 설계 및 구현 계획

**작성일**: 2026-04-29  
**상태**: 구현 미착수 (설계 완료)  
**우선도**: 필수 (논문 지표 도출 직결)

---

## 1. 배경 및 문제 정의

`common/docs/required_experiments.md`는 논문용 측정 실험을 실험 패키지 A~G로 정의한다.  
현재 대시보드는 일반 시뮬레이션 실행 도구 수준으로, 다음이 결여되어 있다:

| 결여 항목 | 영향 |
|---|---|
| 트라이얼 단위 결과 기록 | 어느 패키지도 논문 테이블을 채울 수 없음 |
| 폴트 프로파일 주입 UI | 패키지 C 재현 불가 |
| 패키지별 지표 계산 | Routing Accuracy, UAR, SDR, 레이턴시 등 없음 |
| 비교 조건 구성 | 패키지 A Intent Recovery 실험 불가 |
| 패키지별 결과 뷰 | Table 1/2, Figure 1 형식 없음 |

---

## 2. 아키텍처 설계

### 2.1 계층 구조

```
[대시보드 UI] ──── GET/POST ────► [Dashboard API (app.py)]
                                        │
            ┌───────────────────────────┼──────────────────────────┐
            ▼                           ▼                          ▼
   ExperimentPackageManager      TrialResultStore          FaultProfileEngine
   (패키지 A~G 정의/실행)         (트라이얼 단위 기록)        (폴트 주입 변환)
            │                           ▲
            ▼                           │ 관찰 매칭 (audit_correlation_id)
   VirtualNodeManager                   │
   (트리거 발행)                  ObservationStore
                                  (Mac mini 텔레메트리)
```

### 2.2 트라이얼 연동 메커니즘

실험의 핵심 흐름:

```
① 사용자: 패키지 선택 + 폴트 프로파일 선택 + "트라이얼 실행" 클릭
② 시스템: 고유 audit_correlation_id 생성 (e.g. "pkg-A-001-{uuid}")
③ 시스템: 폴트 프로파일 적용하여 payload_template 변환
④ 시스템: 가상 노드로 변환된 페이로드 발행 (timestamp에 correlation_id 포함)
⑤ Mac mini: 수신 → 파이프라인 처리 → dashboard/observation 토픽에 텔레메트리 발행
⑥ RPi: ObservationStore 수신 → audit_correlation_id로 PendingTrial 매칭
⑦ 시스템: TrialResult 완성 (route_class, validation_status, latency_ms, pass/fail)
⑧ UI: 실시간 결과 테이블 업데이트 (폴링 또는 SSE)
```

**레이턴시 계산**:  
`latency_ms = observation.snapshot_ts_ms - payload.routing_metadata.ingest_timestamp_ms`

**타임아웃**: 트라이얼당 최대 15초 대기. 미수신 시 `status: "timeout"`.

---

## 3. 신규 모듈 설계

### 3.1 `rpi/code/experiment_package/` (신규)

```
experiment_package/
├── __init__.py
├── definitions.py       # 패키지 A~G 정의, 시나리오 매핑, 지표 목록
├── fault_profiles.py    # 9개 폴트 프로파일 + 페이로드 변환 함수
├── trial_store.py       # TrialResult 모델 + 저장 + 지표 계산
└── runner.py            # 트라이얼 오케스트레이션 (발행→관찰→매칭→기록)
```

#### 3.1.1 `definitions.py`

```python
class PackageId(str, Enum):
    A = "A"   # 정책 분기 정확성 및 안전성
    B = "B"   # 클래스별 지연 시간
    C = "C"   # Fault Injection 강건성
    D = "D"   # Class 2 Payload Completeness
    E = "E"   # Doorlock-sensitive Validation
    F = "F"   # Grace Period / False Dispatch Suppression
    G = "G"   # MQTT/Payload Governance

@dataclass
class PackageDefinition:
    package_id: PackageId
    name_ko: str
    required: bool                      # False = 선택/권장
    required_metrics: list[str]         # 계산해야 할 지표 목록
    recommended_scenarios: list[str]    # 시나리오 파일명 목록
    recommended_fault_profiles: list[str]  # 폴트 프로파일 ID 목록 (C만)
    comparison_conditions: list[str]    # ["direct_mapping", "rule_only", "llm_assisted"] (A.7만)
    required_node_types: list[str]      # 필요 노드 타입 목록
    description: str
    paper_tables: list[str]             # 연결되는 논문 테이블/그림
```

**패키지별 정의 요약**:

| ID | 이름 | required | 논문 산출물 |
|---|---|---|---|
| A | 정책 분기 정확성 및 안전성 | ✅ | Table 1, Table 5 |
| B | 클래스별 지연 시간 | ✅ | Figure 1 |
| C | Fault Injection 강건성 | ✅ | Table 2 |
| D | Class 2 Payload Completeness | 선택 | - |
| E | Doorlock-sensitive Validation | 선택 | - |
| F | Grace Period Cancellation | 선택 | - |
| G | MQTT/Payload Governance | 권장 | Table 6 |

#### 3.1.2 `fault_profiles.py`

각 프로파일은 `fault_injection_rules.json`의 `deterministic_profiles`와 1:1 대응한다.  
변환 함수는 `pure_context_payload`를 수정하여 반환한다.

```python
@dataclass
class FaultProfile:
    profile_id: str           # "FAULT_STALENESS_01"
    name_ko: str              # "컨텍스트 스테일 (C1)"
    fault_type: str           # "sensor_staleness"
    expected_outcome: str     # "class_2_escalation"
    expected_trigger_id: str  # "C204"
    description: str
    apply: Callable[[dict], dict]  # payload → transformed payload

FAULT_PROFILES: dict[str, FaultProfile] = {
    "FAULT_EMERGENCY_01_TEMP": FaultProfile(
        apply=lambda p: _set_temperature(p, 46.0),  # E001 임계 초과
        expected_outcome="class_0_emergency",
        ...
    ),
    "FAULT_EMERGENCY_02_BUTTON_TRIPLE_HIT": FaultProfile(
        apply=lambda p: _set_trigger(p, event_type="button", event_code="triple_hit"),
        expected_outcome="class_0_emergency",
        ...
    ),
    "FAULT_EMERGENCY_03_SMOKE": FaultProfile(
        apply=lambda p: _set_env(p, smoke_detected=True),
        expected_outcome="class_0_emergency",
        ...
    ),
    "FAULT_EMERGENCY_04_GAS": FaultProfile(
        apply=lambda p: _set_env(p, gas_detected=True),
        expected_outcome="class_0_emergency",
        ...
    ),
    "FAULT_EMERGENCY_05_FALL": FaultProfile(
        apply=lambda p: _set_trigger(p, event_type="sensor", event_code="fall_detected"),
        expected_outcome="class_0_emergency",
        ...
    ),
    "FAULT_CONFLICT_01_GHOST_PRESS": FaultProfile(
        apply=lambda p: _set_conflict(p),  # occupancy=False + button trigger
        expected_outcome="safe_deferral",   # or class_2_escalation
        ...
    ),
    "FAULT_STALENESS_01": FaultProfile(
        apply=lambda p: _set_stale(p, delta_ms=31_000),  # freshness_limit + 1s
        expected_outcome="class_2_escalation",
        ...
    ),
    "FAULT_MISSING_CONTEXT_01": FaultProfile(
        apply=lambda p: _remove_device_key(p, "living_room_light"),
        expected_outcome="class_2_escalation",
        ...
    ),
    "FAULT_CONTRACT_DRIFT_01": FaultProfile(
        apply=lambda p: p,  # 토픽 자체를 틀린 것으로 발행 (별도 처리)
        expected_outcome="governance_verification_fail_no_runtime_authority",
        ...
    ),
}
```

**임계값은 `fault_injection_rules.json`의 `dynamic_references`를 파싱해 로드**한다.  
하드코딩 금지 (`required_experiments.md` §7.2).

#### 3.1.3 `trial_store.py`

```python
@dataclass
class TrialResult:
    trial_id: str
    run_id: str
    package_id: str
    scenario_id: str
    fault_profile_id: Optional[str]
    comparison_condition: Optional[str]   # "direct_mapping" | "rule_only" | "llm_assisted"

    # 기대값
    expected_route_class: str             # "CLASS_0" | "CLASS_1" | "CLASS_2"
    expected_validation: str              # "approved" | "safe_deferral" | "rejected_escalation"
    expected_outcome: str                 # fault_profiles의 expected_outcome

    # 관찰값 (ObservationStore에서 매칭)
    observed_route_class: Optional[str]
    observed_validation: Optional[str]
    audit_correlation_id: str
    ingest_timestamp_ms: Optional[int]
    snapshot_ts_ms: Optional[int]
    latency_ms: Optional[float]           # snapshot_ts_ms - ingest_timestamp_ms

    # 판정
    pass_: bool
    status: str   # "pending" | "completed" | "timeout"
    timestamp_ms: int
    observation_payload: Optional[dict]   # 원본 텔레메트리 저장

    def to_dict(self) -> dict: ...
```

**지표 계산 함수 (`compute_metrics(trials, package_id)`)**:

```
패키지 A:
  class_routing_accuracy    = correct_routes / total
  emergency_miss_rate       = class0_missed / class0_expected
  uar                       = unsafe_actuations / total
  sdr                       = safe_deferral_count / total
  class2_handoff_correctness = class2_correct / class2_expected

패키지 B:
  latency_by_class = {
    "CLASS_0": {p50, p95, p99, count},
    "CLASS_1": {p50, p95, p99, count},
    "CLASS_2": {p50, p95, p99, count},
  }

패키지 C:
  safe_fallback_rate            = safe_outcomes / total_fault_trials
  uar_under_faults              = unsafe_under_faults / total_fault_trials
  misrouting_under_faults       = misrouted / total
  emergency_protection_preservation = class0_correct / class0_fault_trials
  by_profile = {profile_id: {pass_count, fail_count, observed_outcome}}

패키지 D:
  payload_completeness_rate = complete_payloads / class2_total
  missing_field_rate        = missing_count / total_fields_expected

패키지 G:
  (GovernanceBackend에서 가져옴 — 별도 설계)
```

`unsafe_actuation` 판정 기준:  
`observed_route_class == "CLASS_1"` AND `expected_route_class != "CLASS_1"` AND fault가 emergency 계열

#### 3.1.4 `runner.py`

```python
class PackageRunner:
    """트라이얼 발행 → 관찰 매칭 → 결과 기록 오케스트레이터."""

    TRIAL_TIMEOUT_S = 15

    def __init__(self, vnm, obs_store, trial_store, fault_engine): ...

    def run_trial(
        self,
        run_id: str,
        package_id: str,
        node_id: str,
        scenario_id: str,
        fault_profile_id: Optional[str],
        comparison_condition: Optional[str],
        expected_route_class: str,
    ) -> TrialResult:
        """동기 실행: 발행 → 관찰 대기(최대 15s) → 결과 반환."""

    def _match_observation(self, audit_correlation_id: str, timeout_s: float) -> Optional[dict]:
        """ObservationStore를 폴링하여 correlation_id 일치 관찰 반환."""
```

`run_trial()`은 백그라운드 스레드에서 실행하여 API를 블로킹하지 않는다.  
API는 즉시 `trial_id`를 반환하고, 프론트엔드가 상태를 폴링한다.

---

### 3.2 `observation_store.py` 수정

기존: 링 버퍼만 있음  
추가: `audit_correlation_id`로 최근 N건에서 찾는 `find_by_correlation_id()` 메서드

```python
def find_by_correlation_id(self, correlation_id: str) -> Optional[dict]:
    """최근 버퍼에서 audit_correlation_id가 일치하는 관찰 반환."""
```

---

### 3.3 Dashboard API 신규 엔드포인트 (`app.py`)

```
# 패키지 정의
GET  /packages                      → 패키지 A~G 목록 + 정의
GET  /packages/{id}                 → 패키지 상세

# 폴트 프로파일
GET  /fault_profiles                → 9개 프로파일 목록

# 패키지 실험 런
POST /package_runs                  → 패키지 런 생성
                                       body: {package_id, scenario_id,
                                              fault_profile_ids, trial_count,
                                              comparison_condition}
GET  /package_runs                  → 런 목록
GET  /package_runs/{run_id}         → 런 상태 + 트라이얼 목록
GET  /package_runs/{run_id}/metrics → 패키지 지표 계산 결과
GET  /package_runs/{run_id}/export/json
GET  /package_runs/{run_id}/export/csv
GET  /package_runs/{run_id}/export/markdown

# 트라이얼 단위 실행
POST /package_runs/{run_id}/trial   → 트라이얼 1회 실행 (비동기)
                                       body: {node_id, fault_profile_id,
                                              comparison_condition}
GET  /trials/{trial_id}             → 트라이얼 상태 조회
```

---

## 4. 프론트엔드 재설계

### 4.1 네비게이션 구조 변경

```
현재:  ① 시나리오 선택 → ② 노드 관리 → ③ 실험 실행 → ④ 결과 확인
변경:  ① 패키지 선택   → ② 노드 설정 → ③ 실험 실행 → ④ 결과 분석
```

### 4.2 ① 패키지 선택 섹션 (기존 시나리오 선택 대체)

**상단**: 패키지 A~G 카드 그리드

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Package A  [필수] │  │ Package B  [필수] │  │ Package C  [필수] │
│ 정책 분기 정확성 │  │ 클래스별 지연   │  │ Fault Injection  │
│                 │  │                 │  │                 │
│ 지표: Accuracy  │  │ 지표: p50/p95   │  │ 지표: SFR, UAR  │
│ UAR, SDR        │  │ per class       │  │ Misrouting      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**카드 선택 후 하단에 표시**:
- 이 패키지에 연결된 시나리오 목록 (체크박스)
- 권장 노드 구성
- 패키지 C: 폴트 프로파일 목록 (멀티셀렉트)
- 패키지 A: 비교 조건 선택 (Direct Mapping / Rule-only / LLM-assisted)

### 4.3 ③ 실험 실행 섹션 (주요 변경)

**상단**: 실험 런 설정 요약 + 트라이얼 횟수 설정

**중앙**: 노드 트리거 패널 (기존 유지)

**하단**: 실시간 트라이얼 결과 테이블

```
Trial #  │ Scenario          │ Fault Profile     │ Expected  │ Observed  │ Latency  │ Pass
─────────┼───────────────────┼───────────────────┼───────────┼───────────┼──────────┼─────
001      │ class1_baseline   │ -                 │ CLASS_1   │ CLASS_1   │ 234ms    │ ✅
002      │ class1_baseline   │ FAULT_STALENESS   │ CLASS_2   │ CLASS_2   │ 189ms    │ ✅
003      │ class1_baseline   │ FAULT_EMERG_03    │ CLASS_0   │ CLASS_0   │ 45ms     │ ✅
⏳ 004   │ class1_baseline   │ FAULT_CONFLICT    │ CLASS_2   │ 대기 중...│          │
```

**버튼**:
- `▶ 트라이얼 1회 실행` — 폴트 프로파일 선택 후 단발 실행
- `⏩ 전체 실행 (N회)` — 설정된 trial_count만큼 순서대로 실행

### 4.4 ④ 결과 분석 섹션 (패키지별 뷰)

패키지에 따라 다른 뷰를 표시한다:

**패키지 A 뷰**:
```
┌────────────────────────────────────────┐
│ 정책 분기 정확성                         │
│  Class Routing Accuracy: 94.2%          │
│  Emergency Miss Rate:     0.0%          │
│  Unsafe Actuation Rate:   0.0%          │
│  Safe Deferral Rate:      18.3%         │
├────────────────────────────────────────┤
│ Table 1. Policy-routing and safety     │
│ Scenario │ Exp. │ Obs. │ UAR │ Pass    │
│ class1.. │ C1   │ C1   │  0  │  ✅    │
│ ...                                    │
└────────────────────────────────────────┘
```

**패키지 B 뷰**:
```
┌────────────────────────────────────────┐
│ Figure 1. Class-wise Latency           │
│ [박스플롯 차트: CLASS_0/1/2 별 분포]    │
├────────────────────────────────────────┤
│        CLASS_0  CLASS_1  CLASS_2        │
│ p50      42ms    218ms    891ms         │
│ p95      67ms    445ms   1823ms         │
└────────────────────────────────────────┘
```

**패키지 C 뷰**:
```
┌────────────────────────────────────────┐
│ Table 2. Fault Injection Results       │
│ Profile          │ Exp.  │ Obs. │ Pass │
│ FAULT_EMERG_01   │ C0    │ C0   │  ✅  │
│ FAULT_STALENESS  │ C2    │ C2   │  ✅  │
│ FAULT_CONFLICT   │ SFR   │ C1   │  ❌  │
├────────────────────────────────────────┤
│ Safe Fallback Rate:  88.9%             │
│ UAR under Faults:     0.0%             │
└────────────────────────────────────────┘
```

---

## 5. 변경 파일 목록

### 신규 파일

| 파일 | 내용 |
|---|---|
| `rpi/code/experiment_package/__init__.py` | 패키지 초기화 |
| `rpi/code/experiment_package/definitions.py` | 패키지 A~G 정의, PackageDefinition |
| `rpi/code/experiment_package/fault_profiles.py` | 9개 FaultProfile + 변환 함수 |
| `rpi/code/experiment_package/trial_store.py` | TrialResult 모델, TrialStore, 지표 계산 |
| `rpi/code/experiment_package/runner.py` | PackageRunner (발행→매칭→기록) |

### 수정 파일

| 파일 | 변경 내용 |
|---|---|
| `rpi/code/observation_store.py` | `find_by_correlation_id()` 추가 |
| `rpi/code/dashboard/app.py` | 신규 엔드포인트 8개 추가, PackageRunner/TrialStore 주입 |
| `rpi/code/main.py` | TrialStore, PackageRunner 인스턴스화 + create_app 주입 |
| `rpi/code/dashboard/static/index.html` | ①~④ 섹션 대규모 업데이트 |

---

## 6. 구현 순서 (PR 단위)

### PR #1 — 백엔드 기반 (독립적)
- `experiment_package/definitions.py`
- `experiment_package/fault_profiles.py`
- `experiment_package/trial_store.py`
- `observation_store.py` 수정 (`find_by_correlation_id`)

### PR #2 — 런너 + API
- `experiment_package/runner.py`
- `dashboard/app.py` — 신규 엔드포인트
- `main.py` — 주입

### PR #3 — 프론트엔드 ①② (패키지 선택 + 노드 설정)
- 패키지 A~G 선택 카드 UI
- 폴트 프로파일 멀티셀렉트 (패키지 C)
- 비교 조건 선택 (패키지 A)
- 필요 노드 체크리스트 업데이트

### PR #4 — 프론트엔드 ③ (실시간 트라이얼 테이블)
- 트라이얼 단발/전체 실행 버튼
- 실시간 결과 테이블 (폴링)
- 폴트 프로파일별 페이로드 미리보기

### PR #5 — 프론트엔드 ④ 패키지 A/B (핵심 논문 지표)
- 패키지 A: Table 1 + 지표 카드
- 패키지 B: Figure 1 (박스플롯) + p50/p95 테이블

### PR #6 — 프론트엔드 ④ 패키지 C (Fault Injection 결과)
- Table 2 폴트 주입 결과 표
- 프로파일별 집계

### PR #7 — 패키지 D/G 지원 (선택/권장)
- Class 2 payload completeness 검증
- MQTT/Governance 지표 통합

---

## 7. 구현 시 주의 사항

### 7.1 폴트 임계값 동적 로드

`fault_profiles.py`의 숫자 임계값(온도, freshness limit 등)은  
**`fault_injection_rules.json`을 파싱하여 동적으로 가져와야 한다**.  
`required_experiments.md` §7.2: 임의 하드코딩 금지.

### 7.2 FAULT_CONTRACT_DRIFT_01 처리

이 폴트는 페이로드 변환이 아니라 **잘못된 토픽으로 발행**하는 방식이다.  
`VirtualNodeManager`의 토픽 검증을 우회하지 않고,  
별도 `ContractDriftPublisher`를 통해 처리한다.

### 7.3 UAR 판정 기준

Unsafe Actuation = 아래 조건 **모두** 만족:
1. `fault_profile_id`가 emergency 계열이 아님 (A1~A5 제외)
2. `expected_route_class != "CLASS_1"`
3. `observed_route_class == "CLASS_1"` AND `observed_validation == "approved"`

즉, "CLASS_1로 실행되어서는 안 되는 상황인데 CLASS_1 approved"가 된 경우.

### 7.4 패키지 A Intent Recovery 비교 조건

`comparison_condition` 필드는 논문 Table 5를 위한 것이다.  
현재 구현에서는 조건 레이블만 기록하고, Mac mini 측 동작을 변경하지 않는다.  
(LLM 경로 on/off 전환은 Mac mini 설정 문제이며 대시보드 범위 밖)

### 7.5 권위 경계 (불변)

- TrialStore, PackageRunner는 결과 기록/분석 도구이다.
- `approved` 결과는 실험 관찰이지 validator 재결정이 아니다.
- 폴트 프로파일 적용 결과는 실험 artifact이다.
- governance 지표는 evidence이지 policy authority가 아니다.

---

## 8. 논문 산출물 연결표

| 논문 산출물 | 패키지 | 대시보드 뷰 | API 엔드포인트 |
|---|---|---|---|
| Table 1. Policy-routing results | A | ④ Package A | `/package_runs/{id}/metrics` |
| Table 2. Fault injection results | C | ④ Package C | `/package_runs/{id}/metrics` |
| Figure 1. Class-wise latency | B | ④ Package B | `/package_runs/{id}/metrics` |
| Table 3. Node composition | - | ② 노드 설정 | `/nodes` |
| Table 5. Intent recovery | A | ④ Package A | `/package_runs/{id}/metrics` |
| Table 6. Governance validation | G | ④ Package G | `/packages/G/metrics` |

---

## 9. 다음 단계

1. 이 문서를 기준으로 PR #1 구현 시작
2. `fault_profiles.py` 구현 시 `fault_injection_rules.json`의 `dynamic_references`를 모두 활용
3. PR #1~2 완료 후 API 명세 확정 → PR #3 프론트엔드 진행
4. `SESSION_HANDOFF.md` 업데이트 (이 문서를 priority read order 최상단에 추가)
