# SESSION_HANDOFF — Paper-Eval Trial Data Fidelity Diagnosis (gemma4:e4b sweep)

**Date:** 2026-05-03
**Predecessor:** [`SESSION_HANDOFF_2026-05-03_STEP4_AXIS_A_V2_BUILD_LEVERS_B_C.md`](SESSION_HANDOFF_2026-05-03_STEP4_AXIS_A_V2_BUILD_LEVERS_B_C.md) (PR #148, merged).
**Plan baseline:** [`PLAN_2026-05-03_PAPER_EVAL_TRIAL_DATA_FIDELITY_FIXES.md`](PLAN_2026-05-03_PAPER_EVAL_TRIAL_DATA_FIDELITY_FIXES.md) (this PR).

---

## 이번 세션의 범위

PR #148 (Step 4 Axis A v2 build) 머지 후 v2 sweep을 직접 운영하면서 발견한 **paper-eval 데이터 충실도 문제** 진단 + 수정 계획 + 우선순위. 코드 수정 0 (다음 PR에서 fix 1+2 구현).

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/docs/runtime/PLAN_2026-05-03_PAPER_EVAL_TRIAL_DATA_FIDELITY_FIXES.md` (신규) | Fix 1+2 설계, scope 정의, files-to-change 명시. |
| `common/docs/runtime/SESSION_HANDOFF_2026-05-03_TRIAL_DATA_FIDELITY_DIAGNOSIS.md` (신규) | 본 핸드오프 — diagnosis 결과 + 결정 audit trail. |
| `integration/paper_eval/matrix_extensibility_v2_llm_only.json` (신규) | LLM_ASSISTED 단독 매트릭스 (debug iteration용; n=30). |
| `integration/paper_eval/matrix_extensibility_v2_llm_only_debug5.json` (신규) | n=5 debug variant (~15 min/iteration). |
| `common/docs/runtime/SESSION_HANDOFF.md` | 인덱스 업데이트. |

코드 변경: **0**. canonical policy/schema 변경: **0**. 다음 PR에서 fix 1+2 구현.

---

## v2 sweep 운영 기록 (3 attempts)

| Attempt | sweep_id | Outcome | Wall time | Insight |
|---|---|---|---|---|
| 1 | `3c502d34126f` | 취소 (LLM_ASSISTED 9/30, 100% fallback=True) | ~1 hour | `llm_request_timeout_ms=8000` (canonical)이 gemma4:e4b ~89s 호출에 너무 짧음 → `requests.Timeout` → adapter fallback. |
| 2 | `3d0335ae8b52` | 완료, 그러나 LLM_ASSISTED 30/30 timeout (status=timeout, observation_payload=NULL) | ~1.5 hours | `llm_request_timeout_ms`을 120000으로 임시 bump 후 재실행. Class 1 LLM은 정상 응답하나 `_TRIAL_TIMEOUT_S=30s`가 LLM call(~89s) + downstream pipeline에 비해 너무 짧음 → 모든 trial이 trial budget 안에 observation 못 받음. |
| 3 | `c367f278c025` → `4ce2309375a5` (debug5) | 3차 실행은 LLM_ASSISTED 7/30에서 사용자 요청에 따라 취소. debug5 (n=5)로 빠른 iteration 시작. | ~1.5 hours + 14 min | `_TRIAL_TIMEOUT_S=180`으로 임시 bump 후 LLM-only matrix 작성. debug5 결과: 3 timeout / 1 PASS / 1 FAIL via CLASS_2. |

### 임시(uncommitted) 로컬 수정사항 — 본 PR 범위 밖

운영 도중 적용된 임시 수정 (모두 uncommitted, sweep 종료 후 revert 예정):

- `common/policies/policy_table.json`: `llm_request_timeout_ms` 8000 → 120000
- `rpi/code/experiment_package/runner.py`: `_TRIAL_TIMEOUT_S` 30.0 → 180.0
- `~/smarthome_workspace/.env`: `OLLAMA_MODEL` llama3.2 → gemma4:e4b

이 수정들은 진단을 진행하기 위한 운영 환경 조정이며 commit 안 함. 본 PR (#148 후속 PR)이 끝나면 revert + .env 복귀.

---

## Debug5 결과 — 핵심 데이터

```
Trial 0  status=timeout    pass=False  observed=None       (no obs)
Trial 1  status=timeout    pass=False  observed=None       (no obs)
Trial 2  status=completed  pass=True   observed=CLASS_1    light_on bedroom_light  (90s)  ← paper hypothesis 그대로!
Trial 3  status=completed  pass=False  observed=CLASS_2    safe_deferral           (172s)
Trial 4  status=timeout    pass=False  observed=None       (no obs)
```

**중요 관찰:**

- gemma4:e4b는 **결정적이지 않음** — 같은 입력에 대해 일부는 `light_on bedroom_light` (paper hypothesis), 일부는 `safe_deferral` 선택.
- Trial 2가 paper-grade evidence를 **단일 trial에서** 산출 — 시스템 자체는 잘 작동.
- Trial 3은 시스템 동작상 정상 (LLM 보수적 deferral → CLASS_2 escalation), 그러나 dashboard에는 단순 fail로만 표시됨 → outcome 데이터 누락이 진짜 문제.
- Trial 0/1/4 (60% timeout)은 budget 부족 — Fix 1으로 해결.

---

## 문제 분류 (PLAN doc §1.3)

| 문제 | 본 PR | 영향 |
|---|---|---|
| **A — Trial timeout 부족** (`_TRIAL_TIMEOUT_S=30s`가 LLM 호출에 비해 너무 짧음) | ✓ Fix 1 | 60% timeout |
| **B — `trial_store`가 단일 best_match obs만 저장** (CLASS_2 path의 multi-snapshot 누락) | ✓ Fix 2 | CLASS_2 outcome 보이지 않음 |
| **C — Digest/dashboard breakdown 부족** (`expected==observed` binary만 표시) | 후속 PR | "왜 fail했는가" 분석 불가 |
| **D — Trial isolation bug** (이전 trial의 context publish가 다음 trial의 single_click selection으로 leak) | 별도 PR | 측정 신뢰도 영향 |

---

## 결정 요약 (사용자와의 대화)

1. **DIRECT_MAPPING + RULE_ONLY는 매번 재실행하지 않음** — 결정적이고 충분히 검증됨. Iteration sweep는 `matrix_extensibility_v2_llm_only.json` (n=30) 또는 `_debug5.json` (n=5) 사용. 최종 paper archive 시점에만 full v2 matrix 1회 실행.
2. **Fix 1+2 우선** — 데이터 충실도가 paper-honest 분석의 전제. dashboard 렌더링(C)은 데이터 캡처(B)에 종속되므로 후속.
3. **Trial isolation bug (D)는 별 PR** — 측정 신뢰도에 영향이지만 Fix 1+2와 독립적, scope 분리.
4. **canonical `llm_request_timeout_ms` 영구 변경 안 함** — 운영 default 8000은 production 안전성 보장. paper-eval 측정용 120000은 일시적, sweep 종료 후 revert.

---

## Test plan (현재 세션)

PLAN doc만 추가 — 코드 무변경. 기존 test suite 그대로:

```bash
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 721 passed (PR #148 머지 후 그대로)

cd rpi/code && python -m pytest tests/ -q
# 311 passed
```

---

## 다음 단계

다음 PR (이 plan을 reference)에서:
1. Fix 1 (`runner.py` timeout 분기)
2. Fix 2 (`trial_store` multi-snapshot)
3. Tests
4. debug5 sweep 재실행 → Fix 검증
5. Fix C (dashboard breakdown)는 다시 별 PR

운영 backlog (PLAN doc §7):
- Problem C dashboard breakdown (HIGH)
- Trial isolation bug (HIGH)
- `_TRIAL_TIMEOUT_S` env-var (MEDIUM)
- Auto-drive policy for CLASS_1-expected LLM trials (MEDIUM)
- Lever A schema extension (MEDIUM, Step 5)

---

## Notes

- 진단 과정에서 v2 archive를 **만들지 않은 이유**: 데이터가 dashboard에 정확히 표시되지 않는 상태에서 archive를 만들면 paper-honest 분석 불가. Fix 1+2+C 적용 후 깨끗한 archive 만들 예정.
- `matrix_extensibility_v2_llm_only.json`은 iteration용으로 commit. v1↔v2 비교는 여전히 full v2 매트릭스 사용 — 새 파일은 paper archive를 대체하지 않음.
- Fix 1+2 후 debug5 재실행으로 0% timeout + observation_history 캡처 확인하면 다음 단계 (n=30 iteration → full v2 archive)로 진행.
