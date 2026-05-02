# SESSION_HANDOFF — doc 12 Phase 1 Scanning Implementation + Phase 1.5 Design

**Date:** 2026-05-02
**Tests:** mac_mini 516/516 (was 499; +17 new — 4 init, 8 response flow, 5 guards/schema). rpi 160/160 unchanged.
**Schema validation:** clarification_interaction_schema.json (input_mode + scan_history added, both optional). policy_table.json (3 new fields). No other canonical asset modified.

**Plan baseline:** Combines two pieces from the 2026-05-02 conversation:
1. Phase 1 implementation per approach (A) — scanning state machine, ordering inherited from candidate generation source.
2. Phase 1.5 design — deterministic ranking heuristics added to doc 12 §14, implementation deferred until measurement informs the rules.

User's stated goal: paper-eval needs to compare deterministic vs LLM-based ordering side by side.

---

## 이번 세션의 범위

PR #103에서 design doc만 land했고, 5개 design 결정과 ordering 방식이 maintainer 승인됨. 사용자가 추가로 "결정론적 ranking과 LLM-based ordering 둘 다 구현해서 비교" 요청. Phase 1은 단순(생성 결과 순서 그대로)으로 land해서 빠르게 측정 시작 가능; Phase 1.5는 design만 추가하고 측정 후 구현하기로 분리.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/docs/architecture/12_class2_scanning_input_mode_plan.md` | **§14 신규** (Phase 1.5 deterministic ranking heuristics, 8 sub-section). Why-it-exists, ranking step 위치, rule shape (`class2_scan_ordering_rules` 정책 필드 sketch), rule semantics (bucket selection, context override, unmatched-target tail, no mutation), audit record 확장 (`scan_ordering_applied`), feature flag (`class2_scan_ordering_mode`), comparison condition 추가 (`class2_scan_source_order` / `class2_scan_deterministic`), Phase 1.5 구현 항목 list, open question (context-driven candidate injection 거부). §15는 source notes (이전 §13 자리). |
| `common/schemas/clarification_interaction_schema.json` | optional `input_mode` (enum: `direct_select` / `scanning`) + optional `scan_history` 배열 (turn_index, candidate_id, response: yes/no/silence/dropped, elapsed_ms, input_source). 기존 single-mode 레코드는 영향 없음. |
| `common/policies/policy_table.json` | 3 신규 필드: `class2_input_mode` (default `direct_select`, production 영향 0), `class2_scan_per_option_timeout_ms` (default 8000), `class2_scan_user_phase_extension` (default 1.5). 자체 documenting `_class2_input_mode_description` 포함. |
| `mac_mini/code/class2_clarification_manager/manager.py` | `__init__`이 3 신규 정책 필드 로드. `start_session(input_mode=...)` 옵션 인자 추가, scanning 일 때 `current_option_index=0`, `scan_history=[]`, `scan_per_option_timeout_ms` dynamic attr 설정. 신규 `submit_scan_response(session, option_index, response, input_source, elapsed_ms, ...)`: yes → terminal Class2Result (submit_selection 재사용), no/silence on non-final → 같은 session 반환 + index 진행, no/silence on final → terminal escalation, stale/out-of-range → `dropped` 기록 후 unchanged. 신규 `handle_scan_silence(session, ...)`: 현재 옵션에 silence 응답 편의 메서드. `_build_record`가 `input_mode`, `scan_history` 자동 surface (둘 다 backward-compat 옵셔널). |
| `mac_mini/code/tests/test_class2_clarification_manager.py` | 17 신규 테스트 (TestScanningSessionInit 4, TestScanningResponseFlow 8, TestScanningGuardsAndSchema 5). 정책 default + explicit override + 모든 yes/no/silence path + stale drop + out-of-range + guards + schema validation 커버. |

### Phase 1 vs Phase 1.5 분리 이유

- **Phase 1** (이 PR) = state machine 만. ordering은 candidate generation 결과 그대로. 운영자가 PR F의 `class2_static_only` / `class2_llm_assisted` 모드로 ordering 주체를 선택. 측정 가능한 baseline.
- **Phase 1.5** (design only, 구현 추후) = deterministic ranking step. policy 규칙이 generation 결과를 permute. 두 모드 모두 같은 ranking을 거치게 해서 audit 일관성 확보. paper-eval 비교 가능.

