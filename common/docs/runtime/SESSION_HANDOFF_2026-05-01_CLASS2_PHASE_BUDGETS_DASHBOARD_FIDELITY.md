# SESSION_HANDOFF — CLASS_2 Phase Budgets Dashboard Card + Virtual Node Timing Advisory (no dashboard hardcoding)

**Date:** 2026-05-01
**Tests:** 469/469 mac_mini fast suite (unchanged), 149/149 rpi (was 144; +5 new — 3 snapshot, 2 dashboard API; 2 skipped only because httpx is not installed locally)
**Schema validation:** scenario JSON parse check passes

**Plan baseline:** Follow-up to PR #95 (caregiver timeout policy promotion). Closes the dashboard-side rendering gap from doc 10's roadmap and the user's explicit guidance:

> "대시보드는 특히 대시보드 자체의 하드코딩 보다는 가상 노드들의 사전 설정 형식으로 해서 시뮬레이션의 fidelity가 높게 해야 하니까 그런것들을 고려해줘"

---

## 이번 세션의 범위

CLASS_2 trial timeout이 4개 phase budget의 합이라는 사실을 사용자가 dashboard에서 직접 검증할 수 있어야 하지만, 지금까지 dashboard는 어떤 budget도 표시하지 않았다. 단순히 dashboard에 숫자를 박아 넣는 대안은 fidelity를 떨어뜨리고 추후 정책 변경 시 drift 위험이 있다. 본 PR은:

1. runner의 phase budget을 그대로 노출하는 **API endpoint** + **trial별 snapshot** + **VirtualNodeProfile advisory 필드**를 갖춰서, 모든 숫자가 정책/runner/profile에서 직접 흘러나오도록 한다.
2. dashboard는 fetch만 하고 렌더만 하므로 자체 하드코딩 0.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `rpi/code/experiment_package/trial_store.py` | `TrialResult.class2_phase_budgets_snapshot: Optional[dict]` 추가. `to_dict()`가 항상 키를 노출 (None일 수도 있음). 정책이 후에 변경되더라도 trial이 실제로 사용한 budget이 보존됨. |
| `rpi/code/experiment_package/runner.py` | `start_trial_async`가 CLASS_2 trial 생성 시 `_class2_llm_budget_s/_class2_user_phase_timeout_s/_class2_caregiver_phase_timeout_s/_class2_trial_timeout_slack_s/_class2_trial_timeout_s` 5개를 snapshot에 동결. source label 포함. |
| `rpi/code/virtual_node_manager/models.py` | `VirtualNodeProfile.simulated_response_timing_ms: Optional[dict]` advisory 필드 추가. 자유형 키 (`user_response_ms`, `caregiver_response_ms` 등) — 다른 simulator 인격이 강제 schema 없이 자기 timing을 선언 가능. `to_dict()`에서 set일 때만 표면화 (없으면 dashboard가 "(unset)" 표기). |
| `rpi/code/dashboard/app.py` | `GET /package_runs/class2_phase_budgets` 추가 — runner 인스턴스 속성을 그대로 미러. `policy_fields` 블록이 어떤 정책 키에서 왔는지도 attribution. `/{run_id}` parameterised route보다 **앞에** 등록되어 path 충돌 없음. |
| `rpi/code/dashboard/static/index.html` | `pkg-class2-budgets-card` HTML + `renderClass2PhaseBudgets()` JS 추가. trial별 snapshot이 모두 동일하면 그것을 우선 사용 (historical accuracy), 그렇지 않으면 live API fallback. node card는 `simulated_response_timing_ms`가 set일 때만 ⏱ 행을 표기. **dashboard JS에 timing 숫자 0.** |
| `rpi/code/tests/test_rpi_components.py` | `TestClass2PhaseBudgetsSnapshot` 3개, `TestDashboardClass2PhaseBudgetsApi` 2개 (httpx 없으면 skip), `TestVirtualNodeManager.test_simulated_response_timing_*` 2개 추가. |

### Fidelity 원칙

- **policy_table → runner instance attr → API → JS render.** 모든 숫자는 `policy_table.global_constraints`(또는 missing 시 module default)에서 흘러나오며 dashboard layer에서 새 숫자를 만들지 않는다.
- **per-trial snapshot이 historical truth.** 정책이 후에 바뀌어도 과거 trial이 실제 사용한 budget은 export JSON에 보존된다.
- **VirtualNodeProfile advisory.** 가상 노드가 "이 simulator는 사용자가 1.5s에 반응한다"라고 자기 선언 가능. dashboard는 그것을 표시만 하고 비교 대상은 정책-derived budget이다.

### Single source of truth (renewed)

```
policy_table.global_constraints
    ├─ llm_request_timeout_ms          → runner._class2_llm_budget_s
    ├─ class2_clarification_timeout_ms → runner._class2_user_phase_timeout_s
    └─ caregiver_response_timeout_ms   → runner._class2_caregiver_phase_timeout_s
                                              ↓
                                runner._class2_trial_timeout_s (sum + slack)
                                              ↓
                            ┌─────────────────┴─────────────────┐
                  TrialResult.class2_phase_budgets_snapshot   GET /package_runs/class2_phase_budgets
                            ↓                                       ↓
                  trial export (historical)              dashboard live render (current)
                                              ↓
                            VirtualNodeProfile.simulated_response_timing_ms
                                  (advisory — node-declared, dashboard renders alongside)
```

### Test plan

```bash
cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 149 passed, 2 skipped in 9.46s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 469 passed in 33.75s
```

The 2 skips in rpi are `TestDashboardClass2PhaseBudgetsApi` cases that require httpx to drive the FastAPI TestClient — both pass when httpx is available; the skip markers exist only because this dev box does not ship httpx. Pre-existing test_pipeline.py is excluded as before because Ollama drives it locally.

### Out of scope (next work candidates)

- Trial detail UI (per-trial expandable view) — current dashboard only lists trials in tables; the snapshot is reachable only via export JSON. A small detail panel would surface `class2_phase_budgets_snapshot` per trial.
- Modal form field for editing `simulated_response_timing_ms` on virtual node creation/edit. Today it must be set programmatically. The model + to_dict surface is in place; the modal form addition is mechanical.
- Comparison metric: dashboard could compute `node.simulated_response_timing_ms.user_response_ms` vs `policy.user_phase_timeout_s * 1000` and flag "simulator over-runs phase budget" when set.

### Files touched

```
rpi/code/dashboard/app.py
rpi/code/dashboard/static/index.html
rpi/code/experiment_package/runner.py
rpi/code/experiment_package/trial_store.py
rpi/code/tests/test_rpi_components.py
rpi/code/virtual_node_manager/models.py
common/docs/runtime/SESSION_HANDOFF_2026-05-01_CLASS2_PHASE_BUDGETS_DASHBOARD_FIDELITY.md (this file)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### Notes

- canonical policy/schema assets는 건드리지 않음. 정책은 PR #95에서 이미 갖춰진 `caregiver_response_timeout_ms`를 활용만 함.
- governance/authority boundary 변경 없음. dashboard는 read-only 표시 layer로 유지.
- `class2_phase_budgets_snapshot`은 trial 생성 시점에 1회 계산되며, 이후에도 mutable한 dict이지만 runner는 이를 다시 쓰지 않는다. 외부 코드가 mutation하면 historical accuracy가 깨지므로 export 직후 readonly로 취급할 것.
