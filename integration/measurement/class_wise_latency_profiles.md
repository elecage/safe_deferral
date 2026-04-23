# class_wise_latency_profiles.md

이 문서는 `integration/measurement/`에서 사용할 **class-wise latency evaluation profile**의 목적, 범위, 구성 원칙을 정리한다.

이 문서는 latency threshold 자체를 canonical truth로 정의하지 않는다.  
정책/스키마/trigger semantics의 authoritative baseline은 `common/`의 frozen assets에 남는다.

---

## 1. 목적

class-wise latency profile은 다음을 지원하기 위해 사용한다.

- Class 0 / Class 1 / Class 2 경로별 측정 목적 구분
- out-of-band timing capture workflow 문서화
- repeatable latency evaluation setup 정의
- paper-ready result 정리의 기반 마련

즉, 이 문서는 **어떤 경로를 어떤 방식으로 측정할지**를 구조화하는 문서다.

---

## 2. 기본 원칙

- measurement layer는 operational control path가 아니다.
- timing infrastructure는 evaluation-only support path로 유지한다.
- class-wise latency measurement는 hub-side decision logic을 우회하는 제어 경로를 만들면 안 된다.
- 가능한 한 동일 input plane을 통과하는 경로를 관찰해야 한다.
- measurement 결과는 reproducibility-oriented summary로 정리 가능해야 한다.

---

## 3. 측정 대상 클래스

### 3.1 Class 0
대표 목적:
- emergency override path의 end-to-end latency 측정
- emergency trigger ingestion 이후 emergency routing / notification / warning path의 지연 특성 파악

대표 예시:
- `E001` high-temperature emergency
- `E002` bounded emergency triple-hit input
- `E003` smoke-detected trigger
- `E004` gas-detected trigger
- `E005` fall-detected trigger

### 3.2 Class 1
대표 목적:
- bounded low-risk assistance path의 latency 측정
- policy router → LLM-allowed path → deterministic validator → dispatcher/ACK path의 지연 특성 파악

주의:
- LLM 경로가 포함될 수 있으므로 variation 기록이 중요하다.
- 평균뿐 아니라 repeated-run summary가 필요하다.

### 3.3 Class 2
대표 목적:
- caregiver escalation / safe fallback path의 latency 측정
- context insufficiency 또는 high-safety escalation path의 end-to-end 지연 특성 파악

주의:
- notification channel variation과 mock fallback variation을 분리 기록하는 것이 바람직하다.

---

## 4. 권장 profile 구성 항목

각 latency profile은 최소한 다음 항목을 포함하는 것이 좋다.

- `profile_id`
- `class_label`
- `scenario_id`
- `trigger_family` 또는 `path_type`
- `measurement_goal`
- `capture_points`
- `input_origin`
- `expected_safe_outcome`
- `repeat_count`
- `notes`

---

## 5. 권장 capture point 개념

정확한 capture point 명칭은 실제 측정 인프라에 따라 달라질 수 있지만, 다음 구분을 권장한다.

### 5.1 ingress point
- MQTT ingress
- physical bounded input ingress
- scenario publish ingress

### 5.2 routing point
- Policy Router decision point
- class assignment completion point

### 5.3 validation / dispatch point
- Deterministic Validator completion point
- dispatcher issue point
- ACK observation point

### 5.4 escalation / notification point
- Class 2 notification issue point
- external notification confirmation point

### 5.5 audit observation point
- verification-safe audit stream observation point
- closed-loop evaluation observation point

---

## 6. profile 예시 구조

아래는 실제 측정 파일이 아니라, profile 문서화 예시다.

```text
profile_id: LAT_CLASS0_E001_BASELINE
class_label: CLASS_0
scenario_id: SCN_CLASS0_E001_BASELINE
measurement_goal: Measure end-to-end latency for policy-aligned emergency override handling.
input_origin: Raspberry Pi evaluation publish or bounded physical node event ingress
capture_points:
  - ingress_point
  - routing_point
  - notification_or_warning_point
  - audit_observation_point
expected_safe_outcome: Immediate emergency override path
repeat_count: 30
notes: Keep timing path out-of-band and separate from operational control.
```

---

## 7. 결과 정리 원칙

latency 결과는 다음 방식으로 정리하는 것을 권장한다.

- class-wise summary
- repeated-run summary
- average / median / max / min
- run count
- capture path description
- measurement limitations

중요한 점은, 결과가 단일 수치보다 **재현 가능한 evaluation package**로 남아야 한다는 것이다.

---

## 8. 권장 후속 파일

이 문서 다음 단계로는 다음 자산을 추가하는 것이 좋다.

- `integration/measurement/result_template.md`
- `integration/measurement/timing_capture_points.md`
- `integration/measurement/wiring_notes.md` (hardware timing support 사용 시)
- class-specific profile example files

---

## 9. 한계

이 문서는 측정 구조를 정의하는 문서이지, 실제 latency result나 threshold truth를 제공하지 않는다.

- canonical emergency semantics는 `common/policies/`에 남는다.
- 실제 timing instrumentation은 measurement support implementation에 달려 있다.
- 이 문서만으로 실측이 수행되지는 않는다.

즉, 이 문서는 **measurement-ready documentation layer**다.
