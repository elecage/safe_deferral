# SESSION_HANDOFF — TTS Selection Announcement Natural Phrasing (selection_label)

**Date:** 2026-05-02
**Tests:** mac_mini 711/711 (was 701; +10 new). rpi 235/235 unchanged.
**Schema validation:** none modified. Change is a TTS-side improvement; no canonical asset / dashboard contract change.

**Plan baseline:** Follow-up to user feedback: "사용자가 긴급상황인가요?를 선택하셨습니다" 같은 표현이 어색함. "사용자가 긴급 상황을 선택하셨습니다", "사용자가 조명 제어를 선택하셨습니다" 처럼 noun-phrase 사용이 자연스러움. 후보가 가진 prompt(질문문)와 별도로 짧은 noun-phrase label을 도입.

---

## 이번 세션의 범위

`announce_class2_selection`이 사용자가 선택한 후보의 **prompt(질문문)** 를 그대로 끼워넣어 발화하는 게 어색했음:
- 기존: "사용자가 '긴급상황인가요?'을(를) 선택했습니다."
- 개선: "사용자가 긴급 상황을 선택하셨습니다."

후보 dict + ClarificationChoice에 optional `selection_label` 필드 신규 추가. announce 시 label 우선 사용 + 한국어 조사(을/를) 자동 선택. label 없는 caller(LLM-생성 후보 등)는 기존 prompt-fallback 발화.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `mac_mini/code/tts/speaker.py` | `announce_class2_selection`에 optional `selection_label` 파라미터 신규. label 있으면 "{prefix} {label}{을/를} 선택하셨습니다." 형식; 없으면 기존 fallback. **`_korean_object_particle()` 헬퍼** 추가 — Hangul jongseong (받침) 검사로 을/를 자동 선택 (U+AC00..U+D7A3 범위 + (code-0xAC00) % 28 == 0 → 받침 없음 → 를). non-Hangul → 을(를) 폴백. "선택했습니다" → "선택하셨습니다" (honorific) 일관 사용. |
| `mac_mini/code/safe_deferral_handler/models.py` | `ClarificationChoice` dataclass에 `selection_label: Optional[str] = None` 필드 추가. backward-compat (default None). |
| `mac_mini/code/class2_clarification_manager/manager.py` | (1) `_state_aware_lighting_candidate`이 state-aware label도 생성 ("거실 조명 켜기" / "거실 조명 끄기"). (2) `_build_default_candidates`의 lighting C4 override가 prompt + label 둘 다 override ("다른 동작"). (3) `_DEFAULT_CANDIDATES`의 22개 entry 모두 `selection_label` 필드 추가 (긴급 상황 / 보호자 연락 / 대기 / 거실 조명 / 침실 조명 / 다시 시도 / 방문자 확인 요청 / 조명 제어). (4) `ClarificationChoice` 생성 시 `selection_label=item.get("selection_label")` 전달. |
| `mac_mini/code/class2_clarification_manager/refinement_templates.py` | `_state_aware_room_choice`도 state-aware label 생성 ("거실 조명 켜기" / "침실 조명 끄기" 등). multi-turn refinement (REFINE_LIVING_ROOM/BEDROOM)도 자연 발화. |
| `mac_mini/code/main.py` | 5개 `announce_class2_selection` 호출 사이트에 `selection_label=getattr(chosen, "selection_label", None)` 전달. caller가 label을 모르면 None — speaker 측 fallback이 처리. |
| `mac_mini/code/tests/test_tts_speaker.py` | 기존 `TestAnnounceClass2SelectionPromptVerbatim` → `TestAnnounceClass2SelectionFallback`로 rename (이제 fallback path 검증). 신규 `TestAnnounceClass2SelectionLabel` 5 테스트: label 형식 사용, jongseong → 을 / no jongseong → 를, caregiver prefix, 빈 label → fallback. |
| `mac_mini/code/tests/test_class2_clarification_manager.py` | 신규 `TestSelectionLabelPropagation` 5 테스트: 모든 trigger session의 모든 후보가 selection_label 가짐 (regression invariant), state-aware off → 켜기 label, on → 끄기 label, lighting C4 override → "다른 동작", non-lighting C4 → "대기" 유지. |

### 디자인 원칙

