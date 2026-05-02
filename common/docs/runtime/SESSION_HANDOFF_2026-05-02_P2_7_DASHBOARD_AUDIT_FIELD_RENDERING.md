# SESSION_HANDOFF — P2.7 Dashboard Audit-Field Rendering

**Date:** 2026-05-02
**Tests:** mac_mini 700/700 (was 694; +6 new in test_dashboard_audit_field_rendering_p2_7.py). rpi 168/168 unchanged.
**Schema validation:** none modified. Dashboard JS parses cleanly (93153 chars across script blocks).

**Plan baseline:** PR #7 of `PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md`. Closes the audit's "PR #99 trial detail UI's coverage of the 4 new audit fields is unverified" gap.

---

## 이번 세션의 범위

PR #99의 trial detail row가 doc 12 / doc 11에서 추가된 4개 audit 필드 (`input_mode`, `scan_history`, `scan_ordering_applied`, `refinement_history`)를 raw JSON dump 안에 포함은 했지만 dedicated UI 블록은 없었음. P2.7은:

1. 4개 dedicated rendering 블록을 `renderPkgATrialDetailBody`에 추가 (ad-hoc structural patterns).
2. Static check 6개 — JS parse + 각 블록 패턴 + canonical extraction (`trial.clarification_payload`).

### 변경 요약

| 파일 | 변경 |
|---|---|
| `rpi/code/dashboard/static/index.html` | `renderPkgATrialDetailBody`에 4개 신규 블록 (각각 절대 backward-compat — 필드 부재 시 0 DOM 추가): **Class 2 Interaction Mode** (input_mode + candidate_source), **Scan History** (per-turn timeline with response icons + colors yes/no/silence/dropped), **Scan Ordering Applied** (matched_bucket + applied_overrides + final_order arrow chain), **Refinement History** (turn_index + parent → child transition). 모두 `cp = t.clarification_payload || {}`로 single canonical 경로에서 읽음. |
| `mac_mini/code/tests/test_dashboard_audit_field_rendering_p2_7.py` (신규) | 6 테스트. JS parse via Node (skip if Node 미설치), 4 신규 블록 source 패턴 검증, single canonical extraction (`cp = t.clarification_payload`) 검증. |

### 디자인 원칙

- **Backward compat absolute**: 4개 블록 모두 필드가 없으면 빈 string 리턴 → legacy direct_select 단일-턴 record가 영향 0.
- **Visual hierarchy**: Phase budget snapshot → Audit/contract → 4 mode/scanning/ordering/refinement → raw JSON payloads. 사용자가 high-level부터 detail로.
- **icon + color으로 빠른 인식**: scan_history `yes/no/silence/dropped` 각각 ✓/✗/⏱/⚠ + 색상 (green/dim/yellow/red). 시각적 검토가 빠름.
- **Static patterns + canonical alias**: `cp.input_mode` etc. — schema 위치가 단일 source of truth (`clarification_payload`). 만약 future refactor가 필드를 다른 곳으로 옮기면 테스트가 catch.

### Boundary 영향

없음. dashboard read-only display layer만 확장. Production runtime / authority surface 0 변경.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_dashboard_audit_field_rendering_p2_7.py -v
# 6 passed in 0.21s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 700 passed (was 694; +6 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (unchanged)
```

수동 검증 (deployment 시):
- 단일-턴 direct_select trial → 4개 신규 블록 모두 미렌더 (legacy 호환)
- scanning trial with input_mode='scanning' + scan_history → Interaction Mode + Scan History 블록 표시
- deterministic ordering trial → 추가로 Scan Ordering Applied 블록 표시 with matched_bucket/overrides/final_order
- refinement trial → 추가로 Refinement History 블록 with parent→child arrow

### Files touched

```
rpi/code/dashboard/static/index.html
mac_mini/code/tests/test_dashboard_audit_field_rendering_p2_7.py (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_P2_7_DASHBOARD_AUDIT_FIELD_RENDERING.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### P2 완료

- ✅ P2.6 — manifest schema + comparison_conditions tagging (PR #118)
- ✅ P2.7 — dashboard audit-field rendering (this PR)

### 다음 단계 (PLAN doc §3 sequencing)

- **P3.8**: fixture comment cleanup (옛 prompt references in test fixtures). `sc01_light_on_request.json` 위치 정리도 후보.

8 PR backfill plan의 마지막 PR 1개 남음.

### Notes

- JS unit test 인프라가 없어 static substring matching에 의존. 패턴은 의도적으로 structural (function pattern + label substring) — cosmetic 편집은 허용, 삭제는 즉시 fail.
- `node` PATH에 없으면 JS parse test skip — CI에서는 Node 설치 가정.
- 4개 신규 블록의 시각적 확인은 dashboard 띄워서 직접 — automated UI test는 별도 인프라 필요 (out of scope).
