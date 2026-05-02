# SESSION_HANDOFF — doc 12 Phase 1.5 Deterministic Scanning Ordering

**Date:** 2026-05-02
**Tests:** mac_mini 584/584 (was 560; +24 new — 13 pure ordering, 6 manager integration, 5 router passthrough). rpi 164/164 (was 160; +4 new — runner prefix routing + Package A definition).
**Schema validation:** policy_router_input_schema (+1 enum field), clarification_interaction_schema (+1 optional object field), policy_table (+3 fields). All optional — production unchanged.

**Plan baseline:** doc 12 §14 Phase 1.5 (originally deferred until after measurement). User requested implementation alongside Phase 5 so paper-eval can compare LLM-determined ordering against deterministic ranking side by side.

---

## 이번 세션의 범위

PR #104 Phase 1이 만든 scanning state machine은 candidate 순서를 source layer가 준 그대로 사용. doc 12 §14에서 ranking이 별도 layer로 분리되어야 한다고 design — paper에서 "LLM이 generation은 잘하지만 ordering은 별로다" / "정책 rule이 더 나은 priority를 만든다" 같은 가설을 검증 가능하게.

본 PR은 design을 그대로 구현. 정책 default `source_order`라서 production 흐름 변경 0; deployment가 `class2_scan_ordering_mode='deterministic'`을 켜야만 ranking이 활성화됨.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/schemas/policy_router_input_schema.json` | optional `routing_metadata.class2_scan_ordering_mode` (enum: source_order / deterministic). |
| `common/schemas/clarification_interaction_schema.json` | optional `scan_ordering_applied` 객체 — rule_source, matched_bucket, applied_overrides, final_order. ranking이 실제 적용된 trial에만 존재. |
| `common/policies/policy_table.json` | `class2_scan_ordering_mode` (default `source_order`). `class2_scan_ordering_rules`: by_trigger_id (8개 trigger + `_default`)에 우선순위 list, context_overrides 3개 (smoke/gas → CLASS_0 boost, doorbell → CAREGIVER boost). |
| `mac_mini/code/policy_router/models.py` | `PolicyRouterResult.class2_scan_ordering_mode` 필드. |
| `mac_mini/code/policy_router/router.py` | meta에서 추출 + 모든 4 return 사이트에 propagate. |
| `mac_mini/code/class2_clarification_manager/scan_ordering.py` (신규) | 순수 함수 모듈. `apply_scan_ordering(candidates, pure_context_payload, trigger_id, rules) → ScanOrderingResult`. Stable-sort algorithm: bucket selection → context override stacking (later wins front) → priority position sort. Unknown target → end preserving source order. `ScanOrderingResult.to_audit_dict()`. |
| `mac_mini/code/class2_clarification_manager/manager.py` | `__init__`이 ordering policy 필드 로드. `start_session(scan_ordering_mode=...)` 옵션 인자. scanning + deterministic 일 때 `apply_scan_ordering` 호출 + audit를 session에 stash. `_build_record`가 audit를 `scan_ordering_applied`로 surface. direct_select / source_order 모드는 ranking skip. |
| `mac_mini/code/main.py` | `_handle_class2`가 `route_result.class2_scan_ordering_mode`를 manager에 전달. |
| `rpi/code/experiment_package/runner.py` | `class2_scan_` prefix가 `class2_` prefix보다 먼저 체크 (more specific first). `class2_scan_*` → `routing_metadata.class2_scan_ordering_mode`, `class2_*` → `class2_candidate_source_mode`, others → `experiment_mode`. |
| `rpi/code/experiment_package/definitions.py` | Package A `comparison_conditions`에 `class2_scan_source_order`, `class2_scan_deterministic` 추가 + 세 condition 공간이 orthogonal 합성됨을 주석으로 명시. |
| `mac_mini/code/tests/test_scan_ordering.py` (신규) | 13 순수 ordering 테스트 (bucket selection, stable sort, tail behaviour, context overrides, multiple stacking, missing field path, permutation invariant, audit dict shape). |
| `mac_mini/code/tests/test_class2_clarification_manager.py` | TestScanOrderingManagerIntegration 6개 (source_order skip, deterministic reorders by trigger, smoke override, explicit arg overrides policy, direct_select skips ranking, schema validation). |
| `mac_mini/code/tests/test_policy_router.py` | TestClass2ScanOrderingModePassthrough 5개 (default None, CLASS_1/CLASS_2 propagate, invalid → C202, composes with candidate_source_mode). |
| `rpi/code/tests/test_rpi_components.py` | TestClass2ScanOrderingModePropagation 4개 (`class2_scan_*` prefix routing, 다른 prefix 회귀, Package A definition). |

### 디자인 원칙 (doc 12 §14 그대로)

- **순수 permutation**: ranking은 candidate 추가/제거/수정 안 함. action_hint, target_hint, prompt 모두 그대로.
- **Stable sort**: 같은 priority bucket의 candidate들은 source order 보존. 두 OPT_LIVING_ROOM/OPT_BEDROOM 둘 다 CLASS_1이면 들어온 순서대로.
- **Unknown target → tail**: priority list에 없는 transition target은 끝으로 가지만 source order 보존. 정책에 새 target 추가해도 기존 ordering 안 깨짐.
- **Context override stacking**: later override가 front spot 차지. doorbell + smoke 둘 다 true면 doorbell이 마지막에 fired되어 CAREGIVER가 first.
- **PR #101과 직교**: `class2_candidate_source_mode`와 `class2_scan_ordering_mode`는 독립. 같은 trial이 둘 다 지정 가능 → paper-eval에서 source × ordering 2D 매트릭스 비교 가능.

### Boundary 영향

없음. ranking layer는 candidate identity / authority / validator / dispatcher 모두 안 건드림. 정책 default `source_order` — production 흐름 byte-identical.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_scan_ordering.py tests/test_class2_clarification_manager.py::TestScanOrderingManagerIntegration tests/test_policy_router.py::TestClass2ScanOrderingModePassthrough -v
# 24 passed

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 584 passed (was 560; +24 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 164 passed (was 160; +4 new)
```

