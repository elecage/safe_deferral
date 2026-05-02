# SESSION_HANDOFF — Paper-Eval Phase 2 Cross-Run Aggregator

**Date:** 2026-05-02
**Tests:** rpi 214/214 (was 185; +29 new). mac_mini 700/700 unchanged.
**Schema validation:** none modified. Aggregator is a pure consumer of the manifest produced by Phase 1.

**Plan baseline:** Phase 2 of `13_paper_eval_matrix_plan.md`. Builds on Phase 1 (PR #123 — sweep orchestrator) and Phase 0 (PR #122 — design + matrix v1). Implements the cross-run aggregator that joins per-cell trial snapshots into a matrix-shaped `AggregatedMatrix` for the Phase 3 digest exporter.

---

## 이번 세션의 범위

doc 13 §7에서 sketch한 cross-run aggregator 구현. sweep_manifest.json을 입력으로 받아 cell당 `CellResult` 산출, 전체 `AggregatedMatrix`로 묶어 Phase 3 digest의 입력으로 제공. 외부 의존성 0 (dashboard 호출 없음, 완전 오프라인).

### 변경 요약

| 파일 | 변경 |
|---|---|
| `rpi/code/paper_eval/sweep.py` | **CellRunResult에 4 필드 추가** (additive — 기존 manifest reader는 그대로 호환): `trials_snapshot` (Phase 2 enabler — `GET /package_runs/{run_id}` 결과 캡처), `scenarios`, `expected_route_class`, `expected_validation` (cell-level 메타데이터 — manifest 단독으로 aggregator가 reasoning 가능). `_run_cell()`이 metrics_snapshot 다음에 `client.get_package_run(run_id)` 호출하여 trials_snapshot 채움. skip된 cell은 trials_snapshot=None. |
| `rpi/code/paper_eval/aggregator.py` (신규) | 전체 aggregator. **Data model**: `CellResult` (cell_id, comparison_condition, scenarios, n_trials, pass_rate, by_route_class, latency_ms_p50/p95, class2_clarification_correctness, scan_history_yes_first_rate, scan_history_present_count, scan_ordering_applied_present_count, skipped, incomplete, notes), `AggregatedMatrix` (matrix_version, matrix_path, sweep_started/finished_at_ms, anchor_commits, cells, cell_by_id() helper). **Loader**: `load_sweep_manifest(path)` — JSON parse + 최소 structural 검증 (cells field, matrix_version field). **Primitives**: `_percentile()` (nearest-rank, _metrics_b 스타일), `_completed_trials()` (status=='completed' 필터), `_by_route_class()` (CLASS_0/1/2/unknown 4-bucket), `_scan_history_yes_first_rate()` (deterministic ordering 효과 측정용 proxy), `_scan_ordering_applied_present_count()` (presence count, v1 — 매칭 검증은 Phase 3로 deferred), `_class2_clarification_correctness()` (expected CLASS_2 trials 중 observed CLASS_2 + payload 둘 다 만족 fraction). **Orchestration**: `_aggregate_cell(cell_dict)` → CellResult, `aggregate(manifest)` → AggregatedMatrix, `write_aggregated()`. **CLI**: `python -m paper_eval.aggregator --manifest ... --output ...`. exit code: 0 모두 깨끗, 1 manifest 못 읽음, 2 일부 cell skipped/incomplete (CI에서 0만 success로 처리). |
| `rpi/code/tests/test_paper_eval_sweep.py` | **+1 테스트** (`test_manifest_carries_trials_snapshot_for_phase2`) — non-skipped cell이 모두 trials_snapshot/scenarios/expected_* 채우는지 검증. Phase 2 의존성 회귀 방지. |
| `rpi/code/tests/test_paper_eval_aggregator.py` (신규) | 28 테스트. **TestLoadSweepManifest** 4 (missing file, missing cells, missing matrix_version, minimal valid). **TestPercentile** 3 (empty, single value, p50/p95 of 1..10). **TestCompletedTrials** 2 (filters non-completed, handles None). **TestByRouteClass** 3 (3 canonical classes + unknown 버킷, unknown string → unknown bucket, empty → zero counts). **TestScanHistoryYesFirstRate** 2 (no history → None, mixed yes/no first → fraction 정확). **TestScanOrderingAppliedPresentCount** 1 (empty list ≠ presence). **TestClass2ClarificationCorrectness** 2 (no expected → None, mixed pass/fail trials → fraction). **TestAggregateCell** 4 (skipped → zero metrics + note, incomplete → completed-only aggregation, missing trials_snapshot → note for older manifest, full Class 2 scanning cell → 모든 metric 정확). **TestAggregate** 2 (synthetic manifest round-trip, write_aggregated round-trip). **TestEndToEnd** 1 — Sweeper로 fake client로 sweep → write_manifest → load_sweep_manifest → aggregate full pipeline 실행 → matrix v1 12 cells 모두 30 trial로 채워진 AggregatedMatrix 검증. **TestCLI** 4 (--help, missing manifest exit=1, clean aggregation exit=0, skipped cell exit=2). |

### 디자인 원칙

- **Boundary**: aggregator는 dashboard / runner / validator / dispatcher를 호출하지 않는다. sweep_manifest.json만 읽는 순수 함수형 모듈. Phase 3 (digest) 마찬가지.
- **Offline-first**: sweep finish time에 trials_snapshot을 manifest에 박아둠으로써 sweep 종료 후 aggregation까지 dashboard 가용성 의존 0. doc 13 §3 reproducibility 원칙과 정렬.
- **Lenient on older manifests**: trials_snapshot이 없는 manifest (Phase 1 직후 변경 전 형식)도 aggregator가 죽지 않고 n_trials=0 + 명시적 note로 변환. 사일런트 fail 없음.
- **Optional[float] for cell-condition-dependent fields**: scan_history_yes_first_rate / class2_clarification_correctness / latency_ms_p50/p95 등은 해당하지 않는 cell에서 None — 0.0이 아니라. 0.0은 "0% yes-first rate"라는 거짓 정보이기 때문.
- **Notes 채널**: skipped / incomplete / missing-snapshot 같은 운영 정보는 CellResult.notes에 human-readable string. digest는 표 footer에 그대로 노출하면 됨.
- **Sequential per-cell aggregation**: cell당 작업이 trial 수 × O(상수). 12 × 30 = 360 trials = ~ms. concurrent 필요 없음.
- **Output: machine-readable JSON only.** 사람-읽기 좋은 표는 Phase 3 (digest)에서.

### 사용 예시

```bash
# 1. Phase 1: sweep 실행 (이전 PR)
PYTHONPATH=rpi/code python -m paper_eval.sweep \
    --matrix integration/paper_eval/matrix_v1.json \
    --output runs/$(date +%Y%m%d_%H%M%S)/ \
    --node-id <virtual-context-node-id>

# 2. Phase 2: 위 결과 aggregate
PYTHONPATH=rpi/code python -m paper_eval.aggregator \
    --manifest runs/<timestamp>/sweep_manifest.json \
    --output runs/<timestamp>/aggregated_matrix.json \
    --verbose

# 출력: runs/<timestamp>/aggregated_matrix.json
# 다음 단계 (Phase 3 digest exporter)가 이 aggregated를 입력으로 받음.
```

### Boundary 영향

없음. canonical asset 미수정. dashboard / runtime 변경 0. paper-eval 모듈은 read-only consumer (sweep는 이미 read-only HTTP client; aggregator는 manifest read-only).

### Test plan

```bash
cd rpi/code && python -m pytest tests/test_paper_eval_sweep.py tests/test_paper_eval_aggregator.py -v
# 46 passed in 1.11s

cd rpi/code && python -m pytest tests/ -q
# 214 passed (was 185; +29 new: 28 aggregator + 1 sweep regression)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 700 passed (unchanged)

# CLI smoke
PYTHONPATH=rpi/code python -m paper_eval.aggregator --help
# (clean usage output)
```

### Files touched

```
rpi/code/paper_eval/sweep.py (additive: 4 fields + trials_snapshot fetch)
rpi/code/paper_eval/aggregator.py (new)
rpi/code/tests/test_paper_eval_sweep.py (+1 regression test)
rpi/code/tests/test_paper_eval_aggregator.py (new, 28 tests)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_PAPER_EVAL_PHASE2_AGGREGATOR.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (doc 13 §9)

- **Phase 3** — `paper_eval/digest.py`: AggregatedMatrix를 paper-ready CSV + Markdown으로. 입력은 aggregated_matrix.json (이번 PR 출력). doc 13 §8 sketch — sub-grid별 (Class 1 D1 / Class 2 D2×D3×D4 / baseline) 그루핑, anchor_commits를 footer에 표기.
- **Phase 4** (deferred) — dashboard sweep-progress UI.

Phase 3는 self-contained. Phase 2 직후 바로 진행 가능.

### Notes

- `trials_snapshot`을 manifest에 박는 결정은 sweep 종료 후 dashboard가 살아있어야 aggregation이 가능한 상황을 피하기 위함. sweep + aggregate를 하루 간격으로 운영해도 reproducible.
- `scan_ordering_applied_match_rate`는 spec (doc 13 §7)에 있지만 v1에서는 "presence count"만 측정. expected ordering vs applied ordering 매칭 비율은 Phase 3 digest가 cell의 `_policy_overrides` (e.g. `class2_scan_ordering_rules`)와 비교하는 게 자연스러워서 그쪽으로 deferred.
- `_completed_trials`는 `status=='completed'`만 통과시킴 — `'pending'` / `'timeout'`은 descriptive stat에 기여하지 않고 `incomplete` 플래그로만 추적. trial_store._metrics_a와 동일한 정책.
- `_percentile`은 trial_store._metrics_b의 nearest-rank 구현과 동일 — single-run dashboard metric과 paper-eval digest 값이 정확히 일치하도록 의도된 선택.
- `_class2_clarification_correctness`는 trial_store._metrics_a의 `class2_handoff_correctness`보다 **엄격함**: routing match뿐 아니라 clarification_payload 존재까지 요구. Class 2 routing이 일어났는데 payload 누락 = doc 4 contract 회귀이므로 이걸 디지털 세틀먼트 단계 metric으로 노출.
- 12-cell sweep × 30 trials × ~5KB trial dict ≈ 1.8MB manifest. 운영상 무리 없음.
