# SESSION_HANDOFF — P0.2 MQTT/Payload Contract Reference + Example Payloads

**Date:** 2026-05-02
**Tests:** mac_mini 598/598 (was 589; +9 new in test_payload_examples_doc12.py). rpi 168/168 unchanged.
**Schema validation:** all three new examples validate against their schemas (jsonschema Draft7Validator).

**Plan baseline:** PR #2 of `PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md`. Brings the MQTT/payload contract reference and concrete example payloads in line with the four `routing_metadata` experiment-mode fields and five `clarification_interaction` optional fields that landed in PRs #101, #104, #110, #111.

---

## 이번 세션의 범위

P0.1 (PR #113)에서 architecture docs 01–04를 backfill했지만, MQTT/payload contract reference는 여전히 새 필드들을 모름. Example payloads 디렉토리에는 단일-턴 direct-select 예제만 있어서 ops/debugging 시 새 모드의 예시를 볼 수 없음. 본 PR은 두 갭을 모두 close.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/mqtt/topic_payload_contracts.md` | `safe_deferral/context/input` rules에 4 routing_metadata 옵션 필드 표 (필드 / enum / honored-by / 영향) + plan refs. paper-eval all-modes 예제 link 추가. `safe_deferral/clarification/interaction` rules에 5 옵션 필드 표 (`candidate_source` / `input_mode` / `scan_history` / `scan_ordering_applied` / `refinement_history`) + 두 신규 예제 link. backward-compat 명시. |
| `common/payloads/examples/policy_router_input_paper_eval_all_modes.json` (신규) | Package A 시험 trial 예제 — 4 routing_metadata 필드 모두 set. `_example_purpose` 키로 의도 doc화. |
| `common/payloads/examples/clarification_interaction_scanning_yes_first.json` (신규) | scanning session example: `input_mode='scanning'`, `scan_history` 1 yes turn, `scan_ordering_applied` C206 bucket attribution. |
| `common/payloads/examples/clarification_interaction_multi_turn_refinement.json` (신규) | multi-turn refinement terminal record: parent C1_LIGHTING_ASSISTANCE → REFINE_BEDROOM, `refinement_history` 1 entry, terminal `transition_target=CLASS_1`. |
| `mac_mini/code/tests/test_payload_examples_doc12.py` (신규) | 9 테스트. 각 예제 schema 검증 + 핵심 invariant (4 modes 모두 enum value, scan_history first=yes, scan_ordering_applied.final_order matches candidate_choices, refinement_history captures parent→child, terminal transition). `_example_purpose` meta key는 검증 전 strip. |

### 디자인 원칙

- **Schema validation 자동화**: 9 테스트가 examples 변경 시 즉시 fail. doc/example drift 미연 방지.
- **`_example_purpose` 키 도입**: 예제 JSON 자체에 의도/plan ref를 doc화. 스키마 통과를 위해 underscore-prefixed (test에서 strip). 향후 다른 예제도 같은 패턴 적용 가능.
- **3개 예제로 완전 cover**: 4 routing_metadata 필드 (paper-eval 예제 1개) + 5 clarification 필드 (scanning + refinement 예제 2개로 cover). minimal 새 예제로 모든 새 필드 시연.
- **3 examples ≠ 16 examples 검증**: 본 PR은 새 예제 3개만 검증. 기존 16개 검증은 별도 PR (P3 cleanup 또는 별도 audit).

### Boundary 영향

없음. doc + example + test only. canonical schema/policy/scenario 미수정. Production behaviour byte-identical.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_payload_examples_doc12.py -v
# 9 passed in 0.08s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 598 passed (was 589; +9 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (unchanged)

# 수동: contracts.md 표가 doc 04 §4.7 / §7.1과 일치하는지 cross-check
```

테스트 커버:
- policy_router_input paper-eval: schema 통과 + 4 필드 enum value 검증
- scanning yes-first: schema 통과 + scan_history[0]=yes + scan_ordering_applied.final_order=candidate_choices 순서 + input_mode='scanning'
- multi-turn refinement: schema 통과 + refinement_history 1 entry parent→child + terminal CLASS_1

### Files touched

```
common/mqtt/topic_payload_contracts.md
common/payloads/examples/policy_router_input_paper_eval_all_modes.json (new)
common/payloads/examples/clarification_interaction_scanning_yes_first.json (new)
common/payloads/examples/clarification_interaction_multi_turn_refinement.json (new)
mac_mini/code/tests/test_payload_examples_doc12.py (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_P0_2_MQTT_CONTRACT_AND_EXAMPLES.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (PLAN doc §3 sequencing)

P0 완료. 다음은 **P1 — scenario coverage**:
- **PR #3 P1.3**: scanning input scenarios (2–3 시나리오, `class2_input_mode='scanning'`)
- **PR #4 P1.4**: multi-turn refinement scenarios
- **PR #5 P1.5**: deterministic ordering scenarios

이후 P2 (manifest tagging + dashboard 검증), P3 (fixture cleanup).

### Notes

- 본 PR로 P0 (필수 정합성) 완료. 이후 PR들은 시나리오 작성 시 본 contracts.md 표 + 3 example을 reference로 사용 가능.
- `_example_purpose` underscore-prefixed key는 schema가 unknown top-level field를 허용해서 통과. 다른 dir의 예제도 같은 패턴 도입 시 lookup helper 필요할 수 있음 — 현재 scope 밖.
- 본 PR 9개 테스트는 examples + schema + 새 PR refs를 anchor하는 living verification — schema enum 변경 / example 누락 / refs drift 시 즉시 fail.
