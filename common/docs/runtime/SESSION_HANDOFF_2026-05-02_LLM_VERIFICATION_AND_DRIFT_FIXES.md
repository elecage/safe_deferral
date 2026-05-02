# SESSION_HANDOFF — Repo-Wide Verification + LLM-Path P0 Fix + sim_state_store Drift Fix

**Date:** 2026-05-02
**Tests:** mac_mini 701/701 (was 700; +1 regression test). rpi 235/235 unchanged. Real LLM (Ollama llama3.2) Class 1 fallback rate: 100% → 0% after fix.

**Plan baseline:** Follow-up to user request "전체 저장소 정합성 검토 + 코드 동작 검증 + LLM 호출 검증". The paper-eval toolchain (PRs #122–#127) was complete; this PR validates the rest of the system actually runs end-to-end with a real local LLM.

---

## 이번 세션의 범위

1. **전체 테스트 baseline 재확인** — mac_mini 700/700, rpi 235/235.
2. **저장소 정합성 검토** (general-purpose agent로 위임) — 7개 카테고리 (canonical asset / schema vs code / doc vs code / scenario / test coverage / dead code / boundary). P0 0개, P1 1개, P2 3개 발견. CLAUDE.md 모든 non-negotiable boundary 준수 확인.
3. **LLM 어댑터 실제 동작 검증** — Ollama llama3.2 (`http://localhost:11434/api/generate`)에 실제 호출. Class 1 path **100% fallback** P0 발견. Class 2 path 정상 (0/3 fallback).
4. **P0 fix + P1 fix 적용** + 회귀 테스트 추가.

### 발견된 이슈

#### P0 — Class 1 LLM path 100% fallback (production-blocking)

**증상**: `LocalLlmAdapter.generate_candidate(...)` 호출 시 Ollama llama3.2가 valid JSON을 반환하는데도 어댑터가 항상 `is_fallback=True`로 처리. 운영 환경에서 LLM 후보가 단 한 번도 채택되지 않음.

**원인 (1)**: LLM이 `light_on`/`light_off` 응답에 `deferral_reason: ""` (빈 문자열)을 함께 반환. `candidate_action_schema.json`의 `not.required: ["deferral_reason"]` 절이 light_on/off 액션에 deferral_reason 존재 자체를 거부하므로 검증 실패. 어댑터의 `_parse_and_validate`가 `None` 값만 strip하고 빈 문자열은 그대로 통과.

**원인 (2)**: `prompt_builder.py`의 `_SYSTEM_HEADER`가 출력 schema 예시에 `deferral_reason` 필드를 항상 포함시켜 LLM이 비어 있을 때도 채워서 반환하도록 유도.

**Fix**:
- `mac_mini/code/local_llm_adapter/adapter.py::_parse_and_validate` — `None` strip 로직을 빈 문자열까지 포함하도록 확장. docstring에 "왜 ""도 strip하나" 명시 (LLM verbosity + schema if/then 충돌이 production fallback 100% 유발한 사례).
- `mac_mini/code/local_llm_adapter/prompt_builder.py::_SYSTEM_HEADER` — 단일 schema 예시를 두 개 alternative (A: 조명 행동 — `deferral_reason` 필드 없음 명시; B: safe_deferral — `deferral_reason` 필수 enum 값)로 분리. 규칙 5에 "deferral_reason 필드는 절대로 포함하지 마세요 (빈 문자열도 안 됨)" 추가.

**검증** (Ollama llama3.2 실제 호출):
- Fix 전: Class 1 fallback 100% (5/5)
- adapter fix만: 40% (2/5)
- adapter + prompt fix: **0% (0/10)**

**Regression test**: `tests/test_local_llm_adapter.py::TestValidOutput::test_light_on_with_empty_deferral_reason_is_accepted` — `deferral_reason: ""`가 들어와도 LLM 후보가 채택되어야 함을 명시. Class 2 path는 영향 없음 (실제 LLM 호출에서 fallback 0/3).

#### P1 — `sim_state_store.DEVICE_FIELDS["tv_main"]` enum drift

**증상**: `rpi/code/sim_state_store.py:53` `DEVICE_FIELDS["tv_main"] = ["on", "off", "standby"]`이 `common/schemas/context_schema.json:158-167`이 허용하는 `["on", "off", "playing", "standby"]`과 불일치. `integration/tests/data/sample_policy_router_input_class2_insufficient_context.json:26`은 실제로 `"tv_main": "playing"` 사용 — get_state_snapshot이 노출하는 device_fields 메타데이터가 schema/실제 사용 contract을 잘못 광고.

**Fix**: `tv_main` enum에 `"playing"` 추가. update_device 자체는 permissive였으나 `device_fields` 노출이 UI/test consumer에게 잘못된 contract 전달 가능.

### 정합성 검토 결과 (요약)

| 카테고리 | 발견 |
|---|---|
| A. Canonical asset 참조 | No findings (P2: payloads README 3개 파일 누락 — 별건) |
| B. Schema vs code | **P1: tv_main 'playing' 누락** (이번 PR fix). doorlock/front_door_lock device_states 누수 없음 (test_context_intake에서 이미 거부 검증). |
| C. Doc vs code drift | No drift. doc 02/04/13 모두 코드와 일치. |
| D. 시나리오 contract | scanning 시나리오 2개에 ordering 태그 추가 가능 — needs investigation (별건). |
| E. 테스트 커버리지 | critical path (policy_router, validator, llm_adapter, class2 manager 등) 모두 커버. main.py / governance / preflight는 통합 테스트로 간접 커버. |
| F. Dead code / TODO / FIXME | clean — production .py 파일에 TODO/FIXME/XXX/HACK 0건. |
| G. Boundary 위반 | **No findings**. dashboard / governance가 operational control 발행 안 함. C208 doorlock-sensitive routing 정확히 enforce. RPi virtual node는 CLAUDE.md 허용 범위 내. |

### 변경 요약

| 파일 | 변경 |
|---|---|
| `mac_mini/code/local_llm_adapter/adapter.py` | `_parse_and_validate`: 빈 문자열도 strip. docstring에 production 100% fallback 사례 + 이유 기록. |
| `mac_mini/code/local_llm_adapter/prompt_builder.py` | `_SYSTEM_HEADER`: schema 예시를 두 alternative로 분리 + 규칙 5에 "deferral_reason 절대 포함 안 함" 추가. |
| `mac_mini/code/tests/test_local_llm_adapter.py` | +1 회귀 테스트 (`test_light_on_with_empty_deferral_reason_is_accepted`). |
| `rpi/code/sim_state_store.py` | `tv_main` enum에 `"playing"` 추가. |

### 디자인 원칙

- **Defensive parsing**: LLM이 schema에 정확히 맞춰 응답할 거라 가정하지 않음. 빈 문자열 = 필드 없음 (semantically equivalent to None) — 이 invariant는 candidate_action_schema의 if/then 절에 잘 매칭됨.
- **Prompt 명시성**: schema 예시 한 개 + 조건문보다 두 alternative 예시가 instruction-tuned 모델에 더 robust. 같은 정책을 prompt 명시 + adapter 검증 두 곳에서 enforce (defense in depth).
- **테스트 mock vs 실제 LLM 갭**: MockLlmClient는 빈 `deferral_reason`을 emit하지 않아서 production-only bug가 unit 테스트로 잡히지 않았음. 회귀 테스트는 실제 LLM이 emit하는 형태(`""`)를 mock으로 직접 주입.
- **Boundary 무영향**: schema / policy 수정 0. canonical asset 수정 0. 모든 변경은 LLM I/O 어댑터 + 시뮬레이터 메타데이터 수준.

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 701 passed (was 700; +1 regression test)

cd rpi/code && python -m pytest tests/ -q
# 235 passed (unchanged)

# Real LLM verification (requires Ollama running with llama3.2):
PYTHONPATH=mac_mini/code python -c "
from local_llm_adapter.adapter import LocalLlmAdapter
from local_llm_adapter.llm_client import OllamaClient
a = LocalLlmAdapter(llm_client=OllamaClient(model='llama3.2'))
ctx = {...}  # see handoff for full payload
fb = sum(1 for _ in range(10) if a.generate_candidate(ctx).is_fallback)
print(f'Class 1 fallback rate: {fb}/10')   # → 0/10 after fix
"
```

### Files touched

```
mac_mini/code/local_llm_adapter/adapter.py (modified)
mac_mini/code/local_llm_adapter/prompt_builder.py (modified)
mac_mini/code/tests/test_local_llm_adapter.py (+1 test)
rpi/code/sim_state_store.py (modified)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_LLM_VERIFICATION_AND_DRIFT_FIXES.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계

- **Operations**: Mac mini stack을 띄우고 실제 sweep 1회 실행해서 paper-eval matrix v1 variance 측정. 이 PR이 prerequisite (LLM이 실제로 동작해야 paper-grade 데이터 산출 가능).
- **Phase 4 (deferred)**: dashboard sweep-progress UI. 별건.
- **별건 P2 finding (이번 PR 범위 밖)**:
  - `common/payloads/README.md`에 3개 파일 누락 — 별 PR로 간단히 backfill.
  - scanning scenario 2개에 ordering 태그 보강 — needs investigation: matrix_v1.json cell 커버리지와 함께 검토.
  - `rpi/code/main.py` / `rpi/code/governance/{backend,ui_app}.py` / `rpi/code/preflight/` / `rpi/code/scenario_manager/` 전용 테스트 파일 부재 — 통합 테스트가 간접 커버하지만 단위 테스트 보강 가치 있음.

### Notes

- 이 PR은 **production 회귀를 막는 P0 fix가 핵심**. paper-eval matrix v1 sweep을 실제로 돌렸을 때 LLM-assisted Class 1 cell이 100% safe_deferral로 떨어져서 `direct_mapping` cell과 metric 차이가 0에 가까워지는 패턴이 나왔을 것.
- adapter `_parse_and_validate`의 strip 로직은 schema의 `additionalProperties: false`가 아니라 if/then 충돌 회피용. 새 optional 필드를 schema에 추가할 때 같은 패턴(빈 값 strip + 명시적 prompt 분기)이 필요함.
- prompt 두 alternative 분리는 instruction-tuned 모델의 알려진 약점(긴 조건문보다 명시적 예시 따라하기) 대응. gemma4 등 다른 모델로 교체 시 fallback rate 재측정 권장.
- LLM 호출 wall time: 1 call ≈ 1.5–4초 (Ollama llama3.2, M-series Mac). 10 calls 약 30초. paper-eval 12 cell × 30 trials sweep는 LLM 측만 고려해도 ~2시간 (sequential).
