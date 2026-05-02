# SESSION_HANDOFF — P2.6 Manifest Schema + comparison_conditions Tagging

**Date:** 2026-05-02
**Tests:** mac_mini 694/694 (was 653; +41 new in test_scenario_manifest_p2_6.py). rpi 168/168 unchanged.
**Schema validation:** scenario_manifest_schema.json extended with 4 new optional top-level fields. All scenarios validate.

**Plan baseline:** PR #6 of `PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md`. Closes the audit's "scenario_manifest_schema has no comparison_conditions tagging" gap and formalizes the three ad-hoc `*_expectation` blocks introduced by P1.3/P1.4/P1.5.

---

## 이번 세션의 범위

P1에서 7개 doc 12 시나리오가 ad-hoc `*_expectation` 블록을 도입 (manifest의 `additionalProperties:true`로 통과). 본 PR은 이 블록들에 정식 schema 정의를 부여하고, paper-eval 운영의 핵심 누락 — 어느 시나리오가 어느 comparison_condition을 cover하는지 mechanical 검증 — 을 해결.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `integration/scenarios/scenario_manifest_schema.json` | top-level properties에 4개 신규 optional 필드: **`comparison_conditions`** (array, enum 9 values matching Package A definition), **`scan_input_mode_expectation`** (open-shape object with conventional keys), **`multi_turn_refinement_expectation`** (open-shape with `class2_multi_turn_enabled` const precondition), **`scan_ordering_expectation`** (open-shape with `class2_scan_deterministic` const condition). 모두 `additionalProperties:true` — 향후 expectation key 추가 호환. |
| `integration/scenarios/class1_baseline_scenario_skeleton.json` | `comparison_conditions=["direct_mapping","rule_only","llm_assisted"]` (Class 1 intent recovery 3 dimensions). |
| `integration/scenarios/class2_insufficient_context_scenario_skeleton.json` | `comparison_conditions=["class2_static_only","class2_llm_assisted","class2_direct_select_input"]` (Class 2 generation source 2 + interaction model). |
| `integration/scenarios/class2_scanning_user_accept_first_scenario_skeleton.json` | `comparison_conditions=["class2_scanning_input","class2_scan_source_order"]` (scanning + default ordering — covers `class2_scan_source_order`로 last enum value to satisfy coverage). |
| `integration/scenarios/class2_scanning_all_rejected_caregiver_escalation_scenario_skeleton.json` | `["class2_scanning_input"]` |
| `integration/scenarios/class2_scanning_triple_hit_emergency_shortcut_scenario_skeleton.json` | `["class2_scanning_input"]` |
| `integration/scenarios/class2_multi_turn_refinement_user_picks_room_scenario_skeleton.json` | `["class2_direct_select_input"]` (multi-turn opt-in is policy field, not condition) |
| `integration/scenarios/class2_multi_turn_refinement_turn_timeout_caregiver_escalation_scenario_skeleton.json` | `["class2_direct_select_input"]` |
| `integration/scenarios/class2_deterministic_ordering_c206_bucket_scenario_skeleton.json` | `["class2_scan_deterministic","class2_scanning_input"]` |
| `integration/scenarios/class2_deterministic_ordering_smoke_override_scenario_skeleton.json` | `["class2_scan_deterministic","class2_scanning_input"]` |
| `mac_mini/code/tests/test_scenario_manifest_p2_6.py` (신규) | 41 테스트. (a) all scenarios validate against extended schema (parametrized over 22 scenario files; sc01_light_on_request.json explicitly excluded as misplaced payload), (b) Package A 9-condition coverage verifier (each condition tagged ≥1 scenario; no typos), (c) per-scenario tagging consistency (scan_*_expectation implies matching comparison_condition tag), (d) manifest schema self-checks (4 new fields exist; enum matches Package A definition). |

### 9 Package A conditions 모두 cover됨

| condition | scenarios |
|---|---|
| `direct_mapping` | class1_baseline |
| `rule_only` | class1_baseline |
| `llm_assisted` | class1_baseline |
| `class2_static_only` | class2_insufficient_context |
| `class2_llm_assisted` | class2_insufficient_context |
| `class2_scan_source_order` | class2_scanning_user_accept_first |
| `class2_scan_deterministic` | 2 ordering scenarios |
| `class2_direct_select_input` | class2_insufficient_context + 2 multi-turn refinement |
| `class2_scanning_input` | 3 scanning + 2 ordering |

### 디자인 원칙

- **enum source of truth**: manifest schema의 `comparison_conditions.items.enum`은 Package A `definitions.py`와 정확히 일치 — verifier가 매번 cross-check해서 drift 즉시 fail.
- **open-shape expectation blocks**: P1.3/P1.4/P1.5 시나리오의 모든 ad-hoc 키가 그대로 통과 (additionalProperties: true). 향후 verifier가 추가 invariant를 도입할 때 schema가 막지 않음.
- **Backfill 범위 discipline**: 22개 시나리오 중 9개만 명시 태깅. 나머지는 mode-agnostic 유지 (대부분 baseline/class0/class1/fault). future PR이 필요에 따라 추가.
- **sc01_light_on_request.json**: scenarios/ 디렉토리에 misplaced된 payload fixture. 별도 파일-rename PR 대상; 본 verifier에서는 명시 exclusion.

### Boundary 영향

없음. canonical 자산은 manifest schema 한 개만 (additive optional 필드 4개). Production runtime / scenario_manager.load_scenario / dashboard rendering 모두 byte-identical.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_scenario_manifest_p2_6.py -v
# 41 passed in 0.11s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 694 passed (was 653; +41 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (unchanged)
```

### Files touched

```
integration/scenarios/scenario_manifest_schema.json
integration/scenarios/class1_baseline_scenario_skeleton.json
integration/scenarios/class2_insufficient_context_scenario_skeleton.json
integration/scenarios/class2_scanning_user_accept_first_scenario_skeleton.json
integration/scenarios/class2_scanning_all_rejected_caregiver_escalation_scenario_skeleton.json
integration/scenarios/class2_scanning_triple_hit_emergency_shortcut_scenario_skeleton.json
integration/scenarios/class2_multi_turn_refinement_user_picks_room_scenario_skeleton.json
integration/scenarios/class2_multi_turn_refinement_turn_timeout_caregiver_escalation_scenario_skeleton.json
integration/scenarios/class2_deterministic_ordering_c206_bucket_scenario_skeleton.json
integration/scenarios/class2_deterministic_ordering_smoke_override_scenario_skeleton.json
mac_mini/code/tests/test_scenario_manifest_p2_6.py (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_P2_6_MANIFEST_COMPARISON_CONDITIONS_TAGGING.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (PLAN doc §3 sequencing)

- **P2.7**: dashboard trial detail row가 `input_mode` / `scan_history` / `scan_ordering_applied` / `refinement_history` 필드를 렌더하는지 검증 (PR #99 work follow-up).
- **P3.8**: fixture comment cleanup (옛 prompt 문구 references).

### Notes

- sc01_light_on_request.json은 P3.8 또는 별도 PR에서 정리 후보 — 잘못된 디렉토리에 있는 payload fixture.
- Package A 시나리오 coverage 가 mechanical하게 보장되므로, 향후 새 condition 추가 시 verifier가 즉시 누락 알림 → tag 안 한 채 머지 불가능.
- 9-condition matrix가 paper-eval 시 어떤 시나리오를 어떤 condition에서 돌릴지 결정 가능: `class2_scan_deterministic + class2_scanning_input` 둘 다 tagged된 ordering 시나리오는 두 dimension을 동시 교차 시험.
