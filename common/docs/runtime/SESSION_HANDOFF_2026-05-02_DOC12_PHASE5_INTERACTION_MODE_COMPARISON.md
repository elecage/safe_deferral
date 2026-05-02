# SESSION_HANDOFF — doc 12 Phase 5 Interaction-Model Comparison Conditions

**Date:** 2026-05-02
**Tests:** mac_mini 589/589 (was 584; +5 new in TestClass2InputModePassthrough). rpi 168/168 (was 164; +4 new in TestClass2InputModePropagation).
**Schema validation:** policy_router_input_schema (+1 enum field). No other canonical asset modified.

**Plan baseline:** doc 12 §9 Phase 5 — paper-eval scenario fixture variant for interaction-model comparison. Final round closing doc 12.

---

## 이번 세션의 범위

doc 12에서 마지막 미land 항목인 paper-eval interaction-model 비교 framework 추가. PR #110 ordering comparison과 같은 prefix-routing 패턴으로 새 comparison_condition 두 개 (`class2_direct_select_input` / `class2_scanning_input`) 추가. 같은 trial 안에서 source × ordering × interaction-model 3차원 비교 가능.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/schemas/policy_router_input_schema.json` | optional `routing_metadata.class2_input_mode` (enum: direct_select / scanning). per-trial override of policy default. |
| `mac_mini/code/policy_router/models.py` | `PolicyRouterResult.class2_input_mode` 필드. |
| `mac_mini/code/policy_router/router.py` | meta에서 추출 + 4 return 사이트 모두 propagate. |
| `mac_mini/code/main.py` | `_handle_class2`가 `route_result.class2_input_mode`를 manager `start_session(input_mode=...)` 인자로 전달 (PR #104에서 이미 manager는 input_mode kwarg 지원, main.py wiring만 추가). |
| `rpi/code/experiment_package/runner.py` | prefix routing 확장: `class2_*_input` (suffix-matched, more specific than bare `class2_*`)이 `class2_scan_*` 다음, `class2_*` 앞에 위치. `class2_direct_select_input` → `direct_select`, `class2_scanning_input` → `scanning`. |
| `rpi/code/experiment_package/definitions.py` | Package A `comparison_conditions`에 `class2_direct_select_input`, `class2_scanning_input` 추가. 4개 condition space orthogonal composition 주석 갱신. |
| `mac_mini/code/tests/test_policy_router.py` | TestClass2InputModePassthrough 5개 (default None, CLASS_1/CLASS_2 propagate, invalid → C202, all 3 modes 동시 합성). |
| `rpi/code/tests/test_rpi_components.py` | TestClass2InputModePropagation 4개 (`class2_*_input` prefix routing, 다른 prefix 회귀, Package A definition). |

### 4-dimensional comparison framework

paper-eval는 이제 다음 4 dimension을 trial 별로 독립적으로 설정 가능:

| dimension | comparison_condition prefix | routes to |
|-----------|------------------------------|-----------|
| Class 1 intent recovery (PR #79) | (no prefix) | `experiment_mode` |
| Class 2 candidate generation (PR #101) | `class2_` (no special suffix) | `class2_candidate_source_mode` |
| Class 2 scanning ordering (Phase 1.5) | `class2_scan_` | `class2_scan_ordering_mode` |
| Class 2 interaction model (this PR) | `class2_*_input` (suffix-matched) | `class2_input_mode` |

Most-specific prefix wins (runner checks `class2_scan_` → `class2_*_input` → bare `class2_` → bare). 4 condition spaces never collide.

### 디자인 결정

- **Suffix-matched prefix** (`class2_*_input`): bare `class2_` prefix already had two condition spaces (PR #101 + Phase 1.5), so adding `_input` suffix makes the new mapping unambiguous. Most-specific-first checking handles disambiguation.
- **Per-trial override of policy default**: `routing_metadata.class2_input_mode`가 `policy.class2_input_mode`를 trial별로 override. 운영자가 deployment-wide 설정을 유지하면서도 paper-eval은 fine-grained 조절 가능.
- **manager / TTS / state machine 모두 변경 없음**: PR #104가 이미 `start_session(input_mode=...)` kwarg 지원. main.py wiring만 추가.

### Boundary 영향

없음. interaction model은 presentation layer 변경뿐. validator / dispatcher / authority surface 그대로. 정책 default `direct_select` 유지 — production 흐름 byte-identical.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 589 passed (was 584; +5 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (was 164; +4 new)
```

테스트 cover:
- `class2_direct_select_input` → `routing_metadata.class2_input_mode = "direct_select"`, 다른 3개 field 미오염
- `class2_scanning_input` → `class2_input_mode = "scanning"`
- 다른 class2_* prefix들 회귀 통과 (most-specific first 정확)
- 4 dimension 동시 설정 시 모두 propagate
- 잘못된 enum → C202 schema validation failure
- Package A definition에 새 condition 노출

### Files touched

```
common/schemas/policy_router_input_schema.json
mac_mini/code/policy_router/models.py
mac_mini/code/policy_router/router.py
mac_mini/code/main.py
mac_mini/code/tests/test_policy_router.py                                (+5 tests)
rpi/code/experiment_package/runner.py
rpi/code/experiment_package/definitions.py
rpi/code/tests/test_rpi_components.py                                    (+4 tests)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_DOC12_PHASE5_INTERACTION_MODE_COMPARISON.md (new)
common/docs/runtime/SESSION_HANDOFF.md                                   (index update)
```

### doc 12 완료 ✅

| Phase | PR | Status |
|-------|-----|--------|
| 1 — manager state machine | #104 | ✅ |
| 2 — TTS scanning helpers | #107 | ✅ |
| 3 — scan input adapter | #108 | ✅ |
| 4 — Mac mini main-loop wiring | #109 | ✅ |
| 1.5 — deterministic ranking | #110 | ✅ |
| 5 — interaction-mode comparison | this PR | ✅ |

doc 12 전체 land. paper-eval 가능한 모든 차원이 갖춰짐. production direct_select / source_order 흐름은 byte-identical로 유지.

### Next 후보

doc 12 완전 종료. 다음 작업 후보:
- 실제 paper-eval 측정 (4 dimension matrix 설정해서 trial 돌리기) — 코드보다 시나리오 / 정책 / 분석 작업
- 다른 영역 (architecture / 새 시나리오 / dashboard 개선 등) — 사용자 우선순위 따라
