# SESSION_HANDOFF — doc 12 Class 2 Scanning Input Mode Design

**Date:** 2026-05-02
**Tests:** unchanged (design-only PR; no code).
**Schema validation:** none modified in this PR.

**Plan baseline:** Step 1 of the 3-step plan agreed in the 2026-05-02 conversation about Class 2 accessibility:
1. **doc 12 작성 (this PR)** — scanning input mode 디자인 문서.
2. **이전 턴 두 항목** — TTS 머리말 적응 PR + 조명 state-aware + "다른 동작" 옵션 PR (다음 라운드).
3. **doc 12 Phase 1 구현** — manager scanning state machine.

---

## 이번 세션의 범위

대화 중 사용자가 두 가지 접근성 문제를 제기:

1. TTS 머리말이 "보호자 확인이 필요합니다"인데 첫 옵션이 조명. 의미 불일치.
2. 중증 운동/인지 장애 사용자에게 N-way menu select은 부적절. AAC 분야의 scanning (옵션을 하나씩 yes/no) 패턴이 더 맞음.

(1)은 별도의 작은 PR (다음 단계). (2)는 새 interaction primitive라서 design 문서가 먼저 필요 — 이번 PR이 그것.

doc 12는 5개 design 질문에 권장 답을 baked-in으로 작성:

1. **per-option 시간 예산**: `class2_scan_per_option_timeout_ms = 8000` (8s). 4 옵션 × 8 = 32s. user phase 예산 부족분은 새 정책 곱셈자 `class2_scan_user_phase_extension = 1.5`로 흡수.
2. **침묵 의미**: 비최종 옵션 침묵 = `no` 자동 진행, 최종 옵션 침묵 = caregiver escalation. "silence ≠ consent" invariant 보존.
3. **back-up**: 1라운드에서는 단방향. 두 번째 attempt (`class2_max_clarification_attempts=2`)가 안전망.
4. **Mode flag**: `class2_input_mode = "direct_select" | "scanning"`, default `direct_select` (production 영향 0).
5. **MQTT 입력 contract**: 새 `scan_response` 키 (`{option_index, response}`). 기존 `selected_candidate_id`는 direct_select에서 그대로 유지. 두 키는 mutually exclusive. 옵션 index 불일치 응답은 race로 간주하고 drop.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/docs/architecture/12_class2_scanning_input_mode_plan.md` (신규) | 13 섹션 design 문서. Purpose, scope, non-negotiable boundaries, 5개 design 결정, data model (policy + ClarificationSession dynamic attrs + schema 확장), Manager API sketch, TTS pattern, MQTT contract, Phase split (1-5), 다른 진행 중 작업과의 관계 (PR #94/#101/#102 + 이전 턴 항목들), Phase 1 test plan, 미해결 질문, 출처 노트. |
| `common/docs/architecture/00_architecture_index.md` | doc 12를 active read order + roles 표에 추가. |
| `common/docs/runtime/SESSION_HANDOFF_2026-05-02_DOC12_SCANNING_INPUT_MODE_DESIGN.md` (신규) | 본 핸드오프. |
| `common/docs/runtime/SESSION_HANDOFF.md` | index 갱신. |

### 디자인 핵심

- **Scanning은 presentation primitive 변경**, 후보 set이나 권한 surface는 그대로.
- **두 mode 공존**, 제거 없음. direct_select가 빠르고 명확한 사용자에게 여전히 적합.
- **Phase 1 = manager state machine만**. TTS / MQTT / Mac mini main-loop는 Phase 2-4로 분리. 각 phase는 독립적으로 review 가능하고, scanning을 disable하면 전체 흐름 영향 0.
- **PR #102 multi-turn**과 자연스럽게 결합 — 두 flag 모두 on이면 refinement 턴도 새 scanning session으로 진행 (additional API 변경 0).
- **PR #101 LLM-vs-static**과 직교 — 후보 출처와 발화 방식은 별개 차원.
- **PR #94 trial timeout**에 영향 — `_class2_user_phase_timeout_s` 계산식이 scanning일 때 `× class2_scan_user_phase_extension`. Runner가 trial mode를 알아야 해서 Phase 4에서 처리.

### 미해결 (doc 12 §12)

1. 두 번째 attempt 시 첫 attempt의 silence vs explicit no를 어떻게 다룰지 (usability data 후 결정).
2. per-option 예산 가변(앞 옵션에 더 시간) vs 고정 — 측정 후 결정.
3. per-user mode override (운영 features) — 본 round 범위 밖, API에 hook 마련.
4. caregiver-side scanning — Telegram inline keyboard는 direct_select 유지 확인 필요 (Phase 4에서).

### Test plan

```bash
# 본 PR은 docs only. 모든 기존 테스트 변경 없이 통과.
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 499 passed (unchanged)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 160 passed (unchanged)
```

### Files touched

```
common/docs/architecture/12_class2_scanning_input_mode_plan.md (new)
common/docs/architecture/00_architecture_index.md
common/docs/runtime/SESSION_HANDOFF_2026-05-02_DOC12_SCANNING_INPUT_MODE_DESIGN.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계

- **2단계** (병렬 가능):
  - **2A**: TTS 머리말 적응 PR (작음). 후보 구성/trigger를 보고 caregiver-bound vs user-disambiguation 머리말 선택. PR #97 verbatim invariant 호환.
  - **2B**: 조명 state-aware + "다른 동작" 명시 옵션 PR (중간). `_DEFAULT_CANDIDATES`를 정적 dict에서 함수로 변경. `device_states.living_room_light` 보고 동적 prompt + action_hint. PR #102 refinement template 'C1_LIGHTING_ASSISTANCE'도 동시 갱신.

- **3단계**: doc 12 Phase 1 구현 — manager scanning state machine (`submit_scan_response`, `handle_scan_silence`), 정책 필드, 스키마 확장, 테스트. Production single-turn 영향 0 (feature flag default `direct_select`).

### Notes

- 본 PR은 design only. Maintainer가 5개 결정에 동의하지 않으면 재작성 후 다음 PR 진행.
- doc 12는 doc 11과 같은 형식 (Phase 0 design only → Phase 1+ 단계별 구현).
- Authority boundary 변경 0 (presentation 변경뿐).
