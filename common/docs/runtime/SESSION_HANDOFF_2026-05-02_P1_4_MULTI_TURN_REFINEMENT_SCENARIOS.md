# SESSION_HANDOFF — P1.4 Multi-Turn Refinement Scenarios

**Date:** 2026-05-02
**Tests:** mac_mini 635/635 (was 618; +17 new in test_scenarios_doc12_multi_turn.py). rpi 168/168 unchanged.
**Schema validation:** both new scenarios validate against `scenario_manifest_schema.json` (Draft 7, same pattern as P1.3).

**Plan baseline:** PR #4 of `PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md`. Closes the audit's "0 scenarios exercise refinement_history" gap (PR #102 / doc 11 Phase 6.0).

---

## 이번 세션의 범위

doc 11 Phase 6.0이 PR #102에서 land됐지만 scenario coverage 0. 본 PR이 두 시나리오 추가하여 happy path + long-tail (timeout) 모두 cover.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `integration/scenarios/class2_multi_turn_refinement_user_picks_room_scenario_skeleton.json` (신규) | parent C1_LIGHTING_ASSISTANCE → refinement REFINE_BEDROOM → terminal CLASS_1. state-aware action_hint='light_on' (bedroom currently off). |
| `integration/scenarios/class2_multi_turn_refinement_turn_timeout_caregiver_escalation_scenario_skeleton.json` (신규) | parent C1_LIGHTING_ASSISTANCE picked → no refinement response → handle_timeout → SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION. silence ≠ consent invariant explicit. category='class2_timeout' (manifest enum). |
| `mac_mini/code/tests/test_scenarios_doc12_multi_turn.py` (신규) | 17 테스트. Schema validation + scenario_id pattern + 정책 precondition consistency (`class2_multi_turn_enabled=true`) + path-specific terminal invariants (CLASS_1 vs caregiver, refinement_history length, state-aware action_hint, timeout still records history). |

### 디자인 원칙 (P1.3과 일관)

- **Declarative only**: 새 fixture는 기존 자산 재사용.
- **`multi_turn_refinement_expectation` 신규 필드**: `additionalProperties:true`로 manifest 통과. P2.6에서 정식 schema 확장.
- **정책 precondition 강조**: 두 시나리오 모두 `requires_class2_multi_turn_enabled_in_policy=true` precondition + expectation 블록의 `scenario_requires_policy_field/value` — paper-eval 시 잘못된 deployment에서 돌리는 위험 차단.
- **silence ≠ consent timeout-path explicit assertion**: refinement-turn timeout이 어떻게 caregiver escalation으로 가는지 명시.

### Boundary 영향

없음. canonical 자산 미수정. Production direct_select / `class2_multi_turn_enabled=false` 흐름 byte-identical.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_scenarios_doc12_multi_turn.py -v
# 17 passed in 0.09s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 635 passed (was 618; +17 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (unchanged)
```

### Files touched

```
integration/scenarios/class2_multi_turn_refinement_user_picks_room_scenario_skeleton.json (new)
integration/scenarios/class2_multi_turn_refinement_turn_timeout_caregiver_escalation_scenario_skeleton.json (new)
mac_mini/code/tests/test_scenarios_doc12_multi_turn.py (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_P1_4_MULTI_TURN_REFINEMENT_SCENARIOS.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (PLAN doc §3 sequencing)

- **P1.5**: deterministic ordering scenarios (1–2개) — `class2_scan_ordering_mode='deterministic'` + ordering rule attribution
- 이후 P2 (manifest tagging + dashboard rendering 검증), P3 (fixture cleanup).

### Notes

- 두 expectation 블록 (`scan_input_mode_expectation`, `multi_turn_refinement_expectation`)이 ad-hoc으로 도입됐고 P2.6에서 정식 schema 추가 + `comparison_conditions[]` tagging 통합 예정.
- 현재 refinement 템플릿은 `C1_LIGHTING_ASSISTANCE`만 (refinement_templates._REFINEMENT_TEMPLATES). 향후 추가 템플릿이 land하면 P1.4 시나리오 family 확장 가능.