이렇게 분리하면:
1. Phase 1 빠르게 land → 실제 사용 데이터 모음 → 어떤 ordering rule이 의미 있는지 파악
2. Phase 1.5 rules 작성 시 데이터 기반 → 추측 아닌 측정 기반 결정
3. 두 단계 모두 land 후 paper에서 직접 비교 가능 (LLM-determined order vs deterministic rule)

### 유지된 boundary

- **No new authority surface.** Scanning은 presentation 변경뿐. action_hint/target_hint 어떤 후보도 canonical low-risk catalog 밖으로 안 나감.
- **Silence ≠ consent.** 비최종 옵션 silence = `no` 자동 진행, 최종 옵션 silence = caregiver escalation. 어떤 자동 실행도 없음.
- **Production 영향 0.** `class2_input_mode` default `direct_select`. 모든 기존 호출자 unchanged.
- **submit_selection 재사용.** Scanning yes 응답이 terminal로 갈 때 기존 submit_selection pipeline 호출 → transition 결정/caregiver 알림/audit record 조립이 한 곳에서. 코드 중복 0.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_class2_clarification_manager.py::TestScanningSessionInit \
    tests/test_class2_clarification_manager.py::TestScanningResponseFlow \
    tests/test_class2_clarification_manager.py::TestScanningGuardsAndSchema -v
# 17 passed in 0.38s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 516 passed (was 499; +17 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 160 passed (unchanged)
```

테스트 커버 항목:
- Default session = direct_select, scanning attrs 없음
- Explicit `input_mode='scanning'` → pointer/history 초기화
- Policy default가 `'scanning'`이면 implicit scanning, explicit arg가 override
- Yes on first option → terminal Class2Result with action_hint, scan_history[0].response='yes', input_mode='scanning' attribution
- No on non-final → 같은 session, index +1, history에 'no'
- Silence on non-final → advance + history에 'silence' (구분됨)
- handle_scan_silence 편의 메서드 동작
- 모든 옵션 거부 → terminal escalation to caregiver, history에 N개 'no'
- Final option silence → escalation
- Stale input (option_index 다름) → 'dropped' 기록, current_option_index 그대로
- Out-of-range option_index → 'dropped' + candidate_id='<out_of_range>'
- direct_select session에 scanning 메서드 호출 → ValueError
- 잘못된 response 값 → ValueError
- 스키마: scanning + history 통과
- 스키마: direct_select 레코드도 input_mode='direct_select' attribution 포함, scan_history 없음

### Files touched

```
common/docs/architecture/12_class2_scanning_input_mode_plan.md   (§14 추가, §13→§15)
common/policies/policy_table.json                                 (3 new fields)
common/schemas/clarification_interaction_schema.json              (input_mode, scan_history)
mac_mini/code/class2_clarification_manager/manager.py             (state machine + 2 new methods)
mac_mini/code/tests/test_class2_clarification_manager.py          (17 new tests)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_DOC12_PHASE1_SCANNING_PLUS_PHASE1_5_DESIGN.md (new)
common/docs/runtime/SESSION_HANDOFF.md                            (index update)
```

### 다음 단계

세 갈래 모두 가능:
- **Phase 2-4 (doc 12)**: TTS scanning helpers (`announce_class2_option`, `announce_class2_scanning_start`), MQTT input contract, Mac mini main-loop 통합. 본 PR의 manager API 위에 layer 추가.
- **Phase 1.5 구현 (doc 12 §14)**: `class2_scan_ordering_rules` 정책 + ranking step + comparison_condition prefix routing. 측정 후 추천.
- **이전 턴 대기 중인 두 항목**: TTS 머리말 trigger-aware 적응 (2-A) + 조명 state-aware (2-B). 둘 다 scanning과 무관하게 옳음. 진행 후 doc 12 Phase 2 (scanning TTS) 자연스러워짐.

추천 순서: **이전 턴 두 항목 (2-A, 2-B) → doc 12 Phase 2-3 → Phase 4 통합 → Phase 1.5 측정 후 결정**.

### Notes

- Authority boundary 변경 0.
- production 흐름 (default direct_select) 영향 0 — 새 기능 모두 opt-in.
- submit_selection 시그니처 그대로 — legacy 호출자 영향 0. scanning 호출자만 새 API 사용.
- 같은 dynamic-attr 패턴 사용 (PR #87/#102와 일관) — ClarificationSession dataclass 모델 변경 없음.
- Phase 1.5 design은 PR #101의 `class2_candidate_source_mode` 패턴을 mirror — 동일한 prefix-based comparison_condition 구조라서 paper-eval 비교 시 두 dimension (source × ordering) 독립 조작 가능.