### Files touched

```
common/schemas/policy_router_input_schema.json
common/schemas/clarification_interaction_schema.json
common/policies/policy_table.json
mac_mini/code/policy_router/models.py
mac_mini/code/policy_router/router.py
mac_mini/code/class2_clarification_manager/scan_ordering.py             (new)
mac_mini/code/class2_clarification_manager/manager.py
mac_mini/code/main.py
mac_mini/code/tests/test_scan_ordering.py                                (new)
mac_mini/code/tests/test_class2_clarification_manager.py                 (+6 tests)
mac_mini/code/tests/test_policy_router.py                                (+5 tests)
rpi/code/experiment_package/runner.py
rpi/code/experiment_package/definitions.py
rpi/code/tests/test_rpi_components.py                                    (+4 tests)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_DOC12_PHASE1_5_DETERMINISTIC_RANKING.md (new)
common/docs/runtime/SESSION_HANDOFF.md                                   (index update)
```

### doc 12 진행 상황

- ✅ Phase 1 (PR #104) — manager state machine
- ✅ Phase 2 (PR #107) — TTS scanning helpers
- ✅ Phase 3 (PR #108) — scan input adapter
- ✅ Phase 4 (PR #109) — Mac mini main-loop wiring
- ✅ Phase 1.5 (this PR) — deterministic ranking heuristics
- ⏭ Phase 5 — interaction-mode comparison conditions (다음 PR)

### Notes

- ranking 활성화는 정책 한 줄 변경: `class2_scan_ordering_mode = "deterministic"`. 측정 후 rules 자체를 정책 파일에서 수정 가능 (코드 변경 없음).
- Phase 5와 함께 land 후, paper-eval에서 4가지 cell 비교 가능: (static / llm_assisted) × (source_order / deterministic).
- Mac mini deployment-side에서 specific trigger의 ordering이 wrong-first로 자주 나오면 정책 `by_trigger_id`만 수정. 운영 절차 가벼움.
