# SESSION_HANDOFF — Lighting State-Aware Candidates + "다른 동작" Safety Net (Step 2-B)

**Date:** 2026-05-02
**Tests:** mac_mini 531/531 (was 520; +11 new — 5 state-aware lighting, 2 other-action, 4 refinement state-aware). rpi 160/160 unchanged.
**Schema validation:** none modified (all changes flow through existing `pure_context_payload` argument; candidate_id and transition target unchanged).

**Plan baseline:** Step 2-B of the 3-step plan agreed in the 2026-05-02 conversation. Closes accessibility issue (3) — "조명 도움이 필요하신가요?" was unnatural Korean and ignored current lighting state. Also adds "다른 동작이 필요하신가요?" as the explicit safety net for "system assumed wrong action" (user's request after I asked about safety net).

---

## 이번 세션의 범위

PR #105가 머리말을 trigger-aware로 만들었지만, 후보 prompt 자체는 여전히 정적 hardcoded:
- "조명 도움이 필요하신가요?" — 부자연스러운 한국어
- `action_hint=light_on` 항상 — 조명이 켜져 있어도 "켜기"만 제안

본 PR은 후보 prompt + action_hint를 **device 현재 상태 기반으로 동적 생성**:
- `living_room_light=off` → "거실 조명을 켜드릴까요?" + `light_on`
- `living_room_light=on`  → "거실 조명을 꺼드릴까요?" + `light_off`

또한 사용자의 요청대로 **"다른 동작이 필요하신가요?"** 안전망 추가 — 시스템이 추측한 동작이 잘못됐을 때 사용자가 명시적으로 거부할 수 있는 옵션.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `mac_mini/code/class2_clarification_manager/manager.py` | `_LIGHTING_CANDIDATE_TARGETS` (candidate_id → device + room label) + `_LIGHTING_REASONS` (insufficient_context, missing_policy_input, unresolved_context_conflict) 정의. `_state_aware_lighting_candidate(item, device_states)` 헬퍼가 prompt + action_hint를 state 기반으로 override. `_build_default_candidates(reason, pure_context_payload)` 함수가 정적 dict 위에 state-aware override + lighting reason의 C4 prompt 변경 적용. `_build_choices`가 새 함수 사용. `start_session`이 `pure_context_payload`를 `_build_choices`에 넘기고 session에 stash. `submit_selection_or_refine`이 `get_refinement_template`에 payload 전달. |
| `mac_mini/code/class2_clarification_manager/refinement_templates.py` | `get_refinement_template(parent_id, pure_context_payload=None)`가 dynamic하게 state-aware refinement choices 생성. `_state_aware_room_choice` 헬퍼가 device state 보고 prompt + action_hint 결정. refinement_question은 generic ("어느 방의 조명을 도와드릴까요?")으로 — 각 옵션이 명시적 verb 보유. `_REFINEMENT_TEMPLATES` static export는 backward compat용 (off-state default). |
| `mac_mini/code/caregiver_escalation/telegram_client.py` | C4 caregiver label 변경: `"⏸ 취소 / 대기"` → `"⏸ 취소 / 다른 동작 / 대기"`. 같은 transition target에서 두 prompt 의미 모두 cover. comment로 dual semantic 명시. |
| `mac_mini/code/tests/test_class2_clarification_manager.py` | 11 신규 테스트 + 1 update. TestStateAwareLightingCandidates 5개 (off→켜기, on→끄기, no-payload-default, room별 독립 state, 옛 generic prompt 부재). TestOtherActionSafetyNet 2개 (lighting reason → 다른 동작, non-lighting → 취소 유지). TestRefinementTemplateStateAware 4개. PR #102 test_chosen_candidate_with_template_returns_refinement_session에서 refinement_question 새 문구로 update. |

### Backward compat 설계

- **candidate_id 모두 유지** (C1_LIGHTING_ASSISTANCE, OPT_LIVING_ROOM, OPT_BEDROOM, C4_CANCEL_OR_WAIT, REFINE_LIVING_ROOM/BEDROOM). 모든 기존 테스트 / 통합 fixture / Telegram label / audit가 candidate_id 기반이라 영향 없음.
- **transition target 모두 유지**. 호출 흐름 동일.
- **`pure_context_payload=None` legacy 호출자**: off-state 기본값 → "켜드릴까요?" + light_on. 기존 동작과 거의 동일 (단, prompt 문구만 자연스럽게 변경).
- **C4 prompt 변경은 lighting reason에서만**. 다른 reason (sensor_staleness, actuation_ack_timeout, timeout_or_no_response, caregiver_required_sensitive_path)에서는 "취소하고 대기할까요?" 그대로 유지 — 시스템이 특정 동작을 추측한 게 아니므로 "다른 동작" 의미 없음.

### Boundary 영향

없음. 후보 권한 surface, validator, dispatcher 모두 그대로. 모든 state-aware override는 canonical low-risk catalog 내 (`light_on`/`light_off` × `living_room_light`/`bedroom_light`).

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 531 passed (was 520; +11 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 160 passed (unchanged)
```

테스트 cover 항목:
- C1_LIGHTING_ASSISTANCE off → action_hint='light_on', prompt에 "거실" + "켜드릴까요"
- C1_LIGHTING_ASSISTANCE on → action_hint='light_off', prompt에 "꺼드릴까요"
- 정책 prompt cap (80자) 준수 — Phase 4 invariant 유지
- pure_context_payload 미제공 → off-state 기본값 (backward compat)
- OPT_LIVING_ROOM / OPT_BEDROOM 각 room state 독립 적용
- 옛 "조명 도움이 필요하신가요?" prompt 모든 trigger에서 부재 확인
- C4 prompt: lighting reason → "다른 동작이 필요하신가요?", non-lighting → "취소하고 대기할까요?"
- C4 candidate_id + transition target 변경 없음
- Refinement state-aware: room별 독립 state, no-payload backward compat, generic question
- PR #102 multi-turn test 1개 update (새 refinement_question 문구로)

### Files touched

```
mac_mini/code/class2_clarification_manager/manager.py          (state-aware helpers + plumbing)
mac_mini/code/class2_clarification_manager/refinement_templates.py (dynamic + state-aware)
mac_mini/code/caregiver_escalation/telegram_client.py          (C4 label dual-semantic)
mac_mini/code/tests/test_class2_clarification_manager.py       (+11 new, 1 updated)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_LIGHTING_STATE_AWARE_AND_OTHER_ACTION.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (추천 순서대로)

- **doc 12 Phase 2**: TTS scanning helpers (`announce_class2_option`, `announce_class2_scanning_start`).
- **doc 12 Phase 3**: MQTT input contract.
- **doc 12 Phase 4**: Mac mini main-loop 통합.
- **(측정)** → **doc 12 Phase 1.5** deterministic ranking 구현.

### Notes

- LLM-generated 후보는 본 PR의 state-aware override를 거치지 않음. LLM이 자체 state awareness를 가져야 함 (pure_context_payload에 device_states가 들어가므로 LLM prompt 컨텍스트로 활용 가능). 향후 phase: LLM action_hint를 state에 대해 validate하는 검증 단계 고려.
- `_REFINEMENT_TEMPLATES` static export는 PR #102 테스트 (TestRefinementTemplates의 invariant tests)와의 backward compat. 실제 production 흐름은 `get_refinement_template()` 함수 호출 사용.
- C4 Telegram label dual-semantic은 임시 절충안. 진짜 분리하려면 새 candidate_id (예: C5_OTHER_ACTION + class2_max_candidate_options 5로 증가) 도입 필요. paper-eval 측정 후 결정 가능.
