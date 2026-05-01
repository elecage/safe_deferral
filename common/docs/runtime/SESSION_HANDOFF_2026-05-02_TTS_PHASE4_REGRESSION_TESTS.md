# SESSION_HANDOFF — TTS Phase 4 Regression Tests (verbatim prompt + policy cap)

**Date:** 2026-05-02
**Tests:** 478/478 mac_mini fast suite (was 469; +9 new TTS regression cases). rpi unchanged (149/149).
**Schema validation:** policy_table.json parses cleanly; cap value loaded by tests.

**Plan baseline:** Closes the only open item in `09_llm_driven_class2_candidate_generation_plan.md` Phase 4 — "add a regression test that the announced text equals the candidate's prompt and that prompt length ≤ the policy cap." Phases 1-3 (PRs #87, #88) and Phase 5 (PR #89) already shipped; Phase 4 itself was free-of-code (the speaker already reads `candidate.prompt`), so all that remained was the regression net.

---

## 이번 세션의 범위

LLM-driven Class 2 candidate generation의 conversational layer는 Phase 1-3 이후 자동으로 활성화됨 (`tts/speaker.announce_class2()`가 `candidate.prompt`를 그대로 발화). 하지만 다음 두 invariant가 무방비 상태였다:

1. **Verbatim 발화** — 어떤 변환/잘림/재템플릿도 없이 candidate prompt가 announced text에 그대로 들어가는지.
2. **정책 cap 준수** — `_DEFAULT_CANDIDATES` static fallback의 모든 prompt가 `policy_table.global_constraints.class2_conversational_prompt_constraints.max_prompt_length_chars` (현재 80자) 이내인지. LLM rejection 후의 fallback도 정책을 위반하지 않는다는 안전망.

본 PR은 새 테스트 모듈 `mac_mini/code/tests/test_tts_speaker.py`를 추가만 함. 코드/정책 변경 없음.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `mac_mini/code/tests/test_tts_speaker.py` (신규) | 4 클래스, 9 테스트. Verbatim + 순서, 빈 리스트 fallback, NoOpSpeaker 안전성, post-selection prompt echo, 정책 cap 준수, deferral 발화 sanity. 정책 파일을 직접 로드해 cap 값을 dynamic하게 읽으므로 정책 수정 시 자동 추적. |

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/test_tts_speaker.py -v
# 9 passed in 0.08s

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 478 passed in 33.71s   (was 469 before)
```

`test_pipeline.py`는 Ollama 로컬 실행으로 인한 기존 slowness 이슈로 fast suite에서 계속 제외 (이전 PR들과 동일 운영).

### Single source of truth (확인)

- 정책 cap = `common/policies/policy_table.json :: global_constraints.class2_conversational_prompt_constraints.max_prompt_length_chars` — 코드/테스트 어디에도 hardcoded value 없음 (PR #88에서 확립한 패턴 그대로 따름).
- Adapter가 LLM 출력을 cap으로 reject → manager가 `_DEFAULT_CANDIDATES`로 fallback → speaker가 prompt를 그대로 발화. 모든 단계의 prompt가 같은 cap을 만족하므로 fallback 경로 자체가 정책 위반을 일으키지 않는다는 invariant를 테스트가 보호.

### Files touched

```
mac_mini/code/tests/test_tts_speaker.py (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_TTS_PHASE4_REGRESSION_TESTS.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### Out of scope (next from the menu)

다음 작업 후보 (1, 3, 2 순서로 합의):
- ✅ #1 Phase 4 회귀 테스트 (this PR)
- ⏭ #3 Virtual node modal에 `simulated_response_timing_ms` 필드 추가 (PR #96의 fidelity 마무리)
- ⏭ #2 Trial detail UI (per-trial `class2_phase_budgets_snapshot` 노출)
