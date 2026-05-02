# SESSION_HANDOFF — Paper-Eval Matrix Plan + Matrix v1 (Phase 0)

**Date:** 2026-05-02
**Tests:** unchanged (planning + JSON-only PR; no code, no schema, no scenario modifications). mac_mini 700/700, rpi 168/168.
**Schema validation:** none modified. matrix_v1.json validated against its own implicit shape (12 cells, all scenarios present, all comparison_conditions match Package A enum).

**Plan baseline:** Phase 0 of `13_paper_eval_matrix_plan.md`. Follow-up to PR #121 (sc01 relocation), which closed the post-doc-12 backfill. Sets up the operational paper-eval layer that the 4-dimensional comparison framework (PRs #79 / #101 / #110 / #111) needs.

---

## 이번 세션의 범위

post-doc-12 backfill (PRs #112–#121) 끝나서 architectural / docs / scenarios / dashboard 정합성 회복. 다음 단계는 **실제 measurement 운영** — paper-eval matrix 셋업. 이 작업은 4 PR 분할이 적절하므로 doc 11 / doc 12 패턴 그대로:

- Phase 0 (this PR): design + matrix definition v1 + handoff. **No code.**
- Phase 1+: 후속 PR (sweep orchestrator, aggregator, digest exporter).

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/docs/architecture/13_paper_eval_matrix_plan.md` (신규) | 12-section design doc. Purpose, scope, non-negotiable boundaries (no new authority surface, no canonical-asset modification, reproducibility-first, no paper-ready conclusions baked in), matrix v1 design (4 dimensions × cell selection × trials per cell × scenarios per cell × expected outcome anchors), matrix file shape, sweep orchestrator design (Phase 1), cross-run aggregator design (Phase 2), paper digest exporter (Phase 3), 5-phase split table, anti-goals, open questions, source notes. |
| `integration/paper_eval/matrix_v1.json` (신규) | Concrete matrix v1: 12 cells (1 baseline + 3 Class 1 D1 + 8 Class 2 D2×D3×D4 + 2 multi-turn refinement variants). Each cell declares cell_id, comparison_condition, scenarios, trials_per_cell (default 30), expected_route_class / expected_validation, optional _policy_overrides for cells requiring policy flag flips. Top-level `_dimensions` documents the 4-axis space. `anchor_commits` slot for orchestrator to fill at sweep start (matrix_file_sha / scenarios_dir_sha / policy_table_sha) — reproducibility marker. |
| `common/docs/architecture/00_architecture_index.md` | doc 13 추가 to active read order + roles table. |
| `common/docs/runtime/SESSION_HANDOFF_2026-05-02_PAPER_EVAL_MATRIX_PLAN.md` (this) | 본 핸드오프. |
| `common/docs/runtime/SESSION_HANDOFF.md` | index 갱신. |

### 디자인 핵심 (doc 13에서 발췌)

- **12 cells**: 1 baseline + 3 Class 1 (D1: direct_mapping/rule_only/llm_assisted) + 2 Class 2 generation (D2) + 2 ordering (D3) + 2 interaction model (D4) + 2 multi-turn refinement (opt-in policy flag).
- **30 trials per cell**: descriptive stats 충분. 12 × 30 = 360 trials, worst-case wall ~37시간 (대부분 trials는 초 단위로 끝남).
- **Per-cell scenarios**: P2.6에서 tagged된 scenarios만 사용. orchestrator가 tag 일관성 검증 후 trial 실행.
- **Reproducibility anchors**: 각 sweep run이 matrix file SHA + scenarios dir SHA + policy_table SHA를 manifest에 기록 → 같은 commit set으로 figure 재생성 가능.
- **No new authority surface**: 모든 작업이 기존 `POST /package_runs` + `POST /package_runs/{id}/trial`을 통해. validator/dispatcher 우회 0.
- **No paper-ready conclusions in toolchain**: 도구는 *measurements*만 produce. 해석 (effect sizes, narratives, claims)은 paper author 책임.

### Phase split (doc 13 §9)

| Phase | PR | Deliverable |
|-------|-----|-------------|
| 0 | this PR | Design doc + matrix_v1.json + handoff |
| 1 | next | `paper_eval/sweep.py` orchestrator CLI + library + tests |
| 2 | after | `paper_eval/aggregator.py` cross-run aggregator + tests |
| 3 | after | `paper_eval/digest.py` CSV + Markdown exporter + tests |
| 4 | optional | Dashboard sweep-progress UI (deferred until 1–3 prove the toolchain) |

각 implementation PR은 self-contained: Phase 0 (this) 의존, 후속 phase 미의존. Phase 1, 2, 3 land 순서 유연.

### Test plan

```bash
# Matrix v1 self-validation (sanity)
python -c "
import json, pathlib
matrix = json.load(open('integration/paper_eval/matrix_v1.json'))
assert len(matrix['cells']) == 12
known_conds = {'direct_mapping','rule_only','llm_assisted','class2_static_only','class2_llm_assisted','class2_scan_source_order','class2_scan_deterministic','class2_direct_select_input','class2_scanning_input', None}
for c in matrix['cells']:
    assert c['comparison_condition'] in known_conds
    for s in c['scenarios']:
        assert pathlib.Path('integration/scenarios') / s
print('OK')
"

# Existing suites unchanged
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 700 passed (unchanged)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (unchanged)
```

### Files touched

```
common/docs/architecture/13_paper_eval_matrix_plan.md (new)
common/docs/architecture/00_architecture_index.md (index entry)
integration/paper_eval/matrix_v1.json (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_PAPER_EVAL_MATRIX_PLAN.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 누적 진행 상황 (post-doc-12 + paper-eval Phase 0)

doc 12 (interaction model, ordering, refinement) 완료 후 작업 sequence:

1. **post-doc-12 backfill** (PRs #112–#120) — docs/contracts/scenarios/manifest/dashboard 정합성 회복. 8 PRs.
2. **sc01 relocation** (PR #121) — payload fixture canonical 위치로 이동.
3. **paper-eval matrix plan** (this PR) — 운영 layer roadmap + matrix v1.

다음 라운드: doc 13 Phase 1 — sweep orchestrator. `paper_eval/sweep.py` CLI + library + tests. 기존 dashboard API만 호출 (새 endpoint 없음).

### Notes

- doc 13은 doc 11 / doc 12와 같은 design-then-implement 패턴. Phase 0 design이 maintainer 검토 후 Phases 1–3 자동 진행 가능.
- matrix v1은 **immutable**: matrix_v2가 필요하면 sibling 파일 (`matrix_v2.json`)로 추가, v1 보존. 이전 paper figures 재생성 가능성 보장.
- `_policy_overrides` (multi-turn cells에서 사용)는 orchestrator가 sweep 시작 전 정책 flag 확인 후 cell 실행 여부 결정. 잘못된 deployment 환경에서 silent run 방지.
- Open questions (doc 13 §11): trials per cell (30 vs 100), Phase 4 dashboard UI 필요성, matrix versioning convention. 모두 측정 데이터 후 결정.
