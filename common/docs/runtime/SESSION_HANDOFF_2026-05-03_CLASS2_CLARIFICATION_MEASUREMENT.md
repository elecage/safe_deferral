# SESSION_HANDOFF — Class 2 Clarification Process Measurement (Plan + Build)

**Date:** 2026-05-03
**Predecessor:** PR #150 (`5009257` Fix 1+2 / `40f3bab` Problem C dashboard breakdown).
**Plan baseline:** [`PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md`](PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md).

---

## 이번 세션의 범위

PR #150 머지 후 verification sweep 결과를 사용자가 분석하다가 발견한 **architectural gap**:

> 현재 시나리오는 "LLM이 보수적 deferral한다"만 측정. paper의 진짜 contribution인 "LLM defer → Class 2 명확화 dialogue → 의도 점진적 recovery"는 measured 안 되고 있음.

이번 세션은 그 gap을 닫기 위한 PLAN doc 작성 + 단계별 구현 시작.

### 사용자 architectural feedback (원문)

> 내가 원한 건 class 1인데, 다른 모호한 상황으로 인해 class 2가 되면 LLM은 여기서 보류한다로 끝나는 게 아니라 재질문을 통해 점진적 명확화 과정을 거쳐야 해. 그렇다면 그런식으로 명확화를 한다는 모습이 보여야 하는데, 이걸 그냥 보류만 해버리면 LLM의 역할은 제한적일 뿐만 아니라 효용성이 떨어지는 것이라고 보는데.

이 한 문장이 §7.4 framing의 절반 진실 문제를 정확히 짚었음.

### 현재 측정의 한계 (verification sweep 5 trials)

```
trial 0  pass=❌ match=❌  class2_safe_deferral  final=none           255s
trial 1  pass=✅ match=✅  class1_direct         light_off→living    105s
trial 2  pass=❌ match=❌  class2_safe_deferral  final=none           247s
trial 3  pass=❌ match=❌  class2_safe_deferral  final=none           225s
trial 4  pass=✅ match=✅  class1_direct         light_on→living      87s
```

3/5 trial이 `class2_safe_deferral` — 시스템의 Class 2 clarification 메커니즘이 *작동하긴 했지만* (LLM-driven candidate set 생성됨) 가상 사용자가 응답을 안 해서 caregiver phase로 falls through. 이건 paper-honest 측정이 아니라 **incomplete** 측정.

### 시스템에는 이미 명확화 메커니즘이 있음

| 메커니즘 | 위치 | 현재 paper-eval에서 사용? |
|---|---|---|
| LLM-driven Class 2 candidate generation | `class2_clarification_manager` | ✅ |
| Static fallback candidate | `_DEFAULT_CANDIDATES` | ✅ |
| Single-turn user selection | `submit_selection(candidate_id)` | 일부 (CLASS_2 expected cells만) |
| Multi-turn refinement | `class2_multi_turn_enabled` opt-in | ❌ |
| Scanning input | `class2_input_mode=scanning` opt-in | ❌ |
| Auto-drive simulator | `runner._simulate_class2_button` | 제한적 (expected_route=CLASS_2 only) |

**시스템은 이미 multi-turn perception을 처리할 수 있음. 매트릭스/시나리오가 그걸 exercise 안 하는 게 문제.**

---

## 이번 PR(예정)의 핵심 디자인

### 1. Cell-level user_response_script 도입

매트릭스 cell이 사용자 응답을 명시:

```jsonc
{
  "cell_id": "EXT_A_LLM_DEFER_FIRST_CANDIDATE_ACCEPT",
  "_user_response_script": {
    "mode": "first_candidate_accept",
    "rationale": "LLM defer 후 첫 candidate 즉시 수락 → CLASS_2→CLASS_1 recovery 측정"
  },
  ...
}
```

지원 모드:
- `no_response` (default) — 현재 동작; baseline
- `first_candidate_accept` — single_click → 첫 candidate 선택
- `first_candidate_then_yes` — scanning mode, option 0에 yes
- `scan_until_yes` — multi-step scanning, `yes_at` 인덱스에서 yes (점진적 refinement)

### 2. Runner auto-drive 확장

현재: `expected_route_class==CLASS_2 && expected_transition_target==CLASS_1`일 때만 single_click 자동 발행.

확장: cell이 `user_response_script`를 declare하면 **expected_route_class=CLASS_1이라도** observed CLASS_2 escalation 후 script대로 응답 시뮬레이션.

### 3. 새 매트릭스 (구조만, scenario는 v2와 공유)

