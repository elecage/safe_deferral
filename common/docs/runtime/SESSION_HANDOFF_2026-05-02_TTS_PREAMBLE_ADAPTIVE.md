# SESSION_HANDOFF — TTS Preamble Adaptive (Step 2-A)

**Date:** 2026-05-02
**Tests:** mac_mini 520/520 (was 516; +4 new in TestAnnounceClass2AdaptivePreamble). rpi 160/160 unchanged.
**Schema validation:** none modified.

**Plan baseline:** Step 2-A of the 3-step plan agreed in the 2026-05-02 conversation. Closes accessibility issue (1) — TTS announcing "보호자 확인이 필요합니다" even when the candidate set is user-resolvable lighting. Independent of scanning (doc 12); applies in direct_select mode and remains valid for the future scanning preamble work in doc 12 Phase 2.

---

## 이번 세션의 범위

PR #97의 verbatim invariant는 이미 잡혀 있었지만, **머리말은 모든 trial에서 같은 문구**였음:

```python
parts = ["보호자 확인이 필요합니다. 다음 중 선택해 주세요."]
```

문제: `insufficient_context` 후보 set은 (a) CLASS_1 조명 (b) CLASS_0 응급 (c) CAREGIVER (d) SAFE_DEFERRAL인데 — 이 중 (c)만 실제로 보호자 호출. 사용자가 "보호자 확인이 필요한 상황"이라고 듣고 → "조명을 켜드릴까요?"가 첫 옵션으로 나오면 인지 부조화.

C208 (방문자/도어락) 후보 set은 CAREGIVER + CLASS_0 + SAFE_DEFERRAL — CLASS_1 없음. 여기서는 "보호자 확인이 필요" 머리말이 맞음.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `mac_mini/code/tts/speaker.py` | `announce_class2()`가 candidate transition_target을 검사. **CLASS_1이 하나라도 있으면** → "어떻게 도와드릴까요? 다음 중 선택해 주세요." (사용자 본인이 해결 가능). **CLASS_1이 없으면** (C208/C207/all-caregiver-bound) → 기존 "보호자 확인이 필요합니다. 다음 중 선택해 주세요." 유지. 빈 candidate 리스트는 defensive하게 caregiver fallback. log line이 어느 머리말 사용했는지 표시. |
| `mac_mini/code/tests/test_tts_speaker.py` | 4 신규 테스트 (`TestAnnounceClass2AdaptivePreamble`): CLASS_1 있는 set → neutral 머리말, CLASS_1 없는 set → caregiver 머리말, all-SAFE_DEFERRAL → caregiver, verbatim invariant 보존. |

### 디자인 결정

- **transition_target 기반 판정** (trigger_id 기반 아님). 이유: caller가 trigger_id를 안 넘겨도 정확히 동작. 후보 set 자체가 의도를 표현하므로 self-contained.
- **"어떻게 도와드릴까요?"** = 중립적, 친근한 표현. 영어 권 시스템의 "What can I do for you?"에 가까움.
- **빈 candidate fallback은 caregiver** — defensive 안전. 후보가 없을 만큼 시스템이 모호하면 사용자가 직접 결정하기보다 보호자 개입이 안전.

### Boundary 영향

없음. 머리말 문구만 변경. 후보 권한 surface, validator, candidate generation 모두 그대로.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_tts_speaker.py -v
# 13 passed in 0.08s (was 9; +4 new)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 520 passed (was 516; +4 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 160 passed (unchanged)
```

테스트 커버:
- CLASS_1 후보 포함 set → "어떻게 도와드릴까요" 머리말, 옛 caregiver 문구는 부재
- CLASS_1 없음 (C208/C207 type) → "보호자 확인이 필요합니다" 머리말 유지
- All SAFE_DEFERRAL (degenerate but possible) → caregiver 머리말
- 머리말 변경에도 PR #97 verbatim invariant 보존 (각 candidate prompt가 발화에 들어감)

### Files touched

```
mac_mini/code/tts/speaker.py
mac_mini/code/tests/test_tts_speaker.py
common/docs/runtime/SESSION_HANDOFF_2026-05-02_TTS_PREAMBLE_ADAPTIVE.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (추천 순서대로)

- **2-B**: 조명 state-aware + "다른 동작" 옵션. `_DEFAULT_CANDIDATES`를 정적 dict에서 함수로 변경. `device_states.living_room_light` 보고 동적 prompt + action_hint 결정.
- **doc 12 Phase 2**: TTS scanning helpers (`announce_class2_option`, `announce_class2_scanning_start`).
- **doc 12 Phase 3**: MQTT input contract (`scan_response` 키).
- **doc 12 Phase 4**: Mac mini main-loop 통합.
- **(측정)** → **doc 12 Phase 1.5** deterministic ranking 구현.

### Notes

- doc 12 Phase 2 (scanning TTS)에서 머리말이 또 바뀜. 본 PR의 "어떻게 도와드릴까요?" / "보호자 확인이 필요합니다"는 direct_select용. scanning은 별도 함수 (`announce_class2_scanning_start`)에서 "질문을 하나씩 드리겠습니다. 예 / 아니오로 답해 주세요." 같은 안내. 두 layer는 충돌하지 않음.
- log line 갱신으로 audit/debug 시 어느 머리말이 사용됐는지 확인 가능.
