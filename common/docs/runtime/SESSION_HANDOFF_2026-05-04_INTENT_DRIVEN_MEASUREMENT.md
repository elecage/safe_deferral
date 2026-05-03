# SESSION_HANDOFF — Intent-Driven Measurement (PLAN + Build)

**Date:** 2026-05-04
**Predecessor:** PR #151 `9ed412f` (Step 6 Class 2 clarification measurement) — `_user_response_script`, `outcome_match_rate`, observation_history-based trajectory all in place.
**Plan baseline:** [`PLAN_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md`](PLAN_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md).

---

## 이번 세션의 범위

PR #151 머지 후 사용자 architectural feedback이 측정 framework의 다음 layer를 짚음:

> 기대값이 단순히 class 1, class 2여서는 안되고, 실제로 의도하는 바가 거실 등을 켜고 싶은 것인지, 침실 등을 켜고 싶은것인지 또는 끄고 싶은 것인지에 대한 최초 의도를 설정하고, 해당 의도대로 응답을 하는 시나리오가 나와야 되는 것이야.

PR #151의 `outcome_match_rate`는 "system이 actuation에 도달했나"를 측정. 이번 PR은 **"system이 사용자가 의도한 actuation에 도달했나"**를 측정하는 framework를 도입.

### 핵심 디자인 — 3-level metric stack

| Level | Metric | 의미 |
|---|---|---|
| 1 | `pass_rate` | observed_route_class == expected (routing fidelity) |
| 2 | `outcome_match_rate` | system reached *some* expected_validation action (actuation fidelity) |
| **3** | **`intent_match_rate`** | **system reached *the user's intended* action (semantic fidelity)** |

Gap interpretation:
- `outcome_match - intent_match`: actuation은 됐지만 의도와 다른 동작 (perception failure hidden by aggregate metrics)
- `pass - intent_match`: routing 맞지만 의도 빗나감

### Scenario user_intent 도입

```jsonc
{
  "scenario_id": "...",
  "user_intent": {
    "action": "light_on",
    "target_device": "bedroom_light",
    "rationale": "거실 등은 이미 켜져 있고 침실 등은 꺼져 있음 → 침실 등 켜기 의도"
  },
  ...
}
```

Optional 필드. 부재 시 `intent_match_rate = None` (legacy scenario 보존).

---

## PR scope split — #152 (이번) vs #153 (follow-up)

| | PR #152 (이번) | PR #153 (follow-up) |
|---|---|---|
| Intent contract (scenario field, metric) | ✓ | — |
| Intent_match_rate (aggregator/digest/dashboard) | ✓ | — |
| Paper doc §6 update | ✓ | — |
| `accept_intended_candidate_direct` (existing direct-select) | ✓ | — |
| Scanning script (`scan_until_yes`, `accept_intended_via_scan`) | — | ✓ |
| Multi-turn refinement script | — | ✓ |
| Coverage matrix v4 (다양한 cells) | — | ✓ |

이 분리는 framework review가 깔끔하고 reviewable scope를 작게 유지. PR #152 머지 후 #153가 framework 위에서 coverage 확장.

---

## 변경 요약 (이 PR 시점, PLAN-only)

| 파일 | 변경 |
|---|---|
| `common/docs/runtime/PLAN_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md` (신규) | 8섹션 PLAN doc — design, scope, phases, risks, files |
| `common/docs/runtime/SESSION_HANDOFF_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md` (신규) | 본 핸드오프 |
| `common/docs/runtime/SESSION_HANDOFF.md` | 인덱스 업데이트 |

코드 변경: 0. canonical asset 변경: 0. 본 핸드오프 후 같은 PR 안에서 §4.1 → 4.9 단계별 구현.

---

## 단계별 구현 plan (PLAN doc §4)

| Phase | Work |
|---|---|
| 4.1 | Scenario user_intent + loader |
| 4.2 | TrialResult.user_intent_snapshot + runner snapshot |
| 4.3 | Aggregator intent_match helpers + CellResult |
| 4.4 | Digest CSV/MD intent column |
| 4.5 | Dashboard intent column (Paper-Eval + 결과분석) |
| 4.6 | Paper doc §6 |
| 4.7 | Tests at every layer |
| 4.8 | v3 scenario user_intent 추가 (end-to-end 검증) |
| 4.9 | v3 debug5 sweep 재실행 → intent_match column 채워짐 확인 |

---

## Anti-goals

- Scenario user_intent를 canonical context_schema에 넣지 않음 — experimental 정보, asset boundary 위반 안 함.
- Trial-level user_intent override를 허용하지 않음 — scenario 단위로만 declare. (다양한 intent는 다른 scenario로 분리.)
- LLM이 user_intent를 prompt에 보지 않음 — 사용자가 직접 표현 못하는 정보(어차피 의도 추론하라는 것). 추론 후 system이 해당 의도와 일치하는지 *측정*만 함.
- canonical 매트릭스 비교 framework를 흔들지 않음 — pass/match는 그대로, intent_match가 추가 layer.

---

## Test plan (PLAN-only PR; 코드 변경 없음)

```bash
cd rpi/code && python -m pytest tests/ -q   # 376/376 (PR #151 후 그대로)
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py   # 721/721
```

---

## 다음 단계

이 PLAN/handoff commit 후, 같은 PR에서 §4.1 → 4.9 순서로 구현. 4.4-4.5 (digest + dashboard)에서 column 위치를 결정 — `outcome_match_rate` 다음에 `intent_match_rate` 두는 게 paper-doc의 3-level stack 순서와 일치.

운영 backlog (PLAN doc §7):
- PR #153 — Scanning + multi-turn + coverage matrix v4 (HIGH)
- Trial isolation bug (HIGH)
- Per-trial drill-down (MEDIUM)
- Caregiver-phase scripts (MEDIUM)

---

## Notes

- `_trial_intent_match`는 None을 명시적 third state로 사용 — "intent declared 안 됨". `outcome_match`처럼 boolean 단일이 아니라 ternary. 이 차이로 legacy scenario의 metric이 0.0이 아닌 None으로 표시되어 **"미측정"과 "0%"가 구분**됨.
- Paper doc §6의 quantitative 인용은 hardware verification에서 산출 — 개발 환경 numbers 아님 (§3 separation 유지).
- v3 매트릭스의 LLM_ASSISTED scenario에 user_intent 추가 시, 기존 v3 sweep 결과는 intent_match=None으로 표시 (snapshot 부재). 새 sweep부터 채워짐.
