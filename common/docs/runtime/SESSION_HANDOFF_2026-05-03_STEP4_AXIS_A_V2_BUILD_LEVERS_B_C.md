# SESSION_HANDOFF — Step 4 (Axis A v2) Build — Levers B + C, Lever A Deferred

**Date:** 2026-05-03
**Tests:** mac_mini 720/720 (was 719, +1 prompt rule-9 regression guard); rpi 311/311 (was 306, +5 v2 matrix structural tests).
**Plan baseline:** [`PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md`](PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md) (updated in this PR — §1 scope reduction).
**Predecessor handoff:** [`SESSION_HANDOFF_2026-05-03_STEP4_AXIS_A_V2_QUEUED.md`](SESSION_HANDOFF_2026-05-03_STEP4_AXIS_A_V2_QUEUED.md) (PR #147, plan + queued).

**Trigger:** PR #147 plan called for Levers A + B + C in a single Step 4 PR. During implementation, the canonical `common/schemas/context_schema.json` was confirmed to NOT permit `user_state.inferred_attention` or `recent_events` (`additionalProperties: false`, only `trigger_event` / `environmental_context` / `device_states` declared). The plan's "no schema change" claim for Lever A was therefore wrong. Per CLAUDE.md ("Canonical policy/schema assets are not casual edit targets"), the user chose Option C: ship Levers B + C now and defer Lever A (schema extension + fixture/scenario v2 + prompt_builder field surfacing) to a separate Step 5 PR.

---

## 이번 세션의 범위

Step 4 코드/asset 변경 + plan doc scope 축소 + 본 핸드오프. v2 sweep 운영 전 build를 paper-honest하게 박는다 — **Lever A 가 슬쩍 빠진 것이 아니라 schema 전제 오류로 명시적으로 deferred** 되었음을 audit trail에 기록.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `mac_mini/code/local_llm_adapter/prompt_builder.py` | `_SYSTEM_HEADER`에 rule 9 추가 (Lever C). general-purpose guidance: "device_states / environmental_context를 명시적으로 활용; 충분한 신호 시 safe_deferral보다 actuator catalog 안의 행동을 우선 고려". 시나리오-특정 표현 없음. |
| `mac_mini/code/tests/test_local_llm_adapter.py` | `test_system_header_contains_context_use_guidance` regression guard 추가 (+1 test). |
| `integration/paper_eval/matrix_extensibility_v2.json` (신규) | v1 scenario/fixture 재사용, 3 cell × 30 trial. `_recommended_per_trial_timeout_s=480`, `_recommended_ollama_model=gemma4:e4b`, `_levers_active`, `_levers_deferred` 명시. expected_route_class/expected_validation는 v1과 동일. |
| `rpi/code/tests/test_paper_eval_sweep.py` | `TestExtensibilityMatrixV2` 추가 (+5 test): 로딩, v1 scenario 재사용, scenario-tag/policy-overrides check, expected가 v1과 일치, recommended timeout/model 검증. |
| `common/docs/runtime/PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md` | §1 scope 업데이트 — Lever A deferred 명시, schema 전제 오류 기록, timeout 240s → 480s 변경 근거 추가. |
| `common/docs/runtime/SESSION_HANDOFF_2026-05-03_STEP4_AXIS_A_V2_BUILD_LEVERS_B_C.md` (신규) | 본 핸드오프. |
| `common/docs/runtime/SESSION_HANDOFF.md` | index 업데이트. |

코드 변경: prompt_builder line 1줄 + 매트릭스 1개 신규 + 테스트 6개 신규. canonical policy/schema 변경 0.

### Lever 결정 (이번 PR 시점)

| Lever | 상태 | 근거 |
|---|---|---|
| **A — Fixture context enrichment** | **deferred to Step 5** | canonical `context_schema.json`의 `additionalProperties: false`가 `user_state` / `recent_events` 거부. schema 확장은 별 PR. |
| **B — gemma4:e4b** | **포함** | env-only 변경 (`OLLAMA_MODEL=gemma4:e4b`), 코드 무변경. matrix v2 README에 documented. |
| **C — Prompt rule 9** | **포함** | general-purpose 1줄, 시나리오-특정 표현 없음. paper-honest. |

### Timeout 결정

| 대상 | 값 | 근거 |
|---|---|---|
| v1 (llama3.2 3B) 원본 | 120s | 12 timeout 발생 |
| v1 README 추천 재실행 | 240s | llama3.2 기준 충분 |
| **v2 (gemma4:e4b 8B) 추천** | **480s** | 모델 크기 ~4×, 사용자 명시적 지시 ("gemma4 응답 속도 느림"). 240s × 2 = 안전 마진. |

### v2 Sweep 운영 절차 (구현 후, Step 4 PR 머지 후)

1. `~/smarthome_workspace/.env`에 `OLLAMA_MODEL=gemma4:e4b` 설정
2. `./scripts/local_e2e_launcher.sh` → healthy 대기. **첫 호출에서 gemma4:e4b 다운로드/로드 시간 별도** (모델 ~9.6 GB).
3. context_node + 2 actuator_simulator (living_room_light, bedroom_light) 생성
4. POST `/paper_eval/sweeps`:
   - `matrix_path=integration/paper_eval/matrix_extensibility_v2.json`
   - `per_trial_timeout_s=480`
5. dashboard 모니터링 → 완료 대기. **예상 wall time: ~1~2시간** (v1 대비 4× 모델 + 4× timeout 마진).
6. `runs_archive/2026-05-03_extensibility_axis_a_v2/`에 archive 생성:
   - v1 metrics 옆에 v2 metrics 비교 테이블
   - 모델 (gemma4:e4b), prompt 변경 (line 9), Lever A 부재 명시
7. **Regression check**: `matrix_smoke.json` + `matrix_phase_b.json`을 gemma4:e4b + new prompt로 재실행. 부작용을 v2 archive README에 기록.
8. v2 sweep 완료 후 `.env`을 `OLLAMA_MODEL=llama3.1`로 복귀 — llama3.2는 한글 표현 품질 문제로 default에서 제외. (v1 phase_c / extensibility_axis_a archive는 llama3.2 실행이라 historical reproducibility는 archive 자체에서만 유효.)

### Step 5 (Lever A) 향후 PR 스케치

별 PR로 분리. 변경 범위:

1. **Schema 확장** (`common/schemas/context_schema.json`):
   - `properties`에 `user_state` (object, optional) 추가 — 내부 `inferred_attention` enum (`engaged`, `transitioning`, `idle`)
   - `properties`에 `recent_events` (array, optional) 추가 — items: `{event_type, event_code, timestamp_ms}`
   - `required` 배열은 그대로 (새 필드는 optional)
2. **Intake validation**: 새 필드를 적절히 통과시키는지 확인 (대부분 자동)
3. **prompt_builder 확장**: `build_prompt`이 `user_state`와 `recent_events`를 prompt section에 surface
4. **v2 fixture 신규**: `sample_policy_router_input_extensibility_a_v2_richer_context.json` — `inferred_attention="engaged"` + `recent_events=[occupancy_motion_in_bedroom @ now-30s]`
5. **v2 scenario manifest 신규**: 새 fixture 참조, comparison_conditions 동일
6. **v3 matrix 신규**: `matrix_extensibility_v3.json` — 새 scenario 사용, gemma4:e4b + line 9 + 풍부한 context, per_trial_timeout_s=480
7. **테스트**: schema validation, prompt_builder가 새 필드를 surface하는지, v3 matrix 구조 invariant
8. v3 sweep 운영 → `runs_archive/2026-05-03_extensibility_axis_a_v3/`

### Step 4의 paper-evidence 디자인 (재확인)

PLAN §5의 세 outcome 시나리오 모두 paper-valid:

1. **v2 LLM pass ≫ v1 (60%+ vs 28%)**: Lever C가 효과적 → Lever C만으로 LLM recovery에 큰 영향 → §5.8 evidence 강화. (추후 Lever A를 더해도 marginal일 가능성을 측정.)
2. **v2 ≈ v1 (~28%)**: LLM의 deferral이 모델 capacity나 prompt doctrine 결과 → `01_paper_contributions §7.4` framing 강화 → Step 5 (Lever A)가 fixture 시그널이 진짜 차이를 만드는지 별도 측정.
3. **v2 < v1**: regression — Lever C 의심 → Step 5 진행 전 line 9 롤백 검토.

각 시나리오 모두 paper에 기여. **negative result도 valid evidence**.

### Anti-goals (재확인)

- v1 archive 무수정 (PR #146 그대로)
- canonical asset 변경 0 (이번 PR)
- Same scenario/fixture로 lever B+C만 변동 → v1↔v2 비교 깨끗
- gemma4:e4b는 `.env`에서만 활성, sweep 후 llama3.1로 복귀 (llama3.2는 한글 품질 문제로 default에서 제외)
- Regression check 필수 (matrix_smoke + matrix_phase_b)

### Files touched (이 PR)

```
mac_mini/code/local_llm_adapter/prompt_builder.py            (rule 9 added)
mac_mini/code/tests/test_local_llm_adapter.py                (+1 test)
integration/paper_eval/matrix_extensibility_v2.json          (new)
rpi/code/tests/test_paper_eval_sweep.py                      (+5 tests)
common/docs/runtime/PLAN_2026-05-03_AXIS_A_V2_RICHER_CONTEXT_AND_LARGER_MODEL.md  (§1 update)
common/docs/runtime/SESSION_HANDOFF_2026-05-03_STEP4_AXIS_A_V2_BUILD_LEVERS_B_C.md  (new)
common/docs/runtime/SESSION_HANDOFF.md                       (index update)
```

### Test plan (실행 결과)

```bash
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 720 passed in 43.35s (was 719 — +1 line-9 regression guard)

cd rpi/code && python -m pytest tests/ -q
# 311 passed in 14.11s (was 306 — +5 TestExtensibilityMatrixV2)
```

### 다음 단계

1. **이 PR 머지 후 v2 sweep 운영** (위 절차) → archive 생성 → side-by-side README
2. v2 결과 해석 후 Step 5 (Lever A schema 확장) 진행 여부 결정
3. (병렬 가능) backlog 진행:
   - Multi-turn recovery sweep (HIGH, paper integrity)
   - target-device-correctness metric → Axes B/C (MEDIUM, 큰 작업)
   - Item 2 fix (cancel partial) (MEDIUM, ops)
   - Temp/top_p sweep (LOW)
   - matrix_v1 retry (LOWEST)
   - doc 13 update (LOW, cosmetic)

### Notes

- **Schema 전제 오류는 audit trail에 명시 보존** — 이게 paper-honest. 그냥 schema를 슬쩍 늘려서 통과시키지 않은 이유: canonical asset 변경은 review가 분리되어야 함 (CLAUDE.md).
- v2 matrix가 `_recommended_per_trial_timeout_s`/`_recommended_ollama_model` 필드를 가진 이유: 운영자가 v1의 120s budget을 v2에 재사용하지 않도록 in-file documentation. 실제 timeout은 sweep POST 시점에 set.
- gemma4:e4b 첫 호출 시 모델 로드 latency 측정해서 archive README에 기록 (v1 llama3.2 ~11s와 비교).
