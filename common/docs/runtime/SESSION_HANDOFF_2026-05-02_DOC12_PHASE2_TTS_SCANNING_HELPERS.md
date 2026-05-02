# SESSION_HANDOFF — doc 12 Phase 2 TTS Scanning Helpers

**Date:** 2026-05-02
**Tests:** mac_mini 540/540 (was 531; +9 new — 3 scanning_start, 5 option, 1 composition flow). rpi 160/160 unchanged.
**Schema validation:** none modified.

**Plan baseline:** doc 12 Phase 2 per the recommended order. Phase 1 (PR #104) added the manager scanning state machine; this PR adds the TTS layer that Phase 4 main-loop wiring will call. Production behaviour unchanged — these helpers are not invoked anywhere yet (default `class2_input_mode = direct_select`).

---

## 이번 세션의 범위

doc 12 §7에서 sketch한 두 TTS 함수 구현 + 단위 테스트. Mac mini main-loop는 아직 손대지 않음 (Phase 4 작업).

### 변경 요약

| 파일 | 변경 |
|---|---|
| `mac_mini/code/tts/speaker.py` | 신규 `announce_class2_scanning_start(speaker, total_options)` — scanning 세션 시작 시 한 번 발화. "질문을 하나씩 드리겠습니다. 총 N개입니다. 예 또는 아니오로 답해 주세요." 형식. total_options=0 fallback은 caregiver-bound message. 신규 `announce_class2_option(speaker, option_index, candidate, total_options)` — per-option 발화. 형식: `{n}/{N}. {candidate.prompt}` (1-based n). PR #97 verbatim invariant 보존 (각 발화에 candidate.prompt 그대로 포함). |
| `mac_mini/code/tests/test_tts_speaker.py` | import에 두 새 함수 추가. 9 신규 테스트 (TestAnnounceClass2ScanningStart 3, TestAnnounceClass2Option 5, TestScanningTTSCompositionFlow 1). |

### 디자인 결정 (doc 12 §7 그대로)

- **`{n}/{N}.` position cue**: 사용자가 "이 옵션이 마지막인지"를 알 수 있어 답변 결정에 도움. 1-based로 표시 (option_index는 내부적으로 0-based).
- **per-option 발화는 단순**: yes/no 힌트는 start 발화에서 한 번만 (반복하면 cognitive load ↑).
- **start preamble은 한 번**: 매 옵션마다 "예 / 아니오로 답해 주세요" 안 함. start preamble로 모드 설명, 이후엔 질문만.
- **prompt verbatim**: PR #97 invariant 그대로. announce_class2가 한 번에 다 말하던 prompt들이 이제 한 발화당 하나씩 나옴.
- **defensive 0-fallback**: total_options=0이면 caregiver-bound 메시지. silence ≠ consent invariant 보존.

### Boundary 영향

없음. TTS layer만 변경. Manager / validator / dispatcher 모두 그대로.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_tts_speaker.py -v
# 22 passed (was 13; +9 new)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 540 passed (was 531; +9 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 160 passed (unchanged)
```

테스트 cover 항목:
- scanning_start: total count + 예/아니오 hint 발화, total_options=0 → caregiver fallback, NoOpSpeaker 안전
- option: `{n}/{N}.` 형식, 1-based 변환, candidate.prompt verbatim, invalid inputs → ValueError, NoOpSpeaker 안전
- composition flow: 1 preamble + N options 순서대로, 각 발화에 올바른 position cue + prompt

### Files touched

```
mac_mini/code/tts/speaker.py
mac_mini/code/tests/test_tts_speaker.py
common/docs/runtime/SESSION_HANDOFF_2026-05-02_DOC12_PHASE2_TTS_SCANNING_HELPERS.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (추천 순서대로)

- **doc 12 Phase 3**: MQTT input contract — `bounded_input_node`에 `scan_response = {option_index, response}` 키 추가, mutually exclusive with 기존 `selected_candidate_id`.
- **doc 12 Phase 4**: Mac mini main-loop 통합 — `_handle_class2`가 `session.input_mode` 따라 분기, scanning이면 본 PR의 helpers 사용.
- **(측정)** → **doc 12 Phase 1.5** deterministic ranking 구현.

### Notes

- 본 PR의 두 함수는 production에서 호출되지 않음 (Phase 4 wiring 전). 그래서 production 동작 변화 0.
- `announce_class2_option`이 `option_index`를 받지만 candidate 자체에서도 추출 가능. Phase 4에서 callers가 일관되게 0-based session.current_option_index를 넘기도록 — Phase 1 manager API와 정렬.
- 추후 Phase 1.5 deterministic ranking 적용 시 후보 순서가 달라져도 본 PR helpers는 그대로 작동 (presentation 책임만 가짐, ordering은 매개 안 함).
