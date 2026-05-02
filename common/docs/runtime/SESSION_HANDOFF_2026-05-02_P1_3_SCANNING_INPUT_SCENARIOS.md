# SESSION_HANDOFF — P1.3 Scanning Input Scenarios

**Date:** 2026-05-02
**Tests:** mac_mini 618/618 (was 598; +20 new in test_scenarios_doc12_scanning.py). rpi 168/168 unchanged.
**Schema validation:** all three new scenarios validate against `integration/scenarios/scenario_manifest_schema.json` (Draft 7).

**Plan baseline:** PR #3 of `PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md`. Closes the "0 scenarios exercise scanning input_mode" gap from the post-doc-12 audit.

---

## 이번 세션의 범위

doc 12 PRs land 후 scanning interaction model이 production / paper-eval에서 작동 가능하지만, 시나리오로는 한 번도 시험되지 않았음. 본 PR은 3개 deterministic scenario를 추가하여 모든 scanning terminal path를 cover:

1. **happy path** — single_click on option 0 → CLASS_1
2. **long-tail rejection** — every option no/silence → caregiver Phase 2
3. **emergency shortcut** — triple_hit during scan → CLASS_0 (no caregiver phase)

각 scenario는 declarative-only — payload fixture는 기존 `sample_policy_router_input_class2_insufficient_context.json`를 재사용하고, expected example payload는 PR #114에서 추가한 `clarification_interaction_scanning_yes_first.json`을 참조. 새 사용자-facing fixture는 0개 (scope discipline).

### 변경 요약

| 파일 | 변경 |
|---|---|
| `integration/scenarios/class2_scanning_user_accept_first_scenario_skeleton.json` (신규) | scanning happy path. user single_click on option 0. terminal CLASS_1. caregiver phase 미사용. |
| `integration/scenarios/class2_scanning_all_rejected_caregiver_escalation_scenario_skeleton.json` (신규) | every option no/silence → caregiver escalation. silence ≠ consent 명시. |
| `integration/scenarios/class2_scanning_triple_hit_emergency_shortcut_scenario_skeleton.json` (신규) | mid-scan triple_hit → CLASS_0 (emergency shortcut). caregiver phase 미사용. |
| `mac_mini/code/tests/test_scenarios_doc12_scanning.py` (신규) | 20 테스트. 각 scenario schema validation (Draft 7) + scenario_id pattern + comparison_condition declaration + per-path terminal invariants (transition target, caregiver phase invocation, scan_history shape, silence semantic, emergency shortcut). |

### 디자인 원칙

- **Declarative only**: 새 시나리오는 expectation을 declare; 실제 runtime fixtures (input/output payloads)는 기존 자산 재사용.
- **`scan_input_mode_expectation` 신규 필드**: 각 시나리오에 scanning-specific expectations 블록 (comparison_condition, expected scan_history length, expected_terminal_invokes_caregiver_phase 등). manifest schema는 `additionalProperties: true`라 통과 — 정식 schema 확장은 P2.6에서 진행 (comparison_conditions tagging과 함께).
- **Schema validation 자동화**: 20 테스트로 시나리오 변경 시 즉시 fail. PR 추가 시 같은 패턴으로 P1.4/P1.5도 cover.
- **invariant 1:1 매칭**: 각 path별 핵심 invariant (CLASS_1 terminal vs caregiver Phase 2 vs CLASS_0 emergency, silence ≠ consent, emergency shortcut bypasses remaining options) 모두 explicit assertion.

### Boundary 영향

없음. canonical policy/schema/payload 모두 미수정. Scenario assets only. Production behaviour byte-identical.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_scenarios_doc12_scanning.py -v
# 20 passed in 0.07s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 618 passed (was 598; +20 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (unchanged)
```

### Files touched

```
integration/scenarios/class2_scanning_user_accept_first_scenario_skeleton.json (new)
integration/scenarios/class2_scanning_all_rejected_caregiver_escalation_scenario_skeleton.json (new)
integration/scenarios/class2_scanning_triple_hit_emergency_shortcut_scenario_skeleton.json (new)
mac_mini/code/tests/test_scenarios_doc12_scanning.py (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_P1_3_SCANNING_INPUT_SCENARIOS.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (PLAN doc §3 sequencing)

- **P1.4**: multi-turn refinement scenarios (1–2개) — `class2_multi_turn_enabled=true` + refinement flow
- **P1.5**: deterministic ordering scenarios (1–2개) — `class2_scan_ordering_mode='deterministic'` + ordering rule attribution

이후 P2 (manifest tagging + dashboard rendering 검증), P3 (fixture cleanup).

### Notes

- `scan_input_mode_expectation`은 시나리오에서 새로 도입한 ad-hoc 필드. P2.6에서 manifest schema에 정식 추가 + comparison_conditions tagging field와 함께 정합화 예정.
- 시나리오는 deterministic 형식이지만 `randomized_stress` 모드도 manifest schema에서 허용 — paper-eval 시 변형 가능.
- 본 PR은 scanning scenarios만; multi-turn / deterministic ordering은 별도 PR.
