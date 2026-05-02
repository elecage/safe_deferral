# SESSION_HANDOFF — Dashboard Fidelity Comparison Metric (declared vs policy)

**Date:** 2026-05-02
**Tests:** rpi 157/157 unchanged (no backend changes); JS syntax verified (88696 chars). mac_mini fast suite untouched.

**Plan baseline:** Closes the first of three follow-on candidates after PRs #97/#98/#99. JS-only. Builds on PR #98 (modal field) and PR #96 (live phase budget API) without touching either.

---

## 이번 세션의 범위

PR #96–#99로 declared timing과 policy budget이 dashboard에서 모두 보이게 됐지만, 사용자가 두 값을 머리속으로 비교해야 했음. 본 PR은 자동 비교를 추가:

- 노드 카드의 ⏱ row가 각 declared key를 정책 phase budget과 비교
- declared > budget → ⚠ 빨간색 + tooltip에 "exceeds policy budget Xms — simulator would over-run the phase window"
- declared ≤ budget → ✓ 녹색 + tooltip
- 매핑되지 않은 key (future persona metric) → 색 변화 없음 (neutral)

### 변경 요약

| 파일 | 변경 |
|---|---|
| `rpi/code/dashboard/static/index.html` | `loadNodes()`가 `/package_runs/class2_phase_budgets`를 `/nodes`와 함께 fetch하여 `_class2BudgetsCache`에 저장. `_TIMING_CLAIM_TO_BUDGET_MS` map이 두 known key (user_response_ms / caregiver_response_ms)를 정책 phase budget으로 매핑. `_compareTimingClaim()`이 status (`exceeds` / `within` / `neutral`)와 비교한 budget 반환. `renderNodes()`의 timing row가 각 segment를 색 + ✓/⚠로 렌더. |

### 디자인 원칙 (PR #98 + #99 위에 자연스럽게)

- **Three-state UI** — exceeds / within / neutral. unmapped key는 절대 ⚠ 표기 안 함 (future persona metric을 무관하게 추가해도 false alarm 없음).
- **Live policy** — 정책이 바뀌면 다음 `loadNodes()` 호출에서 자동 반영 (refresh 버튼 또는 다른 트리거).
- **Fail-soft** — `/package_runs/class2_phase_budgets` 호출 실패해도 노드는 정상 렌더 (cache가 null일 때 모든 비교가 neutral).
- **Backend 변경 없음** — dashboard만으로 비교 가능.

### Fidelity loop 완성형

```
정책 phase budgets ──┐                 ┌── declared simulated_response_timing_ms
                    │                  │
                    └──── 노드 카드 ⏱ row ────┘
                          (자동 비교, ⚠ over-run / ✓ within)
```

### Test plan

```bash
node -e "..."   # JS parse: OK (88696 chars)
cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 157 passed (unchanged)
```

수동 테스트:
- Modal로 `caregiver_response_ms = 350000` 설정 → 노드 카드에서 ⚠ 빨간색 + tooltip
- `caregiver_response_ms = 12000` 설정 → ✓ 녹색
- 임의 key (`extra_persona_metric_ms = 999`) 설정 → 색 없음 (neutral)
- 정책 caregiver_response_timeout_ms를 줄여서 budget 변경 → refresh 시 비교 결과 변경

### Files touched

```
rpi/code/dashboard/static/index.html
common/docs/runtime/SESSION_HANDOFF_2026-05-02_DASHBOARD_FIDELITY_COMPARISON_METRIC.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### Next (남은 두 항목)

다음에 진행:
- ⏭ PR F (doc 10 §3.3 P2.3) — `class2_candidate_source_mode` (static_only / llm_assisted) experiment_mode 확장. PR #79 패턴 mirror. 정책 + manager + scenario + metric 모두 변경.
- ⏭ doc 09 Phase 6 — multi-turn clarification. 본격 구현 전 design alignment 필요 (다단계 session state, time-bound, schema extension, TTS pattern).

### Notes

- Authority boundary 변경 없음. 비교는 read-only display.
- `_TIMING_CLAIM_TO_BUDGET_MS`에 새 key 추가하면 자동으로 비교 활성. 정책에 새 phase budget이 생기면 같은 패턴으로 mapping 한 줄 추가.
