# SESSION_HANDOFF — Phase 6.0 Class 2 Multi-Turn Refinement (doc 11)

**Date:** 2026-05-02
**Tests:** mac_mini 499/499 (was 486; +13 new — 1 in TestLlmCandidateGeneratorHook, 12 in Phase 6.0 classes). rpi 160/160 unchanged.
**Schema validation:** policy_table.json + clarification_interaction_schema.json updated; no other canonical asset modified.

**Plan baseline:** Closes doc 09 Phase 6 design discussion via new design doc `11_class2_multi_turn_refinement_plan.md`. Phase 6.0 implementation lands behind a feature flag; Phase 6.1 (Mac mini main-loop wiring + TTS helpers) deferred per doc 11 §7.

---

## 이번 세션의 범위

doc 09 Phase 6는 "extending it is a separate design discussion"으로 deferred 상태였음. 본 PR이 그 separate design discussion (doc 11) + Phase 6.0 구현. 의도적으로 production 단일-턴 흐름을 건드리지 않고 (feature flag 기본 false), API + audit record + 정적 refinement template만 추가.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/docs/architecture/11_class2_multi_turn_refinement_plan.md` (신규) | 본 PR의 design doc. Scope, boundaries, data model, manager API, time budget, phase split (6.0 vs 6.1), test plan, open questions. |
| `common/docs/architecture/00_architecture_index.md` | doc 11을 active read order + roles 표에 추가. |
| `common/docs/architecture/09_llm_driven_class2_candidate_generation_plan.md` | Phase 6 섹션 헤더에 "Phase 6.0 landed; see doc 11" 상태 업데이트. |
| `common/policies/policy_table.json` | `class2_multi_turn_enabled` (default false) + `class2_refinement_turn_timeout_ms` (default 30000) + 자체 documenting `_class2_multi_turn_description` 추가. |
| `common/schemas/clarification_interaction_schema.json` | optional top-level `refinement_history` 필드 (turn_index, parent_candidate_id, refinement_question, selected_candidate_id, selection_source, selection_timestamp_ms). 기존 single-turn 레코드는 영향 없음 (optional). |
| `mac_mini/code/class2_clarification_manager/refinement_templates.py` (신규) | 정적 `_REFINEMENT_TEMPLATES` 테이블. 현재 1개 entry: `C1_LIGHTING_ASSISTANCE` → 거실 / 침실. `RefinementTemplate` dataclass + `get_refinement_template(parent_id)` 헬퍼. 모든 refinement candidate가 canonical low-risk catalog 안에 머무름 (light_on / living_room_light / bedroom_light). |
| `mac_mini/code/class2_clarification_manager/manager.py` | `__init__`에서 두 새 정책 필드 로드. 신규 `submit_selection_or_refine()` API: feature flag off일 때는 기존 `submit_selection`과 동일, on일 때는 chosen candidate에 template이 있으면 새 refinement `ClarificationSession` 반환. Refinement session은 `is_refinement_turn=True`, `parent_clarification_id`, `parent_candidate_id`, `refinement_question` 등 dynamic attrs 보유. `_build_record`가 refinement-turn session에 대해 `refinement_history` 항목을 자동 삽입. |
| `mac_mini/code/tests/test_class2_clarification_manager.py` | 13 신규 테스트 (1 disabled-default, 12 enabled+template invariants). |

### Phase 6.0 vs 6.1 (의도적 분리)

**6.0 (this PR)** — 안전하게 land 가능한 모든 것:
- ✅ Feature flag policy field
- ✅ Schema extension (optional, backward-compat)
- ✅ Manager API (`submit_selection_or_refine`)
- ✅ Static refinement template + safety invariant test
- ✅ Audit record extension (`refinement_history`)
- ✅ Tests (12 cases)

**6.1 (deferred)** — Mac mini main-loop wiring:
- ⏭ TTS helpers (`announce_class2_refinement`)
- ⏭ `_handle_class2()`가 union return type 처리
- ⏭ Refinement-턴 timeout 시 caregiver 메시지 포맷
- ⏭ Trial runner expectation 확장 (`expected_refinement_turns`)

이유: Mac mini의 두-phase background waiter는 큰 refactor가 필요하므로 별도 PR로 분리해야 review가 깔끔함. 6.0의 manager API는 production 흐름과 완전히 분리되어 있어 test로 boundary 검증 가능.

### 디자인 결정 (doc 11에서 발췌)

- **Max 1 refinement turn.** 깊은 refinement는 새 failure mode를 만들고, 그건 측정한 후 늘려야 함.
- **Per-turn timeout, not aggregate.** 사용자 mental model에 가까움 ("질문마다 ~초").
- **Static template만, LLM 미사용 (이번 round).** Phase 7+에서 LLM-driven refinement 가능. 지금은 catalog 안에 안전하게 머무는 것이 우선.
- **Feature flag default false.** Production 단일-턴 흐름 절대 건드리지 않음.
- **Refinement candidate authority bounded.** 모든 refinement 옵션은 canonical low-risk catalog (`light_on`, `living_room_light`/`bedroom_light`) 또는 None. Test가 이를 강제.

### Authority boundary 영향

없음. Refinement candidate는 parent candidate가 도달 가능한 path만 좁힐 수 있고, 새 권한 surface는 추가하지 않음. 모든 turn이 deterministic validator를 거치며, 정책상 disabled된 상태로 ship됨.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 499 passed (was 486; +13 new)

# Phase 6.0 specific:
python -m pytest tests/test_class2_clarification_manager.py::TestMultiTurnRefinementDisabled \
    tests/test_class2_clarification_manager.py::TestMultiTurnRefinementEnabled \
    tests/test_class2_clarification_manager.py::TestRefinementTemplates -v
# 12 passed in 0.28s

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 160 passed (unchanged)
```