`matrix_extensibility_v3_clarification.json` — 4 cells, 모두 llm_assisted, 같은 scenario, 다른 script:

| Cell | Script | Per-cell expected | 측정 의미 |
|---|---|---|---|
| `EXT_A_LLM_DEFER_NO_RESPONSE` | no_response | CLASS_2+safe_deferral | Baseline (caregiver fallback) |
| `EXT_A_LLM_DEFER_FIRST_CANDIDATE_ACCEPT` | first_candidate_accept | CLASS_1+approved | 1-step 명확화 recovery |
| `EXT_A_LLM_DEFER_SCANNING_ACCEPT_FIRST` | first_candidate_then_yes | CLASS_1+approved | AAC 첫 옵션 수락 |
| `EXT_A_LLM_DEFER_SCANNING_ACCEPT_SECOND` | scan_until_yes (yes_at=1) | CLASS_1+approved | **점진적 명확화** (첫 거부 → 두 번째 수락) |

### 4. Paper signal — pass_rate vs match_rate gap

이번 measurement의 핵심 paper-grade signal:

- `pass_rate` (strict): observed_route_class == CLASS_1 비율
- `match_rate` (soft): final actuation == light_on/off 비율

clarification cells에서:
- pass_rate < match_rate → "strict route 안 맞췄지만 actuation 도달" → **명확화 dialogue가 recovery에 기여한 비율**
- 이 gap이 §7.4 framing의 두 번째 절반 ("LLM이 보수적이지만 시스템은 clarification으로 의도 풀어냄")의 정량 evidence

---

## 변경 요약 (이 PR 시점)

| 파일 | 변경 |
|---|---|
| `common/docs/runtime/PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md` (신규) | 8섹션 PLAN doc — scope, design, 단계, 위험, 후속 backlog. |
| `common/docs/runtime/SESSION_HANDOFF_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md` (신규) | 본 핸드오프. |
| `common/docs/runtime/SESSION_HANDOFF.md` | 인덱스 업데이트. |

**코드 변경: 0** (PLAN-only). 본 핸드오프 후 같은 PR 안에서 단계별 구현 시작.

---

## 단계별 구현 plan (PLAN doc §4)

| Phase | Work |
|---|---|
| 4.1 | `Cell.user_response_script` + `load_matrix` 로더 |
| 4.2 | `TrialResult.user_response_script` + `start_trial_async` 전달 |
| 4.3 | Runner auto-drive `first_candidate_accept` 확장 |
| 4.4 | Runner auto-drive scanning script 확장 (복잡하면 follow-up PR) |
| 4.5 | `matrix_extensibility_v3_clarification.json` 신규 |
| 4.6 | 모든 layer test |
| 4.7 | Debug sweep verification |

---

## Anti-goals

- 실제 LLM 기반 user 시뮬레이션 (사용자 응답을 LLM이 생성하는 것) — 측정 결정성 위배.
- Trial 단위 응답 변동 — cell의 script는 deterministic. LLM 비결정성으로 인한 variance만 측정.
- canonical asset 변경 — 모든 변경이 매트릭스/runner 단에서 끝남.
- v2 매트릭스 무효화 — v2는 paper-archive 그대로, v3는 clarification orthogonal measurement.

---

## Test plan (PLAN-only PR; 코드 변경 없음)

```bash
cd rpi/code && python -m pytest tests/ -q
# 348/348 (PR #150 후 그대로)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 721/721
```

---

## 다음 단계

이 PLAN/handoff commit 후, 같은 PR에서 §4.1 → 4.7 순서로 구현. 4.4 (scanning) 구현 복잡도가 예상보다 높으면 4.3까지만 PR로 marshal하고 scanning은 follow-up.

운영 backlog (PLAN doc §7):
- Trial isolation bug (HIGH)
- Multi-turn refinement scenario (MEDIUM)
- Real-LLM Class 2 candidate quality eval (MEDIUM)

---

## Notes

- v3 매트릭스는 v1/v2와 paper-comparable하지 **않음** — clarification process를 새 axis로 측정. v1/v2는 single-shot recovery, v3는 multi-turn perception.
- `class2_safe_deferral` final_action=`none` 케이스가 60% 되는 게 paper에서 "LLM 보수적"의 evidence이지만, 그 자체로는 § contribution을 절반만 보여줌. v3가 나머지 절반을 채움.
- 사용자 의도가 명확하므로 PLAN doc은 v3 매트릭스를 위한 **operator runbook + 측정 의도 + paper reframing language까지 포함**해서 향후 paper revision 시 reference 가능하게 함.
