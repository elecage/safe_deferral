# SESSION_HANDOFF — P3.8 Fixture Comment Cleanup + Plan Completion

**Date:** 2026-05-02
**Tests:** mac_mini 700/700 (unchanged; cosmetic-only changes). rpi 168/168 unchanged.
**Schema validation:** none modified.

**Plan baseline:** Final PR (#8) of `PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md`. Closes the audit's "old prompt strings still in test fixture comments" item and adds a completion note to the plan doc.

---

## 이번 세션의 범위

P0/P1/P2 7개 PR 머지 후 마지막 정리. 옛 "조명 도움이 필요하신가요?" 문구가 코드의 4 곳에 fossil처럼 남아 있었음 (manager의 dead fallback dict text + speaker docstring + test fixture). 사용 안 되는 placeholder지만 코드 reviewer에게 혼란.

또한 PLAN doc에 8 PR 모두 완료 기록 (§8 Completion 섹션) — backfill 전체 trail이 PLAN doc 하나로 navigable해짐.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `mac_mini/code/class2_clarification_manager/manager.py` | `_DEFAULT_CANDIDATES['insufficient_context'][0].prompt` 와 `_DEFAULT_CANDIDATES['missing_policy_input'][0].prompt`를 `"조명 도움이 필요하신가요?"` → `"조명을 도와드릴까요?"` (중립 placeholder). 두 항목 모두 `_state_aware_lighting_candidate`가 항상 override하므로 emission되지 않음 — 단지 reviewer를 위한 cleanup. 각 항목에 NOTE 주석 추가하여 placeholder 의도 + override 메커니즘 명시. |
| `mac_mini/code/tts/speaker.py` | `announce_class2_selection` docstring 예제를 옛 문구 → `"거실 조명을 켜드릴까요?"`/`"거실 조명을 꺼드릴까요?"`/`"보호자에게 연락할까요?"` (state-aware lighting + caregiver). doc 12 PR #106 이후의 실제 emission과 일치. |
| `mac_mini/code/tests/test_tts_speaker.py` | `test_each_prompt_appears_verbatim` 와 `test_noop_speaker_does_not_raise`의 fixture 문자열을 `"조명 도움이 필요하신가요?"` → `"거실 조명을 켜드릴까요?"`. 테스트 의미 변경 0 (verbatim invariant는 prompt 텍스트와 무관). reviewer가 fixture를 보면 production emission 형태와 매치되어 학습에 도움. |
| `common/docs/runtime/PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md` | §8 "Completion (added 2026-05-02 by P3.8)" 신규 섹션 — 8 PR 모두 land됐음 명시 (PR # / branch 이름 / 제목 표). 누적 영향 (mac_mini 560→700 +140 tests, rpi 160→168 +8, production byte-identical). plan을 historical record로 close. |

### 의도적으로 안 한 것

- **`sc01_light_on_request.json` 위치 변경**: 이 파일은 `integration/scenarios/`에 있지만 실제로는 payload fixture (적절한 위치는 `integration/tests/data/`). 이동은 `docs/setup/05_integration_run.md`의 두 reference도 같이 갱신해야 하므로 별도 PR이 적합. P2.6 verifier가 이미 explicit exclusion으로 처리.
- **historical SESSION_HANDOFF / PLAN doc 안의 옛 prompt references**: 역사적 기록이므로 그대로 유지.
- **`tests/test_class2_clarification_manager.py`의 invariant test (line ~1427)**: 옛 prompt가 더 이상 쓰이지 않음을 검증하는 의도된 negative assertion. 그대로 유지.

### Boundary 영향

없음. 모든 변경이 dead-code text / docstring / test fixture / plan doc. Production runtime / canonical asset / authority surface 0.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 700 passed (unchanged — cosmetic-only changes)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (unchanged)
```

### Files touched

```
mac_mini/code/class2_clarification_manager/manager.py
mac_mini/code/tts/speaker.py
mac_mini/code/tests/test_tts_speaker.py
common/docs/runtime/PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md
common/docs/runtime/SESSION_HANDOFF_2026-05-02_P3_8_FIXTURE_COMMENT_CLEANUP.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 8-PR Backfill 완료 ✅

| Tier | PR | Title |
|------|----|-------|
| Plan | #112 | docs: post-doc-12 architecture audit + 8-PR backfill plan |
| P0.1 | #113 | docs(architecture): backfill docs 01–04 with doc 12 features |
| P0.2 | #114 | docs(mqtt): MQTT contract reference + 3 example payloads |
| P1.3 | #115 | test(scenarios): scanning input scenarios |
| P1.4 | #116 | test(scenarios): multi-turn refinement scenarios |
| P1.5 | #117 | test(scenarios): deterministic ordering scenarios |
| P2.6 | #118 | test(scenarios): manifest schema + comparison_conditions tagging |
| P2.7 | #119 | feat(dashboard): dedicated audit-field blocks |
| P3.8 | (this PR) | docs/test: fixture comment cleanup + plan completion note |

누적 impact (audit 시작 시점부터):
- **테스트**: mac_mini 560 → 700 (+140 across 8 PRs)
- **rpi**: 160 → 168 (+8)
- **Production behaviour**: byte-identical
- **신규 시나리오**: 7
- **신규 example payloads**: 3
- **architectural docs 갱신**: 5 (01–04 + manifest schema)
- **canonical asset 변경**: 1 (manifest schema에 optional 필드 4개)

doc 12 / doc 11 / PR #101 등의 Class 2 확장 전체가 docs / contracts / scenarios / tests / dashboard 모든 layer에서 정합성 회복.

### 이 다음

PLAN doc은 historical record로 보존 — closed 상태. doc 12 / 11 features 위에 새 작업이 land될 때 같은 plan-then-execute pattern을 따르면 됨.
