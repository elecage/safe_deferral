# SESSION_HANDOFF — P1.5 Deterministic Ordering Scenarios

**Date:** 2026-05-02
**Tests:** mac_mini 653/653 (was 635; +18 new in test_scenarios_doc12_ordering.py). rpi 168/168 unchanged.
**Schema validation:** both new scenarios validate against `scenario_manifest_schema.json`. Policy cross-checks live in the verifier so policy edits to `class2_scan_ordering_rules` immediately surface scenario drift.

**Plan baseline:** PR #5 of `PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md`. Closes the audit's "0 scenarios exercise scan_ordering_applied" gap (PR #110 / doc 12 §14).

---

## 이번 세션의 범위

PR #110에서 land된 deterministic ordering이 production 흐름에서 작동하지만 scenario coverage 0. 본 PR이 두 시나리오로 (a) trigger-bucket attribution, (b) context override 두 핵심 메커니즘을 cover.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `integration/scenarios/class2_deterministic_ordering_c206_bucket_scenario_skeleton.json` (신규) | C206 trigger-bucket priority [CLASS_1, CLASS_0, CAREGIVER_CONFIRMATION, SAFE_DEFERRAL] 적용 → CLASS_1 첫 announce. context override 미발동 (smoke/gas/doorbell 모두 false). matched_bucket='C206', applied_overrides=[]. |
| `integration/scenarios/class2_deterministic_ordering_smoke_override_scenario_skeleton.json` (신규) | environmental_context.smoke_detected=true 컨텍스트가 C206 bucket의 default를 override → CLASS_0 첫 announce. applied_overrides에 smoke_detected 항목 1개. terminal CLASS_0. |
| `mac_mini/code/tests/test_scenarios_doc12_ordering.py` (신규) | 18 테스트. Schema validation + scenario_id pattern + comparison_condition 일관성 + per-path invariants (matched_bucket, applied_overrides count, final_order first target, terminal transition). **policy cross-check 2개**: scenario assertions이 실제 policy_table.global_constraints.class2_scan_ordering_rules 값과 match — policy 수정 시 즉시 fail. |

### 디자인 원칙 (P1.3/P1.4와 일관 + 정책 cross-check 추가)

- **Declarative only**: 새 input fixture 0개.
- **`scan_ordering_expectation` 신규 필드**: `additionalProperties:true`로 manifest 통과. P2.6에서 정식 schema 추가.
- **scanning prerequisite 명시**: 두 시나리오 모두 `scenario_assumes_scanning_input_mode_active=true` 선언 — ordering이 scanning에서만 의미가 있음을 paper-eval 기록에 명시.
- **Policy cross-check (신규 패턴)**: 시나리오의 expected first target이 실제 policy의 bucket priority와 일치해야 통과. 누군가 `class2_scan_ordering_rules.by_trigger_id.C206` 또는 `context_overrides[0].boost_first`를 변경하면 본 verifier가 즉시 fail. P1.3/P1.4와는 다른 추가 안전망.

### Boundary 영향

없음. canonical 자산 미수정 (단, 시나리오가 정책을 cross-reference). Production source_order 모드 byte-identical.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_scenarios_doc12_ordering.py -v
# 18 passed in 0.09s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 653 passed (was 635; +18 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (unchanged)
```

### Files touched

```
integration/scenarios/class2_deterministic_ordering_c206_bucket_scenario_skeleton.json (new)
integration/scenarios/class2_deterministic_ordering_smoke_override_scenario_skeleton.json (new)
mac_mini/code/tests/test_scenarios_doc12_ordering.py (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_P1_5_DETERMINISTIC_ORDERING_SCENARIOS.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### P1 완료 상황

- ✅ P1.3 — scanning input scenarios (PR #115)
- ✅ P1.4 — multi-turn refinement scenarios (PR #116)
- ✅ P1.5 — deterministic ordering scenarios (this PR)

P1 모두 land. 도합 7 신규 scenario, 55 신규 verifier test (20 + 17 + 18). 4-dimensional comparison framework의 두 차원 (input mode + ordering mode)가 시나리오로 cover됨. 나머지 두 차원 (Class 1 intent recovery, Class 2 candidate generation source)은 기존 시나리오 + comparison_condition 변경만으로 cover 가능.

### 다음 단계 (PLAN doc §3 sequencing)

- **P2.6**: `scenario_manifest_schema.json`에 `comparison_conditions[]` 필드 + (optional) ad-hoc expectation 블록들 (`scan_input_mode_expectation`, `multi_turn_refinement_expectation`, `scan_ordering_expectation`) 정식 schema 정의.
- **P2.7**: dashboard trial detail row가 `input_mode` / `scan_history` / `scan_ordering_applied` / `refinement_history` 필드를 렌더하는지 검증.
- **P3.8**: fixture comment cleanup (옛 prompt 문구 references).

### Notes

- Policy cross-check 패턴이 좋게 작동 — P2.6에서 manifest schema가 `comparison_conditions[]` 추가하면 같은 패턴으로 시나리오 ↔ Package A definition cross-check 도입 가능.
- 두 시나리오 모두 `category='class2_insufficient_context'` 사용 (manifest enum). 향후 `category='class2_paper_eval_ordering'` 같은 dedicated 값 도입은 paper-eval 시 dashboard filtering이 필요해지면 P2.6와 함께 진행.
