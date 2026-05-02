# SESSION_HANDOFF — PR F: class2_candidate_source_mode (LLM-vs-static comparison condition)

**Date:** 2026-05-02
**Tests:** mac_mini 486/486 (was 478; +8 new — 3 manager static_only/llm_assisted, 5 router pass-through). rpi 160/160 (was 157; +3 new — runner prefix routing + Package A definition).
**Schema validation:** policy_router_input_schema.json + clarification_interaction_schema.json updated; no other canonical asset modified.

**Plan baseline:** Delivers PR F from `10_llm_class2_integration_alignment_plan.md` §3.3 P2.3 (originally deferred; user requested it now). Mirrors PR #79's `experiment_mode` plumbing pattern but on a separate field so Class 1 and Class 2 condition spaces never collide.

---

## 이번 세션의 범위

doc 10에서 마지막 미해결 P2 항목이었던 LLM-vs-static comparison을 위해 `class2_candidate_source_mode` 필드를 도입. Package A에 두 새 comparison condition (`class2_static_only`, `class2_llm_assisted`)을 추가하여 paper evaluation 시 LLM 기여도를 직접 측정할 수 있게 함.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/schemas/policy_router_input_schema.json` | `routing_metadata.class2_candidate_source_mode` 필드 추가 (enum: `static_only` / `llm_assisted`). `experiment_mode`와 같은 패턴, 같은 boundary 주의문. |
| `common/schemas/clarification_interaction_schema.json` | `candidate_source` enum에 `static_only_forced` 추가. 기존 `default_fallback`과 의도적으로 구분 — "LLM 시도하다 실패"가 아니라 "runner가 명시적으로 LLM 차단"임을 audit에서 분간 가능. |
| `mac_mini/code/policy_router/models.py` | `PolicyRouterResult.class2_candidate_source_mode: Optional[str]` 필드 + boundary 주석. |
| `mac_mini/code/policy_router/router.py` | meta에서 추출 + 모든 3개 return 사이트 (CLASS_2 staleness, CLASS_0 emergency, CLASS_1 default) 및 `_class2()` helper에서 propagate. |
| `mac_mini/code/class2_clarification_manager/manager.py` | `start_session(candidate_source_mode=...)` 파라미터. `"static_only"` → LLM 호출 자체를 skip하고 `_DEFAULT_CANDIDATES` 사용 + `candidate_source = "static_only_forced"`로 기록. 기존 default_fallback 경로와 명확히 분리. |
| `mac_mini/code/main.py` | `_handle_class2()`가 `route_result.class2_candidate_source_mode`를 manager에 전달. |
| `rpi/code/experiment_package/runner.py` | `comparison_condition`이 `"class2_"` prefix로 시작하면 `routing_metadata.class2_candidate_source_mode`로 routing (prefix 제거 후), 아니면 기존대로 `experiment_mode`. 두 condition 공간이 절대 충돌하지 않음. |
| `rpi/code/experiment_package/definitions.py` | Package A의 `comparison_conditions`에 `class2_static_only`, `class2_llm_assisted` 추가 + 분기 주석. |
| `mac_mini/code/tests/test_class2_clarification_manager.py` | 3 신규 테스트 (static_only가 LLM stub.calls=[] 보장, llm_assisted는 기존 동작 유지, schema validation). |
| `mac_mini/code/tests/test_policy_router.py` | 5 신규 테스트 (default None, CLASS_1 propagate, CLASS_2 static_only/llm_assisted, 잘못된 enum → C202). |
| `rpi/code/tests/test_rpi_components.py` | 3 신규 테스트 (`class2_static_only` → class2 mode field로 routing, experiment_mode 미오염, Package A definition 노출). |
| `common/docs/architecture/10_llm_class2_integration_alignment_plan.md` | PR F 표 항목에 delivery note 추가. |

### 디자인 결정

- **별도 field, prefix-based runner routing.** `experiment_mode`를 재사용하지 않고 새 field를 추가. 이유: 두 mode는 완전히 다른 routing branch (Class 1 vs Class 2)를 제어하며, 한 field에 다 넣으면 enum이 서로 다른 의미를 갖게 되어 schema도 documentation도 모호해짐. Runner는 `comparison_condition` 값의 `class2_` prefix로 어느 field에 쓸지 결정. 사용자에게는 condition 이름이 명시적이라 선택 시 의도가 분명.
- **`static_only_forced` ≠ `default_fallback`.** 두 값을 의도적으로 구분. 후자는 LLM 시도 후 실패한 audit 기록 (LLM 신뢰도 분석 시 중요), 전자는 실험 설계상 LLM을 명시적으로 비활성화한 경우. paper에서 "LLM이 항상 fallback에 의존했다"는 잘못된 결론을 내리지 않도록.
- **Boundary 유지.** 두 schema 필드 모두 description에 명시: "LLM prompt에 들어가지 않음, Class 0 emergency / Class 1 routing / validator authority에 영향 없음." 기존 `experiment_mode` boundary와 같은 패턴.

### Authority boundary 영향

없음. 두 mode 모두 candidate generation 단계만 제어하고, 이후의 deterministic validator / dispatcher / caregiver escalation 경로는 그대로 유지. `static_only` mode에서도 동일한 `_DEFAULT_CANDIDATES`가 사용되므로 안전 invariant 변하지 않음.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 486 passed (was 478; +8 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 160 passed (was 157; +3 new)
```

### Files touched

```
common/schemas/policy_router_input_schema.json
common/schemas/clarification_interaction_schema.json
common/docs/architecture/10_llm_class2_integration_alignment_plan.md
mac_mini/code/policy_router/models.py
mac_mini/code/policy_router/router.py
mac_mini/code/class2_clarification_manager/manager.py
mac_mini/code/main.py
mac_mini/code/tests/test_class2_clarification_manager.py
mac_mini/code/tests/test_policy_router.py
rpi/code/experiment_package/runner.py
rpi/code/experiment_package/definitions.py
rpi/code/tests/test_rpi_components.py
common/docs/runtime/SESSION_HANDOFF_2026-05-02_PR_F_CLASS2_CANDIDATE_SOURCE_MODE.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### Out of scope (남은 메뉴 항목)

- ✅ #1 Dashboard 비교 metric (PR #100)
- ✅ #2 PR F — class2_candidate_source_mode (this PR)
- ⏭ #3 doc 09 Phase 6 — multi-turn clarification

doc 09 Phase 6는 본격 구현 전 design alignment 필요 (다단계 session state, time-bound 정책, schema extension, TTS pattern). 다음 단계에서 design 제안부터.

### Notes

- `comparison_condition` 자유 문자열이 prefix-routing되므로 새로운 mode 추가 시 schema enum + runner 분기 + Package definition 세 곳만 갱신.
- `candidate_source_mode` 파라미터의 default는 None — 기존 호출자 (legacy/test) 영향 없음, 모두 backward-compat.