테스트 cover 항목:
- Flag off → submit_selection_or_refine = submit_selection (terminal Class2Result, no refinement_history)
- Flag on + template 있는 candidate → refinement ClarificationSession 반환
- Flag on + template 없는 candidate → terminal (unchanged)
- Flag on + unknown candidate id → terminal escalation (defensive)
- Refinement session 해결 → terminal Class2Result + refinement_history 1 entry
- Refinement session에서 한 번 더 refine 시도 → terminal (max 1 turn 보장)
- Refinement turn timeout → terminal escalation + refinement_history (timed-out turn 기록)
- Schema validation: refinement_history 있는 record 통과
- Refinement template invariant: action_hint/target_hint가 canonical low-risk catalog 안
- Refinement question이 정책 prompt cap 안 (Phase 4 invariant 확장)

### Files touched

```
common/docs/architecture/11_class2_multi_turn_refinement_plan.md (new)
common/docs/architecture/00_architecture_index.md
common/docs/architecture/09_llm_driven_class2_candidate_generation_plan.md
common/policies/policy_table.json
common/schemas/clarification_interaction_schema.json
mac_mini/code/class2_clarification_manager/refinement_templates.py (new)
mac_mini/code/class2_clarification_manager/manager.py
mac_mini/code/tests/test_class2_clarification_manager.py
common/docs/runtime/SESSION_HANDOFF_2026-05-02_PHASE6_MULTI_TURN_REFINEMENT_6_0.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### Out of scope (메뉴 완료)

세 후속 항목 모두 완료:
- ✅ #1 Dashboard 비교 metric (PR #100)
- ✅ #2 PR F class2_candidate_source_mode (PR #101)
- ✅ #3 doc 09 Phase 6 → doc 11 Phase 6.0 (this PR)

남은 future work (doc 11 §7 + open questions):
- Phase 6.1 — Mac mini main-loop + TTS 통합 (별도 PR)
- 추가 refinement template entries (review 거쳐 추가)
- LLM-driven refinement (Phase 7+ — separate design)
- doc 11 §9의 open questions (template location refactor, refinement budget knob, caregiver-side refinement message)

### Notes

- `class2_multi_turn_enabled = false` 기본값 덕분에 production 흐름 변경 0. flag 켜야만 Phase 6.0 surface 보임.
- `submit_selection`은 시그니처 그대로 — legacy 호출자 전혀 영향 없음. 새 API `submit_selection_or_refine`이 multi-turn aware caller 진입점.
- Refinement-turn session은 dynamic attrs를 사용 (`session.is_refinement_turn` 등) — 기존 `candidate_source` 패턴 따름. ClarificationSession 모델 변경 없음.
