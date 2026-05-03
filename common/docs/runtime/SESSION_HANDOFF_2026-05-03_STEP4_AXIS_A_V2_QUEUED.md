# SESSION_HANDOFF — Step 4 (Axis A v2) Queued After Step 3 Completion

**Date:** 2026-05-03
**Tests:** rpi 306/306, mac_mini 719/719 unchanged from #146.
**Plan baseline:** `PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md` (this PR).

**Trigger:** Step 3 archive (PR #146) measured EXT_A_LLM_ASSISTED at pass_rate=28% with 12 timeouts under 120s budget, plus the 5 successful trials all chose context-aware toggle (light_off living) rather than the hypothesised bedroom-light recovery. User decided Step 4 should retry under three orthogonal improvements before settling the paper interpretation.

---

## 이번 세션의 범위

오직 plan + handoff 기록. Step 4 구현은 별 PR. 결정 audit trail을 코드 변경 전에 박아두는 게 paper-honest.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/docs/runtime/PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md` (신규) | Step 4 plan: 3 levers (A: fixture context enrich, B: gemma4:e4b 모델 swap, C: 일반 prompt 가이드 한 줄 추가). 운영 절차, 성공 기준, 안티-목표, 8-section spec. |
| `common/docs/runtime/SESSION_HANDOFF_2026-05-03_STEP4_AXIS_A_V2_QUEUED.md` (신규) | 본 핸드오프. |
| `common/docs/runtime/SESSION_HANDOFF.md` | index 업데이트. |

### 결정 요약 (사용자와의 대화에서)

LLM_ASSISTED 셀의 28% 회수율을 어떻게 해석/개선할지 4개 lever 제시했고 사용자가 선택:

| Lever | 결정 | 근거 |
|---|---|---|
| **A — Fixture context enrich** (`user_state.inferred_attention`, `recent_events`) | **수락** | schema는 이미 지원, fixture만 enrich, paper-honest |
| **B — 더 큰 모델** | **gemma4:e4b** (≈9.6 GB, 8B 파라미터) — laptop 감당 가능 | gemma4:31b (19 GB)는 OOM 위험 |
| **C — Prompt 조정** | **일반 가이드 한 줄만** (no scenario-specific cherry-picking) | 시나리오 맞춰 retrofit하면 paper-dishonest. "device_states / environmental_context를 활용; 충분한 신호 시 safe_deferral보다 catalog action 우선 고려" 정도 |
| D — 결과 그대로 | (병행) | v1 archive는 그대로, v2 archive와 side-by-side 비교 |

### Step 4의 paper-evidence 디자인

이 4개 lever 결정 후 PLAN doc §5에 명시한 **세 가지 결과 시나리오** 모두 paper-에 가치 있음:

1. **v2 LLM pass ≫ v1 (60%+ vs 28%)**: levers C/A가 효과적 → "richer context + 일반 가이드가 LLM recovery에 큰 영향" → paper §5.8 evidence 강화
2. **v2 ≈ v1 (~28%)**: LLM의 deferral이 모델 capacity가 아니라 prompt doctrine 결과 → `01_paper_contributions §7.4` framing ("LLM은 진짜 ambiguous에서 보수적") 강화
3. **v2 < v1**: regression — lever C 의심 → 별도 조사 필요

각 시나리오 모두 paper에 기여함. **negative result도 valid evidence.**

### Step 4 안티-목표

- Phase C (PR #140) archive 무수정. v2는 *추가* data point.
- Same scenario 의미 유지 (single_click + living_on + bedroom_off). "context의 양"과 "model"과 "prompt doctrine" 만 변동.
- v2 sweep 후 .env를 OLLAMA_MODEL=llama3.2 default로 복귀 — 다른 archive 재현성 유지.
- **Regression check 필수**: matrix_smoke + matrix_phase_b를 새 prompt + gemma4:e4b로 재실행. covered input에서 정상 동작 확인. regression 시 lever C 롤백 검토.

### Files touched (이 PR)

```
common/docs/runtime/PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-03_STEP4_AXIS_A_V2_QUEUED.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

코드 변경 0. canonical asset 변경 0. tests 변경 0.

### Test plan

**Doc-only PR**, 코드 무변경. 기존 test suite 그대로:
```bash
cd rpi/code && python -m pytest tests/ -q   # 306 passed
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py   # 719 passed
```

### 다음 단계 (Step 4 별 PR)

PLAN doc §3에 명시된 파일 변경 (fixture / scenario / matrix / prompt / tests) + Step 4 sweep 운영 + side-by-side archive. 사용자 GO 후 진행.

전체 잔여 backlog (PLAN doc §8):
1. **Step 4 (이 plan)** — Axis A v2 — HIGH
2. Multi-turn recovery sweep — HIGH (paper integrity)
3. target-device-correctness metric → Axes B/C — MEDIUM (큰 작업)
4. Item 2 fix (cancel partial) — MEDIUM (ops)
5. Temp/top_p sweep — LOW (보조)
6. #1 retry — LOWEST
7. doc 13 update — LOW (cosmetic)

### Notes

- PLAN doc은 "결정을 코드 변경 전에 박는" pattern (#112 / #122 / #134 등에서 확립). Step 4 구현 PR이 이 plan을 reference하면 audit trail이 paper-honest.
- **새 fixture/scenario/matrix 별도 파일** 결정 (v1 reuse 안 함) — v1 archive의 reproducibility 보존 + side-by-side 깨끗.
- gemma4:e4b 처음 사용. 실제 LLM call 시 latency 측정해서 v1 (llama3.2 11s)와 비교 필요.
