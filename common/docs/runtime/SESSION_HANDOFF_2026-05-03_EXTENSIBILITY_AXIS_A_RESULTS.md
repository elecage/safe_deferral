# SESSION_HANDOFF — Extensibility Axis A Operational Results + Step-2 Fixes

**Date:** 2026-05-03
**Tests:** mac_mini 719/719, rpi 306/306 unchanged from #145.
**PRs in this session:** code/asset fixes for the experiment design (this PR) + data archive (this PR).

**Plan baseline:** Step 3 of `PLAN_2026-05-02_PAPER_REFRAME_AND_OPEN_OPS_BACKLOG.md`. Operational sweep of `matrix_extensibility.json` (built in #145). Three fixture-level bugs surfaced during operation; this PR ships the fixes plus the third (successful) sweep's archive.

---

## 이번 세션의 범위

`required_experiments §5.8` Axis A의 첫 운영 sweep. `matrix_extensibility.json`을 launcher + dashboard로 실행. 3 sweep 시도 (앞 2개는 운영 중 design bug 노출 → cancel + 수정).

### 변경 요약

| 파일 | 변경 |
|---|---|
| `integration/tests/data/sample_policy_router_input_extensibility_a_novel_event_code.json` | (1) `_purpose` 필드 제거 — `policy_router_input_schema.json`의 `additionalProperties: false`가 거부했음 (sweep #1 90/90 timeout 원인). (2) `triple_hit` → `single_click` — policy router의 C206이 unrecognized button을 자동 escalation시키므로 (sweep #2 모두 CLASS_2 routing 원인) 유일하게 recognized된 single_click을 사용하고 differentiation을 context로 옮김. |
| `common/schemas/context_schema.json` | button event_code enum에 `quadruple_click` append (sweep #2 직전 한 번 사용 시도). 사용 안 하지만 schema에 남겨도 무해 (append-only). |
| `integration/paper_eval/matrix_extensibility.json` | 디자인 재설계 — per-cell expected로 변경. DIRECT_MAPPING + RULE_ONLY expected = CLASS_2 + safe_deferral ("이 input에서 mode가 정확하다면 defer"); LLM_ASSISTED expected = CLASS_1 + approved ("context-aware recovery"). matrix_description에 build path 명시 (앞 2 sweep의 lesson 영구 기록). |
| `integration/scenarios/extensibility_a_novel_event_code_bedroom_needed_scenario_skeleton.json` | description 업데이트 — single_click + context-driven design 설명. |
| `rpi/code/tests/test_paper_eval_sweep.py` | TestExtensibilityMatrix의 `test_per_cell_expected_encodes_mode_specific_correct_behaviour` — uniform expected 가정 폐기, per-cell mode-specific expected 검증으로 변경. |
| `integration/paper_eval/runs_archive/2026-05-03_extensibility_axis_a/` (신규 디렉토리) | sweep `5a28912087de`의 manifest + aggregated + digest CSV/MD + comprehensive README (build path + paper-relevant takeaways + limitations). |

### 운영 결과 (sweep `5a28912087de`, 36분)

| Cell | n | pass_rate | by_route | latency p50/p95 | 해석 |
|---|---:|---:|---|---:|---|
| EXT_A_DIRECT_MAPPING | 30/30 | **0%** | CLASS_1: 30 | 1ms | direct_mapping이 30/30 light_on living 발행 (이미 켜진 상태) — context blind를 측정값으로 입증 |
| EXT_A_RULE_ONLY | 30/30 | **100%** | CLASS_2: 30 | 0ms | rule이 자체 조건 미충족 인지 → safe_deferral. narrow heuristic의 안전 self-recognition |
| EXT_A_LLM_ASSISTED | 18/30 (12 timeout) | **27.8%** | CLASS_1: 5, CLASS_2: 13 | 11.4s/12.1s | 5 successful LLM trials 모두 `light_off living_room_light` 선택 — **state-aware toggle interpretation** |

### Paper-relevant 발견

1. **Context-blind vs context-aware**: direct_mapping은 30/30 모두 같은 action (light_on living, 이미 켜진 상태) — context 무시. LLM의 5 successful trials는 모두 `light_off living` (켜진 light을 토글) — **state를 읽고 다른 action 선택**. 이 contrast가 Contribution 1의 **perception scalability** 직접 evidence.
2. **Rule_only as safety baseline**: 100% safe-defer. 좁은 heuristic은 over-act 안 하는 면에서 우수, 그러나 user의 실제 intent 회복 불가.
3. **LLM은 free upgrade가 아님**: 11.4s p50 latency, 40% timeout (120s budget), 28% pass rate (Phase C의 96.6% 대비 큰 차이). **LLM의 가치는 anticipated 입력에서의 정확성이 아니라 unanticipated 입력에서의 robustness** — 정확히 paper §7.4의 "no speed claim" framing 입증.
4. **두 LLM 실패 mode**: (a) safe_deferral 자기 선택 (13/30), (b) Class 2 escalation 중 timeout (12/30). 후자는 per_trial_timeout=240s로 조정 시 회수 가능.

### Build path (sweep #1, #2의 design bug)

paper-honest라 archive README + matrix_description에 영구 기록:

1. **Sweep #1 `16289c7a1fd5`**: 90/90 timeout. 원인: fixture에 `_purpose` 문서 필드 추가 → schema validator 거부. 교훈: doc-side 필드는 canonical-schema-validated payload에 안전하지 않음.
2. **Sweep #2 `a35c64b3ebaa`**: 모든 trial CLASS_0 E002. 원인: `triple_hit`는 canonical panic-button trigger. `quadruple_click` 시도했지만 policy router's C206 (`recognized_class1_button_event_codes=['single_click']`)이 auto-escalation. 교훈: "novel button code"는 safety policy 자체에 의해 막혀서 differentiation 도구로 못 쓴다 — context-driven design이 답.
3. **Sweep #3 `5a28912087de` (이번 archive)**: single_click + 재설계 context + per-cell expected → 정상 측정 데이터 산출.

### Limitations (paper-honest)

- **Single axis only.** Axes B/C는 v2 — `pass_`가 target_device 정확성을 안 봐서 metric 확장 필요.
- **Per-cell expected encoding**: pass rate는 "mode가 자기 design intent대로 동작했나"이지 "modes가 같은 출력으로 수렴했나" 아님. paper text에서 명시 필요.
- **LLM hypothesis mismatch**: 가정은 "LLM이 bedroom 추론"이지만 실제로는 toggle-off living 선택. 둘 다 context-aware actuator-catalog 안 응답이라 scalability 주장은 유지. 단일 "correct" action 강제하는 시나리오 design은 future work.
- **per_trial_timeout 부족**: 120s가 LLM cell의 12 trial timeout 유발. 240s 권장.

### Boundary 영향

- **Schema 추가는 append-only**: button event_code enum에 `quadruple_click` (사용 안 했지만 schema에 남김), scenario_manifest category 3 라벨 (#145에서 추가) 모두 backward-compat.
- **canonical policy 무수정**.
- **dashboard / sweep_runner / mac_mini 코드 무수정.**

### Test plan

```bash
cd rpi/code && python -m pytest tests/ -q
# 306 passed (TestExtensibilityMatrix 4개 포함, per-cell expected 검증 업데이트됨)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 719 passed (manifest validator picks up new scenario)
```

### Files touched

```
integration/tests/data/sample_policy_router_input_extensibility_a_novel_event_code.json (modified — _purpose removed, event_code change)
common/schemas/context_schema.json (append quadruple_click to button enum)
integration/paper_eval/matrix_extensibility.json (per-cell expected redesign)
integration/scenarios/extensibility_a_novel_event_code_bedroom_needed_scenario_skeleton.json (description update)
rpi/code/tests/test_paper_eval_sweep.py (test redesigned for per-cell expected)
integration/paper_eval/runs_archive/2026-05-03_extensibility_axis_a/ (new — manifest + aggregated + digest + README)
common/docs/runtime/SESSION_HANDOFF_2026-05-03_EXTENSIBILITY_AXIS_A_RESULTS.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계

남은 PLAN backlog 우선순위 (사용자 결정):

1. **Multi-turn recovery sweep**: Phase C의 invalid 두 셀 회수, policy 임시 활성화 → 2 cells × 30 trials. paper integrity.
2. **per_trial_timeout 240s로 EXT_A_LLM_ASSISTED 단일 셀 재실행**: 12 timeout 회수 → LLM의 진짜 차세 분포 측정.
3. **Item 2 fix**: cancel partial preservation. ops 안정성.
4. **target-device-correctness metric** + Axes B/C build → 더 강한 paper Table Y.
5. **Temp/top_p sweep**: stochasticity 정량화 (보조 데이터).

### Notes

- LLM이 일관되게 `light_off living` 선택 (5/5)은 흥미로운 신호 — 이미 켜진 light에 대한 single_click을 토글로 해석. 이는 paper에서 "LLM은 state를 읽는다"는 양의 evidence.
- 5/30 pass rate는 paper에서 "context-aware recovery" 내러티브로 해석 가능, 단순 정확도 비교로는 약함. paper text가 by_route_class 분포와 함께 인용해야 강함.
- archive README는 paper draft에 직접 인용 가능하도록 self-contained로 작성 — runtime artifact + interpretation + limitations 모두 포함.
