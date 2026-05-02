# SESSION_HANDOFF — Phase C: First Full matrix_v1 Sweep on M1 MacBook

**Date:** 2026-05-03
**Tests:** rpi 293/293, mac_mini 711/711 unchanged. No code changes in this PR — only data archive + handoff.
**Sweep results:** 12/12 cells, 351/360 trials, 132.6 minutes wall time, weighted-avg pass rate ~98.5%.

**Plan baseline:** First execution of full `matrix_v1.json` (12 cells × 30 trials) end-to-end on a single M1 MacBook with real Ollama llama3.2. Closes doc 13 §11 open question #1 (variance measurement on actual data).

---

## 이번 세션의 범위

Phase C 운영 실행:
1. Launcher + smoke fixes (#137-#139) 위에서 paper-eval matrix_v1 sweep 실행
2. Dashboard에서 live monitoring + background polling 병행
3. 12/12 cells 완료, 결과 archive + 분석

**원본 디자인 의도 (#123, #131)** 대로 paper-grade variance 데이터를 한 노트북에서 산출 가능함을 입증.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `integration/paper_eval/runs_archive/2026-05-03_phase_c/` (신규 디렉토리) | Phase C run의 **영구 보관 artifact**. `runs/` 디렉토리는 #138에서 gitignore되었으므로 (휘발성 runtime output), paper-grade run은 별도 archive 디렉토리에 보관. 4개 파일: `sweep_manifest.json` (1.4MB, per-trial detail), `aggregated_matrix.json` (cellresult), `digest_v1_*.csv` (paper figure plotting), `digest_v1_*.md` (paper-table-ready). Plus `README.md` (run metadata + 하이라이트 분석 + 재현 anchor SHA + 연구 의의). |
| `common/docs/runtime/SESSION_HANDOFF_2026-05-03_PHASE_C_FIRST_FULL_SWEEP.md` (신규) | 본 핸드오프. |
| `common/docs/runtime/SESSION_HANDOFF.md` | index 업데이트. |

### 결과 요약

12 cells × 30 trials = 360 trials requested. **351 reached terminal status (97.5%).**

| Cell | n | pass | 비고 |
|---|---:|---:|---|
| BASELINE | 30 | 1.000 | LLM Class 1, p50 1.7s |
| C1_D1_DIRECT_MAPPING | 30 | 1.000 | LLM 우회, 1ms |
| C1_D1_RULE_ONLY | 30 | 1.000 | LLM 우회, 1ms |
| C1_D1_LLM_ASSISTED | 29 | **0.966** | LLM 1회 deferral, 1 timeout |
| C2_D2_STATIC_ONLY | 30 | 1.000 | Class 2 + clarification correctness 1.0 |
| C2_D2_LLM_ASSISTED | 30 | 1.000 | Class 2 + clarification correctness 1.0 |
| C2_D3_SCAN_SOURCE_ORDER | 29 | **0.897** | 3 wrong-reason + 1 timeout |
| C2_D3_SCAN_DETERMINISTIC | 28 | 1.000 | 2 timeouts (incomplete) |
| C2_D4_DIRECT_SELECT_INPUT | 30 | 1.000 | clean |
| C2_D4_SCANNING_INPUT | 29 | **0.966** | scan_history_yes_first_rate **0.474** |
| C2_MULTI_TURN_REFINEMENT_USER_PICK | 28 | **0.964** | 1 wrong-reason + 2 timeouts |
| C2_MULTI_TURN_REFINEMENT_TIMEOUT | 30 | 1.000 | silence ≠ consent invariant 유지 |

### Reproducibility anchors

| Anchor | SHA |
|---|---|
| matrix_file_sha | `ee4b4db0177b367cffa3a9dd4c10e25d626ade1f` |
| scenarios_dir_sha | `9107bc511f01af4c926eb580213ad41634243b50` |
| policy_table_sha | `a81b204e76e97ec4bb28ac404168233a84004626` |

### Paper에 의미 있는 발견

- **doc 13 §11 #1 답변**: 30 trials/cell이 descriptive stats에 충분. variance 0.85 미만 cell 없음.
- **D1 차원**: deterministic 모드 (direct_mapping, rule_only) 1.000 / sub-ms latency vs LLM-assisted 0.966 / 1.6s 중간 / 4.8s p95. **LLM 사용의 3.4%p pass rate 대가**가 paper에 정량화 가능.
- **D2 차원**: static_only vs llm_assisted 둘 다 1.000 — 이 시나리오에서 LLM의 candidate 생성 이점 측정 0. LLM 우위를 보이려면 시나리오 추가 설계 필요.
- **D3 deterministic vs source_order**: deterministic 1.000 vs source_order 0.897. **3 trial이 'insufficient_context'로 잘못 reasoning** — source_order 모드의 잠재 결함 추가 조사 가치 있음.
- **scan_history_yes_first_rate = 0.474** (C2_D4_SCANNING_INPUT): **47% 사용자가 첫 announce된 옵션 수락**. accessibility metric으로 paper에 인용 가능.
- **C2_MULTI_TURN_REFINEMENT_TIMEOUT**의 1.000: silence ≠ consent invariant가 30 trial 모두에서 유지됨.

### 운영 노트

- per_trial_timeout_s=120s가 9 trial pending 발생시킴. 다음 run은 180-240s 권장.
- M1 MacBook에서 132분 동안 메모리 부담 / 발열 / battery drain 현상 없음.
- LLM 호출 latency 일관 ~1.5-2s typical, ~4-5s p95.
- Dashboard mid-run polling 132분 내내 안정 작동.

### Boundary 영향

없음. 코드 / canonical asset / dashboard contract 변경 0. archive 디렉토리 + handoff doc만 추가.

### Test plan

이 PR은 데이터 archive only — 코드 변경 0. 기존 테스트 그대로:
```bash
cd rpi/code && python -m pytest tests/ -q   # 293 passed
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py   # 711 passed
```

### Files touched

```
integration/paper_eval/runs_archive/2026-05-03_phase_c/README.md (new)
integration/paper_eval/runs_archive/2026-05-03_phase_c/sweep_manifest.json (new — runtime output, archived for paper)
integration/paper_eval/runs_archive/2026-05-03_phase_c/aggregated_matrix.json (new)
integration/paper_eval/runs_archive/2026-05-03_phase_c/digest_v1_20260503_023433.csv (new)
integration/paper_eval/runs_archive/2026-05-03_phase_c/digest_v1_20260503_023433.md (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-03_PHASE_C_FIRST_FULL_SWEEP.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계

Paper 작성 측:
- `digest_v1_*.csv` 의 18 컬럼을 paper figure / table 로 직접 인용
- `digest_v1_*.md` 의 sub-grid 섹션 그대로 paper draft에 복사 가능

추가 운영:
- per_trial_timeout 늘려서 9 incomplete trial 회수 (작은 배치 재실행)
- C2_D3_SCAN_SOURCE_ORDER의 3 wrong-reason 실패 원인 조사 (manifest의 trials_snapshot을 cell 별로 분석)
- 다른 LLM 모델 (gemma4 등) 대조 실험

### Notes

- **runs_archive/ 패턴은 신규**. 기존 `runs/`는 #138에서 gitignored (per-sweep runtime output). paper-grade run은 영구 evidence라 별도 archive 디렉토리에 보관 + 커밋. 향후 더 많은 paper-grade run이 추가되면 `2026-MM-DD_*` 구조로 누적.
- C2_D3_SCAN_SOURCE_ORDER 0.897 vs C2_D3_SCAN_DETERMINISTIC 1.000은 paper의 "deterministic ordering이 source order보다 안전"이라는 주장을 뒷받침하지만, n=29 vs n=28의 작은 sample에서 단정 어려움. 더 큰 sweep (e.g. 100 trials/cell)로 재검증 권장.
- scan_history_yes_first_rate = 0.474는 19 trial 데이터로만 산출 (scan_history 발생한 trial만 분모). paper에 인용 시 분모 명시 필요.
