# SESSION_HANDOFF — Paper-Eval Phase 3 Digest Exporter

**Date:** 2026-05-02
**Tests:** rpi 235/235 (was 214; +21 new). mac_mini 700/700 unchanged.
**Schema validation:** none modified. Digest is a pure consumer of aggregated_matrix.json.

**Plan baseline:** Phase 3 of `13_paper_eval_matrix_plan.md`. Builds on Phase 2 (PR #125 — cross-run aggregator), Phase 1 (PR #123 — sweep orchestrator), Phase 0 (PR #122 — design + matrix v1). Closes the toolchain: matrix file → sweep → aggregator → digest → paper-ready CSV + Markdown.

---

## 이번 세션의 범위

doc 13 §8에서 sketch한 paper digest exporter 구현. aggregated_matrix.json (Phase 2 출력)을 입력으로 받아 paper-ready CSV (one row per cell) + Markdown (sub-grid 그루핑 + reproducibility footer) 산출. paper 작성자가 figure / table에 직접 인용 가능.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `rpi/code/paper_eval/digest.py` (신규) | 전체 digest exporter. **Loader**: `load_aggregated(path)` — JSON parse + 최소 structural 검증 (cells field). **CSV**: `to_csv(matrix)` — `_CSV_COLUMNS` 18-필드 stable schema (cell_id, condition, scenarios, n_trials, pass_rate, by_route_class_class0/1/2/unknown, latency p50/p95, class2_clarification_correctness, scan_history_yes_first_rate, scan_history_present_count, scan_ordering_applied_present_count, skipped, incomplete, notes). 새 필드는 마지막에 append-only — 기존 paper 코드 깨지지 않음. None은 빈 string으로 (스프레드시트에서 수치 파싱 안전). **Markdown**: `to_markdown(matrix)` — 3 sub-grid 그루핑: Baseline / Class 1 — Intent Recovery (D1) / Class 2 — Candidate Source × Ordering × Interaction (D2 × D3 × D4). 각 sub-grid는 cell_id 접두사로 매칭 (`BASELINE`, `C1_*`, `C2_*`); 매칭 안 되는 cell은 "Other cells" 섹션에 노출 (사일런트 드롭 방지). Footer는 anchor_commits (matrix_file_sha / scenarios_dir_sha / policy_table_sha) + sweep timing — 동일 anchor_commits → 동일 input → digest 재생성 가능. None 값은 em-dash로 (zero와 시각적으로 구분). **Filename convention**: `digest_<matrix_version>_<timestamp>.{csv,md}` — `time.strftime("%Y%m%d_%H%M%S")` 기본, `--timestamp` 오버라이드. **CLI**: `python -m paper_eval.digest --aggregated ... --output-dir ...`. exit code: 0 success, 1 aggregated 파일 없음/malformed. |
| `rpi/code/tests/test_paper_eval_digest.py` (신규) | 21 테스트. **TestLoadAggregated** 3 (missing file, missing cells, minimal valid). **TestFlattenCellForCsv** 2 (full cell flatten 정확, None → 빈 string). **TestToCsv** 3 (header가 _CSV_COLUMNS와 정확히 일치, one row per cell, empty matrix → header only). **TestToMarkdown** 6 (3 sub-grid 모두 출력, anchor commits in footer, unresolved → 'unresolved' string, unmatched cell_id → "Other cells", None → em-dash, empty sub-grid → "no cells" 메시지). **TestWriteDigest** 3 (filename convention 정확, missing matrix_version → "unknown" fallback, content round-trip). **TestEndToEnd** 1 — Sweeper → write_manifest → aggregate → write_digest 전체 파이프라인 → matrix v1 12 cells 모두 CSV row + Markdown 3-subgrid 정확. **TestCLI** 3 (--help, missing aggregated → exit=1, clean run → both files written). |

### 디자인 원칙

- **Boundary**: digest는 dashboard / runner / aggregator instance를 호출하지 않는다. aggregated_matrix.json만 읽는 순수 함수형 모듈. 출력은 사람-읽기 좋은 텍스트지만 interpretation 0 ("static_only is worse than llm_assisted" 같은 결론은 paper 작성자 몫).
- **Stable CSV column order (`_CSV_COLUMNS`)**: 새 metric 추가 시 끝에만 append. 기존 paper figure 코드가 column-name으로 인덱싱해도 안 깨짐. 명시적 제약사항으로 docstring + 테스트로 박힘.
- **Sub-grid grouping by cell_id prefix**: `BASELINE`, `C1_*`, `C2_*`. 매칭 안 되는 cell은 사일런트 드롭하지 않고 "Other cells" 섹션으로 — typo / 새 cell_id 컨벤션 추가 시에도 반드시 출력에 보임.
- **None vs zero 구분**: CSV에선 None → empty string (수치 파싱 안전); Markdown에선 None → em-dash (시각적 구분). 0.0이 "0% rate"로 잘못 읽히는 경우 방지.
- **Reproducibility footer**: anchor_commits (3개 SHA) + sweep window timing이 모든 markdown digest에 박힘. 같은 anchor → 같은 digest 재생성 가능 (doc 13 §3 reproducibility-first 원칙).
- **Filename has matrix_version**: matrix_v2가 도입되면 digest_v1_*.{csv,md} / digest_v2_*.{csv,md} 가 한 디렉토리에 공존. v1은 immutable.
- **Output: text only.** 그래픽 figure는 paper 측 코드가 CSV에서 생성. digest 자체는 plot 안 함.

### 사용 예시

```bash
# 1. Phase 1: sweep 실행
PYTHONPATH=rpi/code python -m paper_eval.sweep \
    --matrix integration/paper_eval/matrix_v1.json \
    --output runs/$(date +%Y%m%d_%H%M%S)/ \
    --node-id <virtual-context-node-id>

# 2. Phase 2: aggregate
PYTHONPATH=rpi/code python -m paper_eval.aggregator \
    --manifest runs/<timestamp>/sweep_manifest.json \
    --output runs/<timestamp>/aggregated_matrix.json

# 3. Phase 3: digest (NEW)
PYTHONPATH=rpi/code python -m paper_eval.digest \
    --aggregated runs/<timestamp>/aggregated_matrix.json \
    --output-dir runs/<timestamp>/digest/ \
    --verbose

# 출력:
#   runs/<timestamp>/digest/digest_v1_<ts>.csv  ← paper 작성자가 pivot/plot
#   runs/<timestamp>/digest/digest_v1_<ts>.md   ← paper 본문 직접 인용 가능
```

### Boundary 영향

없음. canonical asset 미수정. dashboard / runtime 변경 0. paper-eval 모듈 전체 (sweep + aggregator + digest)가 read-only consumer chain.

### Test plan

```bash
cd rpi/code && python -m pytest tests/test_paper_eval_digest.py -v
# 21 passed in 0.35s

cd rpi/code && python -m pytest tests/ -q
# 235 passed (was 214; +21 new digest tests)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 700 passed (unchanged)

# CLI smoke
PYTHONPATH=rpi/code python -m paper_eval.digest --help
# (clean usage output)
```

### Files touched

```
rpi/code/paper_eval/digest.py (new)
rpi/code/tests/test_paper_eval_digest.py (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_PAPER_EVAL_PHASE3_DIGEST.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (doc 13 §9)

doc 13 phase 0–3가 모두 ship됨. 남은 항목:

- **Phase 4 (deferred)** — dashboard sweep-progress UI. operator-CLI가 충분한지 사용 후 결정. doc 13 §11 open question #2.
- **Operations**: 실제 sweep 1회 실행 → digest 생성 → variance 측정. doc 13 §11 open question #1 (30 trials/cell이 충분한 noise floor인지) 답변.
- **doc 13 자체 업데이트**: §9 Phase split 표에 Phase 1/2/3 PR# 채우고 status 갱신 가능.

paper-eval 도구 측에서는 유의미한 다음 작업 없음 — variance가 부족하다면 v1 트라이얼 수 늘리거나 matrix_v2 분기.

### Notes

- digest CSV header `_CSV_COLUMNS`는 18 필드 — 첫 sweep 후 paper 작성자가 추가 metric 요청하면 append-only로 확장. 기존 column 순서/이름 변경 금지.
- Markdown 표는 paper-table density를 위해 9 컬럼만 (cell_id / condition / n / pass / p50 / p95 / class2 ✓ / scan-yes-first / notes). 전체 by_route_class breakdown은 CSV에. paper 작성자가 markdown 표를 그대로 paper 본문에 복사할 수 있도록 의도된 디자인.
- `_SUB_GRIDS`는 module-level constant. 새 sub-grid 추가/순서 변경은 명시적 코드 수정 — 의도된 stability.
- 12 cells × 30 trials → CSV ~3KB, Markdown ~5KB. paper-friendly 사이즈.
- end-to-end 테스트(TestEndToEnd)는 Sweeper → manifest → aggregate → digest 전체 파이프라인을 fake DashboardClient 위에서 1초 안에 검증. CI 부담 0.
