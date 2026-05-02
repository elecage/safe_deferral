# SESSION_HANDOFF — Paper-Eval Phase 1 Sweep Orchestrator

**Date:** 2026-05-02
**Tests:** rpi 185/185 (was 168; +17 new in test_paper_eval_sweep.py). mac_mini 700/700 unchanged.
**Schema validation:** none modified. matrix_v1.json self-validation runs as part of orchestrator startup.

**Plan baseline:** Phase 1 of `13_paper_eval_matrix_plan.md`. Builds on Phase 0 (PR #122 — design + matrix v1) and the post-doc-12 backfill (#112-#121). Implements the orchestrator that reads matrix_v1.json and drives the dashboard HTTP API to run all 12 cells end-to-end.

---

## 이번 세션의 범위

doc 13 §6에서 sketch한 Sweep Orchestrator 구현. 기존 dashboard HTTP API (`POST /package_runs`, `POST /package_runs/{id}/trial`, `GET /package_runs/{id}`, `GET /package_runs/{id}/metrics`, `GET /nodes`, `GET /health`)만 호출 — runner / validator / dispatcher 우회 0. Sequential cells, sequential trials within cell. CLI + library API 양쪽 제공.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `rpi/code/paper_eval/__init__.py` (신규) | 패키지 docstring + import 안내. Lazy 형태로 (CLI 실행 시 RuntimeWarning 방지). |
| `rpi/code/paper_eval/sweep.py` (신규) | 전체 orchestrator. **Data model**: `Cell`, `MatrixSpec`, `CellRunResult`, `SweepResult` dataclasses. **Loader**: `load_matrix(path, scenarios_dir)` — JSON parse + structural 검증 (필수 field, comparison_condition enum 매칭, scenario file 존재, trials_per_cell ≥ 1). **HTTP**: `DashboardClient` (requests-based wrapper). **Validation**: `_validate_cell_scenario_tags(cell, scenarios_dir)` — P2.6 invariant 재사용 (cell의 condition이 각 scenario의 comparison_conditions[]에 포함되는지). **Sweeper**: `Sweeper.run() → SweepResult`. 사전 검사 (dashboard health + node 존재) → 12 cells 순차 처리 → cell당 (a) tag 검증 (실패 시 skipped+reason), (b) `POST /package_runs` 1회, (c) `POST /package_runs/{id}/trial` N회 (round-robin scenarios), (d) `GET /package_runs/{id}` polling until 모든 trial completed or per-cell deadline 초과 → manifest 작성. **CLI**: `python -m paper_eval.sweep --matrix ... --output ... --node-id ...`. exit code: 0 success, 1 dashboard 못 시작, 2 일부 cell skipped/incomplete. **Reproducibility**: `resolve_anchor_commits()`로 git rev-parse 3개 (matrix file, scenarios dir, policy_table) 자동 캡처해서 manifest 기록. |
| `rpi/code/tests/test_paper_eval_sweep.py` (신규) | 17 테스트. **TestLoadMatrix** 5 (real matrix v1 loads, missing field raises, unknown condition raises, missing scenario raises, zero trials raises). **TestValidateCellScenarioTags** 4 (BASELINE 면제, 정상 tagged 통과, mistagged 에러, 누락 scenario 에러). **TestSweeperHappyPath** 2 (real matrix v1 sweep 12 cells × 30 trials = 360 calls; manifest JSON write). **TestSweeperFailureModes** 4 (dashboard unreachable raises before progress, missing node raises before progress, mistagged cell skipped with reason, run never completes marks incomplete). **TestCLI** 2 (--help, dashboard unreachable returns nonzero). 모든 테스트 fake `DashboardClient` (MagicMock spec) 사용 — 실제 네트워크 0. |

### 디자인 원칙

- **Boundary**: 새 endpoint, 새 schema, 새 권한 surface 모두 0. 기존 dashboard API contract 그대로 사용.
- **Fail fast**: dashboard 미동작 / node 부재 시 cell 처리 시작 전에 raise. half-run 방지.
- **Skip with reason**: tag 검증 실패한 cell은 skip하고 manifest에 사유 기록 — 나머지 cells는 계속 진행. 한 cell 실패가 sweep 전체를 멈추지 않음.
- **Reproducibility**: 모든 sweep manifest에 git SHA 3개 (matrix / scenarios / policy_table) 포함. 같은 commit set으로 figure 재생성 가능.
- **Sequential simplicity**: cells / trials 모두 순차. concurrency / retry / resume 모두 future work — Phase 1은 정확성 우선.
- **Output: machine-readable JSON only.** 사람-읽기 좋은 digest는 Phase 3 (digest exporter)에서.

### 사용 예시

```bash
# Operator: virtual node 미리 생성 후 sweep 실행
PYTHONPATH=rpi/code python -m paper_eval.sweep \
    --matrix integration/paper_eval/matrix_v1.json \
    --output runs/$(date +%Y%m%d_%H%M%S)/ \
    --node-id <virtual-context-node-id> \
    --dashboard-url http://localhost:8000 \
    --verbose

# 출력: runs/<timestamp>/sweep_manifest.json
# 다음 단계 (Phase 2 aggregator)가 이 manifest를 입력으로 받음.
```

### Boundary 영향

없음. canonical asset 미수정. dashboard / runtime 변경 0. paper-eval 모듈은 read-only consumer.

### Test plan

```bash
cd rpi/code && python -m pytest tests/test_paper_eval_sweep.py -v
# 17 passed in 0.75s

cd rpi/code && python -m pytest tests/test_rpi_components.py tests/test_paper_eval_sweep.py -q
# 185 passed (was 168; +17 new)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 700 passed (unchanged)

# CLI smoke
PYTHONPATH=rpi/code python -m paper_eval.sweep --help
# (clean usage output)
```

### Files touched

```
rpi/code/paper_eval/__init__.py (new)
rpi/code/paper_eval/sweep.py (new)
rpi/code/tests/test_paper_eval_sweep.py (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_PAPER_EVAL_PHASE1_SWEEP_ORCHESTRATOR.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (doc 13 §9)

- **Phase 2** — `paper_eval/aggregator.py`: sweep_manifest.json + per-run metrics를 입력 → cell별 통합된 `CellResult` (pass_rate, p50/p95 latency, by_route_class, scan-specific metrics) → `AggregatedMatrix` dataclass.
- **Phase 3** — `paper_eval/digest.py`: AggregatedMatrix를 paper-ready CSV + Markdown으로.
- **Phase 4** (deferred) — dashboard sweep-progress UI.

Phase 2/3는 self-contained. 어느 것부터 할지 사용자가 선택.

### Notes

- CLI exit code 2 (cell skipped/incomplete)는 운영자에게 "sweep 끝났지만 일부 cell 문제 있음" 신호. CI에서 사용 시 0만 success로 처리.
- `_KNOWN_COMPARISON_CONDITIONS`가 `paper_eval/sweep.py`에 mirror됨 (Package A definition으로부터). 9개 condition이 늘어나면 두 곳 동기화 필요 — 명시적 design choice 유지 (paper_eval은 rpi.experiment_package 경로 의존성 없음).
- `resolve_anchor_commits()`는 git 미설치 / non-repo 환경에서 None 반환 (defensive). 운영 환경 가정 git 있음.
- per-cell deadline = `per_trial_timeout_s × trials_per_cell` — sequential 가정. concurrent trial 들어가면 재계산 필요 (Phase 1 scope 밖).
