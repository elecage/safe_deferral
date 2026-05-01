# SESSION_HANDOFF — LLM Class 2 Integration P2.2 Trial Timeout Decomposition (PR E)

**Date:** 2026-05-01
**Tests:** 440/440 mac_mini fast suite (unchanged), 137 → 142 rpi (+5 new)
**Schema validation:** 15/15 scenario skeletons; expected fixtures unchanged

**Plan baseline:** `common/docs/architecture/10_llm_class2_integration_alignment_plan.md` P2.2 (PR #90)
**Builds on:** PR #87/#88/#89/#91 (Phases 1+2+3+5+P0), PR #92 (P1), PR #93 (P2.1)

---

## 이번 세션의 범위

doc 10의 **P2.2 (trial timeout decomposition)** 처리. `_TRIAL_TIMEOUT_CLASS2_S = 360s`라는 불투명한 단일 상수를 정책 기반 phase별 합산으로 변환. 정책에서 LLM budget이나 Class 2 user phase가 조정되면 trial 타임아웃이 자동 추적.

### `rpi/code/experiment_package/runner.py` 변경

**모듈-레벨 phase-decomposed 상수 신설 (fallback 기본값):**

| 상수 | 의미 | 기본값 |
|---|---|---|
| `_LLM_BUDGET_DEFAULT_S` | LLM candidate generation 최대 시간 | 8.0 (정책의 `llm_request_timeout_ms` ÷ 1000과 동일) |
| `_USER_PHASE_TIMEOUT_DEFAULT_S` | 사용자 응답 창 | 30.0 (정책의 `class2_clarification_timeout_ms` ÷ 1000) |
| `_CAREGIVER_PHASE_TIMEOUT_S` | 보호자 Telegram 응답 창 | 300.0 (Mac mini env `CAREGIVER_RESPONSE_TIMEOUT_S` 기본값과 동일) |
| `_TRIAL_TIMEOUT_CLASS2_SLACK_S` | telemetry publish 여유 | 30.0 |
| `_TRIAL_TIMEOUT_CLASS2_S` (계산값) | 위 4개 합 | 368.0 (이전 360에서 +8) |

**`PackageRunner.__init__`이 정책 기반으로 인스턴스 속성 계산:**

```python
self._class2_llm_budget_s          = policy.llm_request_timeout_ms / 1000  (or default)
self._class2_user_phase_timeout_s  = policy.class2_clarification_timeout_ms / 1000  (or default)
self._class2_caregiver_phase_timeout_s = _CAREGIVER_PHASE_TIMEOUT_S  (constant)
self._class2_trial_timeout_slack_s = _TRIAL_TIMEOUT_CLASS2_SLACK_S
self._class2_trial_timeout_s = sum(four)
```

`_run_trial`이 `_TRIAL_TIMEOUT_CLASS2_S` 모듈 상수 대신 `self._class2_trial_timeout_s`를 사용. 모듈 상수는 backward-compat 용으로 유지(이전 import한 외부 코드 보호).

### 정책 변경 자동 추적 동작

- 정책에서 `llm_request_timeout_ms`를 8000 → 3000으로 줄이면 trial timeout이 368 → 363으로 자동 감소
- `class2_clarification_timeout_ms`를 30000 → 15000으로 줄이면 368 → 353으로 감소
- 정책 로드 실패 또는 필드 누락 시 모듈 default fallback (각 phase 독립적으로)

### Phase 별 속성 노출

각 phase budget이 별도 인스턴스 속성으로 노출됨 → 미래 dashboard / audit trace가 breakdown을 렌더할 수 있음:
- `runner._class2_llm_budget_s`
- `runner._class2_user_phase_timeout_s`
- `runner._class2_caregiver_phase_timeout_s`
- `runner._class2_trial_timeout_slack_s`
- `runner._class2_trial_timeout_s` (sum)

이번 PR은 속성만 노출. dashboard 연결은 별도 PR.

---

## 새 테스트 (+5)

`rpi/code/tests/test_rpi_components.py::TestClass2TrialTimeoutDecomposition`:

1. `test_default_policy_yields_known_total` — shipped 정책 기준 8+30+300+30=368 검증.
2. `test_tighter_policy_tightens_trial_timeout` — stub loader로 더 좁은 정책 주입 (3+15+300+30=348).
3. `test_missing_policy_fields_use_module_defaults` — `global_constraints` 비어 있어도 module default fallback.
4. `test_phase_breakdown_attributes_exposed` — 4개 phase 속성 합 = trial timeout 검증.
5. `test_loader_failure_falls_back_to_defaults` — `load_policy_table()` 예외 발생 시도 안전 fallback.

mac_mini fast suite 440/440 (코드 미변경). rpi 137→142 (+5). scenario 15/15.

---

## 안전 invariant 변동

없음. 본 PR은 trial timeout 계산 방식 변경뿐. 운영 정책이 변하면 timeout이 따라 변하는 것이 의도된 동작 (정책이 단일 source of truth).

기본값 합산 결과(368s)가 이전 하드코딩(360s)보다 8초 길어짐 → 기존 trial들이 "더 오래 기다리는" 방향으로만 변할 수 있음 (절대 더 일찍 fail되지 않음). 안전 측면 회귀 없음.

---

## 주의사항

- **canonical asset 변경 없음.** 정책 필드는 PR #91 P0.2에서 이미 추가된 `llm_request_timeout_ms`와 PR 이전부터 있던 `class2_clarification_timeout_ms`를 재사용. 새 정책 필드 안 추가.
- **`_CAREGIVER_PHASE_TIMEOUT_S = 300.0`은 모듈 상수.** Mac mini의 `CAREGIVER_RESPONSE_TIMEOUT_S` env 기본값과 일치. 두 값을 분리해 운영하면 drift 가능 — 향후 정책에 `caregiver_response_timeout_ms` 추가하여 single source of truth로 통합하는 것이 권장됨 (별도 PR로 분리, 본 PR 범위 외).
- **`_TRIAL_TIMEOUT_CLASS2_S` 모듈 상수 유지:** 외부 코드가 import 중일 수 있으므로 backward-compat. 새 코드는 `runner._class2_trial_timeout_s` 인스턴스 속성 사용 권장.
- **TestClass2SelectionAutoDrive 등 기존 CLASS_2 trial 테스트가 불안정해질 수 있는가?** 검토 결과 영향 없음 — 그 테스트들은 mock observation_store가 즉시 결과를 반환하므로 timeout과 무관.

---

## 다음 세션 권장 작업

doc 10의 마지막 남은 tier:

1. **PR F (defer 권장) — P2.3 `class2_candidate_source_mode` 비교 condition** — paper 평가 사이클 진입 시점에. 현재 PR #89 metric이 LLM/static 분리 측정을 이미 제공하므로 강제 모드 전환은 후순위.
2. **하드웨어 준비 후 E2E 재실행** — PR #87/#88/#89/#91/#92/#93 + 이번 PR의 통합 효과를 실 trial로 검증.

선택 항목:
- `policy_table.global_constraints`에 `caregiver_response_timeout_ms` 추가하여 Mac mini env와 RPi runner의 single source of truth 통합.
- Dashboard에 phase breakdown(`_class2_*_s` 속성 4개) 시각화 추가.
- P0.1 옵션 (a) full-async 재구조화 (응급 0지연이 필요할 때).
