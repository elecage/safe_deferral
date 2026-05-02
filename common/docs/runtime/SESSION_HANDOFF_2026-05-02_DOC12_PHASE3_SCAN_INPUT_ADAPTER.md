# SESSION_HANDOFF — doc 12 Phase 3 Scan Input Adapter

**Date:** 2026-05-02
**Tests:** mac_mini 552/552 (was 540; +12 new in TestScanInputAdapter). rpi 160/160 unchanged.
**Schema validation:** none modified — actual MQTT payload schema unchanged. doc 12 §8 corrected to reflect reality.

**Plan baseline:** doc 12 Phase 3 per the recommended order. Phase 1 (PR #104) added the manager state machine; Phase 2 (PR #107) added TTS helpers; this PR adds the input-event interpreter Phase 4 will wire into the Mac mini main loop. Production behaviour unchanged.

---

## 이번 세션의 범위

doc 12 §8의 원래 sketch가 부정확했음 — `selected_candidate_id` payload field가 idealized였음. 실제 input contract는 button events in `pure_context_payload.trigger_event`. doc 12 §8을 수정 + Phase 3 adapter 구현.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/docs/architecture/12_class2_scanning_input_mode_plan.md` | §8 전면 재작성. §8.1 reality check (실제 payload 구조), §8.2 scanning event 해석 표 (single_click/double_click/triple_hit/silence/other), §8.3 adapter helper 설명, §8.4 새 schema field 도입하지 않은 이유 (input nodes mode-agnostic 유지, race surface 없음, backward-compat 부담 없음). |
| `mac_mini/code/class2_clarification_manager/scan_input_adapter.py` (신규) | 순수 함수 모듈. `interpret_button_event_for_scan(event_code, session) → ScanInputDecision`. 결정 종류: `submit` (option_index + yes/no), `emergency` (CLASS_0 candidate_id), `ignore` (reason). Mac mini main-loop가 호출만 하면 됨 — 어떤 mutation도 없음. |
| `mac_mini/code/tests/test_scan_input_adapter.py` (신규) | 12 테스트. single_click → yes, double_click → no, triple_hit → first CLASS_0 (or ignore if 없음), 알 수 없는 event_code → ignore (reason 포함), 어댑터 순수성 (session 변경 없음). parametrize로 5개 알 수 없는 code 검증. |

### 디자인 결정 (doc 12 §8 새 버전)

- **MQTT schema 미변경**. 입력 노드 (esp32.bounded_input_node, RPi virtual)는 mode-agnostic — 그저 button event 발행. 모드별 해석은 Mac mini의 책임.
- **Single-switch 사용자 fully supported**. 단일 single_click + silence(timeout)만으로 모든 옵션 yes/no 가능.
- **Double-switch 사용자 가속**. double_click으로 명시적 "no" → timeout 8초 기다릴 필요 없음.
- **Race surface 없음**. option_index를 payload에 넣지 않음. Mac mini가 receipt time에 `session.current_option_index`를 읽음. 단일 thread of truth.
- **Triple_hit 응급 shortcut 보존**. 직접-선택과 동일 — scanning에서도 emergency 의도가 빠르게 작동.
- **순수 함수 어댑터**. main-loop / MQTT 결합 없음 → Phase 4 wiring이 mechanical, 단위 테스트가 전체 매핑 표를 망설임 없이 cover.

### Boundary 영향

없음. Mac mini main-loop 변경 없음 (Phase 4 작업). 어댑터는 호출되지 않음 → production 영향 0.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_scan_input_adapter.py -v
# 12 passed in 0.04s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 552 passed (was 540; +12 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 160 passed (unchanged)
```

테스트 cover 항목:
- single_click (current_option_index 변경에 따른 정확한 routing)
- double_click → "no"
- triple_hit → 첫 CLASS_0 candidate (없으면 ignore)
- triple_hit이 여러 CLASS_0 중 첫 번째 deterministic 선택
- 5종 알 수 없는 event code → ignore + reason
- 어댑터가 session을 mutate하지 않음 (purity)

### Files touched

```
common/docs/architecture/12_class2_scanning_input_mode_plan.md     (§8 재작성)
mac_mini/code/class2_clarification_manager/scan_input_adapter.py   (new)
mac_mini/code/tests/test_scan_input_adapter.py                     (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_DOC12_PHASE3_SCAN_INPUT_ADAPTER.md (new)
common/docs/runtime/SESSION_HANDOFF.md                             (index update)
```

### 다음 단계

- **doc 12 Phase 4**: Mac mini main-loop 통합. `_handle_class2`가 `session.input_mode` 따라 분기. scanning이면 (a) `announce_class2_scanning_start` + per-option loop with `announce_class2_option`, (b) `interpret_button_event_for_scan` 사용해 button events를 manager API 호출로 변환, (c) per-option timer가 silence → `handle_scan_silence`. 가장 큰 PR — main-loop 두 phase wait 구조를 일반화 필요.
- **(측정)** → **doc 12 Phase 1.5** deterministic ranking 구현.

### Notes

- 실제 운영에서 single-switch user가 가장 흔한 시나리오 — single_click + silence-as-no가 핵심 path. double_click은 secondary.
- triple_hit emergency shortcut은 두 모드 모두에서 작동하므로, 응급 상황 reaction time이 scanning mode에서도 늘어나지 않음 (per-option loop 거치지 않고 즉시 CLASS_0).
- 어댑터를 main-loop와 분리한 가장 큰 이점: Phase 4 코드 검토가 "wire-up correctness"만 보면 되고, "mapping rules correctness"는 본 PR의 12개 테스트가 보장.
