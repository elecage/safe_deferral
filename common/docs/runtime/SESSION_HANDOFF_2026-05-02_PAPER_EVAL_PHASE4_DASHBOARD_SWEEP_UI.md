# SESSION_HANDOFF — Paper-Eval Phase 4 Dashboard Sweep UI (MVP)

**Date:** 2026-05-02
**Tests:** rpi 291/291 (was 257; +34 new). mac_mini 711/711 unchanged.
**Schema validation:** none modified. Phase 4 is purely additive (dashboard layer + thread runner) on top of the Phases 1–3 pure-function pipeline.

**Plan baseline:** Closes the previously-deferred Phase 4 of `13_paper_eval_matrix_plan.md`. Operator can now start a 12-cell matrix sweep from the dashboard, watch live per-cell progress, and download manifest / aggregated_matrix / digest (CSV + Markdown) — all from the existing dashboard UI without touching the CLI.

---

## 이번 세션의 범위

doc 13 §9 Phase 4를 MVP scope으로 closure. CLI 3-step (sweep / aggregator / digest)을 dashboard에서 한 화면 + 한 클릭으로 실행하고 진행률을 표시하며 결과 artifact 4개를 download할 수 있게 함.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `rpi/code/paper_eval/sweep.py` | **Additive — 기존 Sweeper API backward compat 유지.** `SweepProgressEvent` dataclass + `SweepCancelled` 예외 신규. `Sweeper.__init__`에 optional `progress_callback` + `cancel_check` 파라미터. `Sweeper.run/_run_cell`이 sweep_started / cell_started / cell_progress / cell_completed / cell_skipped / sweep_completed 6 종 이벤트 emit. cancel_check는 셀 사이 + 셀 polling loop 내부에서 polled. 기존 callers (CLI / Phase 1/2/3 tests)는 모두 callback 없이 호출 → no-op default. |
| `rpi/code/paper_eval/sweep_runner.py` (신규) | `SweepRunner` — single-slot background thread wrapper. `start()` spawns thread, `cancel()` sets event, `get_state()`은 thread-safe SweepState dict. State는 sweep_id, status (idle/running/cancelling/completed/cancelled/failed), per-cell `CellProgress` 리스트, manifest_path / aggregated_path / digest_csv_path / digest_md_path. 워커 스레드가 sweep → aggregate → digest 3 단계를 직렬로 실행하고 모든 artifact path를 state에 채워둠. `sweeper_factory` injection으로 테스트가 fake Sweeper substitution 가능. 예외는 모두 status=failed + error 문자열로 captured (UI에서 표시 가능). |
| `rpi/code/dashboard/app.py` | **6개 신규 endpoint** under `/paper_eval/sweeps/` — POST start (matrix_path + node_id + optional timeouts → 200 / 400 / 404 / 409 / 503), GET current (status + cells + paths), POST current/cancel (idempotent on idle), GET current/manifest (JSONResponse), GET current/aggregated (JSONResponse), GET current/digest.csv (PlainTextResponse text/csv), GET current/digest.md (PlainTextResponse text/markdown). `create_app(...)`에 optional `sweep_runner` 파라미터 추가 — None일 때 모든 endpoint 503 응답 (테스트 환경 등). |
| `rpi/code/main.py` | `SweepRunner` 인스턴스화 (repo_root / scenarios_dir / runs_root / dashboard_url) + `create_app(sweep_runner=...)` 전달. `pathlib` import 추가. |
| `rpi/code/dashboard/static/index.html` | **신규 ⑤ Paper-Eval Sweep 섹션.** Nav 항목 5번째로 추가, sweep config 폼 (matrix path / node ID / per-trial timeout / poll interval) + Start/Cancel 버튼, 상태 바 (status / sweep_id / 셀 진행률 / 시작/종료 시각), 셀별 진행률 표 (12행), artifact card (4 download links). JS: `paperEvalStart()` / `paperEvalCancel()` / `paperEvalRefresh()` / 2초 주기 poll (`startPaperEvalPoll` / `stopPaperEvalPoll` — section 진입/이탈 시). 상태 색깔 + 한국어 레이블, 빈 label은 em-dash 처리. |
| `rpi/code/tests/test_paper_eval_sweep.py` | **+9 테스트** (TestProgressCallback ×6, TestCancelHook ×3) — callback default no-op (backward compat), sweep_started/completed 순서, cell_started/completed 12 sets, skipped 셀에 cell_skipped+reason, progress 이벤트의 completed_trials 정확, callback 예외가 sweep을 중단하지 않음, cancel before/after first cell, no-cancel-default 전체 실행. |
| `rpi/code/tests/test_paper_eval_sweep_runner.py` (신규) | **8 테스트** — initial state idle, single-slot 두 번째 start RuntimeError, happy path 모든 artifact path 파일 존재, 진행 이벤트가 cells에 반영, cancel mid-run → status=cancelled, 외부 cancel signal → cancelling→cancelled, idle cancel no-op, sweeper exception → status=failed + error 문자열. `_FakeSweeper`를 `sweeper_factory` injection으로 substitute하여 real network 0. |
| `rpi/code/tests/test_dashboard_paper_eval_endpoints.py` (신규) | **17 테스트** — TestNoRunnerWired ×2 (503), TestStartSweep ×6 (400/404/200/409/relative-path resolution), TestStatusAndCancel ×3 (idle/completed/cancel-idle), TestArtifactDownloads ×5 (404 before completion, manifest/aggregated JSON, digest CSV/Markdown text), **TestNoNewAuthoritySurface ×1** (boundary invariant — `/paper_eval` paths의 actuation/command/publish/doorlock substring 자동 차단). FastAPI TestClient 사용. |
| `common/docs/runtime/SESSION_HANDOFF_2026-05-02_PAPER_EVAL_PHASE4_DASHBOARD_SWEEP_UI.md` (신규) | 본 핸드오프. |
| `common/docs/runtime/SESSION_HANDOFF.md` | index 업데이트. |