- **Optional 필드 + caller fallback**: `selection_label`은 dataclass에 default None. label 없는 후보(예: LLM-generated candidate가 label을 emit 하지 않은 경우)는 speaker 측에서 자동으로 legacy phrasing fallback. 점진적 도입 가능.
- **한국어 조사 자동**: noun이 받침으로 끝나면 을, 모음으로 끝나면 를. 운영자가 label 작성 시 신경 안 써도 자연 발화. non-Hangul 끝(예: "OK", "EMERGENCY")은 "을(를)" 폴백.
- **Honorific 일관성**: "선택했습니다" → "선택하셨습니다". 사용자 대상 발화는 존댓말 유지.
- **State-aware label**: prompt가 state-aware이면 label도 state-aware. 조명 ON 상태에서 "거실 조명 끄기" 선택했다고 발화 — UI 일관성.
- **Boundary 무영향**: schema / policy / topic 변경 0. ClarificationChoice의 새 필드는 schema 노출 (`to_schema_dict`)에 포함 안 됨 — 외부 contract 무변화. 내부 발화 표현만 개선.

### 비포 / 애프터 (실제 TTS 출력)

```
=== C201 insufficient_context (light off) ===
  candidate C1_LIGHTING_ASSISTANCE
    before: 사용자가 '거실 조명을 켜드릴까요?'을(를) 선택했습니다.
    after:  사용자가 거실 조명 켜기를 선택하셨습니다.
  candidate C3_EMERGENCY_HELP
    before: 사용자가 '긴급상황인가요?'을(를) 선택했습니다.
    after:  사용자가 긴급 상황을 선택하셨습니다.
  candidate C2_CAREGIVER_HELP
    before: 사용자가 '보호자에게 연락할까요?'을(를) 선택했습니다.
    after:  사용자가 보호자 연락을 선택하셨습니다.
  candidate C4_CANCEL_OR_WAIT (lighting C206 override)
    before: 사용자가 '다른 동작이 필요하신가요?'을(를) 선택했습니다.
    after:  사용자가 다른 동작을 선택하셨습니다.

=== C208 visitor doorlock-sensitive ===
  candidate C2_CAREGIVER_HELP (visitor variant)
    before: 사용자가 '보호자에게 방문자 확인을 요청할까요?'을(를) 선택했습니다.
    after:  사용자가 방문자 확인 요청을 선택하셨습니다.
```

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_tts_speaker.py tests/test_class2_clarification_manager.py -v
# 153 passed (TTS + Class 2 manager)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 711 passed (was 701; +10 new tests)

cd rpi/code && python -m pytest tests/ -q
# 235 passed (unchanged)
```

### Files touched

```
mac_mini/code/tts/speaker.py (announce_class2_selection + _korean_object_particle helper)
mac_mini/code/safe_deferral_handler/models.py (ClarificationChoice + selection_label)
mac_mini/code/class2_clarification_manager/manager.py (default candidates + propagation)
mac_mini/code/class2_clarification_manager/refinement_templates.py (state-aware refinement label)
mac_mini/code/main.py (5 caller sites pass selection_label)
mac_mini/code/tests/test_tts_speaker.py (renamed fallback test class + 5 new label tests)
mac_mini/code/tests/test_class2_clarification_manager.py (5 new propagation invariant tests)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_TTS_SELECTION_LABEL_NATURAL_PHRASING.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계

남은 P2 finding들로 복귀:
- `common/payloads/README.md` 누락 3개 파일 backfill
- scanning scenario 2개 ordering 태그 needs investigation
- `rpi/code/{main, governance, preflight, scenario_manager}` 전용 unit test 부재

### Notes

- LLM-생성 Class 2 후보는 현재 `selection_label`을 emit하지 않음 — 발화는 fallback path (prompt verbatim) 사용. 향후 LocalLlmAdapter의 `generate_class2_candidates` prompt에 label 필드 추가하고 schema 검증으로 enforce 가능 (별 PR 권장 — LLM 출력 형식 변경은 보수적으로).
- `_korean_object_particle`는 mixed Korean/English label에서 마지막 문자 기준으로만 판단. 예: "WiFi 연결" 같은 label은 마지막 "결" 받침 있음 → 을. 운영상 충분.
- `to_schema_dict` (ClarificationChoice.to_schema_dict)는 `selection_label`을 포함하지 않음 — 외부 schema contract (clarification_interaction_schema.json 등) 변경 없음. 내부 표현 개선만.
- Telegram inline keyboard label은 별도 path (caregiver-side); 이 PR 범위 밖.
