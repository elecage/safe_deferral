# SESSION_HANDOFF — doc 12 Phase 4 Mac mini Main-Loop Scanning Wiring

**Date:** 2026-05-02
**Tests:** mac_mini 560/560 (was 552; +8 new in test_pipeline_class2_scanning.py — 5 input intercept, 3 scanning loop). rpi 160/160 unchanged.
**Schema validation:** none modified.

**Plan baseline:** doc 12 Phase 4 — final wiring round. Phase 1 (PR #104) added the manager state machine, Phase 2 (PR #107) added TTS scanning helpers, Phase 3 (PR #108) added the input adapter. This PR connects them in `mac_mini/code/main.py`. Production direct_select path unchanged (default policy `class2_input_mode='direct_select'`).

---

## 이번 세션의 범위

scanning이 정책에 켜졌을 때 실제로 작동하도록 main.py를 wire-up. 모드별 dispatch + 새로운 per-option loop method + button event interpretation 확장.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `mac_mini/code/main.py` | imports에 scanning helpers (`announce_class2_scanning_start`, `announce_class2_option`) + adapter constants/함수. **`_handle_class2`** dispatches by `session.input_mode`: scanning이면 `announce_class2_scanning_start` + `_await_user_scanning_then_caregiver` 호출, 아니면 기존 `announce_class2` + `_await_user_then_caregiver`. **Phase 2 caregiver code 추출** → `_run_caregiver_phase(session, trigger_id, audit_id, entry, caregiver_event)` method. 직접-선택 / scanning 두 path 모두 재사용. **`_await_user_scanning_then_caregiver`** 신규 method: per-option loop (announce → wait per_option_timeout → translate scan_decision → submit_scan_response/handle_scan_silence → terminal Class2Result OR advance). triple_hit emergency shortcut 즉시 처리. 모든 옵션 거부 시 `_run_caregiver_phase` 호출 (caregiver가 override 가능). **`_try_handle_as_user_selection`** scanning branch 추가: entry['input_mode']=='scanning' AND phase==1이면 `interpret_button_event_for_scan` 호출, decision을 entry['scan_decision']에 저장 + user_event signal. 직접-선택 path는 1줄도 안 변경. |
| `mac_mini/code/tests/test_pipeline_class2_scanning.py` (신규) | 8 신규 테스트. **TestTryHandleAsUserSelectionScanning 5개** (single_click → submit yes, double_click → submit no, triple_hit → emergency, unknown → ignore but consume, 직접-선택 path 회귀 테스트). **TestAwaitUserScanningThenCaregiver 3개** (yes-first → terminal CLASS_1 + no caregiver, all silence → 모든 옵션 후 caregiver phase 호출, triple_hit emergency → 즉시 종료 + no caregiver). 외부 의존성 (Telegram, transition execution, telemetry) 모두 mock. |

### 디자인 결정

- **Phase 2 추출만 함**, Phase 1 direct-select는 그대로. 회귀 위험 최소화. `_run_caregiver_phase`는 양 모드 모두 사용 — caregiver가 scanning에서도 사용자가 거부한 옵션을 override 가능.
- **scanning Phase 1은 별도 method**. direct-select Phase 1과 구조가 본질적으로 다름 (single wait vs per-option loop). 두 method가 짧고 읽기 쉬움이 우선.
- **`entry["input_mode"]` marker**. `_try_handle_as_user_selection`이 어느 branch로 갈지 결정. dynamic attr이 아니라 entry dict의 explicit key — 명확함.
- **Emergency shortcut 즉시 종료**. triple_hit은 응급 의도이므로 caregiver phase 거치지 않고 바로 CLASS_0 transition. direct-select와 동일한 결과 보장.
- **`_run_caregiver_phase` 호출 가능성**. 사용자가 모든 옵션 거부 (final no/silence)한 경우에도 caregiver가 CLASS_1를 승인 가능. 즉, 사용자 거부 ≠ 자동 deferral. caregiver judgment이 final.

### Boundary 영향

없음. 정책 default `class2_input_mode='direct_select'`라서 production 흐름 변경 0. scanning 활성화는 deployment-side 결정. 모든 scanning path가 기존 deterministic validator / dispatcher / caregiver 경로를 거침.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_pipeline_class2_scanning.py -v
# 8 passed in 8.75s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 560 passed (was 552; +8 new)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 160 passed (unchanged)
```

테스트 커버:
- single_click → entry['scan_decision'] = ('submit', current_option_index, 'yes'), user_event signaled
- double_click → ('submit', i, 'no')
- triple_hit → ('emergency', CLASS_0_candidate_id)
- 알 수 없는 event_code → consume but no decision/event signal (블록만)
- 직접-선택 path 영향 없음 (entry에 input_mode 없으면 legacy single_click → first candidate logic)
- yes-first scanning loop → terminal Class2Result + execute_class2_transition + caregiver phase 호출 안 됨
- all silence scanning loop → caregiver phase 호출됨 (silence ≠ consent)
- emergency shortcut → 즉시 CLASS_0 terminal + caregiver phase 호출 안 됨

### Files touched

```
mac_mini/code/main.py                                              (Phase 4 wiring)
mac_mini/code/tests/test_pipeline_class2_scanning.py              (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_DOC12_PHASE4_MAIN_LOOP_WIRING.md (new)
common/docs/runtime/SESSION_HANDOFF.md                            (index update)
```

### doc 12 완료 상황

- ✅ Phase 1 (PR #104) — manager state machine
- ✅ Phase 2 (PR #107) — TTS scanning helpers
- ✅ Phase 3 (PR #108) — scan input adapter + corrected MQTT contract doc
- ✅ Phase 4 (this PR) — Mac mini main-loop wiring
- ⏭ Phase 1.5 (deferred) — deterministic ranking heuristics (측정 후)
- ⏭ Phase 5 (out of scope this round) — scenario fixture variant for paper-eval

scanning mode가 정책 flag만 켜면 end-to-end 작동. Phase 1.5 측정 데이터 모은 후 ordering 개선 가능.

### Notes

- 수동 테스트 (deployment 시): `policy_table.global_constraints.class2_input_mode = "scanning"` 설정 → Mac mini 재시작 → CLASS_2 trigger 시 sequential yes/no 발화 확인 + button event 응답 정상 작동.
- direct-select / scanning 모드 전환은 정책만 변경하면 됨 (코드 / 시나리오 / 노드 변경 없음).
- Phase 1.5 ordering 구현 시 scanning loop 자체는 변경 불필요 — manager가 이미 ordered candidate set을 제공하기 때문.
- 별도로 Phase 5 (PR F-style scenario condition `class2_scanning_input_mode` vs `class2_direct_select_mode`)가 paper-eval 비교 시 필요. Phase 1.5와 함께 land 가능.
