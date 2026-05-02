# SESSION_HANDOFF — Per-Trial Detail UI Surfacing class2_phase_budgets_snapshot

**Date:** 2026-05-02
**Tests:** rpi 157/157 unchanged (no backend changes); JS syntax verified via Node parse (86412 chars across script blocks). mac_mini fast suite untouched.

**Plan baseline:** Closes the third item in the post-PR #96 next-work menu. PR #96 added `TrialResult.class2_phase_budgets_snapshot` (frozen at trial creation) but the snapshot was reachable only via export JSON. This PR makes it visible in the UI.

---

## 이번 세션의 범위

PR #96에서 trial-level snapshot이 export JSON에는 들어가지만 dashboard에서는 클릭으로 드릴다운할 수 없었음. 정책이 후에 바뀌어도 trial이 실제 사용한 budget을 UI에서 즉시 검증할 수 없는 게 fidelity 흐름의 마지막 gap.

본 PR은 Package A의 trial table에 expandable detail row를 추가:

- 행 클릭 → 바로 아래 hidden detail row 토글
- detail row는 lazy-render (첫 클릭 시에만 innerHTML 생성, 다시 닫을 때는 그대로 유지)
- 표시 내용:
  - **CLASS_2 Phase Budgets snapshot** — 5개 phase 값 + source label (frozen at creation)
  - **Trial Contract / Audit** — `audit_correlation_id`, `trial_id`, `expected_transition_target`, `expected_validation`, `expected_outcome`, `observed_validation`, `fail_reason`, `requires_validator_reentry_when_class1` (값이 있는 것만)
  - **Notification Payload** (있을 때) — JSON pretty-printed, scrollable, escaped
  - **Clarification Payload** (있을 때) — 동일

### 변경 요약

| 파일 | 변경 |
|---|---|
| `rpi/code/dashboard/static/index.html` | Package A trial table의 각 `<tr>`에 `cursor:pointer`, `onclick="togglePkgATrialDetail(i)"` 추가 + 즉시 뒤따르는 hidden `<tr id="pkg-a-detail-${i}">` 삽입. `pkgATrialsCache` (module-scoped), `togglePkgATrialDetail()`, `renderPkgATrialDetailBody()`, `escapeHtml()` 함수 추가. snapshot 5필드 + 8개 audit 필드 + 두 payload JSON을 표시. lazy-render로 닫혀 있는 detail은 DOM 비용 없음. |

### 디자인 원칙 (PR #96 + #98의 fidelity 흐름 마무리)

- **Snapshot은 historical truth** — detail row의 source label에 "(snapshot · ...)" 표기로 dashboard live 카드(현재 정책)와 구분. PR #96의 `pkg-class2-budgets-card`가 *현재* 값을, detail row가 *과거* 값을 보여줌.
- **Read-only audit surface** — 모든 표시는 read-only. payload JSON은 `<pre>` + escapeHtml로 안전하게 표시. dashboard authority 경계 변경 없음.
- **Lazy render** — 트라이얼 100개 run에서도 닫혀 있는 detail은 innerHTML이 비어 있어 DOM 노드 추가 비용이 0.

### Fidelity 완성 (PR #96 + #98 + 본 PR)

```
정책 + VirtualNodeProfile (canonical / declared)
        ↓
  runner phase budgets + simulated_response_timing_ms
        ↓
┌────────────────┬────────────────┬───────────────────┐
│ live API card  │ trial snapshot │ node card ⏱ row  │
│ (PR #96)       │ (this PR)      │ (PR #96 + #98)    │
└────────────────┴────────────────┴───────────────────┘
        ↓
   사용자가 dashboard에서 모든 fidelity layer를 직접 검증 가능
```

### Test plan

```bash
cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 157 passed in ~10s (unchanged — backend/data unchanged)

node -e "..."   # JS parse: OK (86412 chars)
```

수동 테스트 (dashboard 띄울 때):
- Package A run 보면서 trial 행 클릭 → detail row 표시되는지
- CLASS_2 trial → snapshot 5필드 표시
- non-CLASS_2 trial → snapshot block 숨김, audit/contract block만 표시
- payload가 큰 JSON → scrollable
- 다시 클릭 → detail 숨김, 다시 열면 같은 내용 (lazy cache 유지)

### Files touched

```
rpi/code/dashboard/static/index.html
common/docs/runtime/SESSION_HANDOFF_2026-05-02_TRIAL_DETAIL_UI_SNAPSHOT.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### Out of scope (메뉴 완료)

세 개 항목 모두 완료:
- ✅ #1 Phase 4 회귀 테스트 (PR #97)
- ✅ #3 Modal field for simulated_response_timing_ms (PR #98)
- ✅ #2 Trial detail UI (this PR)

다음 후보:
- (Future) **Dashboard 비교 metric** — declared `user_response_ms`가 정책 `user_phase_timeout_s * 1000`을 초과하면 ⚠ 표기. 본 PR + PR #98로 자연스럽게 가능. JS-only 작업.
- (Future) **PR F (doc 10 §3.3 P2.3)** — Class 2 LLM-vs-static comparison condition. doc 10에서 first paper-evaluation cycle까지 defer 권고됨.
- (Deferred) **doc 09 Phase 6** — multi-turn clarification.

### Notes

- Authority boundary 변경 없음. detail row는 read-only audit surface.
- `<pre>` JSON 표시는 `escapeHtml()`로 XSS 안전. payload는 backend가 schema-validated 값이지만 방어적으로 escape.
- `pkgATrialsCache`는 module-level `let`이라 다음 run 로드 시 자동 갱신 (`pkgATrialsCache = trials;` 첫 줄에서 덮어씀).