### 디자인 원칙

- **Single-slot model**: 한 번에 하나 sweep만. operational reality (한 명 운영자, 한 Mac mini stack) 반영. 큐잉 / 동시 실행 / DB 영속화 모두 deferred — 사용 패턴 보고 결정.
- **Additive callback contracts**: Sweeper의 progress_callback / cancel_check는 모두 default no-op. 기존 18 sweep 테스트 + Phase 2/3 모듈 모두 코드 변경 없이 통과 (35 callback/runner 신규 테스트와 함께 67 → 102 paper_eval 테스트).
- **Boundary invariant as test**: 새 endpoint 추가 시 actuation/command/publish/doorlock substring 자동 거부. governance UI의 동일 패턴과 일관.
- **Defensive thread state**: 워커가 모든 예외 capture → status=failed + error string. UI가 server crash 추측 안 함 — explicit error 표시.
- **Optional dashboard wiring**: `create_app(sweep_runner=None)`이면 endpoints 503. 기존 test 환경 (fake/no runner)에서 deps 충돌 없음.
- **Relative matrix path resolution**: dashboard UI 사용자가 `integration/paper_eval/matrix_v1.json` 같은 repo-relative path 입력 가능 — endpoint가 repo_root 기준 resolve.
- **Artifact path serving, not in-memory**: 파일 시스템에 쓴 manifest/aggregated/digest를 endpoint가 read+stream. crash 후 재시작해도 path만 보존되면 access 가능 (state는 휘발).

### UI 흐름 (사용자 시나리오)

1. Nav "⑤ Paper-Eval Sweep" 클릭
2. matrix path = `integration/paper_eval/matrix_v1.json` (default), node ID 입력 (사전에 생성된 virtual node)
3. "▶ Sweep 시작" → 상태 RUNNING + 12 cells 표가 행별로 채워짐
4. 셀이 완료될 때마다 progress 이벤트 → 표의 해당 행 status 갱신
5. sweep 완료 → status COMPLETED + 4개 download link 자동 표출
6. CSV/Markdown 직접 다운로드하여 paper figure / table 작성

### Boundary 영향

