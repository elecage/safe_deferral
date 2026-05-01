# SESSION_HANDOFF — Caregiver Response Timeout Promoted to policy_table (single source of truth)

**Date:** 2026-05-01
**Tests:** 444/444 mac_mini fast suite (was 440; +4 new resolver tests), 142 → 144 rpi (+2 new)
**Schema validation:** 15/15 scenario skeletons; policy_table parses with new field

**Plan baseline:** Follow-up to PR #94 (P2.2 trial timeout decomposition) noted in doc 10's "Out of Scope" / future-work list.

---

## 이번 세션의 범위

PR #94 (P2.2)에서 `_class2_caregiver_phase_timeout_s`를 runner 인스턴스 속성으로 정책-친화 구조로 옮겼지만, **caregiver Telegram 응답 창 자체는 여전히 두 곳에서 따로 관리**되고 있었다:

- Mac mini: `CAREGIVER_RESPONSE_TIMEOUT_S = int(os.environ.get(..., "300"))` (env 또는 하드코드 300)
- RPi runner: `_CAREGIVER_PHASE_TIMEOUT_S = 300.0` (모듈 상수)

두 값이 분리되어 drift 가능. 본 PR은 `caregiver_response_timeout_ms`를 정책으로 승격하고 양쪽이 같은 source를 보도록 정렬.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/policies/policy_table.json` | `global_constraints.caregiver_response_timeout_ms = 300000` 추가. 자체 documenting `_caregiver_response_timeout_ms_description` 키와 함께. |
| `mac_mini/code/main.py` | `CAREGIVER_RESPONSE_TIMEOUT_S = int(os.environ.get(..., "300"))` 한 줄을 `_resolve_caregiver_response_timeout_s()` 함수 호출로 대체. 해결 순서: env → 정책 → hardcoded 300. |
| `rpi/code/experiment_package/runner.py` | `self._class2_caregiver_phase_timeout_s`가 `gc.get("caregiver_response_timeout_ms", _CAREGIVER_PHASE_TIMEOUT_S * 1000) / 1000`으로 계산. 모듈 상수는 fallback 전용으로 유지. |
| 주석 블록 | runner 헤더 주석에서 caregiver phase 설명을 "정책에서 로드 + Mac mini env override"로 갱신. |

### 해결 순서 정리 (Mac mini)

```
1. CAREGIVER_RESPONSE_TIMEOUT_S env var, set and parseable  → use env (operational override)
2. policy_table.global_constraints.caregiver_response_timeout_ms / 1000  → use policy (canonical)
3. hardcoded 300  → safety floor (only if both fail)
```

### Single source of truth

- **정책 = canonical:** `policy_table.global_constraints.caregiver_response_timeout_ms`
- **Mac mini env = optional override:** ad-hoc 운영 튜닝 시 (예: 테스트 환경에서 짧게)
- **하드코드 = 마지막 안전 장치:** 정책 파일 손상 / 부재 시

---

## 새 테스트 (+6)

`mac_mini/code/tests/test_pipeline_ack_escalation.py::TestResolveCaregiverTimeout` (+4):
1. `test_env_override_wins` — env=42 → 42
2. `test_invalid_env_falls_through_to_policy` — env="not-a-number" → 정책 default 300
3. `test_no_env_uses_policy` — env 미설정 → shipped 정책 300
4. `test_policy_failure_falls_back_to_300` — 정책 로드 예외 → 300

`rpi/code/tests/test_rpi_components.py::TestClass2TrialTimeoutDecomposition` (+2):
1. `test_caregiver_phase_loaded_from_policy` — stub policy로 `caregiver_response_timeout_ms=60000` 주입 → runner phase=60s
2. `test_caregiver_phase_default_from_shipped_policy` — 실 정책 default 300 검증

mac_mini 440→444 (+4), rpi 142→144 (+2). 모두 통과. scenario 15/15 unchanged.

---

## 안전 invariant 변동

없음. 정책 값(300000ms)이 이전 하드코딩(300s)과 동일. env 미설정 시 운영 동작 그대로. env 설정 시 그대로 override 작동.

추가 보장:
- 정책 파일이 손상되어도 mac_mini는 300s fallback (안전 하한)
- 정책에서 caregiver_response_timeout_ms가 줄어들면 mac_mini와 rpi runner 모두 즉시 새 값 채택 (drift 불가)

---

## 주의사항

- **canonical asset 변경 (1건):** `policy_table.json` `global_constraints`에 새 필드 + 자체 description 메타키. Additive — 기존 fixture/스크립트 영향 없음.
- **`_CAREGIVER_PHASE_TIMEOUT_S = 300.0` 모듈 상수 유지:** 이제 fallback 전용. 외부 코드가 import 중일 수 있어 backward-compat.
- **mac_mini 모듈-import 시 정책 로드:** `_resolve_caregiver_response_timeout_s()`가 import 시 한 번 실행됨. 정책 파일이 워크트리에 존재하므로 정상 동작. 정책 로드 실패해도 300으로 안전 fallback.
- **테스트 환경 영향:** 기존 테스트 중 `CAREGIVER_RESPONSE_TIMEOUT_S` 모듈 상수 직접 사용하는 곳은 영향 없음 (값이 동일).

---

## 다음 권장 작업

doc 10 follow-up 잔여:

1. **하드웨어 준비 후 E2E 재실행** — 가장 시급. PR #87/#88/#89/#91/#92/#93/#94 + 본 PR 누적 효과 검증.
2. **#3 Dashboard phase breakdown 시각화** — PR #94가 노출한 phase attribute 4개 (`_class2_llm_budget_s`, `_class2_user_phase_timeout_s`, `_class2_caregiver_phase_timeout_s`, `_class2_trial_timeout_slack_s`)를 dashboard에 렌더. (방금 사용자와 합의한 다음 작업)
3. **(선택, future)** P0.1 옵션 (a) full-async 재구조화 — 응급 0지연 보장이 필요할 때.
4. **(선택)** PR F (P2.3 `class2_candidate_source_mode`) — paper 평가 사이클에서 통제 비교 실험이 필요해질 때.