없음. canonical asset 미수정. dashboard / runtime 변경 0. paper-eval 모듈 전체 (sweep + aggregator + digest + sweep_runner)는 read-only consumer chain 유지. dashboard endpoint는 GovernanceBackend 패턴과 동일하게 boundary invariant test로 enforce.

### Test plan

```bash
cd rpi/code && python -m pytest tests/test_paper_eval_sweep.py tests/test_paper_eval_sweep_runner.py tests/test_dashboard_paper_eval_endpoints.py -v
# 27 + 8 + 17 = 52 passed

cd rpi/code && python -m pytest tests/ -q
# 291 passed (was 257; +34 new — 9 sweep callback + 8 runner + 17 endpoint)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 711 passed (unchanged)
```

수동 smoke check (실제 dashboard 띄울 때):
```bash
# 1. RPi dashboard 실행
PYTHONPATH=rpi/code python rpi/code/main.py
# 2. http://localhost:8888 접속, "⑤ Paper-Eval Sweep" 탭
# 3. 사전에 virtual node 하나 생성 (탭 ②)
# 4. matrix path / node ID 입력 → ▶ Sweep 시작
# 5. 12 cells × 30 trials 진행률 live 관찰
# 6. 완료 후 manifest / aggregated / digest CSV / digest MD 다운로드
```

### Files touched

```
rpi/code/paper_eval/sweep.py (additive — progress_callback + cancel_check)
rpi/code/paper_eval/sweep_runner.py (new)
rpi/code/dashboard/app.py (+6 endpoints + sweep_runner param)
rpi/code/main.py (SweepRunner instantiation + wiring)
rpi/code/dashboard/static/index.html (+nav item, +section, +JS)
rpi/code/tests/test_paper_eval_sweep.py (+9 callback/cancel tests)
rpi/code/tests/test_paper_eval_sweep_runner.py (new, 8 tests)
rpi/code/tests/test_dashboard_paper_eval_endpoints.py (new, 17 tests)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_PAPER_EVAL_PHASE4_DASHBOARD_SWEEP_UI.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계

Paper-eval toolchain phase 0–4 모두 ship. 남은 활동:
- **Operations** — Mac mini stack을 띄운 실제 sweep 1회 → variance 측정 → doc 13 §11 open question #1 (30 trials/cell 적정성) 답변. 이 PR이 dashboard-driven 운영 가능하게 만든 prerequisite.
- **doc 13 ship-state 갱신** — §9 Phase split 표의 Phase 4 row를 'shipped (#PR번호)'로 업데이트 (cosmetic).
- **확장 옵션** (사용 패턴 보고 결정):
  - 동시 sweep 여러 개 + 큐
  - sweep 히스토리 영속화 (현재는 휘발 in-memory state, artifact는 파일에)
  - 차트 (시간별 trial 누적, 셀별 latency 분포)
  - sweep 결과 끼리 비교 view

### Notes

- `sweep_runner.py`의 `SweepRunner._on_event`가 main lock 안에서 cells 리스트 mutate. UI poll이 같은 lock으로 dict snapshot — torn read 없음.
- `_FakeSweeper`가 SweepResult-shaped dict (cells에 trials_snapshot 포함)을 반환해야 aggregator가 정상 동작 (trials_snapshot이 Phase 2 enabler — manifest 단독으로 aggregation). 테스트 fake가 이걸 생략하면 aggregated_path는 생성되지만 모든 cell n_trials=0.
- UI의 2초 poll 주기는 trade-off: 더 짧으면 server 부하 증가, 더 길면 UX 반응성 저하. operational use 후 tuning 가치 있음.
- `/paper_eval/sweeps/current/manifest`가 JSONResponse로 dict를 그대로 반환 — 큰 sweep manifest (12 cells × 30 trials × ~5KB ≈ 1.8MB)이지만 download이라 무리 없음. 향후 streaming이 필요하면 PlainTextResponse로 raw text 반환으로 변경 가능.
- `pathlib` import를 main.py에 추가했지만 이미 다른 곳에서 동일 모듈을 사용 중일 수도 있음 — 중복 import는 Python에서 무해. 명시적 import가 코드 가독성에 더 좋음.
